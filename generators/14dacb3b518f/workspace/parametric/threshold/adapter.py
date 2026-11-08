"""Thin native adapter for the task-local hole-threshold prototype."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_arc_14dacb3b518f_hole_threshold_prototype", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype at {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _threshold(settings: Any) -> int:
    if type(settings) is not dict or set(settings) != {"min_holes"}:
        raise ValueError("settings must name exactly min_holes")
    return _PROTOTYPE._validate_threshold(settings["min_holes"])


def program(settings: dict[str, Any]) -> str:
    return _PROTOTYPE.program_for(_threshold(settings))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    threshold = _threshold(settings)
    episode = _PROTOTYPE.generate_episode(seed, min_holes=threshold, demos=demos, queries=queries)
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": copy.deepcopy(episode["test"]),
        "program_solution": program(settings),
    }
