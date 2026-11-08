"""Independent task oracle and contract probe for e91a8e375e64.

This module deliberately does not import production helpers other than when
``load_generator`` loads the module under test.  Future reviewers can run it
against a staged candidate through ``GENERATOR_UNDER_TEST``.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Callable

from reviewer_support import (
    canonical_pairs as read_canonical_pairs,
    find_root,
    load_selected_generator,
)

TASK_ID = "e91a8e375e64"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def load_generator(path: str | os.PathLike[str] | None = None) -> ModuleType:
    candidate = path or os.environ.get("GENERATOR_UNDER_TEST")
    if candidate is None:
        module, _source, _sha256 = load_selected_generator(TASK_ID, root=ROOT)
        return module

    candidate = Path(candidate)
    spec = importlib.util.spec_from_file_location("generator_under_test", candidate)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return read_canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    side = len(grid)
    if len(grid[0]) != 5 * side + 4:
        raise ValueError("expected width 5P+4")
    for index in range(4):
        separator = index * (side + 1) + side
        if any(row[separator] != 5 for row in grid):
            raise ValueError("separator column is not color 5")
    return [
        [row[index * (side + 1): index * (side + 1) + side] for row in grid]
        for index in range(5)
    ]


def _identity(matrix):
    return [list(row) for row in matrix]


def _rot90(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def _rot180(matrix):
    return [list(reversed(row)) for row in reversed(matrix)]


def _rot270(matrix):
    return [list(row) for row in zip(*matrix)][::-1]


def _flip_h(matrix):
    return [list(reversed(row)) for row in matrix]


def _flip_v(matrix):
    return [list(row) for row in reversed(matrix)]


def _transpose(matrix):
    return [list(row) for row in zip(*matrix)]


def _anti(matrix):
    return _rot180(_transpose(matrix))


TRANSFORMS: tuple[tuple[str, Callable], ...] = (
    ("id", _identity),
    ("rot90", _rot90),
    ("rot180", _rot180),
    ("rot270", _rot270),
    ("flip_h", _flip_h),
    ("flip_v", _flip_v),
    ("transpose", _transpose),
    ("anti", _anti),
)


def infer_transform(a, b) -> tuple[str, Callable]:
    matches = [(name, transform) for name, transform in TRANSFORMS if transform(a) == b]
    if not matches:
        raise ValueError("A does not transform to B")
    return matches[0]


def infer_mapping(c, d) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for source_row, target_row in zip(c, d):
        for source, target in zip(source_row, target_row):
            if source and target:
                if source in mapping and mapping[source] != target:
                    raise ValueError("inconsistent C-to-D mapping")
                mapping[source] = target
    return mapping


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    a, b, c, d, query = split_panels(grid)
    _, transform = infer_transform(a, b)
    mapping = infer_mapping(c, d)
    transformed = transform(query)
    return [[mapping.get(value, value) if value else 0 for value in row] for row in transformed]


def recolor_only_output(grid: list[list[int]]) -> list[list[int]]:
    _, _, c, d, query = split_panels(grid)
    mapping = infer_mapping(c, d)
    return [[mapping.get(value, value) if value else 0 for value in row] for row in query]


def transform_only_output(grid: list[list[int]]) -> list[list[int]]:
    a, b, _, _, query = split_panels(grid)
    _, transform = infer_transform(a, b)
    return transform(query)


def unchanged_query_output(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in split_panels(grid)[4]]


def observed(grid: list[list[int]]) -> dict[str, int]:
    _, _, c, _, _ = split_panels(grid)
    return {
        "panel_size": len(grid),
        "n_map": len({value for row in c for value in row if value != 0}),
    }


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)
