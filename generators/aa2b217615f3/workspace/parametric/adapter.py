"""Matched-input native stacking-order lessons for aa2b217615f3."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
FAR_FIRST = (HERE / "far_first.rkt").read_text(encoding="utf-8")
PROGRAMS = {"near_first": CANONICAL, "far_first": FAR_FIRST}
DEMO_DIMS = ((9, 10), (10, 12), (12, 11), (14, 15), (18, 20), (24, 22))
QUERY_DIMS = ((11, 13), (16, 18), (24, 28), (30, 30))
DIRECTIONS = ("up", "right", "down", "left")
COLORS = (1, 3, 4, 5, 6, 7, 8, 9)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _order(settings: dict[str, Any]) -> str:
    if type(settings) is not dict:
        raise TypeError("settings must be an exact dictionary")
    if set(settings) != {"stack_order"}:
        raise ValueError("settings must name exactly stack_order")
    value = settings["stack_order"]
    if type(value) is not str or value not in PROGRAMS:
        raise ValueError("stack_order must be near_first or far_first")
    return value


def program(settings: dict[str, Any]) -> str:
    return PROGRAMS[_order(settings)]


def _grid(value: Any) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30 or
            type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width or
           any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return [row[:] for row in value]


def _direction(grid: list[list[int]]) -> str:
    h, w = len(grid), len(grid[0])
    found = []
    if all(grid[0][c] == 2 for c in range(w)): found.append("up")
    if all(grid[h - 1][c] == 2 for c in range(w)): found.append("down")
    if all(grid[r][0] == 2 for r in range(h)): found.append("left")
    if all(grid[r][w - 1] == 2 for r in range(h)): found.append("right")
    if len(found) != 1:
        raise ValueError(f"expected one red edge, found {found}")
    return found[0]


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 2) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            result.append({"color": color, "cells": cells})
    return result


def _depth_key(obj: dict[str, Any], direction: str) -> int:
    cells = obj["cells"]
    if direction == "up": return min(r for r, _ in cells)
    if direction == "down": return -max(r for r, _ in cells)
    if direction == "left": return min(c for _, c in cells)
    return -max(c for _, c in cells)


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    source = _grid(grid)
    order = _order(settings)
    direction = _direction(source)
    h, w = len(source), len(source[0])
    objects = sorted(_objects(source), key=lambda obj: _depth_key(obj, direction),
                     reverse=(order == "far_first"))
    out = [[2 if source[r][c] == 2 else 0 for c in range(w)] for r in range(h)]
    occupied = {(r, c) for r in range(h) for c in range(w) if source[r][c] == 2}
    dr, dc = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}[direction]
    for obj in objects:
        distance = 0
        while all(0 <= r + dr * (distance + 1) < h and 0 <= c + dc * (distance + 1) < w
                  and (r + dr * (distance + 1), c + dc * (distance + 1)) not in occupied
                  for r, c in obj["cells"]):
            distance += 1
        for r, c in obj["cells"]:
            nr, nc = r + dr * distance, c + dc * distance
            occupied.add((nr, nc)); out[nr][nc] = obj["color"]
    return out


def has_stacking_witness(grid: list[list[int]]) -> bool:
    source = _grid(grid)
    direction = _direction(source)
    vertical = direction in ("up", "down")
    projections = [({c for _, c in obj["cells"]} if vertical else {r for r, _ in obj["cells"]})
                   for obj in _objects(source)]
    return any(a & b for i, a in enumerate(projections) for b in projections[i + 1:])


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"aa2b217615f3/stack-order-v1/{seed}/{split}/{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _coord(direction: str, h: int, w: int, depth: int, lateral: int) -> tuple[int, int]:
    if direction == "up": return depth, lateral
    if direction == "down": return h - 1 - depth, lateral
    if direction == "left": return lateral, depth
    return lateral, w - 1 - depth


def _paint_local(grid: list[list[int]], direction: str, depth: int, lateral: int,
                 offsets: tuple[tuple[int, int], ...], color: int) -> None:
    h, w = len(grid), len(grid[0])
    cells = [_coord(direction, h, w, depth + dd, lateral + dl) for dd, dl in offsets]
    if any(not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0 for r, c in cells):
        raise AssertionError("invalid authored object placement")
    for r, c in cells:
        grid[r][c] = color


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    dims = DEMO_DIMS if split == "train" else QUERY_DIMS
    _integer(index, 0, len(dims) - 1, "index")
    h, w = dims[index]
    rng = _rng(seed, split, index)
    direction = DIRECTIONS[(index + (0 if split == "train" else 2) + rng.randrange(4)) % 4]
    grid = [[0] * w for _ in range(h)]
    if direction == "up": grid[0] = [2] * w
    elif direction == "down": grid[-1] = [2] * w
    elif direction == "left":
        for row in grid: row[0] = 2
    else:
        for row in grid: row[-1] = 2
    colors = list(COLORS); rng.shuffle(colors)
    axis = h if direction in ("up", "down") else w
    cross = w if direction in ("up", "down") else h
    # Three one-cell objects in one lane and two dominoes in another create
    # independent, visible collision chains.  Additional shapes broaden scope.
    placements = [
        (2, 1, ((0, 0),)), (4, 1, ((0, 0),)), (6, 1, ((0, 0),)),
        (3, cross - 2, ((0, 0), (0, 1))),
        (max(6, axis - 2), cross - 2, ((0, 0), (0, 1))),
        (max(5, axis - 3), max(3, cross // 2 - 1), ((0, 0), (1, 0), (1, 1))),
        (3, max(3, cross // 2 - 2), ((0, 0), (0, 1), (0, 2))),
    ]
    # Clamp only the two deep placements on the smallest axes.
    normalized = []
    for depth, lateral, shape in placements:
        max_dd = max(dd for dd, _ in shape)
        max_dl = max(dl for _, dl in shape)
        depth = min(depth, axis - 1 - max_dd)
        lateral = min(lateral, cross - 1 - max_dl)
        normalized.append((depth, lateral, shape))
    for color, (depth, lateral, shape) in zip(colors, normalized):
        _paint_local(grid, direction, depth, lateral, shape, color)
    if not has_stacking_witness(grid):
        raise AssertionError("authored scene lost its stacking witness")
    return grid


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    _order(settings)
    train = []
    test = []
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            target.append({"input": grid, "output": transform(grid, settings)})
    return {"train": deepcopy(train), "test": deepcopy(test),
            "program_solution": program(settings)}
