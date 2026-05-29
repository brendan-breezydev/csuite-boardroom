"""
Shared Pydantic models for the C-Suite Boardroom Decision Framework.
"""
from __future__ import annotations

from typing import List, Optional, TypedDict
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# CEO pipeline models (reused from ceo_mind)
# ---------------------------------------------------------------------------

class Problem(BaseModel):
    surface_ask: str = Field(..., description="What the user literally asked about.")
    actual_decision: str = Field(..., description="The real underlying decision that must be made.")
    constraints: List[str] = Field(default_factory=list)
    stakeholders: List[str] = Field(default_factory=list)
    time_horizon: str = Field("medium", description="short | medium | long")


class Option(BaseModel):
    name: str
    summary: str
    mechanism: str = Field(..., description="How this option actually works.")
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
# Exec evaluation models (CFO / COO / CMO / CTO)
# ---------------------------------------------------------------------------

class ExecEvaluation(BaseModel):
    role: str
    option_scores: List[OptionEvaluation]
    preferred_option: str
    veto_options: List[str] = Field(default_factory=list)
    key_concern: str
    opening_statement: str = Field(..., description="2-3 sentence speaking-voice summary for the boardroom chat UI.")


# ---------------------------------------------------------------------------
# Boardroom synthesis models
# ---------------------------------------------------------------------------

class ConsensusItem(BaseModel):
    option_name: str
    agreeing_roles: List[str]
    basis: str


class DissentItem(BaseModel):
    option_name: str
    dissenting_role: str
    concern: str
    resolution: str


class BoardroomSynthesis(BaseModel):
    final_recommendation: str
    consensus_items: List[ConsensusItem]
    dissent_items: List[DissentItem]
    conditions: List[str] = Field(default_factory=list)
    synthesis_narrative: str = Field(..., description="Closing boardroom-chair statement.")


# ---------------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------------

class BoardroomState(TypedDict, total=False):
    situation: str
    session_id: str
    problem: Problem
    options: List[Option]
    ceo_evaluations: List[OptionEvaluation]
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
