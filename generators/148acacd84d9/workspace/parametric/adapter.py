"""Native adapter for canonical rotation and rotate-then-marker-gravity."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def _adjacent(name):
    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_148acacd84d9_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _adjacent("prototype")
RULES = _adjacent("rules")
VALUES = ("none", "marker_relay")


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"post_rotation"}
            or type(settings["post_rotation"]) is not str
            or settings["post_rotation"] not in VALUES):
        raise ValueError("settings must contain exactly one supported post_rotation value")
    return settings["post_rotation"]


def program(settings):
    _mode(settings)
    return RULES.program(settings)


def generate(seed, settings, demos=3, queries=4):
    mode = _mode(settings)
    inputs = PROTOTYPE.build_inputs(seed, demos, queries)
    return {
        split: [{"input": grid, "output": RULES.python_apply(grid, mode)}
                for grid in grids]
        for split, grids in inputs.items()
    } | {"program_solution": program(settings)}


def public_turn(episode, query_index=0):
    return PROTOTYPE.public_turn(episode, query_index)
