"""Native sorted-gallery family for 0ff4b77946cc.

The canonical setting always sorts objects by descending size.  The alternate
first finds the largest object and measures its bounding-box orientation; a
wide/square largest object selects descending order while a tall largest object
selects ascending order.  Both settings then use the same top-aligned packer.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import random
from typing import Any

TASK_ID = "0ff4b77946cc"
SETTINGS = ("size_desc", "largest_orientation")
DEFAULT = "size_desc"
PARAMETER = "order_policy"
_HERE = Path(__file__).resolve().parent

# Distinct-size connected shapes.  The largest role has orientation-specific
# variants with the same seven-cell mass, so the first-stage measurement alone
# decides the alternate order direction.
_WIDE7 = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2))
_TALL7 = tuple((c, r) for r, c in _WIDE7)
_SHAPE5 = ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))
_SHAPE4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_SHAPE3 = ((0, 0), (0, 1), (1, 1))

# (height, width, largest orientation, placements).  Each placement is
# (shape-role, top, left); role zero is the seven-cell largest object.
_DEMO_SPECS = (
    (10, 13, "wide_or_square", ((0, 1, 1), (1, 5, 2), (3, 4, 9))),
    (11, 13, "tall",           ((0, 1, 1), (1, 6, 2), (3, 3, 9))),
    (12, 15, "wide_or_square", ((0, 2, 1), (1, 7, 2), (2, 4, 9), (3, 9, 11))),
    (13, 16, "tall",           ((0, 1, 2), (1, 7, 1), (2, 3, 10), (3, 9, 12))),
    (14, 17, "wide_or_square", ((0, 9, 10), (1, 2, 2), (3, 7, 4))),
    (15, 18, "tall",           ((0, 8, 13), (1, 2, 2), (2, 9, 3), (3, 3, 10))),
)
_QUERY_SPECS = (
    (12, 16, "tall",           ((0, 1, 12), (1, 7, 2), (3, 3, 7))),
    (16, 18, "wide_or_square", ((0, 12, 1), (1, 2, 13), (2, 7, 6), (3, 2, 3))),
    (20, 22, "tall",           ((0, 13, 2), (1, 2, 2), (2, 8, 14), (3, 14, 15))),
    (30, 30, "wide_or_square", ((0, 2, 2), (1, 21, 3), (2, 12, 20), (3, 24, 24))),
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
    return _read("canonical.rkt" if value == DEFAULT else "orientation_order.rkt")


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


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    objects: list[dict[str, Any]] = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < height and 0 <= ny < width and
                            (nx, ny) not in seen and grid[nx][ny] == color):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            rows = [x for x, _y in cells]
            cols = [y for _x, y in cells]
            r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
            objects.append({
                "color": color,
                "cells": sorted(cells),
                "size": len(cells),
                "r1": r1,
                "c1": c1,
                "h": r2 - r1 + 1,
                "w": c2 - c1 + 1,
            })
    if not 3 <= len(objects) <= 4:
        raise ValueError("expected 3..4 connected objects")
    colors = [obj["color"] for obj in objects]
    sizes = [obj["size"] for obj in objects]
    if len(colors) != len(set(colors)) or len(sizes) != len(set(sizes)):
        raise ValueError("objects must have distinct colors and sizes")
    required = sum(obj["w"] for obj in objects) + len(objects) - 1
    if required > width:
        raise ValueError("packed gallery exceeds canvas width")
    return objects


def _desc_key(obj: dict[str, Any]) -> tuple[int, int, int, int]:
    return (-obj["size"], obj["h"], obj["w"], obj["color"])


def _asc_key(obj: dict[str, Any]) -> tuple[int, int, int, int]:
    return (obj["size"], obj["h"], obj["w"], obj["color"])


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    objects = _objects(grid)
    largest = min(objects, key=_desc_key)
    orientation = "tall" if largest["h"] > largest["w"] else "wide_or_square"
    return {
        "objects": objects,
        "largest_color": largest["color"],
        "largest_size": largest["size"],
        "largest_bbox": [largest["h"], largest["w"]],
        "largest_orientation": orientation,
        "selected_direction": "ascending" if orientation == "tall" else "descending",
    }


def apply_python(grid: list[list[int]], setting: str = DEFAULT) -> list[list[int]]:
    if type(setting) is not str or setting not in SETTINGS:
        raise ValueError(f"setting must be one of {SETTINGS}")
    height, width = _validate_grid(grid)
    analysis = analyze(grid)
    ascending = setting == "largest_orientation" and analysis["largest_orientation"] == "tall"
    objects = sorted(analysis["objects"], key=_asc_key if ascending else _desc_key)
    output = [[0] * width for _ in range(height)]
    offset = 0
    for obj in objects:
        for r, c in obj["cells"]:
            output[r - obj["r1"]][offset + c - obj["c1"]] = obj["color"]
        offset += obj["w"] + 1
    return output


def _shape_for(role: int, orientation: str):
    if role == 0:
        return _TALL7 if orientation == "tall" else _WIDE7
    return {1: _SHAPE5, 2: _SHAPE4, 3: _SHAPE3}[role]


def _build(spec, seed: int, slot: int) -> list[list[int]]:
    height, width, orientation, placements = spec
    rng = random.Random((seed + 1) * 0x9E3779B1 + slot * 0x85EBCA6B)
    colors = rng.sample(range(1, 10), len(placements))
    grid = [[0] * width for _ in range(height)]
    flip_v = ((seed * 17 + slot * 3) & 1) != 0
    flip_h = ((seed * 11 + slot * 5) & 2) != 0
    for color, (role, top, left) in zip(colors, placements):
        shape = _shape_for(role, orientation)
        for dr, dc in shape:
            r, c = top + dr, left + dc
            if flip_v:
                r = height - 1 - r
            if flip_h:
                c = width - 1 - c
            if not (0 <= r < height and 0 <= c < width) or grid[r][c] != 0:
                raise RuntimeError(f"invalid authored placement at slot {slot}")
            grid[r][c] = color
    observed = analyze(grid)
    if observed["largest_orientation"] != orientation:
        raise RuntimeError(f"largest orientation drift at slot {slot}")
    return grid


def _pairs(specs, seed: int, setting: str, count: int, offset: int):
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
    if {analyze(pair["input"])["largest_orientation"] for pair in train[:2]} != {"wide_or_square", "tall"}:
        raise RuntimeError("minimum lesson does not expose both orientation branches")
    rival = next(value for value in SETTINGS if value != selected)
    if not any(apply_python(pair["input"], rival) != pair["output"] for pair in train):
        raise RuntimeError("demonstrations do not distinguish the selected setting")
    return {
        "train": deepcopy(train),
        "test": deepcopy(test),
        "program_solution": program({PARAMETER: selected}),
    }
