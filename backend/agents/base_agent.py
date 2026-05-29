"""
BaseAgent — abstract base for all C-suite exec agents.
Each concrete agent loads a persona JSON and wraps ChatAnthropic.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import AsyncIterator, List

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from backend.models import ExecEvaluation, Option, OptionEvaluation, Problem


PERSONAS_DIR = Path(__file__).parent.parent / "personas"


class BaseAgent:
    role: str = ""

    def __init__(self, persona_filename: str) -> None:
        persona_path = PERSONAS_DIR / persona_filename
        self.persona = json.loads(persona_path.read_text(encoding="utf-8"))
        self.role = self.persona["role"]
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            temperature=0.2,
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        )

    def _system_prompt(self) -> str:
        return self.persona["system_prompt"]

    def _rubric_block(self) -> str:
        dims = self.persona["evaluation_rubric"]["dimensions"]
        return "Scoring rubric (0-10 per dimension):\n" + "\n".join(
            f"- {d['id']} ({d['owner']}, weight {d['weight']}): {d['question']}"
            for d in dims
        )

    def _red_flags_block(self) -> str:
        flags = self.persona.get("red_flags", [])
        return "Red flags to check:\n" + "\n".join(f"- {f}" for f in flags)

    async def stream_opening(
        self, options: List[Option], problem: Problem
    ) -> AsyncIterator[str]:
        """Stream the exec's opening statement as text chunks."""
        options_summary = "\n".join(
            f"- {o.name}: {o.summary}" for o in options
        )
        messages = [
            SystemMessage(content=self._system_prompt()),
            HumanMessage(content=(
                f"Decision: {problem.actual_decision}\n\n"
                f"Options on the table:\n{options_summary}\n\n"
                f"In 2-3 sentences, give your opening statement as {self.role} "
                f"for this boardroom meeting. Speak in first person. "
                f"Lead with your most important concern or endorsement."
            )),
        ]
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content

    async def evaluate_options(
        self, options: List[Option], problem: Problem
    ) -> ExecEvaluation:
        """Return a structured evaluation of all options."""
        llm_structured = self.llm.with_structured_output(ExecEvaluation)
        options_payload = json.dumps([o.model_dump() for o in options], indent=2)
        messages = [
            SystemMessage(content=self._system_prompt()),
            HumanMessage(content=(
                f"Decision: {problem.actual_decision}\n\n"
                f"Constraints: {problem.constraints}\n\n"
                f"Options:\n{options_payload}\n\n"
                f"{self._rubric_block()}\n\n"
                f"{self._red_flags_block()}\n\n"
                f"Score EVERY option on your rubric dimensions (0-10). "
                f"Compute weighted_score = sum(score_i * weight_i). "
                f"Flag veto_options where any dimension score <= "
                f"{self.persona['evaluation_rubric']['veto_threshold']}. "
                f"Identify your preferred_option (highest weighted score with no veto). "
                f"State your key_concern in one sentence. "
                f"Write a 2-3 sentence opening_statement in first person as the {self.role}."
            )),
        ]
        return await llm_structured.ainvoke(messages)
