"""Thin native adapter loading only the exact adjacent staircase prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path


_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("staircase_8e6c44aee812_native", _path)
if _spec is None or _spec.loader is None:
    raise RuntimeError("could not load adjacent staircase prototype")
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _prototype.generate(seed, settings, demos=demos, queries=queries)
