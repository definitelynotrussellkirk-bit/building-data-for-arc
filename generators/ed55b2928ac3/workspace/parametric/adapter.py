"""Strict native adapter for the ed55b2928ac3 sequential family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("parametric_ed55b2928ac3_prototype", _HOME / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)


def _mode(settings) -> str:
    if type(settings) is not dict or set(settings) != {"finish_mode"}:
        raise ValueError("settings must contain exactly finish_mode")
    mode = settings["finish_mode"]
    prototype._validate_mode(mode)
    return mode


def program(settings):
    return prototype.program_for(_mode(settings))


def generate(seed, settings, demos=3, queries=4, difficulty="medium"):
    if difficulty not in {"easy", "medium", "hard", None}:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    return prototype.generate_claims(seed, _mode(settings), demos=demos, queries=queries)
