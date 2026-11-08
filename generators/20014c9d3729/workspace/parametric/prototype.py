"""Matched-input winner-size relay family for 20014c9d3729.

The canonical setting keeps the unique largest object of each color. The
alternate first computes those per-color winners, relays the minimum winner
size as a global threshold, then keeps every object meeting that threshold.
"""
from __future__ import annotations

from collections import deque
import hashlib
from math import ceil
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "20014c9d3729"
VERSION = "winner-size-relay-v1"
PARAMETER = "selection_policy"
POLICIES = ("per_color_largest", "min_winner_threshold")
DEFAULT_SETTINGS = {PARAMETER: POLICIES[0]}
_DIR = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    POLICIES[0]: "canonical.rkt",
    POLICIES[1]: "min-winner-threshold.rkt",
}
_DEMO_DIMS = ((10, 12), (12, 14), (14, 16), (17, 18), (20, 22), (24, 26))
_QUERY_DIMS = ((13, 15), (18, 20), (24, 27), (30, 30))
_THRESHOLDS = (3, 5, 4, 3, 5, 4, 5, 3, 4, 4)
_STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SHAPES = {
    1: ((0, 0),),
    2: ((0, 0), (0, 1)),
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (1, 1), (2, 1)),
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    7: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
    8: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
}


def _exact_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in POLICIES:
        raise ValueError(f"{PARAMETER} must be one of {POLICIES}")
    return value


def program(settings: dict[str, Any]) -> str:
    return (_DIR / _PROGRAM_FILES[_policy(settings)]).read_bytes().decode("utf-8")


def counterfactual_program() -> str:
    return (_DIR / "max-winner-threshold-counterfactual.rkt").read_bytes().decode("utf-8")


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid must fit within 30x30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    groups = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in _STEPS:
                point = (r + dr, c + dc)
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    queue.append(point)
        groups.append({"color": color, "cells": tuple(sorted(cells))})
    return sorted(groups, key=lambda item: (item["color"], min(item["cells"])))


def _winners(grid: list[list[int]]) -> dict[int, dict[str, Any]]:
    by_color: dict[int, list[dict[str, Any]]] = {}
    for component in _components(grid):
        by_color.setdefault(component["color"], []).append(component)
    result = {}
    for color, group in by_color.items():
        ordered = sorted(group, key=lambda item: (-len(item["cells"]), min(item["cells"])))
        if len(ordered) > 1 and len(ordered[0]["cells"]) == len(ordered[1]["cells"]):
            raise ValueError(f"color {color} lacks a unique largest object")
        result[color] = ordered[0]
    if len(result) < 2:
        raise ValueError("scene must contain at least two colors")
    return result


def relay_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    winners = _winners(_validate_grid(grid))
    sizes = {color: len(component["cells"]) for color, component in winners.items()}
    return {
        "winner_sizes": sizes,
        "minimum_winner_size": min(sizes.values()),
        "maximum_winner_size": max(sizes.values()),
        "winner_cells": {color: component["cells"] for color, component in winners.items()},
    }


def _paint(grid: list[list[int]], predicate) -> list[list[int]]:
    out = [[0 for _ in row] for row in grid]
    for component in _components(grid):
        if predicate(component):
            for r, c in component["cells"]:
                out[r][c] = component["color"]
    return out


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    policy = _policy(settings)
    value = relay_intermediate(grid)
    if policy == "per_color_largest":
        chosen = {tuple(cells) for cells in value["winner_cells"].values()}
        return _paint(grid, lambda component: tuple(component["cells"]) in chosen)
    threshold = value["minimum_winner_size"]
    return _paint(grid, lambda component: len(component["cells"]) >= threshold)


def counterfactual_transform(grid: list[list[int]]) -> list[list[int]]:
    value = relay_intermediate(grid)
    threshold = value["maximum_winner_size"]
    return _paint(grid, lambda component: len(component["cells"]) >= threshold)


def _fixed_threshold_four(grid: list[list[int]]) -> list[list[int]]:
    return _paint(grid, lambda component: len(component["cells"]) >= 4)


def _global_largest(grid: list[list[int]]) -> list[list[int]]:
    components = _components(grid)
    largest = min(components, key=lambda item: (-len(item["cells"]), min(item["cells"])))
    cells = tuple(largest["cells"])
    return _paint(grid, lambda component: tuple(component["cells"]) == cells)


