"""Native alignment-matrix family for 151f4dc0c08f.

The canonical setting emits the direct row/column/45-degree alignment matrix.
The alternative first constructs that graph, computes the connected component
containing the smallest-color marker, then emits the component-membership
matrix.  Inputs are matched across settings and every lesson contains a
transitive chain plus an isolated marker.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from pathlib import Path
import random
from typing import Any

TASK_ID = "151f4dc0c08f"
SETTINGS = ("pair_alignment", "anchor_component")
DEFAULT = "pair_alignment"
PARAMETER = "matrix_rule"
_HERE = Path(__file__).resolve().parent

# (height, width, marker positions).  Role zero is always the smallest-color
# anchor.  The banks are separate so changing the demo count never changes the
# four-query bank or its one-turn prefix.
_DEMO_SPECS = (
    (8, 9, ((1, 1), (2, 2), (2, 5), (6, 0))),
    (9, 10, ((7, 1), (6, 2), (3, 2), (0, 9))),
    (10, 11, ((1, 8), (2, 7), (5, 7), (9, 1), (6, 8))),
    (7, 12, ((0, 0), (1, 1), (1, 6), (6, 10))),
    (12, 12, ((1, 1), (2, 2), (2, 6), (5, 6), (10, 0))),
    (14, 15, ((12, 1), (11, 2), (7, 2), (7, 8), (0, 14))),
)
_QUERY_SPECS = (
    (9, 13, ((1, 10), (2, 9), (6, 9), (8, 1))),
    (16, 17, ((14, 2), (12, 4), (12, 11), (0, 15), (8, 11))),
    (24, 24, ((2, 2), (5, 5), (5, 16), (16, 16), (22, 1))),
    (30, 30, ((1, 1), (5, 5), (5, 20), (20, 20), (25, 25), (29, 0))),
)


def _read(name: str) -> str:
    return (_HERE / name).read_text(encoding="utf-8")


def _setting(settings: dict[str, Any]) -> str:
    if not isinstance(settings, dict) or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must name exactly {PARAMETER}")
    value = settings[PARAMETER]
    if type(value) is not str:
        raise TypeError(f"{PARAMETER} must be a string")
    if value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS}")
    return value


def program(settings: dict[str, Any]) -> str:
    value = _setting(settings)
    return _read("canonical.rkt" if value == DEFAULT else "anchor_component.rkt")


def _validate_count(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid exceeds ARC 30x30 bounds")
    if any(type(row) is not list or len(row) != width or
           any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must contain exact ARC colors")
    return len(grid), width


def _groups(grid: list[list[int]]) -> list[tuple[int, tuple[int, int]]]:
    _validate_grid(grid)
    cells: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                cells.setdefault(value, []).append((r, c))
    if not 2 <= len(cells) <= 6 or any(len(points) != 1 for points in cells.values()):
        raise ValueError("expected 2..6 distinct singleton markers")
    return [(color, cells[color][0]) for color in sorted(cells)]


def _aligned(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] == b[0] or a[1] == b[1] or abs(a[0] - b[0]) == abs(a[1] - b[1])


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    groups = _groups(grid)
    positions = [point for _color, point in groups]
    graph = [[j for j, other in enumerate(positions) if _aligned(point, other)]
             for point in positions]
    direct = sorted(set(graph[0]))
    seen = {0}
    queue = deque([0])
    while queue:
        current = queue.popleft()
        for neighbor in graph[current]:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return {
        "colors": [color for color, _point in groups],
        "positions": positions,
        "graph": graph,
        "anchor_direct_neighborhood": direct,
        "anchor_component": sorted(seen),
    }


def apply_python(grid: list[list[int]], setting: str = DEFAULT) -> list[list[int]]:
    if type(setting) is not str or setting not in SETTINGS:
        raise ValueError(f"setting must be one of {SETTINGS}")
    analysis = analyze(grid)
    n = len(analysis["positions"])
    if setting == "pair_alignment":
        return [[8 if j in analysis["graph"][i] else 0 for j in range(n)] for i in range(n)]
    component = set(analysis["anchor_component"])
    return [[8 if i in component and j in component else 0 for j in range(n)] for i in range(n)]


def apply_wrong_direct_neighbors(grid: list[list[int]]) -> list[list[int]]:
    analysis = analyze(grid)
    n = len(analysis["positions"])
    direct = set(analysis["anchor_direct_neighborhood"])
    return [[8 if i in direct and j in direct else 0 for j in range(n)] for i in range(n)]


def _build(spec: tuple[int, int, tuple[tuple[int, int], ...]], seed: int, slot: int) -> list[list[int]]:
    height, width, raw_positions = spec
    mode = (seed * 17 + slot * 5) % 4
    positions = []
    for r, c in raw_positions:
        if mode & 1:
            r = height - 1 - r
        if mode & 2:
            c = width - 1 - c
        positions.append((r, c))
    rng = random.Random((seed + 1) * 0x9E3779B1 + slot * 0x85EBCA6B)
    palette = sorted(rng.sample(range(1, 10), len(positions)))
    rest = palette[1:]
    rng.shuffle(rest)
    colors = [palette[0], *rest]
    grid = [[0] * width for _ in range(height)]
    for color, (r, c) in zip(colors, positions):
        grid[r][c] = color
    # Authoring invariant: every item contains a genuine transitive extension
    # and at least one marker outside the anchor component.
    analysis = analyze(grid)
    if (analysis["anchor_component"] == analysis["anchor_direct_neighborhood"]
            or len(analysis["anchor_component"]) == len(positions)):
        raise RuntimeError(f"invalid authored relation topology at slot {slot}")
    return grid


def _pairs(specs, seed: int, setting: str, count: int, offset: int) -> list[dict[str, Any]]:
    result = []
    for index, spec in enumerate(specs[:count]):
        grid = _build(spec, seed, offset + index)
        result.append({"input": grid, "output": apply_python(grid, setting)})
    return result


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    demos = _validate_count(demos, 2, 6, "demos")
    queries = _validate_count(queries, 1, 4, "queries")
    selected = _setting(settings)
    train = _pairs(_DEMO_SPECS, seed, selected, demos, 0)
    test = _pairs(_QUERY_SPECS, seed, selected, queries, 100)
    visible = [repr(pair["input"]) for pair in train + test]
    if len(visible) != len(set(visible)):
        raise RuntimeError("authored episode contains duplicate inputs")
    rival = next(value for value in SETTINGS if value != selected)
    if not any(apply_python(pair["input"], rival) != pair["output"] for pair in train):
        raise RuntimeError("demonstrations do not distinguish the selected setting")
    return {
        "train": deepcopy(train),
        "test": deepcopy(test),
        "program_solution": program({PARAMETER: selected}),
    }
