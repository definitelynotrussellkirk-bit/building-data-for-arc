"""Thin native adapter loading only the exact adjacent prototype source."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_cap_bridge_94549757a7f3_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load cap/bridge prototype from {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
claimed_output = _MODULE.claimed_output
cap_stage = _MODULE.cap_stage
vertical_bridge = _MODULE.vertical_bridge
horizontal_bridge = _MODULE.horizontal_bridge
first_column_bridge = _MODULE.first_column_bridge
solve_without_cap = _MODULE.solve_without_cap
analyze_input = _MODULE.analyze_input
public_turn = _MODULE.public_turn
public_turn_bytes = _MODULE.public_turn_bytes
public_turn_id = _MODULE.public_turn_id

GENERATOR_PATH = _MODULE.GENERATOR_PATH
GENERATOR_SHA256 = _MODULE.GENERATOR_SHA256
