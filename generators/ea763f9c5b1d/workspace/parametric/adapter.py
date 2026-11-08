"""Thin native adapter for the ea763f9c5b1d rule-mode family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_ea763f9c5b1d_anchor_threshold_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load parametric prototype at {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
solve_python = _MODULE.solve_python
analyze_scene = _MODULE.analyze_scene
declared_rivals = _MODULE.declared_rivals
