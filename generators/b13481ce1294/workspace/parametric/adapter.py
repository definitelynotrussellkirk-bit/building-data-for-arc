"""Thin exact-path native adapter for b13481ce1294."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_b13481ce1294_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
_IMPL = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _IMPL
_SPEC.loader.exec_module(_IMPL)


def program(settings):
    return _IMPL.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _IMPL.generate(seed, settings, demos, queries)
