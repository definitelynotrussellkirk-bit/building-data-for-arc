"""Native promotion adapter for the nested-ring cross-stop family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "d2534264df36_cross_stop_prototype",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load d2534264df36 parametric prototype")
_prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    return _prototype.generate(seed, settings, demos, queries)
