"""Native adapter; load this task's adjacent prototype by exact path."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_shortest_path_parametric_impl", _PATH)
_IMPL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_IMPL)


def program(settings):
    return _IMPL.program(settings)


def generate(seed, settings, demos, queries):
    return _IMPL.generate(seed, settings, demos, queries)
