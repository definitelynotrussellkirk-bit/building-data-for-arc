"""Thin exact-path adapter for the selection-mode parametric family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_SOURCE = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arc_9bd5d9c04dd8_selection_mode_" + hashlib.sha256(
    str(_SOURCE).encode() + _SOURCE.read_bytes()
).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load task-local prototype: {_SOURCE}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)

program = _PROTOTYPE.program
generate = _PROTOTYPE.generate
analyze = _PROTOTYPE.analyze
apply_python = _PROTOTYPE.apply_python
first_candidate_output = _PROTOTYPE.first_candidate_output
