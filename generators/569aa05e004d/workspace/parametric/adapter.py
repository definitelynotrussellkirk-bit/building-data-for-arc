"""Thin exact-path adapter for the 569aa05e004d row/column prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_569aa05e004d_parametric_impl", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {_PATH}")
_IMPL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_IMPL)

program = _IMPL.program
generate = _IMPL.generate
