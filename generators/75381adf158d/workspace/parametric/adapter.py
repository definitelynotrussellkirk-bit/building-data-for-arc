"""Thin native adapter for the enclosed-hole / largest-escape family."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("family.py")
_NAME = "_arc_75381_holes_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)
program = _MODULE.program
generate = _MODULE.generate
public_turn = _MODULE.public_turn
