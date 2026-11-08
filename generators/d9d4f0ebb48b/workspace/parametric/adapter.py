"""Exact-path native promotion adapter for d9d4f0ebb48b."""
from __future__ import annotations

import importlib.util
from pathlib import Path


_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_d9d4f0ebb48b_parametric_prototype", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    """Return exact Racket source for a declared finite setting."""
    return _PROTOTYPE.program(settings)


def generate(seed, settings, demos, queries):
    """Return setting-neutral inputs and private Python label claims."""
    return _PROTOTYPE.generate(seed, settings, demos, queries)
