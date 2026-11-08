"""Finite doubled-diagonal family for 827c34fc8e04.

The default paints a trail for every marker.  The alternate first selects the
highest-color marker (row-major tie break) and paints only its diagonal trail.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "827c34fc8e04"
HERE = Path(__file__).resolve().parent
SETTINGS = [
    {"trail_mode": "all_markers"},
    {"trail_mode": "max_color_marker"},
]
DEFAULT_SETTINGS = SETTINGS[0]
PROGRAM_FILES = {
    "all_markers": "canonical.rkt",
    "max_color_marker": "max-color-marker.rkt",
}
DEMO_SHAPES = ((4, 5), (5, 4), (6, 6), (7, 8), (8, 7), (9, 9))
QUERY_SHAPES = ((5, 7), (8, 10), (12, 13), (15, 15))


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"trail_mode"}:
        raise ValueError("settings must contain exactly trail_mode")
    value = settings["trail_mode"]
    if value not in PROGRAM_FILES:
        raise ValueError("trail_mode must be all_markers or max_color_marker")
    return value


def _grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must have 1..30 rows")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(
        type(row) is not list or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular 1..30 with exact ARC colors")
    return grid


def program(settings: dict[str, str]) -> str:
    return (HERE / PROGRAM_FILES[_setting(settings)]).read_text(encoding="utf-8")


def _markers(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [(r, c, value) for r, row in enumerate(_grid(grid))
            for c, value in enumerate(row) if value != 0]


def intermediate(grid: list[list[int]], settings: dict[str, str]) -> dict[str, Any]:
    mode = _setting(settings)
    markers = _markers(grid)
    if not markers:
        raise ValueError("input needs at least one marker")
    if mode == "all_markers":
        selected = markers
    else:
        selected = [max(markers, key=lambda item: (item[2], -item[0], -item[1]))]
    return {
        "all_markers": [list(item) for item in markers],
        "selected_markers": [list(item) for item in selected],
        "selected_diagonals": [r - c for r, c, _value in selected],
    }


def transform(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    grid = _grid(grid)
    h, w = len(grid), len(grid[0])
    selected = intermediate(grid, settings)["selected_markers"]
    output = [[0] * (2 * w) for _ in range(2 * h)]
    for r in range(2 * h):
        for c in range(2 * w):
            source = grid[r // 2][c // 2]
            if source:
                output[r][c] = source
            elif any(r - c == 2 * (sr - sc) for sr, sc, _value in selected):
                output[r][c] = 1
    return output


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    shapes = DEMO_SHAPES if split == "train" else QUERY_SHAPES
    _integer(index, "index", 0, len(shapes) - 1)
    h, w = shapes[index]
    # Three separated, distinct-diagonal anchors. Rotating the color assignment
    # makes the selected max-color anchor vary without changing the input grammar.
    positions = [(1, 1), (h - 2, 1), (1, w - 2)]
    if len({r - c for r, c in positions}) != 3:
        raise RuntimeError("profile markers must occupy distinct diagonals")
    rng = _rng(seed, split, index)
    low = rng.sample([2, 3, 4, 5, 6, 7, 8], 2)
    colors = [low[0], low[1], 9]
    shift = index % 3
    colors = colors[-shift:] + colors[:-shift] if shift else colors
    grid = [[0] * w for _ in range(h)]
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color
    return grid


def generate(seed, settings, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result = {"train": [], "test": [], "program_solution": program(settings),
              "settings": deepcopy(settings), "seed": seed, "prototype": True}
    seen: set[str] = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            digest = json.dumps(grid, separators=(",", ":"))
            if digest in seen:
                raise RuntimeError("sampler produced duplicate inputs")
            seen.add(digest)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result
