"""Exact local adapter for matched-color versus occupied-area-queue docking."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path

_SOURCE = Path(__file__).with_name('prototype.py')
_SPEC = importlib.util.spec_from_file_location(
    '_c8ab_docking_' + hashlib.sha256(str(_SOURCE).encode()).hexdigest()[:12],
    _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_SOURCE)
_ENGINE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_ENGINE)


def program(settings):
    return _ENGINE.program(settings)


def generate(seed, settings, demos, queries):
    return _ENGINE.generate(seed, settings, demos, queries)
