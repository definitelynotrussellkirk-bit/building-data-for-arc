"""Thin native adapter for the 70913cf98cee parametric family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

_SOURCE = Path(__file__).with_name("family.py")
_NAME = "_arc_70913cf98cee_family_" + hashlib.sha256(_SOURCE.read_bytes()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent family source: {_SOURCE}")
_FAMILY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FAMILY)


def program(settings):
    return _FAMILY.program(settings)


def generate(seed, settings, demos, queries):
    return _FAMILY.generate(seed, settings, demos, queries)
