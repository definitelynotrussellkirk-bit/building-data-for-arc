"""Exact-adjacent native adapter for the concentric-layer family."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
_path = BASE / "family.py"
_spec = importlib.util.spec_from_file_location("_layers_45a5af55_family", _path)
_family = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _family
_spec.loader.exec_module(_family)

SETTINGS = _family.SETTINGS
DEPENDENCY = _family.DEPENDENCY
analyze = _family.analyze
solve = _family.solve
sample = _family.sample
public_views = _family.public_views


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"layer_order"} or settings["layer_order"] not in SETTINGS:
        raise ValueError("Expected exactly layer_order=outside_in or inside_out")
    return settings["layer_order"]


def program(settings):
    order = _setting(settings)
    return (BASE / ("canonical.rkt" if order == "outside_in" else "inside_out.rkt")).read_text()


def generate(seed, settings, demos, queries):
    order = _setting(settings)
    if type(seed) is not int or isinstance(seed, bool) or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(demos) is not int or isinstance(demos, bool) or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or isinstance(queries, bool) or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")

    def pair(split, index):
        grid = sample(seed, split, index)
        return {"input": grid, "output": solve(grid, order)}

    return {
        "train": [pair("train", index) for index in range(demos)],
        "test": [pair("test", index) for index in range(queries)],
        "program_solution": program(settings),
        "private": {"seed": seed, "settings": copy.deepcopy(settings)},
    }
