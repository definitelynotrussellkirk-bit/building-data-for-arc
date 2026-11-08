"""Native parametric adapter; keeps the implementation source local and explicit."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_parametric_758360aea29b", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_PATH}")
_IMPL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_IMPL)


def program(settings):
    return _IMPL.program(settings)


def generate(seed, settings, demos, queries):
    return _IMPL.generate(seed, settings, demos, queries)
