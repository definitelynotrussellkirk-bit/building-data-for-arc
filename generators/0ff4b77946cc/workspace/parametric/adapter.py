"""Thin exact-path native adapter for the 0ff4b77946cc gallery family."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_0ff4b77946cc_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
_IMPL = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _IMPL
_SPEC.loader.exec_module(_IMPL)

program = _IMPL.program
generate = _IMPL.generate
