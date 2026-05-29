"""
CEO Mind — LangGraph skeleton
=============================

Decision pipeline:

    problem_extractor  ->  option_generator  ->  option_evaluator  ->  best_solution_selector

The CEO node thinks like a composite of Warren Buffett (capital & judgment),
Tim Cook (operations & focus), and Vladislav Doronin (vision & brand).

Persona/rubric/red-flags are loaded from ceo_persona.json.

Run:
    export OPENAI_API_KEY=...          # or ANTHROPIC_API_KEY, depending on LLM choice
    python ceo_graph.py

Dependencies:
    pip install langgraph langchain langchain-openai pydantic
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional, TypedDict

from pydantic import BaseModel, Field

# LangGraph + LangChain
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

# Pick whichever LLM you have keys for. Swap freely.
try:
    from langchain_openai import ChatOpenAI
    DEFAULT_LLM = ChatOpenAI(model="gpt-4o", temperature=0.2)
except Exception:  # pragma: no cover
    DEFAULT_LLM = None


# ---------------------------------------------------------------------------
# Persona loading
# ---------------------------------------------------------------------------

PERSONA_PATH = Path(__file__).parent / "ceo_persona.json"


def load_persona(path: Path = PERSONA_PATH) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


PERSONA = load_persona()
SYSTEM_PROMPT = PERSONA["system_prompt"]
RUBRIC = PERSONA["evaluation_rubric"]
RED_FLAGS = PERSONA["red_flags"]
OPTION_RULES = PERSONA["option_generation_rules"]
SELECTION_RULES = PERSONA["selection_rules"]


# ---------------------------------------------------------------------------
# Structured outputs
# ---------------------------------------------------------------------------

class Problem(BaseModel):
    surface_ask: str = Field(..., description="What the user literally asked about.")
    actual_decision: str = Field(..., description="The real underlying decision the CEO must make.")
    constraints: List[str] = Field(default_factory=list)
    stakeholders: List[str] = Field(default_factory=list)
    time_horizon: str = Field("medium", description="short | medium | long")


class Option(BaseModel):
    name: str
    summary: str
    mechanism: str = Field(..., description="How this option actually works (capital, ops, brand).")
    key_assumption: str
    kill_condition: str = Field(..., description="The single observation that would prove this option wrong.")
    archetype_lean: str = Field(..., description="buffett | cook | doronin | hybrid")


class DimensionScore(BaseModel):
    dimension_id: str
    owner: str
    score: int = Field(..., ge=0, le=10)
    rationale: str


class OptionEvaluation(BaseModel):
    option_name: str
    dimension_scores: List[DimensionScore]
    weighted_score: float
    vetoes: List[str] = Field(default_factory=list)
    dissent: Optional[str] = None


class Recommendation(BaseModel):
    chosen_option: str
    reason: str
    dissenting_concern: Optional[str] = None
    what_would_change_a_no_to_a_yes: Optional[str] = None


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

class CEOState(TypedDict, total=False):
    situation: str
    problem: Problem
    options: List[Option]
    evaluations: List[OptionEvaluation]
    recommendation: Recommendation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _llm():
    if DEFAULT_LLM is None:
        raise RuntimeError(
            "No LLM configured. Install langchain-openai and set OPENAI_API_KEY, "
            "or swap DEFAULT_LLM for another provider."
        )
    return DEFAULT_LLM


def _system_block() -> str:
    return SYSTEM_PROMPT


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
# Nodes
# ---------------------------------------------------------------------------

def problem_extractor(state: CEOState) -> CEOState:
    """Reframe the raw situation into the surface ask + the actual decision."""
    llm = _llm().with_structured_output(Problem)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=_system_block()),
        HumanMessage(content=(
            "Situation:\n"
            f"{state['situation']}\n\n"
            "Extract: surface_ask, the actual underlying decision, constraints, "
            "stakeholders, and time horizon (short/medium/long)."
        )),
    ])
    problem = llm.invoke(prompt.format_messages())
    return {"problem": problem}


def option_generator(state: CEOState) -> CEOState:
    """Generate >=3 structurally different options, including a 'wait' option."""
    llm = _llm().with_structured_output(List[Option])
    rules = "\n".join(f"- {r}" for r in OPTION_RULES)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=_system_block()),
        HumanMessage(content=(
            f"Actual decision: {state['problem'].actual_decision}\n\n"
            f"Constraints: {state['problem'].constraints}\n\n"
            f"Option generation rules:\n{rules}\n\n"
            "Return at least 3 structurally distinct options. "
            "Each option must declare its key_assumption and kill_condition. "
            "One option MUST be a 'do nothing / wait' option."
        )),
    ])
    options = llm.invoke(prompt.format_messages())
    return {"options": options}


def option_evaluator(state: CEOState) -> CEOState:
    """Score every option on the full rubric and surface vetoes + dissent."""
    llm = _llm().with_structured_output(List[OptionEvaluation])
    options_payload = [o.model_dump() for o in state["options"]]
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=_system_block()),
        HumanMessage(content=(
            f"Decision: {state['problem'].actual_decision}\n\n"
            f"Options:\n{json.dumps(options_payload, indent=2)}\n\n"
            f"{_rubric_block()}\n\n"
            f"Red flags to check:\n- " + "\n- ".join(RED_FLAGS) + "\n\n"
            "For EACH option, score every dimension from its owning archetype's "
            "perspective. Compute weighted_score = sum(score_i * weight_i). "
            "Flag vetoes (score <= veto_threshold). Record the strongest dissent."
        )),
    ])
    evaluations = llm.invoke(prompt.format_messages())
    return {"evaluations": evaluations}


def best_solution_selector(state: CEOState) -> CEOState:
    """Pick the option with the highest weighted score and no veto."""
    evals = state["evaluations"]

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
            what_would_change_a_no_to_a_yes=None,
        )
        return {"recommendation": rec}

    # Every option has at least one veto — pick the one whose vetoes are
    # cheapest to remove (proxy: fewest vetoes, then highest weighted score).
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
    return {"recommendation": rec}


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_ceo_graph():
    g = StateGraph(CEOState)
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


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def run(situation: str) -> dict:
    graph = build_ceo_graph()
    final = graph.invoke({"situation": situation})
    return {
        "problem": final["problem"].model_dump(),
        "options": [o.model_dump() for o in final["options"]],
        "evaluations": [e.model_dump() for e in final["evaluations"]],
        "recommendation": final["recommendation"].model_dump(),
    }


if __name__ == "__main__":
    demo = (
        "We are a Series B SaaS company with 18 months of runway. A competitor just "
        "raised $200M and is undercutting our pricing by 40%. The board wants us to "
        "match their price or raise a bridge round. Our gross margin is already tight."
    )
    if os.getenv("OPENAI_API_KEY"):
        out = run(demo)
        print(json.dumps(out, indent=2))
    else:
        print("Graph compiled successfully. Set OPENAI_API_KEY to run the demo.")
        graph = build_ceo_graph()
        print(f"Nodes: {list(graph.get_graph().nodes)}")
