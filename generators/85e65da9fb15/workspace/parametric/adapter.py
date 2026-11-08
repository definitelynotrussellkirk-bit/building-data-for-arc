"""Thin native adapter for the frame/shape assignment-order family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_HOME = Path(__file__).resolve().parent
_PATH = _HOME / "prototype.py"
_NAME = "_arc_85e65da9fb15_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"assignment_order"}:
        raise ValueError("settings must contain exactly assignment_order")
    value = settings["assignment_order"]
    if type(value) is not str or value not in _MODULE.MODES:
        raise ValueError("assignment_order is not a declared setting")
    return value


def program(settings: Any) -> str:
    return _MODULE.program_for(_mode(settings))


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict:
    return _MODULE.generate_episode(seed, _mode(settings), demos, queries)
