"""Native promotion interface, loading only its exact adjacent prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_2ca60ab198d6_nested_rows", _PATH)
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    return _PROTOTYPE.program(settings)


def generate(seed, settings, demos=3, queries=4):
    return _PROTOTYPE.generate(seed, settings, demos, queries)
