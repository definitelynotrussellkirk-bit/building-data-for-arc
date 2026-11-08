"""Matched-input checker-phase episodes for 2b7bcfbf942b.

The canonical setting fills each extracted object's bounding-box interior with a
local checkerboard whose upper-left interior cell is colored.  The alternate
setting flips that local phase while preserving object extraction, border
completion, colors, and fresh-canvas rendering.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "2b7bcfbf942b"
HERE = Path(__file__).resolve().parent
SETTING_NAMES = ("colored_first", "zero_first")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
OPEN_SIDES = ("top", "bottom", "left", "right")
CANONICAL_BBOXES = {(5, 5), (6, 4), (6, 6), (6, 7)}

# Each object spec is (r1, c1, height, width, style).  Profiles are separated
# geometrically and colors are deterministically permuted by seed.
DEMO_PROFILES = (
    ((10, 14), ((1, 1, 5, 5, "frame"), (1, 8, 7, 6, "open"))),
    ((12, 16), ((0, 0, 7, 7, "cross"), (4, 10, 8, 6, "open"))),
    ((14, 18), ((1, 1, 6, 8, "frame"), (8, 1, 5, 6, "open"), (7, 11, 7, 7, "cross"))),
    ((16, 20), ((0, 0, 7, 8, "frame"), (1, 13, 8, 7, "cross"), (10, 5, 6, 9, "open"))),
    ((18, 22), ((1, 1, 8, 7, "open"), (0, 14, 7, 8, "frame"), (11, 0, 7, 9, "cross"), (10, 14, 8, 8, "frame"))),
    ((20, 24), ((0, 0, 8, 9, "cross"), (1, 16, 9, 8, "open"), (12, 1, 8, 8, "frame"), (12, 15, 8, 9, "cross"))),
)
QUERY_PROFILES = (
    ((12, 15), ((1, 1, 6, 6, "frame"), (2, 9, 8, 6, "cross"), (8, 2, 4, 5, "open"))),
    ((18, 20), ((0, 0, 8, 8, "open"), (2, 13, 9, 7, "frame"), (11, 5, 7, 9, "cross"))),
    ((24, 27), ((0, 1, 9, 9, "cross"), (1, 18, 10, 9, "open"), (14, 0, 10, 11, "frame"), (15, 18, 9, 9, "cross"))),
    ((30, 30), ((0, 0, 8, 8, "frame"), (0, 18, 9, 12, "open"), (10, 10, 10, 10, "cross"), (22, 0, 8, 10, "frame"), (21, 20, 9, 10, "cross"))),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _phase(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"checker_phase"}:
        raise ValueError("settings must contain exactly checker_phase")
    value = settings["checker_phase"]
    if type(value) is not str or value not in SETTING_NAMES:
        raise ValueError(f"checker_phase must be one of {SETTING_NAMES}")
    return value


def program_for(phase: str) -> str:
    if phase == "colored_first":
        path = HERE / "canonical.rkt"
    elif phase == "zero_first":
        path = HERE / "zero_first.rkt"
    else:
        raise ValueError(f"unknown checker phase {phase!r}")
    return path.read_text()


def program(settings: dict[str, Any]) -> str:
    return program_for(_phase(settings))


def _validate_grid(grid: Any) -> tuple[list[list[int]], int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    clean = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid cells must be exact integer colors 0..9")
        clean.append(list(row))
    return clean, len(clean), width


def _components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        cells = {start}
        stack = [start]
        unseen.remove(start)
        while stack:
            row, col = stack.pop()
            for dr, dc in CARDINAL:
                nxt = (row + dr, col + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        result.append((color, cells))
    return sorted(result, key=lambda item: min(item[1]))


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _shape_cells(r1: int, c1: int, height: int, width: int, style: str,
                 open_side: str = "top") -> set[tuple[int, int]]:
    r2, c2 = r1 + height - 1, c1 + width - 1
    border = {(row, col) for row in range(r1, r2 + 1) for col in range(c1, c2 + 1)
              if row in (r1, r2) or col in (c1, c2)}
    if style == "frame":
        return border
    if style == "open":
        if open_side == "top":
            removed = {(r1, col) for col in range(c1 + 1, c2)}
        elif open_side == "bottom":
            removed = {(r2, col) for col in range(c1 + 1, c2)}
        elif open_side == "left":
            removed = {(row, c1) for row in range(r1 + 1, r2)}
        elif open_side == "right":
            removed = {(row, c2) for row in range(r1 + 1, r2)}
        else:
            raise ValueError("unknown open side")
        return border - removed
    if style == "cross":
        middle_row = (r1 + r2) // 2
        middle_col = (c1 + c2) // 2
        return ({(middle_row, col) for col in range(c1, c2 + 1)}
                | {(row, middle_col) for row in range(r1, r2 + 1)})
    raise ValueError(f"unknown object style {style!r}")


def _classify(cells: set[tuple[int, int]]) -> str:
    r1, c1, r2, c2 = _bbox(cells)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    if cells == _shape_cells(r1, c1, height, width, "frame"):
        return "frame"
    if cells == _shape_cells(r1, c1, height, width, "cross"):
        return "cross"
    if any(cells == _shape_cells(r1, c1, height, width, "open", side) for side in OPEN_SIDES):
        return "open"
    return "other"


def analyze(grid: Any) -> dict[str, Any]:
    values, height, width = _validate_grid(grid)
    objects = []
    for color, cells in _components(values):
        bbox = _bbox(cells)
        r1, c1, r2, c2 = bbox
        if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
            raise ValueError("each object bounding box must be at least 3x3")
        style = _classify(cells)
        if style == "other":
            raise ValueError("objects must be frames, open frames, or crosses")
        objects.append({
            "color": color,
            "cells": sorted(cells),
            "bbox": bbox,
            "style": style,
            "area": (r2 - r1 + 1) * (c2 - c1 + 1),
        })
    if not objects:
        raise ValueError("grid needs at least one object")
    return {"height": height, "width": width, "objects": objects}


def _checker_colored(row: int, col: int, bbox: tuple[int, int, int, int],
                     phase: str, anchor: str) -> bool:
    r1, c1, _, c2 = bbox
    if anchor == "local":
        parity = (row - (r1 + 1) + col - (c1 + 1)) % 2
    elif anchor == "global":
        parity = (row + col) % 2
    elif anchor == "top_right":
        parity = (row - (r1 + 1) + (c2 - 1) - col) % 2
    else:
        raise ValueError(f"unknown checker anchor {anchor}")
    return parity == (0 if phase == "colored_first" else 1)


def _render(grid: Any, phase: str, *, anchor: str = "local", frames_only: bool = False,
            border_only: bool = False, solid_fill: bool = False,
            largest_only: bool = False, first_color: bool = False,
            source_border: bool = False, canonical_sizes_only: bool = False) -> list[list[int]]:
    if phase not in SETTING_NAMES:
        raise ValueError(f"phase must be one of {SETTING_NAMES}")
    values, height, width = _validate_grid(grid)
    objects = analyze(values)["objects"]
    selected = list(objects)
    if frames_only:
        selected = [obj for obj in selected if obj["style"] == "frame"]
    if canonical_sizes_only:
        selected = [obj for obj in selected if
                    (obj["bbox"][2] - obj["bbox"][0] + 1,
                     obj["bbox"][3] - obj["bbox"][1] + 1) in CANONICAL_BBOXES]
    if largest_only and selected:
        selected = [max(selected, key=lambda obj: (obj["area"], -obj["bbox"][0], -obj["bbox"][1]))]
    common_color = objects[0]["color"]
    out = [[0] * width for _ in range(height)]
    for obj in selected:
        color = common_color if first_color else obj["color"]
        r1, c1, r2, c2 = obj["bbox"]
        source = set(obj["cells"])
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                border = row in (r1, r2) or col in (c1, c2)
                if border:
                    out[row][col] = color if (not source_border or (row, col) in source) else 0
                elif border_only:
                    out[row][col] = 0
                elif solid_fill:
                    out[row][col] = color
                else:
                    out[row][col] = color if _checker_colored(row, col, obj["bbox"], phase, anchor) else 0
    return out


def solve(grid: Any, rule: str) -> list[list[int]]:
    if rule in SETTING_NAMES:
        return _render(grid, rule)
    for suffix, options in (
        ("_global", {"anchor": "global"}),
        ("_top_right", {"anchor": "top_right"}),
        ("_frames_only", {"frames_only": True}),
        ("_largest_only", {"largest_only": True}),
        ("_first_color", {"first_color": True}),
        ("_source_border", {"source_border": True}),
        ("_canonical_sizes_only", {"canonical_sizes_only": True}),
    ):
        if rule.endswith(suffix):
            phase = rule.removesuffix(suffix)
            if phase in SETTING_NAMES:
                return _render(grid, phase, **options)
    if rule == "border_only":
        return _render(grid, "colored_first", border_only=True)
    if rule == "solid_fill":
        return _render(grid, "colored_first", solid_fill=True)
    raise ValueError(f"unknown rule {rule!r}")


CANDIDATE_NAMES = tuple(
    ["colored_first", "zero_first", "border_only", "solid_fill"]
    + [f"{phase}{suffix}" for phase in SETTING_NAMES for suffix in (
        "_global", "_top_right", "_frames_only", "_largest_only",
        "_first_color", "_source_border", "_canonical_sizes_only")]
)


def teaching_survivors(demos: list[dict[str, Any]]) -> list[str]:
    survivors = []
    for candidate in CANDIDATE_NAMES:
        if all(solve(pair["input"], candidate) == pair["output"] for pair in demos):
            survivors.append(candidate)
    return survivors


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = json.dumps([TASK_ID, "checker-phase-v1", seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _build_input(seed: int, split: str, index: int, profile) -> list[list[int]]:
    (height, width), specs = profile
    rng = _rng(seed, split, index)
    colors = list(range(1, 10))
    rng.shuffle(colors)
    grid = [[0] * width for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    for object_index, (r1, c1, box_h, box_w, style) in enumerate(specs):
        side = rng.choice(OPEN_SIDES)
        cells = _shape_cells(r1, c1, box_h, box_w, style, side)
        if occupied & cells:
            raise ValueError("profile objects overlap")
        color = colors[object_index]
        for row, col in cells:
            grid[row][col] = color
        occupied |= cells
    analysis = analyze(grid)
    if len(analysis["objects"]) != len(specs):
        raise RuntimeError("profile objects merged or split")
    return grid


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split == "demo":
        profiles = DEMO_PROFILES
    elif split == "query":
        profiles = QUERY_PROFILES
    else:
        raise ValueError("split must be demo or query")
    _integer(index, 0, len(profiles) - 1, "index")
    return _build_input(seed, split, index, profiles[index])


def generate_episode(seed: int, phase: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if type(phase) is not str or phase not in SETTING_NAMES:
        raise ValueError(f"checker_phase must be one of {SETTING_NAMES}")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train = []
    test = []
    for index in range(demos):
        grid = sample_input(seed, "demo", index)
        train.append({"input": grid, "output": solve(grid, phase)})
    for index in range(queries):
        grid = sample_input(seed, "query", index)
        test.append({"input": grid, "output": solve(grid, phase)})
    return {"train": train, "test": test, "program_solution": program_for(phase)}


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    return generate_episode(seed, _phase(settings), demos=demos, queries=queries)
