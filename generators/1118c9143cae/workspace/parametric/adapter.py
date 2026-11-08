"""Thin exact-path promotion adapter for the 1118c9143cae echo-scope family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_1118c9143cae_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest(),
    _PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load task-local prototype at {_PATH}")
_IMPL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_IMPL)


def program(settings):
    return _IMPL.program(settings)


def generate(seed, settings, demos=3, queries=4):
    episode = _IMPL.generate(seed, settings, demos, queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
