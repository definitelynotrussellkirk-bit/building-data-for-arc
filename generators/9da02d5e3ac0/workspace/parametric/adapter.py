"""Thin native adapter loading this task's exact adjacent prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_row_fill_bridge_9da02d5e3ac0_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load row-fill bridge prototype from {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
claimed_output = _MODULE.claimed_output
row_fill = _MODULE.row_fill
vertical_bridge = _MODULE.vertical_bridge
analyze_input = _MODULE.analyze_input
public_turn = _MODULE.public_turn
public_turn_bytes = _MODULE.public_turn_bytes
public_turn_id = _MODULE.public_turn_id
