"""Native entry point for this task's constructive side-boundary family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


_PATH = Path(__file__).resolve().with_name("native_family.py")
_SPEC = importlib.util.spec_from_file_location(
    "_wall_family_5f9a2df57599_" + hashlib.sha256(str(_PATH).encode()).hexdigest(), _PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load task-local native family: {_PATH}")
_FAMILY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FAMILY)


def normalize_settings(settings=None):
    return _FAMILY.normalize_settings(settings)


def program(settings=None):
    return _FAMILY.program(settings)


def generate(seed, settings=None, demos=3, queries=4):
    return _FAMILY.generate(seed, settings, demos, queries)
