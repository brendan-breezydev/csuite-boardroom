"""
Shared Pydantic models for the C-Suite Boardroom Decision Framework.
"""
from typing import Optional, TypedDict
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# CEO pipeline models (reused from ceo_mind)
# ---------------------------------------------------------------------------

class Problem(BaseModel):
    surface_ask: str = Field(..., description="What the user literally asked about.")
    actual_decision: str = Field(..., description="The real underlying decision that must be made.")
    constraints: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    time_horizon: str = Field("medium", description="short | medium | long")


class Option(BaseModel):
    name: str
    summary: str
    mechanism: str = Field("", description="How this option actually works.")
    key_assumption: str = Field("", description="The key assumption this option depends on.")
    kill_condition: str = Field("", description="The single observation that would prove this option wrong.")
    archetype_lean: str = Field("hybrid", description="buffett | cook | doronin | hybrid")


class DimensionScore(BaseModel):
    dimension_id: str
    owner: str
    score: int = Field(..., ge=0, le=10)
    rationale: str = ""


class OptionEvaluation(BaseModel):
    option_name: str
    dimension_scores: list[DimensionScore]
    weighted_score: float
    vetoes: list[str] = Field(default_factory=list)
    dissent: Optional[str] = None


class Recommendation(BaseModel):
    chosen_option: str
    reason: str
    dissenting_concern: Optional[str] = None
    what_would_change_a_no_to_a_yes: Optional[str] = None


# ---------------------------------------------------------------------------
# Wrapper models for list-typed structured outputs (LangChain requirement)
# ---------------------------------------------------------------------------

class OptionList(BaseModel):
    """Wrapper so with_structured_output() can return a list of Options."""
    options: list[Option]


class OptionEvaluationList(BaseModel):
    """Wrapper so with_structured_output() can return a list of OptionEvaluations."""
    evaluations: list[OptionEvaluation]


# ---------------------------------------------------------------------------
# Exec evaluation models (CFO / COO / CMO / CTO)
# ---------------------------------------------------------------------------

class ExecEvaluation(BaseModel):
    role: str
    option_scores: list[OptionEvaluation]
    preferred_option: str
    veto_options: list[str] = Field(default_factory=list)
    key_concern: str
    opening_statement: str = Field(..., description="2-3 sentence speaking-voice summary for the boardroom chat UI.")


# ---------------------------------------------------------------------------
# Boardroom synthesis models
# ---------------------------------------------------------------------------

class ConsensusItem(BaseModel):
    option_name: str
    agreeing_roles: list[str]
    basis: str


class DissentItem(BaseModel):
    option_name: str
    dissenting_role: str
    concern: str
    resolution: str


class BoardroomSynthesis(BaseModel):
    final_recommendation: str
    consensus_items: list[ConsensusItem]
    dissent_items: list[DissentItem]
    conditions: list[str] = Field(default_factory=list)
    synthesis_narrative: str = Field(..., description="Closing boardroom-chair statement.")


# ---------------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------------

class BoardroomState(TypedDict, total=False):
    situation: str
    session_id: str
    problem: Problem
    options: list[Option]
    ceo_evaluations: list[OptionEvaluation]
    ceo_recommendation: Recommendation
    cfo_evaluation: ExecEvaluation
    coo_evaluation: ExecEvaluation
    cmo_evaluation: ExecEvaluation
    cto_evaluation: ExecEvaluation
    synthesis: BoardroomSynthesis


# ---------------------------------------------------------------------------
# API request/response models
# ---------------------------------------------------------------------------

class BoardroomRequest(BaseModel):
    situation: str = Field(..., min_length=20, description="The business situation to bring to the board.")


class BoardroomStartResponse(BaseModel):
    session_id: str
    status: str = "queued"
