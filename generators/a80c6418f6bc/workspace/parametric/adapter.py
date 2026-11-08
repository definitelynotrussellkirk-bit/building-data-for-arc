"""Thin native adapter for the a80c6418f6bc transfer-orientation family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_a80c6418f6bc_transfer_orientation_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load parametric prototype at {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
solve_python = _MODULE.solve_python
analyze = _MODULE.analyze
declared_rivals = _MODULE.declared_rivals
