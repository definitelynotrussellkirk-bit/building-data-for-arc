"""Thin source-bound adapter for the 7768 target-color prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_task_7768dfc99e25_target_color", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load prototype from {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    return _PROTOTYPE.program(settings)


def generate(seed, settings, demos, queries):
    return _PROTOTYPE.generate(seed, settings, demos, queries)
