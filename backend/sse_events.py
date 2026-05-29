"""
SSE event helpers for the boardroom streaming API.
All events are dicts serialized as JSON on the `data:` line of the SSE stream.
"""
from __future__ import annotations

import json
from typing import Any


def _event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def phase_start(phase: int, label: str) -> str:
    return _event({"type": "phase_start", "phase": phase, "label": label})


def node_start(role: str, node: str, label: str) -> str:
    return _event({"type": "node_start", "role": role, "node": node, "label": label})


def token_stream(role: str, delta: str) -> str:
    return _event({"type": "token_stream", "role": role, "delta": delta})


def node_complete(role: str, node: str, payload: Any) -> str:
    return _event({"type": "node_complete", "role": role, "node": node, "payload": payload})


def options_ready(options: list) -> str:
    return _event({"type": "options_ready", "options": options})


def exec_statement(
    role: str,
    opening_statement: str,
    preferred_option: str,
    key_concern: str,
    veto_options: list,
) -> str:
    return _event({
        "type": "exec_statement",
        "role": role,
        "opening_statement": opening_statement,
        "preferred_option": preferred_option,
        "key_concern": key_concern,
        "veto_options": veto_options,
    })


def scores_ready(role: str, option_scores: list) -> str:
    return _event({"type": "scores_ready", "role": role, "option_scores": option_scores})


def synthesis_start() -> str:
    return _event({"type": "synthesis_start"})


def synthesis_complete(synthesis: dict) -> str:
    return _event({"type": "synthesis_complete", **synthesis})


def error(message: str, session_id: str = "") -> str:
    return _event({"type": "error", "message": message, "session_id": session_id})


def done(session_id: str) -> str:
    return _event({"type": "done", "session_id": session_id})
