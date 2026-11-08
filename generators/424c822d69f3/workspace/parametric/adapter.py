"""Native promotion adapter for the rectangle-anchor parameter family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TARGET = _HERE / "bbox_anchor" / "prototype.py"
_SPEC = importlib.util.spec_from_file_location("rectangle_anchor_native_prototype", _TARGET)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_TARGET}")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"anchor"}:
        raise ValueError("settings must contain exactly anchor")
    prototype.oracle.validate_anchor(settings["anchor"])
    return settings


def _count(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def program(settings):
    settings = _settings(settings)
    return prototype.rule_text(settings["anchor"])


def generate(seed, settings, demos, queries):
    settings = _settings(settings)
    _count("demos", demos, 2, 6)
    _count("queries", queries, 4, 4)
    episode = prototype.generate_episode(
        seed,
        anchor=settings["anchor"],
        demos=demos,
        queries=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
