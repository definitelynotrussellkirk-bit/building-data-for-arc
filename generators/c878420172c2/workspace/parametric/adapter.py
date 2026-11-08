"""Native normalized-overlap family for c878420172c2.

``all_overlap`` is the exact selected canonical rule. ``largest_component``
first computes the normalized color-2/color-3 overlap and then keeps only its
largest four-connected component (row-major top-left breaks equal-size ties).
Inputs are matched across settings.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
MODES = ("all_overlap", "largest_component")
DEFAULT = {"overlap_mode": "all_overlap"}


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"overlap_mode"}
            or type(settings["overlap_mode"]) is not str
            or settings["overlap_mode"] not in MODES):
        raise ValueError("settings must contain only a supported overlap_mode")
    return settings["overlap_mode"]


def program(settings) -> str:
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "all_overlap" else "largest_component.rkt"
    return (HERE / name).read_text()


def _validate_grid(grid) -> tuple[int, int]:
    if (type(grid) is not list or not 5 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 5 <= len(grid[0]) <= 30):
        raise ValueError("expected a rectangular 5..30 grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid cells must be exact ARC integer colors")
    return len(grid), width


def normalize_color(grid, color: int):
    _validate_grid(grid)
    if type(color) is not int or color not in (2, 3):
        raise ValueError("color must be 2 or 3")
    cells = {(row, column) for row, values in enumerate(grid)
             for column, value in enumerate(values) if value == color}
    if not cells:
        return set()
    row0 = min(row for row, _ in cells)
    column0 = min(column for _, column in cells)
    return {(row - row0, column - column0) for row, column in cells}


def stage_a(grid):
    """Return the input-dependent normalized intersection set."""
    return normalize_color(grid, 2) & normalize_color(grid, 3)


def components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        first = min(remaining)
        component = {first}
        stack = [first]
        remaining.remove(first)
        while stack:
            row, column = stack.pop()
            for neighbor in ((row - 1, column), (row + 1, column),
                             (row, column - 1), (row, column + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return sorted(result, key=lambda part: (-len(part), min(part)))


def _paint(cells, height: int, width: int):
    out = [[0] * width for _ in range(height)]
    for row, column in cells:
        if 0 <= row < height and 0 <= column < width:
            out[row][column] = 8
    return out


def stage_b(intersection, height: int, width: int):
    _integer(height, 1, 30, "height")
    _integer(width, 1, 30, "width")
    parts = components(intersection)
    return _paint(parts[0] if parts else set(), height, width)


def solve(grid, overlap_mode="all_overlap"):
    if type(overlap_mode) is not str or overlap_mode not in MODES:
        raise ValueError("unknown overlap mode")
    height, width = _validate_grid(grid)
    intersection = stage_a(grid)
    if overlap_mode == "all_overlap":
        return _paint(intersection, height, width)
    return stage_b(intersection, height, width)


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"c878420172c2-parametric-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _local_pair(height: int, width: int, rng: random.Random):
    core_height = 2 + rng.randrange(2)
    core_width = 2 + rng.randrange(2)
    if core_height * core_width >= 8:
        core_height = 2
    core = {(row, column) for row in range(core_height)
            for column in range(core_width)}
    midpoint_row = max(core_height + 1, height // 2)
    midpoint_column = max(core_width + 1, width // 2)

    shape2 = set(core)
    shape2.update((0, column) for column in range(core_width, width))
    shape2.update((row, width - 1) for row in range(1, height))
    shape2.update((row, column)
                  for row in range(1, midpoint_row)
                  for column in range(midpoint_column, width - 1))

    shape3 = set(core)
    shape3.update((row, 0) for row in range(core_height, height))
    shape3.update((height - 1, column) for column in range(1, width))
    shape3.update((row, column)
                  for row in range(midpoint_row, height - 1)
                  for column in range(1, midpoint_column))

    # Add a two-cell shared component diagonally adjacent to the main core.
    # Shape 2 reaches it from the top/right route; shape 3 reaches it from the
    # left/bottom route.  Their exclusive connectors do not overlap, so the
    # normalized intersection has core + domino + far singleton components.
    secondary_row = core_height
    secondary_column = core_width
    secondary = {(secondary_row, secondary_column),
                 (secondary_row, secondary_column + 1)}
    shape2.update(secondary)
    shape2.update((secondary_row, column)
                  for column in range(secondary_column, width))
    shape3.update(secondary)
    shape3.update((row, secondary_column)
                  for row in range(secondary_row, height))

    if rng.randrange(2):
        shape2 = {(height - 1 - row, column) for row, column in shape2}
        shape3 = {(height - 1 - row, column) for row, column in shape3}
    if rng.randrange(2):
        shape2 = {(row, width - 1 - column) for row, column in shape2}
        shape3 = {(row, width - 1 - column) for row, column in shape3}
    return shape2, shape3


def _profile(seed: int, split: str, index: int):
    demo_specs = (
        (12, 14, 5, 10), (14, 16, 6, 11), (16, 18, 7, 12),
        (18, 20, 8, 14), (22, 24, 10, 17), (24, 26, 11, 18),
    )
    query_specs = (
        (13, 15, 5, 11), (20, 22, 9, 16),
        (30, 30, 13, 22), (27, 29, 12, 21),
    )
    height, width, local_height, local_width = (
        demo_specs if split == "train" else query_specs
    )[index]
    rng = _rng(seed, split, index)
    shape2, shape3 = _local_pair(local_height, local_width, rng)
    grid = [[0] * width for _ in range(height)]

    row2, column2 = 0, 0
    row3, column3 = height - local_height, width - local_width
    if row2 + local_height > row3:
        raise ValueError("profile shapes overlap vertically")
    for row, column in shape2:
        grid[row2 + row][column2 + column] = 2
    for row, column in shape3:
        if grid[row3 + row][column3 + column] != 0:
            raise ValueError("profile shape collision")
        grid[row3 + row][column3 + column] = 3
    return grid


def generate(seed, settings, demos, queries):
    mode = _mode(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    banks = {
        "train": [_profile(seed, "train", index) for index in range(6)],
        "test": [_profile(seed, "test", index) for index in range(4)],
    }
    result = {}
    for split, count in (("train", demos), ("test", queries)):
        result[split] = [
            {"input": copy.deepcopy(grid), "output": solve(grid, mode)}
            for grid in banks[split][:count]
        ]
    return {**result, "program_solution": program(settings), "seed": seed,
            "settings": copy.deepcopy(settings)}


def public_turn(episode, query_index):
    _integer(query_index, 0, 3, "query_index")
    if (type(episode) is not dict or type(episode.get("train")) is not list
            or type(episode.get("test")) is not list
            or query_index >= len(episode["test"])):
        raise ValueError("episode does not contain the requested query")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
