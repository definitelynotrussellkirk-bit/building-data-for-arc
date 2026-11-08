"""Thin exact-path adapter for the c130 edge-rotation prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path


_path = Path(__file__).with_name("edge_rotation.py")
_spec = importlib.util.spec_from_file_location(
    "_task_c130e51c4310_edge_rotation", _path
)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {_path}")
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    episode = _prototype.generate(seed, settings, demos, queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
