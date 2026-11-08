"""Thin exact-path adapter for the c6fa0b0b24da parametric family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("native.py")
_NAME = "_arc_c6fa0b0b24da_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_NATIVE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _NATIVE
_SPEC.loader.exec_module(_NATIVE)


def program(settings):
    return _NATIVE.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _NATIVE.generate(seed, settings, demos=demos, queries=queries)
