"""Thin promotion adapter for the reviewed panel-threshold prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path


_PROTOTYPE_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "a9c4475d7cda_parametric_prototype", _PROTOTYPE_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load parametric prototype from {_PROTOTYPE_PATH}")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _threshold(settings) -> int:
    if not isinstance(settings, dict) or set(settings) != {"panel_threshold"}:
        raise ValueError("settings must contain only panel_threshold")
    value = settings["panel_threshold"]
    prototype._validate_panel_threshold(value)
    return value


def program(settings):
    """Return the exact source-bound Racket program for one setting."""
    return prototype.materialize_rule(_threshold(settings))


def generate(seed, settings, demos, queries):
    """Return one fixed-setting labeled episode for qualification/export."""
    threshold = _threshold(settings)
    episode = prototype.make_episode(
        seed,
        panel_threshold=threshold,
        demo_count=demos,
        query_count=queries,
    )
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["test"]
        ],
        "program_solution": episode["racket_source"],
    }
