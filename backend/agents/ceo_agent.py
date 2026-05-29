"""
CEO Agent — migrated from ceo_mind/ceo_graph.py, now using Claude.
Runs the 4-node pipeline: problem_extractor → option_generator → option_evaluator → best_solution_selector.
Also exposes async helpers used by the boardroom orchestrator for streaming.
"""
import json
import os
from pathlib import Path
from typing import AsyncIterator

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from backend.models import (
    Problem, Option, DimensionScore, OptionEvaluation, Recommendation, BoardroomState,
    OptionList, OptionEvaluationList,
)


PERSONA_PATH = Path(__file__).parent.parent / "personas" / "ceo_persona.json"


def _load_persona() -> dict:
    with PERSONA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


PERSONA = _load_persona()
SYSTEM_PROMPT = PERSONA["system_prompt"]
RUBRIC = PERSONA["evaluation_rubric"]
RED_FLAGS = PERSONA["red_flags"]
OPTION_RULES = PERSONA["option_generation_rules"]


def _llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0.2,
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )


def _rubric_block() -> str:
    dims = "\n".join(
        f"- {d['id']} ({d['owner']}, weight {d['weight']}): {d['question']}"
        for d in RUBRIC["dimensions"]
    )
    return (
        f"Scoring rubric (0-10 each, veto if any dimension <= "
        f"{RUBRIC['veto_threshold']} from its owning archetype):\n{dims}"
    )


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

def problem_extractor(state: BoardroomState) -> BoardroomState:
    llm = _llm().with_structured_output(Problem)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Situation:\n{state['situation']}\n\n"
            "Extract: surface_ask, the actual underlying decision, constraints, "
            "stakeholders, and time horizon (short/medium/long)."
        )),
    ]
    problem = llm.invoke(messages)
    return {"problem": problem}


def option_generator(state: BoardroomState) -> BoardroomState:
    llm = _llm().with_structured_output(OptionList)
    rules = "\n".join(f"- {r}" for r in OPTION_RULES)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Actual decision: {state['problem'].actual_decision}\n\n"
            f"Constraints: {state['problem'].constraints}\n\n"
            f"Option generation rules:\n{rules}\n\n"
            "Return at least 3 structurally distinct options in the 'options' field. "
            "Each option must declare its key_assumption and kill_condition. "
            "One option MUST be a 'do nothing / wait' option."
        )),
    ]
    result = llm.invoke(messages)
    return {"options": result.options}


def option_evaluator(state: BoardroomState) -> BoardroomState:
    llm = _llm().with_structured_output(OptionEvaluationList)
    options_payload = [o.model_dump() for o in state["options"]]
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Decision: {state['problem'].actual_decision}\n\n"
            f"Options:\n{json.dumps(options_payload, indent=2)}\n\n"
            f"{_rubric_block()}\n\n"
            f"Red flags to check:\n- " + "\n- ".join(RED_FLAGS) + "\n\n"
            "For EACH option, score every dimension from its owning archetype's "
            "perspective. Compute weighted_score = sum(score_i * weight_i). "
            "Flag vetoes (score <= veto_threshold). Record the strongest dissent. "
            "Return all evaluations in the 'evaluations' field."
        )),
    ]
    result = llm.invoke(messages)
    return {"ceo_evaluations": result.evaluations}


def best_solution_selector(state: BoardroomState) -> BoardroomState:
    evals = state["ceo_evaluations"]
    clean = [e for e in evals if not e.vetoes]
    if clean:
        winner = max(clean, key=lambda e: e.weighted_score)
        rec = Recommendation(
            chosen_option=winner.option_name,
            reason=(
                f"Highest weighted score ({winner.weighted_score:.2f}) "
                f"with no veto from any archetype."
            ),
            dissenting_concern=winner.dissent,
        )
        return {"ceo_recommendation": rec}

    fallback = min(evals, key=lambda e: (len(e.vetoes), -e.weighted_score))
    rec = Recommendation(
        chosen_option=fallback.option_name,
        reason=(
            "Every option triggered at least one veto. This option has the "
            "fewest vetoes and the highest score among the blocked set."
        ),
        dissenting_concern=fallback.dissent,
        what_would_change_a_no_to_a_yes="; ".join(fallback.vetoes),
    )
    return {"ceo_recommendation": rec}


# ---------------------------------------------------------------------------
# Streaming helper for boardroom orchestrator
# ---------------------------------------------------------------------------

async def stream_ceo_opening(problem: Problem, options: list[Option]) -> AsyncIterator[str]:
    """Stream the CEO's opening statement as text chunks."""
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0.2,
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )
    options_summary = "\n".join(f"- {o.name}: {o.summary}" for o in options)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Decision: {problem.actual_decision}\n\n"
            f"Options on the table:\n{options_summary}\n\n"
            "In 2-3 sentences, give your opening statement as CEO for this boardroom meeting. "
            "Speak in first person. Lead with your most important concern or endorsement."
        )),
    ]
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content


# ---------------------------------------------------------------------------
# Standalone graph (used by boardroom.py)
# ---------------------------------------------------------------------------

def build_ceo_graph():
    g = StateGraph(BoardroomState)
    g.add_node("problem_extractor", problem_extractor)
    g.add_node("option_generator", option_generator)
    g.add_node("option_evaluator", option_evaluator)
    g.add_node("best_solution_selector", best_solution_selector)

    g.set_entry_point("problem_extractor")
    g.add_edge("problem_extractor", "option_generator")
    g.add_edge("option_generator", "option_evaluator")
    g.add_edge("option_evaluator", "best_solution_selector")
    g.add_edge("best_solution_selector", END)

    return g.compile()
