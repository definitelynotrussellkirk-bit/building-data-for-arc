"""Exact-path native adapter for the 959992fc8fa9 finite rule family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_arc_959992fc8fa9_parametric_prototype", _PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings: dict) -> str:
    return _PROTOTYPE.program(settings)


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    return _PROTOTYPE.generate(seed, settings, demos, queries)
