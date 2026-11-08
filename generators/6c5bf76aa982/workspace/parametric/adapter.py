"""Exact-path native promotion adapter for 6c5bf76aa982."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_6c5bf76aa982_parametric_prototype", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    return _PROTOTYPE.program(settings)


def generate(seed, settings, demos, queries):
    return _PROTOTYPE.generate(seed, settings, demos, queries)
