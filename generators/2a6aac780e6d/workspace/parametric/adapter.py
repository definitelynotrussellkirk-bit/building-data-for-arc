"""Thin native adapter for the 2a6aac780e6d key-selected-row family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_arc_2a6aac780e6d_family", HERE / "family.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent family.py")
_FAMILY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FAMILY)


def program(settings):
    return _FAMILY.program(settings)


def generate(seed, settings, demos, queries):
    return _FAMILY.generate(seed, settings, demos, queries)
