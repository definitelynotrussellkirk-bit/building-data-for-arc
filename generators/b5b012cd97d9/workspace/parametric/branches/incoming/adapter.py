"""Thin native adapter for the b5b012cd97d9 parametric prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_b5b012cd97d9_parametric_prototype"
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load parametric prototype from {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