def _keep_all(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


SHORTCUTS = {
    "fixed_size_threshold_four": _fixed_threshold_four,
    "global_largest_only": _global_largest,
    "maximum_winner_threshold": counterfactual_transform,
    "keep_all_objects": _keep_all,
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _orient(shape: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    result = tuple(shape)
    if code >= 4:
        result = tuple((r, -c) for r, c in result)
    for _ in range(code % 4):
        result = tuple((c, -r) for r, c in result)
    return _normalize(result)


def _anchors(length: int, count: int, extent: int = 3) -> list[int]:
    if count == 1:
        return [(length - extent) // 2]
    last = length - extent
    return [round(i * last / (count - 1)) for i in range(count)]


def _plans(index: int, stress: bool) -> list[tuple[int, int]]:
    if stress:
        sizes = ((1, 2, 3, 6), (1, 2, 4, 5), (1, 2, 3, 4), (1, 2, 3, 6))
        return [(color_index, size) for color_index, group in enumerate(sizes) for size in group]
    threshold = _THRESHOLDS[index]
    sizes = ((1, threshold + 2), (threshold, threshold + 1), (2, threshold))
    return [(color_index, size) for color_index, group in enumerate(sizes) for size in group]


def _scene(seed: int, split: str, index: int, dims: tuple[int, int], stress: bool = False) -> list[list[int]]:
    raw = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode("ascii")
    rng = random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))
    height, width = dims
    plans = _plans(index if split == "train" else 6 + index, stress)
    colors = rng.sample(range(1, 10), 4 if stress else 3)
    n = len(plans)
    columns = 4 if stress else 3
    rows = ceil(n / columns)
    row_anchors = _anchors(height, rows)
    col_anchors = _anchors(width, columns)
    slots = [(r, c) for r in row_anchors for c in col_anchors][:n]
    if not stress:
        rng.shuffle(slots)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for serial, ((color_index, size), (top, left)) in enumerate(zip(plans, slots, strict=True)):
        shape = _orient(_SHAPES[size], (serial + rng.randrange(8)) % 8)
        shape_h = max(r for r, _ in shape) + 1
        shape_w = max(c for _, c in shape) + 1
        top = min(top, height - shape_h)
        left = min(left, width - shape_w)
        cells = [(top + r, left + c) for r, c in shape]
        if any(grid[r][c] != 0 for r, c in cells):
            raise RuntimeError("slot construction overlapped")
        color = colors[color_index]
        for r, c in cells:
            grid[r][c] = color
    relay_intermediate(grid)
    return grid


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    components = _components(grid)
    cells = [cell for component in components for cell in component["cells"]]
    height, width = len(grid), len(grid[0])
    sides = []
    if any(r == 0 for r, _ in cells): sides.append("top")
    if any(r == height - 1 for r, _ in cells): sides.append("bottom")
    if any(c == 0 for _, c in cells): sides.append("left")
    if any(c == width - 1 for _, c in cells): sides.append("right")
    value = relay_intermediate(grid)
    return {
        "component_count": len(components),
        "nonzero_count": len(cells),
        "occupied_row_span": max(r for r, _ in cells) - min(r for r, _ in cells) + 1,
        "occupied_col_span": max(c for _, c in cells) - min(c for _, c in cells) + 1,
        "boundary_sides": sides,
        "minimum_winner_size": value["minimum_winner_size"],
        "maximum_winner_size": value["maximum_winner_size"],
    }


def lesson_certificate(train: list[dict[str, Any]], settings: dict[str, Any]) -> dict[str, Any]:
    _policy(settings)
    survivors = []
    for policy in POLICIES:
        candidate = {PARAMETER: policy}
        if all(transform(pair["input"], candidate) == pair["output"] for pair in train):
            survivors.append(candidate)
    surviving_shortcuts = [
        name for name, rival in SHORTCUTS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in train)
    ]
    return {
        "surviving_settings": survivors,
        "surviving_shortcuts": surviving_shortcuts,
        "query_outputs_used": False,
    }


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    _exact_int("demos", demos, 2, 6)
    _exact_int("queries", queries, 1, 4)
    _policy(settings)
    demo_inputs = [_scene(seed, "train", i, dims) for i, dims in enumerate(_DEMO_DIMS)]
    query_inputs = [_scene(seed, "test", i, dims, stress=(i == 3)) for i, dims in enumerate(_QUERY_DIMS)]
    train = [{"input": grid, "output": transform(grid, settings)} for grid in demo_inputs[:demos]]
    test = [{"input": grid, "output": transform(grid, settings)} for grid in query_inputs[:queries]]
    return {"train": train, "test": test, "program_solution": program(settings)}
