"""Exact-path adapter for the a90d16507995 native family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("family.py")
_NAME = "_arc_a90d16507995_family_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_IMPL = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _IMPL
_SPEC.loader.exec_module(_IMPL)


def program(settings):
    return _IMPL.program(settings)


def generate(seed, settings, demos, queries):
    return _IMPL.generate(seed, settings, demos, queries)
