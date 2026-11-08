"""Native adapter for exact outer fill and short-side component relay."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_PROTOTYPE_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_arc_ebe355c22d70_parametric_prototype", _PROTOTYPE_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings: dict) -> str:
    return _PROTOTYPE.program(settings)


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    episode = _PROTOTYPE.generate(seed, settings, demos, queries)
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }
