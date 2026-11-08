"""Native finite parametric adapter for 4b326abc33f4."""
from __future__ import annotations

from copy import deepcopy

from family import (
    CANONICAL_PROGRAM,
    CYCLIC_NEXT_PROGRAM,
    DEMO_PROFILES,
    QUERY_PROFILES,
    apply_mode,
    build_scene,
)


_PARAMETERS = {"assignment_mode": ("local", "cyclic_next")}


def _settings(value):
    if type(value) is not dict or set(value) != set(_PARAMETERS):
        raise ValueError("settings must name exactly assignment_mode")
    mode = value["assignment_mode"]
    if type(mode) is not str or mode not in _PARAMETERS["assignment_mode"]:
        raise ValueError("assignment_mode is undeclared")
    return mode


def _integer(name, value, low, high):
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def program(settings):
    mode = _settings(settings)
    return CANONICAL_PROGRAM if mode == "local" else CYCLIC_NEXT_PROGRAM


def generate(seed, settings, demos, queries):
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    mode = _settings(settings)

    train = []
    for index, profile in enumerate(DEMO_PROFILES[:demos]):
        grid = build_scene(profile, seed * 101 + index)
        train.append({"input": grid, "output": apply_mode(grid, mode)})
    test = []
    for index, profile in enumerate(QUERY_PROFILES[:queries]):
        grid = build_scene(profile, seed * 1009 + 100 + index)
        test.append({"input": grid, "output": apply_mode(grid, mode)})
    return {
        "program_solution": program({"assignment_mode": mode}),
        "train": deepcopy(train),
        "test": deepcopy(test),
    }
