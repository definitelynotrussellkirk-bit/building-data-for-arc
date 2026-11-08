"""Thin promotion adapter for the task-local match-selector family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("parametric_4dd0_match_selector_impl", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load parametric implementation at {_PATH}")
_IMPL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_IMPL)

program = _IMPL.program
generate = _IMPL.generate
