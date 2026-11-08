"""Native object-color versus orientation-legend L-completion family.

Step A finds each same-color three-cell L and derives the missing corner's
orientation index (NW, NE, SW, SE).  In ``orientation_legend`` mode step B
consumes that input-dependent index to select one of four top-row legend colors
and paints the missing corner.  The canonical ``object_color`` mode uses the
L object's own color, exactly matching the selected source rule.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import json
from pathlib import Path
import random
from typing import Any, Callable

HOME = Path(__file__).resolve().parent
MODES = ("object_color", "orientation_legend")
PROGRAMS = {
    "object_color": (HOME / "canonical.rkt").read_text(encoding="utf-8"),
    "orientation_legend": (HOME / "orientation_legend.rkt").read_text(encoding="utf-8"),
}
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
DEMO_SPECS = (
    (9, 10, 6),
    (11, 12, 8),
    (13, 14, 10),
    (15, 16, 12),
    (18, 20, 16),
    (22, 24, 20),
)
QUERY_SPECS = (
    (10, 13, 8),
    (16, 18, 14),
    (24, 22, 20),
    (30, 30, 32),
)


def _plain_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be a plain integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"fill_mode"}:
        raise ValueError("settings must contain exactly fill_mode")
    value = settings["fill_mode"]
    if type(value) is not str or value not in MODES:
        raise ValueError("fill_mode must be object_color or orientation_legend")
    return value


def _objects(grid: list[list[int]]):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            queue = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for dr, dc in CARDINAL:
                    nxt = (row + dr, col + dc)
                    if (0 <= nxt[0] < h and 0 <= nxt[1] < w and nxt not in seen
                            and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        queue.append(nxt)
            result.append((color, sorted(cells)))
    return result


def _l_facts(grid: list[list[int]]):
    facts = []
    for color, cells in _objects(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        if len(cells) != 3 or max(rows) - min(rows) != 1 or max(cols) - min(cols) != 1:
            continue
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        missing = [
            (r, c)
            for r in (r0, r1)
            for c in (c0, c1)
            if (r, c) not in set(cells)
        ]
        if len(missing) != 1:
            raise ValueError("three-cell 2x2 object must have one missing corner")
        row, col = missing[0]
        orientation = 2 * (row - r0) + (col - c0)
        facts.append({"color": color, "cells": cells, "missing": missing[0], "orientation": orientation})
    return facts


def _legend(grid: list[list[int]]) -> list[int]:
    values = [value for value in grid[0] if value != 0]
    if len(values) != 4 or len(set(values)) != 4:
        raise ValueError("orientation legend must contain four distinct nonzero colors")
    return values


def orientation_indices(grid: list[list[int]]) -> list[int]:
    return [fact["orientation"] for fact in _l_facts(grid)]


def label(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError("unknown fill mode")
    legend = _legend(grid)
    out = deepcopy(grid)
    facts = _l_facts(grid)
    if not facts:
        raise ValueError("scene has no L objects")
    for fact in facts:
        row, col = fact["missing"]
        out[row][col] = fact["color"] if mode == "object_color" else legend[fact["orientation"]]
    return out


def _cells(row: int, col: int, missing: int):
    return [
        (row + dr, col + dc)
        for dr in (0, 1)
        for dc in (0, 1)
        if 2 * dr + dc != missing
    ]


def _can_place(grid, row, col, missing, color, *, require_empty_bbox=True):
    h, w = len(grid), len(grid[0])
    if not (0 <= row < h - 1 and 0 <= col < w - 1):
        return False
    if require_empty_bbox and any(grid[row + dr][col + dc] != 0 for dr in (0, 1) for dc in (0, 1)):
        return False
    cells = _cells(row, col, missing)
    if any(grid[r][c] != 0 for r, c in cells):
        return False
    own = set(cells)
    return all(
        grid[r + dr][c + dc] != color
        for r, c in cells
        for dr, dc in CARDINAL
        if 0 <= r + dr < h and 0 <= c + dc < w and (r + dr, c + dc) not in own
    )


def _paint_object(grid, row, col, missing, color, *, require_empty_bbox=True):
    if not _can_place(grid, row, col, missing, color, require_empty_bbox=require_empty_bbox):
        return False
    for r, c in _cells(row, col, missing):
        grid[r][c] = color
    return True


def build_input(seed: int, pair_index: int, spec: tuple[int, int, int]) -> list[list[int]]:
    height, width, count = spec
    rng = random.Random((seed * 1_000_003 + pair_index * 97_409 + height * 1_009 + width * 131) ^ 0x68E9F92D8E4B)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    legend = palette[:4]
    object_colors = palette[4:]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    legend_columns = sorted(rng.sample(range(width), 4))
    for column, color in zip(legend_columns, legend, strict=True):
        grid[0][column] = color

    # A guaranteed cross-color contact defeats the old whole-nonzero-component shortcut.
    top = 2 if pair_index % 2 == 0 else height - 2
    left = 0 if pair_index % 4 < 2 else width - 4
    if not _paint_object(grid, top, left, 3, object_colors[0]):
        raise RuntimeError("could not place first teaching L")
    if not _paint_object(grid, top, left + 2, 2, object_colors[1]):
        raise RuntimeError("could not place touching teaching L")
    placed = 2

    candidates = [(r, c) for r in range(2, height - 1) for c in range(width - 1)]
    rng.shuffle(candidates)
    # Pull boundary anchors forward so large scenes exercise all edges rather than only padding.
    candidates.sort(key=lambda rc: 0 if rc[0] in (2, height - 2) or rc[1] in (0, width - 2) else 1)
    cursor = 0
    while placed < count and cursor < len(candidates) * 8:
        row, col = candidates[cursor % len(candidates)]
        missing = (placed + seed + pair_index) % 4
        color = object_colors[placed % len(object_colors)]
        cursor += 1
        if _paint_object(grid, row, col, missing, color):
            placed += 1
    if placed != count:
        raise RuntimeError(f"could place only {placed}/{count} L objects")
    indices = set(orientation_indices(grid))
    if indices != {0, 1, 2, 3}:
        raise RuntimeError(f"scene must exercise every missing-corner orientation, got {sorted(indices)}")
    if label(grid, "object_color") == label(grid, "orientation_legend"):
        raise RuntimeError("scene does not distinguish the declared settings")
    return grid


def program(settings: dict[str, Any]) -> str:
    return PROGRAMS[_mode(settings)]


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _plain_int("seed", seed, 0, 2**63 - 1)
    _plain_int("demos", demos, 2, 6)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    mode = _mode(settings)
    specs = list(DEMO_SPECS[:demos]) + list(QUERY_SPECS)
    inputs = [build_input(seed, index, spec) for index, spec in enumerate(specs)]
    keys = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("episode inputs must be distinct")
    pairs = [{"input": deepcopy(grid), "output": label(grid, mode)} for grid in inputs]
    return {"train": pairs[:demos], "test": pairs[demos:], "program_solution": PROGRAMS[mode]}


def teaching_check(episode: dict[str, Any], selected_mode: str) -> dict[str, Any]:
    survivors = [
        mode
        for mode in MODES
        if all(label(pair["input"], mode) == pair["output"] for pair in episode["train"])
    ]
    return {"selected_mode": selected_mode, "surviving_modes": survivors}


def _constant_legend(grid):
    out = deepcopy(grid)
    color = _legend(grid)[0]
    for fact in _l_facts(grid):
        out[fact["missing"][0]][fact["missing"][1]] = color
    return out


def _reversed_orientation(grid):
    out = deepcopy(grid)
    legend = _legend(grid)
    for fact in _l_facts(grid):
        out[fact["missing"][0]][fact["missing"][1]] = legend[3 - fact["orientation"]]
    return out


def _row_only_orientation(grid):
    out = deepcopy(grid)
    legend = _legend(grid)
    for fact in _l_facts(grid):
        out[fact["missing"][0]][fact["missing"][1]] = legend[2 * (fact["orientation"] // 2)]
    return out


def _whole_component_object_color(grid):
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    todo = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    while todo:
        start = min(todo)
        todo.remove(start)
        queue = deque([start])
        cells = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in todo:
                    todo.remove(nxt)
                    queue.append(nxt)
                    cells.append(nxt)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        colors = {grid[r][c] for r, c in cells}
        if len(cells) == 3 and len(colors) == 1 and max(rows) - min(rows) == max(cols) - min(cols) == 1:
            missing = next((r, c) for r in (min(rows), max(rows)) for c in (min(cols), max(cols)) if (r, c) not in cells)
            out[missing[0]][missing[1]] = next(iter(colors))
    return out


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "constant_first_legend": _constant_legend,
    "reversed_orientation": _reversed_orientation,
    "row_only_orientation": _row_only_orientation,
    "whole_nonzero_component": _whole_component_object_color,
}
