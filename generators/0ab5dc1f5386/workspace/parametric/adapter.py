"""Thin native adapter loading only the exact adjacent prototype source."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_source_order_0ab5dc1f5386_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load source-order prototype from {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
solve = _MODULE.solve
analyze_input = _MODULE.analyze_input
public_turn = _MODULE.public_turn
public_turn_bytes = _MODULE.public_turn_bytes
public_turn_id = _MODULE.public_turn_id
