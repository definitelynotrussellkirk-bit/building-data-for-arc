"""Thin native adapter for the b91a3b0baac4 sequential beam family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("native.py")
_SPEC = importlib.util.spec_from_file_location(
    "_b91a3b0baac4_native_" + hashlib.sha256(str(_PATH).encode()).hexdigest(),
    _PATH,
)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
beam_only = _MODULE.beam_only
delta_segments = _MODULE.delta_segments
highlight_segment = _MODULE.highlight_segment
marker = _MODULE.marker
observe = _MODULE.observe
predict = _MODULE.predict
public_turn = _MODULE.public_turn
sample_input = _MODULE.sample_input
teaching_certificate = _MODULE.teaching_certificate
transform = _MODULE.transform
HYPOTHESES = _MODULE.HYPOTHESES
MODES = _MODULE.MODES
