"""Thin exact-path adapter for the native 2f8ecb96521c family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("native_family.py")
_NAME = "_arc_2f8ecb96521c_" + hashlib.sha256(str(_PATH).encode("utf-8")).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load native family: {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)
program = _MODULE.program
generate = _MODULE.generate
