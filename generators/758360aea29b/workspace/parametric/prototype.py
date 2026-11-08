"""Finite width-comparison family for 758360aea29b.

The default is the byte-exact canonical pairwise-width rule.  The alternate
selects the unique tallest rectangle, carries its width as an intermediate,
and compares every object by absolute distance from that pivot width.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "758360aea29b"
HERE = Path(__file__).resolve().parent
SETTINGS = [
    {"comparison_mode": "pairwise_width"},
    {"comparison_mode": "pivot_distance"},
]
DEFAULT_SETTINGS = SETTINGS[0]
PROGRAM_FILES = {
    "pairwise_width": "canonical.rkt",
    "pivot_distance": "pivot-distance.rkt",
}
DEMO_PROFILES = (
    (10, 12, (1, 3, 5, 1), (2, 4, 1, 2)),
    (10, 14, (2, 4, 2, 5), (1, 2, 4, 2)),
    (14, 16, (5, 2, 4, 5, 1), (2, 1, 4, 2, 3)),
    (14, 18, (3, 1, 5, 3, 2), (2, 3, 1, 4, 2)),
    (16, 20, (4, 2, 6, 1, 4, 3), (1, 2, 3, 4, 2, 1)),
    (18, 22, (2, 5, 3, 2, 6, 4), (2, 1, 4, 3, 1, 2)),
)
QUERY_PROFILES = (
    (14, 16, (1, 4, 2, 5, 1), (2, 4, 1, 2, 3)),
    (18, 20, (5, 3, 1, 4, 5, 2), (1, 2, 4, 3, 2, 1)),
    (24, 26, (2, 6, 4, 2, 5, 3, 1), (2, 1, 3, 4, 1, 2, 3)),
    (30, 30, (5, 2, 7, 4, 5, 1, 3), (1, 2, 3, 4, 2, 1, 3)),
)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"comparison_mode"}:
        raise ValueError("settings must contain exactly comparison_mode")
    value = settings["comparison_mode"]
    if value not in PROGRAM_FILES:
        raise ValueError("comparison_mode must be pairwise_width or pivot_distance")
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


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    grid = _grid(grid)
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for start_r in range(h):
        for start_c in range(w):
            if grid[start_r][start_c] == 0 or (start_r, start_c) in seen:
                continue
            color = grid[start_r][start_c]
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= rr < h and 0 <= cc < w
                        and grid[rr][cc] == color and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
            result.append({"r1": r1, "c1": c1, "height": r2 - r1 + 1,
                           "width": c2 - c1 + 1, "cells": cells})
    result.sort(key=lambda item: (item["r1"], item["c1"]))
    return result


def intermediate(grid: list[list[int]], settings: dict[str, str]) -> dict[str, Any]:
    mode = _setting(settings)
    objects = _objects(grid)
    if not objects:
        raise ValueError("input needs at least one object")
    widths = [item["width"] for item in objects]
    if mode == "pairwise_width":
        return {"object_widths": widths, "comparison_scores": widths}
    pivot_index = max(range(len(objects)), key=lambda i: objects[i]["height"])
    pivot_width = widths[pivot_index]
    return {
        "object_widths": widths,
        "pivot_object_index": pivot_index,
        "pivot_width": pivot_width,
        "comparison_scores": [abs(width - pivot_width) for width in widths],
    }


def transform(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    scores = intermediate(grid, settings)["comparison_scores"]
    return [[1 if left == right else 2 if left > right else 3 for right in scores]
            for left in scores]


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _positions(height: int, width: int, count: int, max_width: int) -> list[tuple[int, int]]:
    positions = [
        (r, c)
        for r in range(0, height - 3, 5)
        for c in range(0, width - max_width + 1, max_width + 2)
    ]
    if len(positions) < count:
        raise ValueError(f"{height}x{width} cannot hold {count} separated rectangles")
    return sorted(positions[:count])


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    _integer(index, "index", 0, len(profiles) - 1)
    height, width, widths, heights = profiles[index]
    if len(widths) != len(heights) or heights.count(max(heights)) != 1:
        raise RuntimeError("profile must have one unique tallest object")
    rng = _rng(seed, split, index)
    colors = rng.sample(list(range(2, 10)), len(widths))
    positions = _positions(height, width, len(widths), max(widths))
    grid = [[0] * width for _ in range(height)]
    for (r0, c0), rect_width, rect_height, color in zip(positions, widths, heights, colors):
        if r0 + rect_height > height or c0 + rect_width > width:
            raise RuntimeError("profile rectangle does not fit")
        for r in range(r0, r0 + rect_height):
            for c in range(c0, c0 + rect_width):
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
