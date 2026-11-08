"""Thin native adapter for the marker-slice relay family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_parametric_78cc0b96bc87_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
solve_python = _MODULE.solve_python
checkerboard_only = _MODULE.checkerboard_only
analyze_input = _MODULE.analyze_input
public_turn = _MODULE.public_turn
teaching_check = _MODULE.teaching_check
