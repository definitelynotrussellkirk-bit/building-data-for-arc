"""Thin native adapter for the 25c140f9307d payload-policy family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROTOTYPE = HERE / "prototype.py"
_NAME = "_arc_parametric_prototype_" + hashlib.sha256(str(PROTOTYPE).encode("utf-8")).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, PROTOTYPE)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load task-local prototype: {PROTOTYPE}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _MODULE
_SPEC.loader.exec_module(_MODULE)


def program(settings):
    return _MODULE.program(settings)


def generate(seed, settings, demos, queries):
    return _MODULE.generate(seed, settings, demos, queries)
