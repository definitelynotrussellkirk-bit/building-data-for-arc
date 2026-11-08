"""Thin source-bound adapter for the 941f7ac13580 border-size family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_parametric_941_impl_" + hashlib.sha256(str(_PATH).encode()).hexdigest(), _PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_PATH}")
_IMPL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_IMPL)

program = _IMPL.program


def generate(seed, settings, demos, queries):
    episode = _IMPL.generate(seed, settings, demos, queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
