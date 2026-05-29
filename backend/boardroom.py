"""
Boardroom orchestrator — runs all 5 C-suite agents in sequence and streams events
to an asyncio.Queue that the SSE endpoint reads from.

Pipeline:
  Phase 1 (CEO): problem_extractor → option_generator → option_evaluator → best_solution_selector
  Phase 2 (execs): cfo → coo → cmo → cto  (sequential so SSE animates one exec at a time)
  Phase 3: boardroom_synthesis
"""
import asyncio
import json
import os

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from backend import sse_events as ev
from backend.agents.ceo_agent import (
    problem_extractor,
    option_generator,
    option_evaluator,
    best_solution_selector,
    stream_ceo_opening,
)
from backend.agents.cfo_agent import CFOAgent
from backend.agents.coo_agent import COOAgent
from backend.agents.cmo_agent import CMOAgent
from backend.agents.cto_agent import CTOAgent
from backend.models import (
    BoardroomState,
    BoardroomSynthesis,
    ConsensusItem,
    DissentItem,
    ExecEvaluation,
    Option,
    Problem,
)


# ---------------------------------------------------------------------------
# Synthesis node
# ---------------------------------------------------------------------------

def _synthesis_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0.2,
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )


async def _synthesize_boardroom(
    problem: Problem,
    options: list[Option],
    ceo_recommendation,
    cfo_eval: ExecEvaluation,
    coo_eval: ExecEvaluation,
    cmo_eval: ExecEvaluation,
    cto_eval: ExecEvaluation,
) -> BoardroomSynthesis:
    llm = _synthesis_llm().with_structured_output(BoardroomSynthesis)

    exec_summaries = []
    for eval_ in [cfo_eval, coo_eval, cmo_eval, cto_eval]:
        scores = [
            {"option": s.option_name, "weighted_score": s.weighted_score, "vetoes": s.vetoes}
            for s in eval_.option_scores
        ]
        exec_summaries.append({
            "role": eval_.role,
            "preferred_option": eval_.preferred_option,
            "veto_options": eval_.veto_options,
            "key_concern": eval_.key_concern,
            "scores": scores,
        })

    ceo_summary = {
        "role": "CEO",
        "preferred_option": ceo_recommendation.chosen_option,
        "reason": ceo_recommendation.reason,
        "dissenting_concern": ceo_recommendation.dissenting_concern,
    }

    options_list = [{"name": o.name, "summary": o.summary} for o in options]

    messages = [
        SystemMessage(content=(
            "You are the chair of a C-suite boardroom meeting. Your role is to synthesize the "
            "perspectives of five executives (CEO, CFO, COO, CMO, CTO) into a clear, actionable "
            "board resolution. Identify where the board agrees, where it disagrees, and deliver "
            "a final recommendation with any conditions attached. Be decisive. The board must leave "
            "the room with a clear direction."
        )),
        HumanMessage(content=(
            f"Decision: {problem.actual_decision}\n\n"
            f"Options on the table:\n{json.dumps(options_list, indent=2)}\n\n"
            f"CEO position:\n{json.dumps(ceo_summary, indent=2)}\n\n"
            f"Other executive evaluations:\n{json.dumps(exec_summaries, indent=2)}\n\n"
            "Synthesize these perspectives into a BoardroomSynthesis:\n"
            "- final_recommendation: The option the board is committing to (one option name)\n"
            "- consensus_items: Options or concerns where 3+ executives agreed\n"
            "- dissent_items: Where specific executives dissented and how it was resolved\n"
            "- conditions: Conditions this recommendation carries (what must be true for it to hold)\n"
            "- synthesis_narrative: A 3-4 sentence closing statement from the board chair"
        )),
    ]
    return await llm.ainvoke(messages)


# ---------------------------------------------------------------------------
# Main boardroom runner (async, writes to SSE queue)
# ---------------------------------------------------------------------------

