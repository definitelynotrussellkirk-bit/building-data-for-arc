"""Thin native-promotion adapter for the retained cyan-anchor prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "1b9d8370e28b"
PARAMETER_NAME = "cyan_anchor"
PARAMETER_VALUES = ("left", "right")
MIN_COUNT = 1
MAX_COUNT = 32
MAX_DRAW_ATTEMPTS = 4096


def _load_adjacent_prototype():
    path = Path(__file__).resolve().with_name("prototype.py")
    if not path.is_file():
        raise ImportError(f"missing adjacent prototype: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    name = f"_arc_parametric_{TASK_ID}_prototype_{digest}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load_adjacent_prototype()


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not MIN_COUNT <= value <= MAX_COUNT:
        raise ValueError(f"{name} must be in {MIN_COUNT}..{MAX_COUNT}")
    return value


def _validate_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict:
        raise TypeError("settings must be an object")
    if set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain exactly {PARAMETER_NAME!r}")
    value = _PROTOTYPE.validate_parameter(settings[PARAMETER_NAME])
    return {PARAMETER_NAME: value}


def program(settings: dict[str, Any]) -> str:
    """Return exact Racket source for one declared finite setting."""
    normalized = _validate_settings(settings)
    return _PROTOTYPE.materialize_rule(normalized[PARAMETER_NAME])


def _unique_inputs(seed: int, count: int) -> list[list[list[int]]]:
    inputs: list[list[list[int]]] = []
    seen: set[str] = set()
    candidate_index = 0
    while len(inputs) < count and candidate_index < MAX_DRAW_ATTEMPTS:
        grid = _PROTOTYPE.build_input(seed, candidate_index)
        candidate_index += 1
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            continue
        seen.add(key)
        inputs.append(grid)
    if len(inputs) != count:
        raise RuntimeError(
            f"could not draw {count} distinct inputs in {MAX_DRAW_ATTEMPTS} attempts"
        )
    return inputs


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int,
    queries: int,
) -> dict[str, Any]:
    """Generate one matched-input episode with a fixed hidden rule setting."""
    seed = _validate_seed(seed)
    normalized = _validate_settings(settings)
    demos = _validate_count("demos", demos)
    queries = _validate_count("queries", queries)
    selected = normalized[PARAMETER_NAME]

    inputs = _unique_inputs(seed, demos + queries)
    pairs = [
        {
            "input": deepcopy(grid),
            "output": _PROTOTYPE.apply_rule(grid, selected),
        }
        for grid in inputs
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(normalized),
    }
