"""Thin source-bound adapter for the d2 conflict-mode prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_task_d2f8cb1c91b2_conflict_mode", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load prototype from {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    return _PROTOTYPE.program(settings)


def generate(seed, settings, demos, queries):
    return _PROTOTYPE.generate(seed, settings, demos, queries)