async def run_boardroom(situation: str, session_id: str, queue: asyncio.Queue) -> None:
    try:
        # ------------------------------------------------------------------
        # Phase 1: CEO pipeline — each node runs separately so SSE events
        # flow between calls and the connection stays alive.
        # ------------------------------------------------------------------
        await queue.put(ev.phase_start(1, "Problem Analysis & Option Generation"))

        state: BoardroomState = {"situation": situation, "session_id": session_id}

        # Node 1: Extract the real decision (~15s)
        await queue.put(ev.node_start("CEO", "problem_extractor", "Extracting the real decision..."))
        state.update(await asyncio.to_thread(problem_extractor, state))
        await queue.put(ev.node_complete("CEO", "problem_extractor", state["problem"].model_dump()))

        # Node 2: Generate options (~20s)
        await queue.put(ev.node_start("CEO", "option_generator", "Generating strategic options..."))
        state.update(await asyncio.to_thread(option_generator, state))
        await queue.put(ev.options_ready([o.model_dump() for o in state["options"]]))

        # Node 3: Evaluate options across rubric (~25s)
        await queue.put(ev.node_start("CEO", "option_evaluator", "Scoring options across all dimensions..."))
        state.update(await asyncio.to_thread(option_evaluator, state))

        # Node 4: Select best (instant — local logic only)
        await queue.put(ev.node_start("CEO", "best_solution_selector", "Selecting recommendation..."))
        state.update(best_solution_selector(state))

        problem = state["problem"]
        options = state["options"]
        ceo_evaluations = state["ceo_evaluations"]
        ceo_recommendation = state["ceo_recommendation"]

        # Stream CEO opening statement
        await queue.put(ev.node_start("CEO", "opening", "CEO opening statement..."))
        async for chunk in stream_ceo_opening(problem, options):
            await queue.put(ev.token_stream("CEO", chunk))

        ceo_preferred = ceo_recommendation.chosen_option
        ceo_concern = ceo_recommendation.dissenting_concern or "None raised."
        ceo_vetoes = [e.option_name for e in ceo_evaluations if e.vetoes]

        await queue.put(ev.exec_statement(
            role="CEO",
            opening_statement="",
            preferred_option=ceo_preferred,
            key_concern=ceo_concern,
            veto_options=ceo_vetoes,
        ))
        await queue.put(ev.scores_ready(
            "CEO",
            [{"option_name": e.option_name, "weighted_score": e.weighted_score, "vetoes": e.vetoes}
             for e in ceo_evaluations],
        ))

        # ------------------------------------------------------------------
        # Phase 2: Exec evaluations (sequential)
        # ------------------------------------------------------------------
        await queue.put(ev.phase_start(2, "Board Deliberation"))

        exec_agents = [
            (CFOAgent(), "cfo_evaluation"),
            (COOAgent(), "coo_evaluation"),
            (CMOAgent(), "cmo_evaluation"),
            (CTOAgent(), "cto_evaluation"),
        ]

        exec_results: dict = {}

        for agent, state_key in exec_agents:
            role = agent.role
            await queue.put(ev.node_start(role, "evaluation", f"{role} reviewing options..."))

            # Stream opening statement
            async for chunk in agent.stream_opening(options, problem):
                await queue.put(ev.token_stream(role, chunk))

            # Structured evaluation
            evaluation: ExecEvaluation = await agent.evaluate_options(options, problem)
            exec_results[state_key] = evaluation

            await queue.put(ev.exec_statement(
                role=role,
                opening_statement=evaluation.opening_statement,
                preferred_option=evaluation.preferred_option,
                key_concern=evaluation.key_concern,
                veto_options=evaluation.veto_options,
            ))
            await queue.put(ev.scores_ready(
                role,
                [{"option_name": s.option_name, "weighted_score": s.weighted_score, "vetoes": s.vetoes}
                 for s in evaluation.option_scores],
            ))

        # ------------------------------------------------------------------
        # Phase 3: Synthesis
        # ------------------------------------------------------------------
        await queue.put(ev.phase_start(3, "Board Resolution"))
        await queue.put(ev.synthesis_start())

        synthesis = await _synthesize_boardroom(
            problem=problem,
            options=options,
            ceo_recommendation=ceo_recommendation,
            cfo_eval=exec_results["cfo_evaluation"],
            coo_eval=exec_results["coo_evaluation"],
            cmo_eval=exec_results["cmo_evaluation"],
            cto_eval=exec_results["cto_evaluation"],
        )

        await queue.put(ev.synthesis_complete(synthesis.model_dump()))
        await queue.put(ev.done(session_id))

    except Exception as exc:  # noqa: BLE001
        await queue.put(ev.error(str(exc), session_id))
        await queue.put(ev.done(session_id))
