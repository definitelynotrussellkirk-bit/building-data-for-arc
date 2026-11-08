"""Matched-input wall-distance scope family for ARC task ``dc382c7da9a9``.

``all_equidistant`` is the byte-exact canonical rule: paint every blank cell
whose wall-constrained distances from the red and green seeds are equal.

``shortest_path_midpoints`` adds a non-collapsing global relay. Stage A runs BFS
from both seeds and retains their input-dependent shortest-path length L. Stage B
consumes L together with both distance maps and paints only equal-distance cells
whose distance sum is exactly L, i.e. midpoint cells lying on a shortest path.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
from pathlib import Path
from typing import Any

TASK_ID = "dc382c7da9a9"
HERE = Path(__file__).resolve().parent
DISTANCE_SCOPES = ("all_equidistant", "shortest_path_midpoints")
DEFAULT_SCOPE = "all_equidistant"


def _settings(value: Any) -> str:
    if type(value) is not dict or set(value) != {"distance_scope"}:
        raise ValueError("settings must contain only distance_scope")
    scope = value["distance_scope"]
    if type(scope) is not str or scope not in DISTANCE_SCOPES:
        raise ValueError(
            "distance_scope must be all_equidistant or shortest_path_midpoints"
        )
    return scope


def _request(seed: Any, demos: Any, queries: Any) -> tuple[int, int, int]:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    return seed, demos, queries


def program(settings: Any) -> str:
    scope = _settings(settings)
    filename = "canonical.rkt" if scope == DEFAULT_SCOPE else "shortest_path_midpoints.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 3 <= len(value) <= 30
        or type(value[0]) is not list
        or not 3 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 3..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    palette = {cell for row in value for cell in row}
    if palette != {0, 2, 3, 5}:
        raise ValueError("admitted grids use exactly blank 0, seeds 2/3, and wall 5")
    if sum(cell == 2 for row in value for cell in row) != 1:
        raise ValueError("grid must contain exactly one red seed")
    if sum(cell == 3 for row in value for cell in row) != 1:
        raise ValueError("grid must contain exactly one green seed")
    return value


def _neighbors(point: tuple[int, int], height: int, width: int):
    row, col = point
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = row + dr, col + dc
        if 0 <= rr < height and 0 <= cc < width:
            yield rr, cc


def _distances(grid: list[list[int]], start: tuple[int, int]) -> dict[tuple[int, int], int]:
    height, width = len(grid), len(grid[0])
    distances = {start: 0}
    pending = deque([start])
    while pending:
        point = pending.popleft()
        for neighbor in _neighbors(point, height, width):
            row, col = neighbor
            if grid[row][col] != 5 and neighbor not in distances:
                distances[neighbor] = distances[point] + 1
                pending.append(neighbor)
    return distances


def analyze(value: Any) -> dict[str, Any]:
    grid = _grid(value)
    seed_2 = next((r, c) for r, row in enumerate(grid) for c, cell in enumerate(row) if cell == 2)
    seed_3 = next((r, c) for r, row in enumerate(grid) for c, cell in enumerate(row) if cell == 3)
    distance_2 = _distances(grid, seed_2)
    distance_3 = _distances(grid, seed_3)
    if seed_3 not in distance_2:
        raise ValueError("the two seeds must be connected")
    shortest = distance_2[seed_3]
    equal = []
    midpoints = []
    for row, values in enumerate(grid):
        for col, cell in enumerate(values):
            point = (row, col)
            if (
                cell == 0
                and point in distance_2
                and point in distance_3
                and distance_2[point] == distance_3[point]
            ):
                equal.append(point)
                if distance_2[point] + distance_3[point] == shortest:
                    midpoints.append(point)
    if not equal or not midpoints:
        raise ValueError("admitted grids require both equidistant and shortest-path midpoint blanks")
    return {
        "seed_2": seed_2,
        "seed_3": seed_3,
        "distance_2": distance_2,
        "distance_3": distance_3,
        "shortest_distance": shortest,
        "equal_cells": tuple(equal),
        "midpoint_cells": tuple(midpoints),
    }


def solve(value: Any, scope: str) -> list[list[int]]:
    if scope not in DISTANCE_SCOPES:
        raise ValueError(f"unknown distance scope: {scope!r}")
    grid = _grid(value)
    facts = analyze(grid)
    selected = facts["equal_cells"] if scope == "all_equidistant" else facts["midpoint_cells"]
    output = deepcopy(grid)
    for row, col in selected:
        output[row][col] = 8
    return output


def _rotate(grid: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in zip(*grid[::-1]))


def _reflect(grid: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in grid)


def _swap_endpoints(grid: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(3 if cell == 2 else 2 if cell == 3 else cell for cell in row) for row in grid)


def _variants(value: list[list[int]]) -> tuple[list[list[int]], ...]:
    current = tuple(tuple(row) for row in value)
    ordered = []
    seen = set()
    for _ in range(4):
        for transformed in (current, _reflect(current)):
            for candidate in (transformed, _swap_endpoints(transformed)):
                if candidate not in seen:
                    seen.add(candidate)
                    ordered.append([list(row) for row in candidate])
        current = _rotate(current)
    return tuple(ordered)


@lru_cache(maxsize=1)
def _public_inputs() -> tuple[list[list[int]], ...]:
    from reviewer_support import load_selected_generator

    parent, _path, _sha = load_selected_generator(TASK_ID)
    return tuple(deepcopy(parent._PUBLIC_INPUTS[name]) for name in (
        "public_1", "public_3", "public_2", "public_5", "public_4"
    ))


def _stable_index(seed: int, label: str, modulus: int) -> int:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{label}".encode()).digest()
    return int.from_bytes(digest[:8], "big") % modulus


def _room(height: int, width: int, orientation: str, code: int) -> list[list[int]]:
    grid = [[5] * width for _ in range(height)]
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            grid[row][col] = 0

    if orientation == "vertical":
        seed_row = max(2, min(height - 3, height // 2 + (code % 3) - 1))
        midpoint = width // 2
        radius = min(4 + code % 4, midpoint - 2, width - midpoint - 3)
        seed_2, seed_3 = (seed_row, midpoint - radius), (seed_row, midpoint + radius)
        for row in range(3, height - 2, 4):
            if abs(row - seed_row) <= 1:
                continue
            gaps = {2 + ((row + code) % 3), midpoint, width - 3 - ((row + code) % 3)}
            for col in range(2, width - 2):
                if col not in gaps:
                    grid[row][col] = 5
    elif orientation == "horizontal":
        seed_col = max(2, min(width - 3, width // 2 + (code % 3) - 1))
        midpoint = height // 2
        radius = min(4 + code % 4, midpoint - 2, height - midpoint - 3)
        seed_2, seed_3 = (midpoint - radius, seed_col), (midpoint + radius, seed_col)
        for col in range(3, width - 2, 4):
            if abs(col - seed_col) <= 1:
                continue
            gaps = {2 + ((col + code) % 3), midpoint, height - 3 - ((col + code) % 3)}
            for row in range(2, height - 2):
                if row not in gaps:
                    grid[row][col] = 5
    else:
        raise ValueError("orientation must be vertical or horizontal")

    grid[seed_2[0]][seed_2[1]] = 2
    grid[seed_3[0]][seed_3[1]] = 3
    facts = analyze(grid)
    if len(facts["equal_cells"]) <= len(facts["midpoint_cells"]):
        raise AssertionError("constructed room does not separate the two settings")
    return grid


def native_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    seed, _demos, _queries = _request(seed, 2, 1)
    demos = []
    for slot, base in enumerate(_public_inputs()):
        variants = _variants(base)
        demos.append(deepcopy(variants[_stable_index(seed, f"demo-{slot}", len(variants))]))
    demos.append(_room(17, 19, "vertical" if seed % 2 == 0 else "horizontal", seed + 41))
    query_specs = (
        (19, 21, "vertical"),
        (21, 23, "horizontal"),
        (25, 25, "vertical" if seed % 2 else "horizontal"),
        (30, 30, "vertical"),
    )
    queries = [
        _room(height, width, orientation, seed * 17 + slot * 31 + 7)
        for slot, (height, width, orientation) in enumerate(query_specs)
    ]
    keys = [hashlib.sha256(repr(grid).encode()).hexdigest() for grid in demos + queries]
    if len(keys) != len(set(keys)):
        raise AssertionError("native episode contains duplicate inputs")
    for grid in demos + queries:
        if solve(grid, DISTANCE_SCOPES[0]) == solve(grid, DISTANCE_SCOPES[1]):
            raise AssertionError("native input does not separate distance scopes")
    return {"train": demos, "test": queries}


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    scope = _settings(settings)
    seed, demos, queries = _request(seed, demos, queries)
    inputs = native_inputs(seed)
    train = [
        {"input": deepcopy(grid), "output": solve(grid, scope)}
        for grid in inputs["train"][:demos]
    ]
    test = [
        {"input": deepcopy(grid), "output": solve(grid, scope)}
        for grid in inputs["test"][:queries]
    ]
    return {"train": train, "test": test, "program_solution": program(settings)}


def rival_output(value: Any, hypothesis: str) -> list[list[int]]:
    grid = _grid(value)
    facts = analyze(grid)
    if hypothesis in DISTANCE_SCOPES:
        return solve(grid, hypothesis)
    output = deepcopy(grid)
    selected: list[tuple[int, int]] = []
    if hypothesis == "manhattan_equidistant":
        a, b = facts["seed_2"], facts["seed_3"]
        selected = [
            (row, col)
            for row, values in enumerate(grid)
            for col, cell in enumerate(values)
            if cell == 0
            and abs(row - a[0]) + abs(col - a[1])
            == abs(row - b[0]) + abs(col - b[1])
        ]
    elif hypothesis == "all_shortest_path_cells":
        selected = [
            point for point, distance in facts["distance_2"].items()
            if grid[point[0]][point[1]] == 0
            and point in facts["distance_3"]
            and distance + facts["distance_3"][point] == facts["shortest_distance"]
        ]
    elif hypothesis == "first_equidistant_only":
        selected = [facts["equal_cells"][0]]
    elif hypothesis == "red_one_step_farther":
        selected = [
            point for point, distance in facts["distance_2"].items()
            if grid[point[0]][point[1]] == 0
            and point in facts["distance_3"]
            and distance == facts["distance_3"][point] + 1
        ]
    elif hypothesis == "identity":
        selected = []
    else:
        raise ValueError(f"unknown rival: {hypothesis}")
    for row, col in selected:
        output[row][col] = 8
    return output
