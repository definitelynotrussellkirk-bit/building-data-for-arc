"""Thin native adapter loading this task's exact adjacent prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_gallery_order_1216927d148b_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load gallery-order prototype from {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
claimed_output = _MODULE.claimed_output
analyze_input = _MODULE.analyze_input
public_turn = _MODULE.public_turn
public_turn_bytes = _MODULE.public_turn_bytes
public_turn_id = _MODULE.public_turn_id
