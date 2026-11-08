"""Thin native adapter, loading this task's exact adjacent prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_marker_order_1034300a135f_native", _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load marker-order prototype: {_path}")
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.native_program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _prototype.native_generate(seed, settings, demos, queries)
