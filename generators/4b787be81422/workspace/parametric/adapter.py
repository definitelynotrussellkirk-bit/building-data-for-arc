"""Native adapter for this task's source-bound symmetry prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_SOURCE = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arcpuzzles_4b787be81422_symmetry_prototype"
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Cannot load the adjacent symmetry prototype: {_SOURCE}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def _axis(settings: dict) -> str:
    if type(settings) is not dict or set(settings) != {"symmetry_axis"}:
        raise ValueError("settings must contain exactly symmetry_axis")
    axis = settings["symmetry_axis"]
    if type(axis) is not str:
        raise TypeError("symmetry_axis must be a literal string")
    if axis not in _PROTOTYPE.SYMMETRY_AXES:
        raise ValueError(f"symmetry_axis must be one of {_PROTOTYPE.SYMMETRY_AXES}")
    return axis


def program(settings: dict) -> str:
    """Return the prototype's exact selected Racket source."""
    return _PROTOTYPE.program_for(_axis(settings))


def generate(seed: int, settings: dict, demos: int = 3, queries: int = 4) -> dict:
    """Delegate count validation, sampling and claimed labels to the prototype."""
    _axis(settings)
    return _PROTOTYPE.generate_native(seed, settings, demos=demos, queries=queries)
