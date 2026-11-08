"""Thin native adapter for the adjacent largest-hollow threshold prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


_SOURCE = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_97d3714964b0_hollow_threshold_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_SOURCE}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
