"""Thin native adapter for the c1ee27b39d13 column-order family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_c1ee27b39d13_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest(),
    _PATH,
)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate

# Re-export audit helpers for focused task tests and future reviewers.
extract = _MODULE.extract
observe = _MODULE.observe
predict = _MODULE.predict
public_turn = _MODULE.public_turn
teaching_certificate = _MODULE.teaching_certificate
transform = _MODULE.transform
HYPOTHESES = _MODULE.HYPOTHESES
MODES = _MODULE.MODES
