"""Promotion adapter for the proposed panel-count threshold prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "a9c4475d7cda_threshold_prototype_adapter", HERE / "prototype.py"
)
if _spec is None or _spec.loader is None:  # pragma: no cover - import contract guard
    raise ImportError("cannot load local threshold prototype")
prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prototype)


def _threshold(settings) -> int:
    if type(settings) is not dict or set(settings) != {"threshold"}:
        raise ValueError("settings must name exactly threshold")
    return prototype._threshold(settings["threshold"])


def program(settings):
    return prototype.rule_text(_threshold(settings))


def generate(seed, settings, demos, queries):
    threshold = _threshold(settings)
    episode = prototype.generate_episode(
        seed,
        threshold=threshold,
        demos=demos,
        queries=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
