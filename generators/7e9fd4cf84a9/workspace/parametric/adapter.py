"""Thin native adapter for the 7e9fd4cf84a9 fill-scope family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_arc_7e9fd4cf84a9_family", HERE / "native_family.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent native_family.py")
_FAMILY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FAMILY)

program = _FAMILY.program
generate = _FAMILY.generate
solve = _FAMILY.solve
selected_holes = _FAMILY.selected_holes
rival_outputs = _FAMILY.rival_outputs
teaching_survivors = _FAMILY.teaching_survivors
