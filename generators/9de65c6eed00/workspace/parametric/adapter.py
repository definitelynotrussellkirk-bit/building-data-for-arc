"""Thin exact-path native adapter for 9de65c6eed00."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_path = Path(__file__).resolve().with_name("native.py")
_name = "_native_9de65c6eed00_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
if _spec is None or _spec.loader is None:
    raise ImportError(_path)
_native = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _native
_spec.loader.exec_module(_native)

program = _native.program
generate = _native.generate
analyze = _native.analyze
transform = _native.transform
transform_with_anchor = _native.transform_with_anchor
lesson_certificate = _native.lesson_certificate
public_turn = _native.public_turn
counterfactual_program = _native.counterfactual_program
sample_input = _native.sample_input
CORNERS = _native.CORNERS
SETTINGS = _native.SETTINGS
