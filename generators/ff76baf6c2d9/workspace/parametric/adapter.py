"""Thin native adapter loading only this task's adjacent prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path


_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_ff76baf6c2d9_parametric_native", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load parametric prototype: {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    return _PROTOTYPE.native_program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _PROTOTYPE.native_generate(seed, settings, demos, queries)
