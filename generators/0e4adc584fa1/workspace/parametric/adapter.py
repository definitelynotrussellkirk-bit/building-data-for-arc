"""Native adapter for the object-selected control family."""
from __future__ import annotations

import importlib.util
from pathlib import Path


_PATH = Path(__file__).resolve().with_name("native_family.py")
_SPEC = importlib.util.spec_from_file_location("_native_0e4adc584fa1", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load native family from {_PATH}")
_FAMILY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FAMILY)

program = _FAMILY.program


def generate(seed, settings, demos=3, queries=4):
    return _FAMILY.generate(seed, settings, demos, queries)
