"""Thin, unapproved promotion adapter for the task-local sort-key prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("sort_key_parametric_prototype", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load prototype from {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _setting(settings: dict[str, Any] | None) -> str:
    if settings is None:
        return _PROTOTYPE.DEFAULT_SORT_KEY
    if type(settings) is not dict or set(settings) != {"sort_key"}:
        raise ValueError("settings must contain exactly {'sort_key'}")
    value = settings["sort_key"]
    _PROTOTYPE._validate_sort_key(value)
    return value


def program(settings: dict[str, Any] | None = None) -> str:
    return _PROTOTYPE.program_for(_setting(settings))


def generate(
    seed: int,
    settings: dict[str, Any] | None = None,
    demos: int = 3,
    queries: int = 4,
    *,
    bridge=None,
) -> dict[str, Any]:
    episode = _PROTOTYPE.make_episode(
        seed,
        sort_key=_setting(settings),
        demos=demos,
        queries=queries,
        bridge=bridge,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program"],
    }
