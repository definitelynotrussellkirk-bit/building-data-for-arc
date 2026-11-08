"""Thin native adapter for the flood-then-outline family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).with_name("family.py")
_NAME = "_task_75422b6b0a4d_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load parametric family from {_PATH}")
_FAMILY = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _FAMILY
_SPEC.loader.exec_module(_FAMILY)


def program(settings):
    return _FAMILY.program(settings)


def generate(seed, settings, demos, queries):
    return _FAMILY.generate(seed, settings, demos, queries)
