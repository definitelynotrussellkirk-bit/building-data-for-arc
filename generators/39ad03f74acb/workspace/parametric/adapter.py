"""Thin exact-path adapter for the 39ad03f74acb selection-mode prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_task_39ad03f74acb_selection_mode", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load prototype from {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
program = _MODULE.program
generate = _MODULE.generate

# The union keeps the existing helpers available for source-bound old tests.
_UNION_PATH = Path(__file__).resolve().with_name("union.py")
_UNION_SPEC = importlib.util.spec_from_file_location("_union_39ad03f74acb", _UNION_PATH)
_UNION = importlib.util.module_from_spec(_UNION_SPEC)
_UNION_SPEC.loader.exec_module(_UNION)
program = _UNION.program
generate = _UNION.generate
