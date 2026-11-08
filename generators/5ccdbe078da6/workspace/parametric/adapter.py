"""Native promotion adapter loading the exact adjacent prototype source."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_5ccdbe078da6_occlusion_fill_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load 5ccdbe078da6 parametric prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    return _PROTOTYPE.program(settings)


def generate(seed, settings, demos, queries):
    return _PROTOTYPE.generate(seed, settings, demos, queries)
