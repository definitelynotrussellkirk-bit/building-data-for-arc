"""Native parametric adapter for b87dcd3011b1."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent


def _load_local(name: str, filename: str):
    path = HERE / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load_local("_b87dcd3011b1_parametric_prototype", "prototype.py")
PROGRAMS = {
    "all_pairs": (HERE / "canonical.rkt").read_text(),
    "widest_pair_only": (HERE / "widest_pair_only.rkt").read_text(),
}


def _settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"portal_policy"}:
        raise ValueError("settings must name exactly portal_policy")
    policy = settings["portal_policy"]
    if type(policy) is not str or policy not in PROGRAMS:
        raise ValueError("portal_policy must be all_pairs or widest_pair_only")
    return policy


def program(settings: dict[str, Any]) -> str:
    return PROGRAMS[_settings(settings)]


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    if type(seed) is not int or seed < 0:
        raise TypeError("seed must be a nonnegative exact integer")
    policy = _settings(settings)
    if type(demos) is not int or not 3 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 3..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")

    def pairs(role: str, count: int) -> list[dict[str, list[list[int]]]]:
        result = []
        for index in range(count):
            grid = prototype.build_scene(seed, role, index)
            result.append({"input": grid, "output": prototype.apply_policy(grid, policy)})
        return result

    return {
        "train": pairs("demo", demos),
        "test": pairs("query", queries),
        "program_solution": PROGRAMS[policy],
    }
