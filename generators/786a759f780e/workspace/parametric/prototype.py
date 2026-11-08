"""Matched-input hole-priority episodes for 786a759f780e.

The canonical setting sorts complete nonzero components by increasing enclosed
hole count, then increasing painted area, then the first row-major component
color.  The alternate setting reverses only the primary hole-count order while
preserving the same component extraction, secondary keys, crops, and packing.
Python outputs are deterministic claims; native qualification executes every
label through protected Racket.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "786a759f780e"
HERE = Path(__file__).resolve().parent
SETTING_NAMES = ("ascending", "descending")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _cells(rows: tuple[str, ...]) -> tuple[tuple[int, int], ...]:
    return tuple((r, c) for r, row in enumerate(rows) for c, value in enumerate(row) if value == "1")


SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "solid_l": _cells(("10", "10", "11")),
    "solid_3x4": _cells(("1111", "1111", "1111")),
    "solid_5x5": _cells(("11111", "11111", "11111", "11111", "11111")),
    "ring3": _cells(("111", "101", "111")),
    "ring4": _cells(("1111", "1001", "1001", "1111")),
    "ring5": _cells(("11111", "10001", "10001", "10001", "11111")),
    "double3x5": _cells(("11111", "10101", "11111")),
    "double5x5": _cells(("11111", "10201".replace("2", "1"), "10201".replace("2", "1"), "10201".replace("2", "1"), "11111")),
    "triple3x7": _cells(("1111111", "1010101", "1111111")),
}
# The explicit replacement above yields 10101 middle rows, dividing the 5x5
# interior with a solid central column into two enclosed chambers.

# Each object spec: shape, (top,left), rank in a sorted random primary palette.
DEMO_SCENES = (
    {"dims": (11, 20), "objects": (
        ("double3x5", (0, 0), 1), ("ring3", (4, 17), 0), ("solid_3x4", (8, 8), 2))},
    {"dims": (12, 20), "objects": (
        ("ring4", (0, 0), 2), ("ring3", (0, 8), 3),
        ("double3x5", (6, 0), 1), ("ring3", (8, 15), 0))},
    {"dims": (12, 20), "objects": (
        ("ring3", (0, 15), 1), ("solid_3x4", (5, 0), 2), ("double3x5", (8, 10), 0))},
    {"dims": (15, 22), "objects": (
        ("double5x5", (0, 0), 3), ("solid_l", (2, 12), 1),
        ("ring4", (9, 1), 0), ("ring3", (10, 18), 2))},
    {"dims": (18, 24), "objects": (
        ("triple3x7", (0, 8), 4), ("ring5", (6, 0), 1),
        ("solid_3x4", (8, 15), 3), ("double3x5", (14, 9), 0), ("ring3", (15, 21), 2))},
    {"dims": (24, 27), "objects": (
        ("ring4", (0, 0), 4), ("double5x5", (0, 18), 1),
        ("solid_5x5", (9, 8), 3), ("triple3x7", (20, 0), 0), ("ring5", (19, 22), 2))},
)
QUERY_SCENES = (
    {"dims": (12, 15), "objects": (
        ("double3x5", (0, 0), 2), ("solid_l", (5, 7), 1), ("ring3", (9, 12), 0))},
    {"dims": (18, 20), "objects": (
        ("ring4", (0, 12), 3), ("double5x5", (6, 0), 1),
        ("solid_3x4", (12, 10), 2), ("ring3", (15, 17), 0))},
    {"dims": (24, 27), "objects": (
        ("triple3x7", (0, 10), 4), ("ring5", (6, 0), 1),
        ("solid_3x4", (10, 18), 3), ("double3x5", (18, 4), 0), ("ring3", (21, 24), 2))},
    {"dims": (30, 30), "objects": (
        ("triple3x7", (0, 0), 4), ("ring5", (0, 25), 1),
        ("double5x5", (12, 0), 3), ("solid_5x5", (25, 25), 2), ("ring4", (26, 10), 0))},
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"hole_order"}:
        raise ValueError("settings must contain exactly hole_order")
    value = settings["hole_order"]
    if type(value) is not str or value not in SETTING_NAMES:
        raise ValueError(f"hole_order must be one of {SETTING_NAMES}")
    return value


def program_for(order: str) -> str:
    paths = {"ascending": "canonical.rkt", "descending": "descending.rkt", "area_only": "area_only.rkt"}
    if order not in paths:
        raise ValueError("order has no declared Racket program")
    return (HERE / paths[order]).read_text()


def program(settings: dict[str, Any]) -> str:
    return program_for(_setting(settings))


def _validate_grid(grid: Any) -> tuple[list[list[int]], int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    clean: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid cells must be exact integer colors 0..9")
        clean.append(list(row))
    return clean, len(clean), width


def hole_count(crop: list[list[int]]) -> int:
    height, width = len(crop), len(crop[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if crop[r][c] == 0}
    holes = 0
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        touches = False
        while stack:
            row, col = stack.pop()
            if row in (0, height - 1) or col in (0, width - 1):
                touches = True
            for dr, dc in CARDINAL:
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        if not touches:
            holes += 1
    return holes


def _component_record(grid: list[list[int]], cells: set[tuple[int, int]], reading_rank: int) -> dict[str, Any]:
    ordered = sorted(cells)
    top, left = min(r for r, _ in ordered), min(c for _, c in ordered)
    bottom, right = max(r for r, _ in ordered), max(c for _, c in ordered)
    crop = [[grid[r][c] if (r, c) in cells else 0 for c in range(left, right + 1)]
            for r in range(top, bottom + 1)]
    return {
        "color": grid[ordered[0][0]][ordered[0][1]],
        "colors": sorted({grid[r][c] for r, c in ordered}),
        "cells": [list(cell) for cell in ordered],
        "area": len(ordered),
        "top": top, "left": left, "bottom": bottom, "right": right,
        "height": bottom - top + 1, "width": right - left + 1,
        "crop": crop, "holes": hole_count(crop), "reading_rank": reading_rank,
    }


def _components(grid: list[list[int]], *, same_color: bool = False) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            start_color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                for dr, dc in CARDINAL:
                    nr, nc = current[0] + dr, current[1] + dc
                    nxt = (nr, nc)
                    if not (0 <= nr < height and 0 <= nc < width) or nxt in seen:
                        continue
                    value = grid[nr][nc]
                    if value != 0 and (not same_color or value == start_color):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(_component_record(grid, cells, len(result)))
    return result


def analyze(grid: Any) -> dict[str, Any]:
    values, height, width = _validate_grid(grid)
    objects = _components(values)
    if not objects:
        raise ValueError("input must contain at least one nonzero component")
    return {"height": height, "width": width, "objects": objects}


def sorted_objects(objects: list[dict[str, Any]], rule: str) -> list[dict[str, Any]]:
    if rule == "ascending":
        key = lambda obj: (obj["holes"], obj["area"], obj["color"])
    elif rule == "descending":
        key = lambda obj: (-obj["holes"], obj["area"], obj["color"])
    elif rule == "area_only":
        key = lambda obj: (obj["area"], obj["color"])
    elif rule == "holes_only_ascending":
        key = lambda obj: (obj["holes"], obj["reading_rank"])
    elif rule == "holes_only_descending":
        key = lambda obj: (-obj["holes"], obj["reading_rank"])
    elif rule == "ascending_area_descending":
        key = lambda obj: (obj["holes"], -obj["area"], obj["color"])
    elif rule == "descending_area_descending":
        key = lambda obj: (-obj["holes"], -obj["area"], obj["color"])
    elif rule == "ascending_no_color":
        key = lambda obj: (obj["holes"], obj["area"], obj["reading_rank"])
    elif rule == "descending_no_color":
        key = lambda obj: (-obj["holes"], obj["area"], obj["reading_rank"])
    elif rule == "color_order":
        key = lambda obj: (obj["color"],)
    elif rule == "reading_order":
        key = lambda obj: (obj["reading_rank"],)
    elif rule == "reverse_reading":
        key = lambda obj: (-obj["reading_rank"],)
    else:
        raise ValueError(f"unknown sort rule {rule!r}")
    return sorted(objects, key=key)


def pack(objects: list[dict[str, Any]]) -> list[list[int]]:
    if not objects:
        raise ValueError("cannot pack no objects")
    height = max(obj["height"] for obj in objects)
    width = sum(obj["width"] for obj in objects) + len(objects) - 1
    if height > 30 or width > 30:
        raise ValueError("packed output exceeds ARC grid bounds")
    out = [[0] * width for _ in range(height)]
    left = 0
    for obj in objects:
        for row, values in enumerate(obj["crop"]):
            for col, value in enumerate(values):
                if value != 0:
                    out[row][left + col] = value
        left += obj["width"] + 1
    return out


def solve(grid: Any, rule: str) -> list[list[int]]:
    values, _, _ = _validate_grid(grid)
    if rule == "same_color_ascending":
        return pack(sorted_objects(_components(values, same_color=True), "ascending"))
    if rule == "same_color_descending":
        return pack(sorted_objects(_components(values, same_color=True), "descending"))
    analysis = analyze(values)
    return pack(sorted_objects(analysis["objects"], rule))


CANDIDATE_NAMES = (
    "ascending", "descending", "area_only",
    "holes_only_ascending", "holes_only_descending",
    "ascending_area_descending", "descending_area_descending",
    "ascending_no_color", "descending_no_color",
    "color_order", "reading_order", "reverse_reading",
    "same_color_ascending", "same_color_descending",
)


def teaching_survivors(demos: list[dict[str, Any]]) -> list[str]:
    return [name for name in CANDIDATE_NAMES
            if all(solve(pair["input"], name) == pair["output"] for pair in demos)]


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = json.dumps([TASK_ID, "parametric-v1", seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _paint_scene(seed: int, split: str, index: int, scene: dict[str, Any]) -> list[list[int]]:
    rng = _rng(seed, split, index)
    height, width = scene["dims"]
    grid = [[0] * width for _ in range(height)]
    count = len(scene["objects"])
    palette = sorted(rng.sample(range(1, 10), count))
    occupied: set[tuple[int, int]] = set()
    for object_index, (shape_name, (top, left), color_rank) in enumerate(scene["objects"]):
        shape = SHAPES[shape_name]
        primary = palette[color_rank]
        cells = sorted((top + row, left + col) for row, col in shape)
        if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
            raise AssertionError("scene object exceeds canvas")
        if occupied.intersection(cells):
            raise AssertionError("scene objects overlap")
        for row, col in cells:
            grid[row][col] = primary
        # Every object is observably mixed-color, but its first row-major cell
        # remains the primary sort key used by the Racket authority.
        secondary = palette[(color_rank + 1 + object_index) % count]
        if secondary == primary:
            secondary = palette[(color_rank + 1) % count]
        candidates = cells[1:]
        mixed_cell = candidates[rng.randrange(len(candidates))]
        grid[mixed_cell[0]][mixed_cell[1]] = secondary
        occupied.update(cells)
    facts = analyze(grid)["objects"]
    if len(facts) != count:
        raise AssertionError(f"expected {count} components, got {len(facts)}")
    if not all(len(obj["colors"]) > 1 for obj in facts):
        raise AssertionError("every object must expose mixed-color connectivity")
    return grid


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    scenes = DEMO_SCENES if split == "demo" else QUERY_SCENES if split == "query" else None
    if scenes is None or type(index) is not int or not 0 <= index < len(scenes):
        raise ValueError("invalid split/index")
    return _paint_scene(seed, split, index, scenes[index])


def generate_episode(seed: int, order: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if order not in SETTING_NAMES:
        raise ValueError(f"order must be one of {SETTING_NAMES}")
    demo_inputs = [sample_input(seed, "demo", index) for index in range(6)]
    query_inputs = [sample_input(seed, "query", index) for index in range(4)]
    keys = [json.dumps(grid, separators=(",", ":")) for grid in demo_inputs + query_inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("input sampler produced duplicates")
    def pair(grid):
        return {"input": copy.deepcopy(grid), "output": solve(grid, order)}
    episode = {
        "train": [pair(grid) for grid in demo_inputs[:demos]],
        "test": [pair(grid) for grid in query_inputs[:queries]],
        "program_solution": program_for(order),
    }
    if teaching_survivors(episode["train"][:2]) != [order]:
        raise RuntimeError(f"first two demonstrations do not identify {order}: {teaching_survivors(episode['train'][:2])}")
    return episode


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    return generate_episode(seed, _setting(settings), demos=demos, queries=queries)
