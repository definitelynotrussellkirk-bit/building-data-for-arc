"""Thin exact-path adapter for the native corner-direction family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("native.py")
_NAME = "_arc_61c0bcd32328_native_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load native parametric implementation at {_PATH}")
_NATIVE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_NATIVE)

program = _NATIVE.program
generate = _NATIVE.generate
solve_python = _NATIVE.solve_python
analyze = _NATIVE.analyze
teaching_certificate = _NATIVE.teaching_certificate
public_turn = _NATIVE.public_turn
dependency_witness = _NATIVE.dependency_witness
wrong_intermediate_program = _NATIVE.wrong_intermediate_program
