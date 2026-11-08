"""Native spiral-with-optional-terminal-route family for e8b6ff767c21."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from pathlib import Path
from typing import Any


TASK_ID = "e8b6ff767c21"
OVERLAYS = ("none", "terminal_path")
DEMO_LIMIT = 6
QUERY_LIMIT = 4
_HOME = Path(__file__).resolve().parent
CANONICAL_PATH = _HOME / "canonical.rkt"
TERMINAL_PATH = _HOME / "terminal_path.rkt"
_DIRS = ((0, 1), (1, 0), (0, -1), (-1, 0))

_DEMO_CHOICES = (
    ((6, 8), (7, 9), (8, 11), (9, 12)),
    ((9, 9), (10, 12), (11, 10), (12, 13)),
    ((12, 17), (13, 18), (14, 16), (15, 19)),
    ((17, 11), (18, 12), (19, 13), (20, 14)),
    ((23, 19), (24, 20), (25, 21), (26, 22)),
    ((28, 28), (27, 26), (28, 25), (26, 28)),
)
_QUERY_CHOICES = (
    ((5, 30), (6, 29), (7, 30), (8, 29)),
    ((30, 5), (29, 6), (30, 7), (29, 8)),
    ((21, 27), (22, 26), (23, 27), (24, 25)),
    ((30, 30),),
)


def _settings(value: Any) -> str:
    if not isinstance(value, dict) or set(value) != {"route_overlay"}:
        raise ValueError("settings must name exactly route_overlay")
    overlay = value["route_overlay"]
    if overlay not in OVERLAYS:
        raise ValueError("route_overlay must be none or terminal_path")
    return overlay


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low},{high}]")
    return value


def program(settings: dict[str, str]) -> str:
    overlay = _settings(settings)
    path = CANONICAL_PATH if overlay == "none" else TERMINAL_PATH
    source = path.read_text(encoding="utf-8")
    if not source.startswith("(rule!"):
        raise ValueError(f"invalid Racket program resource: {path.name}")
    return source


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid rows must be non-empty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    height = len(grid)
    if not 5 <= height <= 30 or not 5 <= width <= 30:
        raise ValueError("grid dimensions must both be in 5..30")
    if any(type(value) is not int or value != 0 for row in grid for value in row):
        raise ValueError("every input cell must be integer background 0")
    return height, width


def _spiral_state(height: int, width: int) -> tuple[list[list[int]], tuple[int, int]]:
    output = [[0 for _ in range(width)] for _ in range(height)]
    row = col = 0
    output[0][0] = 3
    segment = 0
    while True:
        base = width - 1 if segment % 2 == 0 else height - 1
        shrink = 0 if segment < 3 else 2 * ((segment - 1) // 2)
        length = base - shrink
        if length <= 0:
            return output, (row, col)
        dr, dc = _DIRS[segment % 4]
        for _ in range(length):
            row += dr
            col += dc
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = 3
        segment += 1


def _route(spiral: list[list[int]], endpoint: tuple[int, int]) -> list[tuple[int, int]]:
    height, width = len(spiral), len(spiral[0])
    targets = {
        (endpoint[0] + dr, endpoint[1] + dc)
        for dr, dc in _DIRS
        if 0 <= endpoint[0] + dr < height
        and 0 <= endpoint[1] + dc < width
        and spiral[endpoint[0] + dr][endpoint[1] + dc] == 0
    }
    if not targets:
        raise RuntimeError("spiral terminal has no adjacent corridor cell")
    start = (1, 0)
    if spiral[start[0]][start[1]] != 0:
        raise RuntimeError("spiral entrance is not an open corridor")
    queue: deque[tuple[tuple[int, int], list[tuple[int, int]]]] = deque([(start, [start])])
    seen = {start}
    while queue:
        current, path = queue.popleft()
        if current in targets:
            return path
        for dr, dc in _DIRS:
            neighbor = (current[0] + dr, current[1] + dc)
            if (
                0 <= neighbor[0] < height
                and 0 <= neighbor[1] < width
                and spiral[neighbor[0]][neighbor[1]] == 0
                and neighbor not in seen
            ):
                seen.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    raise RuntimeError("spiral terminal corridor is unreachable from entrance")


def route_metadata(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    spiral, endpoint = _spiral_state(height, width)
    path = _route(spiral, endpoint)
    return {
        "spiral_endpoint": list(endpoint),
        "entrance": [1, 0],
        "terminal_neighbor": list(path[-1]),
        "route": [list(point) for point in path],
        "route_length": len(path),
    }


def native_transform(grid: list[list[int]], overlay: str) -> list[list[int]]:
    if overlay not in OVERLAYS:
        raise ValueError("overlay must be none or terminal_path")
    height, width = _validate_grid(grid)
    spiral, endpoint = _spiral_state(height, width)
    if overlay == "none":
        return spiral
    output = deepcopy(spiral)
    for row, col in _route(spiral, endpoint):
        output[row][col] = 2
    return output


def _shape(seed: int, role: str, index: int) -> tuple[int, int]:
    choices = _DEMO_CHOICES[index] if role == "demo" else _QUERY_CHOICES[index]
    return choices[(seed + 3 * index + (0 if role == "demo" else 1)) % len(choices)]


def _scene(seed: int, role: str, index: int) -> list[list[int]]:
    height, width = _shape(seed, role, index)
    return [[0 for _ in range(width)] for _ in range(height)]


def _pair(grid: list[list[int]], overlay: str) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(grid), "output": native_transform(grid, overlay)}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, DEMO_LIMIT)
    queries = _integer("queries", queries, 1, QUERY_LIMIT)
    overlay = _settings(settings)

    demo_inputs = [_scene(seed, "demo", index) for index in range(demos)]
    query_bank = [_scene(seed, "query", index) for index in range(QUERY_LIMIT)]
    selected_queries = query_bank[:queries]
    all_inputs = demo_inputs + selected_queries
    shapes = [(len(grid), len(grid[0])) for grid in all_inputs]
    if len(set(shapes)) != len(shapes):
        raise RuntimeError("episode inputs must be distinct")
    for grid in all_inputs:
        if native_transform(grid, "none") == native_transform(grid, "terminal_path"):
            raise RuntimeError("scene does not distinguish route overlays")

    return {
        "train": [_pair(grid, overlay) for grid in demo_inputs],
        "test": [_pair(grid, overlay) for grid in selected_queries],
        "program_solution": program(settings),
    }
