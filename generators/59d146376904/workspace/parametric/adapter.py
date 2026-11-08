"""Thin exact-path adapter for the 59d146376904 summary-order family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_59d146376904_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest(), _PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_PATH}")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def program(settings):
    return prototype.program(settings)


def generate(seed, settings, demos=3, queries=4):
    episode = prototype.generate(seed, settings, demos=demos, queries=queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
