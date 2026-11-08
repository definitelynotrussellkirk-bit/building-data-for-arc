#!/usr/bin/env python3
"""Thin promotion adapter for the proposed quarter-turn parameter family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "arcpuzzles_88b8e6aaa49d_parametric_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("could not load the sibling parametric prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def _setting(settings: Any) -> int:
    if not isinstance(settings, dict) or set(settings) != {"quarter_turns"}:
        raise ValueError("settings must contain exactly quarter_turns")
    return _PROTOTYPE._validate_quarter_turns(settings["quarter_turns"])


def program(settings: dict[str, Any]) -> str:
    """Materialize the exact Racket program for one episode setting."""
    return _PROTOTYPE.rule_source(_setting(settings))


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
    *,
    max_attempts: int = _PROTOTYPE.DEFAULT_MAX_ATTEMPTS,
):
    """Generate one Racket-backed proposed episode."""
    return _PROTOTYPE.generate_episode(
        seed,
        quarter_turns=_setting(settings),
        demos=demos,
        queries=queries,
        max_attempts=max_attempts,
    )
