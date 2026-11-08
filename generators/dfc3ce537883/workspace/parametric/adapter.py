"""Thin native promotion adapter for the task-local sequential prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("dfc3ce537883_parametric_prototype", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load prototype from {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _followup(settings: dict[str, Any] | None) -> str:
    return _PROTOTYPE._validate_settings(settings)


def program(settings: dict[str, Any] | None = None) -> str:
    return _PROTOTYPE.program_for(_followup(settings))


def generate(
    seed: int,
    settings: dict[str, Any] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    episode = _PROTOTYPE.make_episode(
        seed,
        followup=_followup(settings),
        demos=demos,
        queries=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program"],
    }
