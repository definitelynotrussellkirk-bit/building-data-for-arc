"""Finite parametric adapter for ARC task 14dacb3b518f."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

_HOME = Path(__file__).resolve().parent


def _load_prototype():
    path = _HOME / "prototype.py"
    name = "_arc_parametric_prototype_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load local prototype: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: Any) -> str:
    prototype = _load_prototype()
    normalized = prototype.validate_settings(settings)
    path = _HOME / "rules" / f"{normalized['rule_mode']}.rkt"
    return path.read_text(encoding="utf-8")


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    prototype = _load_prototype()
    normalized = prototype.validate_settings(settings)
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    demo_inputs, query_inputs = prototype.generate_inputs(seed, demos, queries)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {
            "input": copy.deepcopy(grid),
            "output": prototype.solve(grid, normalized),
        }

    return {
        "train": [pair(grid) for grid in demo_inputs],
        "test": [pair(grid) for grid in query_inputs],
        "program_solution": program(normalized),
    }
