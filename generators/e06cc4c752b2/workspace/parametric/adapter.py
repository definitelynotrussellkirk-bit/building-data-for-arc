"""Exact-path adapter for the task-local parametric prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_e06cc4c752b2_parametric_prototype", _HERE / "prototype.py")
_IMPL = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_IMPL)


def program(settings):
    return _IMPL.program(settings)


def generate(seed, settings, demos, queries):
    return _IMPL.generate(seed, settings, demos, queries)
