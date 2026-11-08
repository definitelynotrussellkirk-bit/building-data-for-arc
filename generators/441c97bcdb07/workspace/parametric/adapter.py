"""Exact-path native adapter for the 441c97bcdb07 completion family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any


_HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = _HERE / "prototype.py"
_MODULE_NAME = "_parametric_441c97bcdb07_" + hashlib.sha256(
    str(_PROTOTYPE_PATH).encode() + _PROTOTYPE_PATH.read_bytes()
).hexdigest()


def _load_prototype():
    module = sys.modules.get(_MODULE_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adjacent prototype from {_PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load_prototype()


def program(settings: Any) -> str:
    selected = _PROTOTYPE.validate_settings(settings)
    return _PROTOTYPE.program_for(selected)


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    selected = _PROTOTYPE.validate_settings(settings)
    return _PROTOTYPE.generate_episode(seed, selected, demos, queries)
