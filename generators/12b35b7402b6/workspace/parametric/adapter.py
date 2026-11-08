"""Thin native adapter for the 12b35b7402b6 linked-payload family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_12b35b7402b6_parametric_impl", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {_PATH}")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def program(settings):
    return prototype.program(settings)


def generate(seed, settings, demos, queries):
    episode = prototype.generate(seed, settings, demos, queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
