"""Native adapter for the task-local aligned-panel parametric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path


_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_aligned_panel_parametric_impl", _path)
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)


def program(settings):
    return _impl.program(settings)


def generate(seed, settings, demos, queries):
    return _impl.generate(seed, settings, demos, queries)
