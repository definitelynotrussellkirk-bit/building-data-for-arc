"""Thin native adapter for the adjacent e8b6ff767c21 spiral family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


_SOURCE = Path(__file__).resolve().with_name("native_family.py")
_NAME = "_e8b6ff767c21_native_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent native family: {_SOURCE}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate
native_transform = _MODULE.native_transform
route_metadata = _MODULE.route_metadata
