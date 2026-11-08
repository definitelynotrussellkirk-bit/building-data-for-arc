"""Exact-path native adapter for the ff973026bfbe column-policy family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any


_PROTOTYPE_PATH = Path(__file__).with_name("prototype.py")
_MODULE_NAME = "_ff973026bfbe_parametric_" + hashlib.sha256(
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
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(_MODULE_NAME, None)
        raise
    return module


_PROTOTYPE = _load_prototype()


def program(settings: Any) -> str:
    selected = _PROTOTYPE.validate_settings(settings)
    return _PROTOTYPE.program_for(selected)


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    selected = _PROTOTYPE.validate_settings(settings)
    return deepcopy(_PROTOTYPE.build_claimed_episode(seed, selected, demos, queries))
