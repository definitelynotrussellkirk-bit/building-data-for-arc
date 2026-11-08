"""Promotion adapter for the proposed a9c4475d7cda panel threshold."""
from __future__ import annotations

from typing import Any

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("a9c4475d7cda_current_threshold_adapter", _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load local prototype: {_path}")
prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prototype)


def _threshold(settings: Any) -> int:
    if type(settings) is not dict:
        raise TypeError("settings must be a dictionary")
    if set(settings) != {"min_panel_count"}:
        raise ValueError("settings must contain exactly min_panel_count")
    return prototype._validate_min_panel_count(settings["min_panel_count"])


def program(settings: Any) -> str:
    threshold = _threshold(settings)
    return prototype.rule_text(threshold)


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    threshold = _threshold(settings)
    episode = prototype.build_claimed_episode(
        seed,
        min_panel_count=threshold,
        demos=demos,
        queries=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
