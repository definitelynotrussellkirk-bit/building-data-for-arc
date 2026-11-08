"""Thin exact-path adapter for the f99a33b5211f local-axis family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_task_f99a33b5211f_local_axis", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load prototype from {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
program = _MODULE.program
generate = _MODULE.generate
