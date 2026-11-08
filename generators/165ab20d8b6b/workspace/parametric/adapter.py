"""Exact-path native adapter for the 165ab20d8b6b neighborhood family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_165ab20d8b6b_native_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover
    raise ImportError(f"cannot load adjacent prototype: {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
