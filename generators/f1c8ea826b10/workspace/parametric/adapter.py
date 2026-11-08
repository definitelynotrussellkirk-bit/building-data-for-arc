"""Native promotion adapter loading only the adjacent family implementation."""
from __future__ import annotations

import importlib.util
from pathlib import Path


_path = Path(__file__).resolve().with_name("native_family.py")
_spec = importlib.util.spec_from_file_location("_native_f1c8ea826b10", _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load native family from {_path}")
_family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_family)

program = _family.program


def generate(seed, settings, demos=3, queries=4):
    return _family.generate(seed, settings, demos, queries)
