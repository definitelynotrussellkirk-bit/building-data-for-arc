"""Native parametric family for straight-segment interior marking.

The canonical rule marks interiors of every straight blue segment.  The relay
variant first identifies the unique longest segment and its orientation, then
marks interiors only in segments perpendicular to that input-derived controller.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

HERE = Path(__file__).resolve().parent
SCOPES = ("all_segments", "perpendicular_to_longest")
_TRAIN_PROFILES = ((9, 10), (10, 12), (12, 14), (14, 16), (18, 20), (22, 24))
_TEST_PROFILES = ((11, 13), (16, 18), (24, 26), (30, 30))


def _scope(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"scope"}:
        raise ValueError("settings must contain exactly scope")
    value = settings["scope"]
    if value not in SCOPES:
        raise ValueError(f"scope must be one of {SCOPES}")
    return value


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def program(settings: Any) -> str:
    scope = _scope(settings)
    name = "canonical.rkt" if scope == "all_segments" else "perpendicular.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
    if type(value) is not list or not value or any(type(row) is not list for row in value):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(value[0])
    if width == 0 or any(len(row) != width for row in value):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row):
        raise ValueError("grid cells must be integer ARC colors")
    return deepcopy(value)


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for nbr in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nbr in remaining:
                    remaining.remove(nbr)
                    component.add(nbr)
                    stack.append(nbr)
        result.append(component)
    return sorted(result, key=lambda cells: min(cells))


def _segment(component: set[tuple[int, int]]) -> tuple[str, list[tuple[int, int]]]:
    if len(component) < 3:
        raise ValueError("every blue component must contain at least three cells")
    rows = {r for r, _ in component}
    cols = {c for _, c in component}
    if len(rows) == 1:
        cells = sorted(component, key=lambda p: p[1])
        if [c for _, c in cells] != list(range(cells[0][1], cells[-1][1] + 1)):
            raise ValueError("horizontal segment must be contiguous")
        return "horizontal", cells
    if len(cols) == 1:
        cells = sorted(component, key=lambda p: p[0])
        if [r for r, _ in cells] != list(range(cells[0][0], cells[-1][0] + 1)):
            raise ValueError("vertical segment must be contiguous")
        return "vertical", cells
    raise ValueError("blue components must be straight segments")


def segments(value: Any) -> list[dict[str, Any]]:
    grid = _grid(value)
    result = []
    for component in _components(grid):
        orientation, cells = _segment(component)
        result.append({"orientation": orientation, "cells": cells, "length": len(cells)})
    if not result:
        raise ValueError("scene needs blue segments")
    return result


def _controller(value: Any) -> dict[str, Any]:
    found = segments(value)
    maximum = max(segment["length"] for segment in found)
    winners = [segment for segment in found if segment["length"] == maximum]
    if len(winners) != 1:
        raise ValueError("scene needs a unique longest controller segment")
    return winners[0]


def controller_orientation(value: Any) -> str:
    return str(_controller(value)["orientation"])


def transform(value: Any, scope: str) -> list[list[int]]:
    if scope not in SCOPES:
        raise ValueError(f"scope must be one of {SCOPES}")
    grid = _grid(value)
    found = segments(grid)
    if scope == "all_segments":
        selected = found
    else:
        orientation = controller_orientation(grid)
        target = "vertical" if orientation == "horizontal" else "horizontal"
        selected = [segment for segment in found if segment["orientation"] == target]
        if not selected:
            raise ValueError("relay scene needs at least one perpendicular segment")
    output = deepcopy(grid)
    for segment in selected:
        for r, c in segment["cells"][1:-1]:
            output[r][c] = 2
    return output


def scene_invariants(value: Any) -> list[str]:
    try:
        grid = _grid(value)
        found = segments(grid)
        controller = _controller(grid)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    colors = {cell for row in grid for cell in row}
    if not colors <= {0, 1}:
        errors.append(f"unexpected colors: {sorted(colors - {0, 1})}")
    orientations = {segment["orientation"] for segment in found}
    if orientations != {"horizontal", "vertical"}:
        errors.append("scene must contain horizontal and vertical segments")
    if len(found) < 4:
        errors.append("scene must contain at least four separate segments")
    target = "vertical" if controller["orientation"] == "horizontal" else "horizontal"
    if not any(segment["orientation"] == target for segment in found):
        errors.append("scene lacks a perpendicular relay target")
    try:
        if transform(grid, "all_segments") == transform(grid, "perpendicular_to_longest"):
            errors.append("settings do not change the output")
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def _rng(seed: int, split: str, index: int, attempt: int) -> random.Random:
    digest = hashlib.sha256(f"39ad03f74acb|{seed}|{split}|{index}|{attempt}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _paint_horizontal(grid: list[list[int]], row: int, left: int, length: int) -> None:
    for c in range(left, left + length):
        grid[row][c] = 1


def _paint_vertical(grid: list[list[int]], top: int, col: int, length: int) -> None:
    for r in range(top, top + length):
        grid[r][col] = 1


def _horizontal_controller_layout(h: int, w: int, rng: random.Random) -> list[list[int]]:
    if h < 8 or w < 8:
        raise ValueError("profiles must be at least 8x8")
    grid = [[0 for _ in range(w)] for _ in range(h)]
    split = max(4, h // 2)
    horizontal_rows = list(range(1, split, 2))
    if len(horizontal_rows) < 2:
        horizontal_rows = [1, 3]
    bottom_top = split + 1
    vertical_capacity = h - bottom_top
    if vertical_capacity < 3:
        bottom_top = h - 3
        vertical_capacity = 3
    vertical_cols = list(range(1, w - 1, 2))
    if len(vertical_cols) < 2:
        vertical_cols = [1, 3]

    controller_length = w - 2
    controller_left = rng.randint(0, w - controller_length)
    controller_row = horizontal_rows[0]
    _paint_horizontal(grid, controller_row, controller_left, controller_length)

    extra_h = min(len(horizontal_rows) - 1, max(1, 1 + h // 6))
    for row in horizontal_rows[1:1 + extra_h]:
        upper = max(3, controller_length - 2)
        length = rng.randint(3, upper)
        left = rng.randint(0, w - length)
        _paint_horizontal(grid, row, left, length)

    rng.shuffle(vertical_cols)
    n_vertical = min(len(vertical_cols), max(2, 2 + w // 6))
    vertical_upper = min(vertical_capacity, controller_length - 2)
    for col in vertical_cols[:n_vertical]:
        length = rng.randint(3, max(3, vertical_upper))
        top = rng.randint(bottom_top, h - length)
        _paint_vertical(grid, top, col, length)
    return grid


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid, strict=True)]


def _scene(seed: int, split: str, index: int, attempt: int = 0) -> list[list[int]]:
    profiles = _TRAIN_PROFILES if split == "train" else _TEST_PROFILES
    h, w = profiles[index]
    rng = _rng(seed, split, index, attempt)
    horizontal_controller = (seed + index + (0 if split == "train" else 1) + attempt) % 2 == 0
    grid = (_horizontal_controller_layout(h, w, rng) if horizontal_controller
            else _transpose(_horizontal_controller_layout(w, h, rng)))
    errors = scene_invariants(grid)
    if errors:
        raise RuntimeError("invalid constructed scene: " + "; ".join(errors))
    return grid


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    scope = _scope(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    seen: set[str] = set()

    def pairs(split: str, count: int) -> list[dict[str, list[list[int]]]]:
        result = []
        for index in range(count):
            for attempt in range(20):
                grid = _scene(seed, split, index, attempt)
                signature = repr(grid)
                if signature not in seen:
                    seen.add(signature)
                    result.append({"input": grid, "output": transform(grid, scope)})
                    break
            else:
                raise RuntimeError("could not make all episode inputs distinct")
        return result

    return {
        "train": pairs("train", demos),
        "test": pairs("test", queries),
        "program_solution": program({"scope": scope}),
    }
