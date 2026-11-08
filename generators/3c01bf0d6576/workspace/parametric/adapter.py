"""Exact-path adapter for the native transform-by-example family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("native_family.py")
_NAME = "_arc_3c01bf0d6576_native_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent native family: {_PATH}")
_FAMILY = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _FAMILY
_SPEC.loader.exec_module(_FAMILY)

program = _FAMILY.program
generate = _FAMILY.generate
transform = _FAMILY.transform
wrong_order_transform = _FAMILY.wrong_order_transform
wrong_order_program = _FAMILY.wrong_order_program
