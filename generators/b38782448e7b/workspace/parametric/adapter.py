"""Thin native adapter for the b38782448e7b completed-column relay family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("native.py")
_SPEC = importlib.util.spec_from_file_location(
    "_b38782448e7b_native_" + hashlib.sha256(str(_PATH).encode()).hexdigest(),
    _PATH,
)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
active_columns = _MODULE.active_columns
background = _MODULE.background
completed_counts = _MODULE.completed_counts
cue_column = _MODULE.cue_column
observe = _MODULE.observe
predict = _MODULE.predict
public_turn = _MODULE.public_turn
relay_column = _MODULE.relay_column
sample_input = _MODULE.sample_input
teaching_certificate = _MODULE.teaching_certificate
toggle_only = _MODULE.toggle_only
transform = _MODULE.transform
HYPOTHESES = _MODULE.HYPOTHESES
MODES = _MODULE.MODES
