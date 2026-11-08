"""Native adapter for the reviewed input-derived translation family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_native_ac4b61e7b230_prototype", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)


def _parameters(settings):
    if type(settings) is not dict or set(settings) != {"translation_mode"}:
        raise ValueError("settings must contain exactly translation_mode")
    return _PROTOTYPE.Parameters(settings["translation_mode"])


def program(settings):
    return _PROTOTYPE.materialize_rule(_parameters(settings))


def generate(seed, settings, demos, queries):
    parameters = _parameters(settings)
    sampled = _PROTOTYPE.sample_inputs(seed, demo_count=demos, query_count=queries)

    def pair(grid):
        frozen = deepcopy(grid)
        return {"input": frozen, "output": _PROTOTYPE.python_mirror(frozen, parameters)}

    return {
        "train": [pair(grid) for grid in sampled["demonstrations"]],
        "test": [pair(grid) for grid in sampled["queries"]],
        "program_solution": program(settings),
    }
