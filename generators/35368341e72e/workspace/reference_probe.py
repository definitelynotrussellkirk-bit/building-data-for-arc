"""Independent, task-local oracle and replay fixtures for 35368341e72e.

This module does not import production helpers other than through load_generator().
Its grid translation mirrors the selected Racket rule from the public layout:
row-0 keys identify fixed 3x3 panels, and the final row selects panels in order.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "35368341e72e"
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"reference_probe_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def prototype_lookup(grid: list[list[int]]) -> dict[int, list[list[int]]]:
    return {
        value: [row[col - 1 : col + 2] for row in grid[1:4]]
        for col, value in enumerate(grid[0])
        if value != 0
    }


def gallery(parts: list[list[list[int]]]) -> list[list[int]]:
    if not parts:
        return [[0]]
    out = [[0] * (4 * len(parts) - 1) for _ in range(3)]
    for index, part in enumerate(parts):
        left = 4 * index
        for row in range(3):
            for col in range(3):
                value = part[row][col]
                if value != 0:
                    out[row][left + col] = value
    return out


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    lookup = prototype_lookup(grid)
    query = [value for value in grid[-1] if value != 0]
    return gallery([lookup[value] for value in query])


def deduplicate_query_output(grid: list[list[int]]) -> list[list[int]]:
    lookup = prototype_lookup(grid)
    seen: set[int] = set()
    query: list[int] = []
    for value in grid[-1]:
        if value != 0 and value not in seen:
            seen.add(value)
            query.append(value)
    return gallery([lookup[value] for value in query])


def observed(grid: list[list[int]]) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_keys": sum(value != 0 for value in grid[0]),
        "query_len": sum(value != 0 for value in grid[-1]),
    }


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def repeated_query(grid: list[list[int]]) -> bool:
    query = [value for value in grid[-1] if value != 0]
    return len(query) > len(set(query))


def witness_input() -> list[list[int]]:
    """A minimal lawful counterexample to 'remove duplicate query keys'."""
    return [
        [0, 1, 0, 0, 2, 0, 0, 3, 0, 0, 0],
        [4, 0, 0, 0, 5, 0, 0, 0, 6, 0, 0],
        [0, 4, 0, 5, 0, 5, 0, 6, 0, 0, 0],
        [0, 0, 4, 0, 5, 0, 6, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
