"""Thin native adapter for the 6b5d8752c5c4 divider-source family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


_HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = _HERE / "prototype.py"
_MODULE_NAME = "_6b5d8752c5c4_divider_source_parametric_prototype"


def _load_prototype():
    module = sys.modules.get(_MODULE_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent prototype: {_PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load_prototype()


def program(settings: Any) -> str:
    """Return the exact Racket program for one declared setting."""
    return _PROTOTYPE.program(settings)


def generate(
    seed: int,
    settings: Any,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    """Return a deterministic private labeled episode."""
    return _PROTOTYPE.generate(seed, settings, demos, queries)
