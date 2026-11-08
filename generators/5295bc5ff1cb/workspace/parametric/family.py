"""Constructive periodic family for reconstruct-then-mark-span lessons.

``tile_only`` is the exact catalog operation: infer the smallest visible row
and column periods, shift the tile one column left, and reconstruct the full
grid. ``tile_then_mark_span`` consumes that reconstructed intermediate, finds
the sole same-color component whose bounding box reaches all four borders, and
repaints that component with the input cover color.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from typing import Iterable

MODES = ("tile_only", "tile_then_mark_span")
_PERIODS = ((4, 4), (4, 5), (5, 4), (5, 5))
_TRAIN_SIZES = (9, 10, 13, 16, 21, 27)
_TEST_SIZES = (12, 18, 24, 30)
_DELTAS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _stable_index(*parts: object, modulus: int) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % modulus


def _smallest_col_period(prefix: list[int]) -> int:
    for period in range(1, len(prefix) + 1):
        if all(value == prefix[index % period] for index, value in enumerate(prefix)):
            return period
    raise AssertionError("finite sequence always has a period")


def _smallest_row_period(grid: list[list[int]], top_h: int, col_period: int) -> int:
    for period in range(1, top_h + 1):
        if all(
            grid[row][col] == grid[row % period][col]
            for row in range(top_h)
            for col in range(col_period)
        ):
            return period
    raise AssertionError("finite matrix always has a row period")


def _facts(grid: list[list[int]]) -> dict[str, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer ARC colors 0..9")
    height = len(grid)
    cover = grid[-1][-1]
    top_h = next((r for r in range(height) if grid[r][0] == cover), height)
    prefix_width = next((c for c in range(width) if grid[0][c] == cover), width)
    if not 1 <= top_h < height or not 2 <= prefix_width < width:
        raise ValueError("input must expose a nonempty periodic prefix followed by cover")
    if any(grid[r][c] == cover for r in range(top_h) for c in range(prefix_width)):
        raise ValueError("cover color may not occur inside the visible prefix")
    if any(
        grid[r][c] != cover
        for r in range(height)
        for c in range(width)
        if r >= top_h or c >= prefix_width
    ):
        raise ValueError("all cells outside the visible prefix must be cover")
    col_period = _smallest_col_period(list(grid[0][:prefix_width]))
    row_period = _smallest_row_period(grid, top_h, col_period)
    return {
        "height": height,
        "width": width,
        "cover": cover,
        "top_h": top_h,
        "prefix_width": prefix_width,
        "row_period": row_period,
        "col_period": col_period,
    }


def _stage_a(grid: list[list[int]]) -> list[list[int]]:
    info = _facts(grid)
    return [
        [
            grid[row % info["row_period"]][(col + 1) % info["col_period"]]
            for col in range(info["width"])
        ]
        for row in range(info["height"])
    ]


def _components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result: list[tuple[int, set[tuple[int, int]]]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        cells = {start}
        pending = deque([start])
        while pending:
            r, c = pending.popleft()
            for dr, dc in _DELTAS4:
                point = (r + dr, c + dc)
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    pending.append(point)
        result.append((color, cells))
    return result


def _spanning_component(grid: list[list[int]]) -> tuple[int, set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    candidates = []
    for color, cells in _components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        if min(rows) == 0 and max(rows) == height - 1 and min(cols) == 0 and max(cols) == width - 1:
            candidates.append((color, cells))
    if len(candidates) != 1:
        raise ValueError(f"expected one four-border-spanning component, found {len(candidates)}")
    return candidates[0]


def analyze(grid: list[list[int]]) -> dict[str, object]:
    info = _facts(grid)
    stage_a = _stage_a(grid)
    color, cells = _spanning_component(stage_a)
    return {
        **info,
        "spanning_color": color,
        "spanning_cell_count": len(cells),
        "spanning_cells": [list(cell) for cell in sorted(cells)],
    }


def solve(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    stage_a = _stage_a(grid)
    if mode == "tile_only":
        return stage_a
    info = _facts(grid)
    _, cells = _spanning_component(stage_a)
    return [
        [info["cover"] if (r, c) in cells else value for c, value in enumerate(row)]
        for r, row in enumerate(stage_a)
    ]


def _palette(seed: int, split_name: str, index: int) -> tuple[int, int, int]:
    token = _stable_index("5295-palette-v1", seed, split_name, index, modulus=8)
    lattice = 2 + token
    cover = 2 + ((token + 3) % 8)
    # Color 1 is deliberately the more frequent visible decoy and is lower
    # than every possible lattice color, defeating two direct color heuristics.
    return 1, lattice, cover


def _construct_input(seed: int, split_name: str, index: int, size: int) -> list[list[int]]:
    period_index = _stable_index("5295-period-v1", seed, split_name, index, modulus=len(_PERIODS))
    row_period, col_period = _PERIODS[period_index]
    top_h = ((size - 1) // row_period) * row_period
    prefix_width = ((size - 1) // col_period) * col_period
    if top_h < row_period or prefix_width < col_period:
        raise ValueError("grid is too small for the selected fundamental period")
    decoy, lattice, cover = _palette(seed, split_name, index)

    # A vertical line plus the tile's final row is a sparse connected lattice.
    # After the canonical one-column shift and global tiling, its component is
    # connected and reaches all four output borders.  The complementary decoy
    # rectangles are more frequent but remain separated by the lattice.
    tile = [
        [lattice if col == 0 or row == row_period - 1 else decoy for col in range(col_period)]
        for row in range(row_period)
    ]
    grid = [[cover for _ in range(size)] for _ in range(size)]
    for row in range(top_h):
        for col in range(prefix_width):
            grid[row][col] = tile[row % row_period][col % col_period]

    info = _facts(grid)
    if (info["row_period"], info["col_period"]) != (row_period, col_period):
        raise ValueError("constructed prefix does not expose its declared smallest periods")
    visible = [grid[r][c] for r in range(top_h) for c in range(prefix_width)]
    if visible.count(decoy) <= visible.count(lattice):
        raise ValueError("decoy must be more frequent than the spanning lattice")
    span_color, _ = _spanning_component(_stage_a(grid))
    if span_color != lattice:
        raise ValueError("reconstructed spanning component is not the intended lattice")
    return grid


def _pair(seed: int, split_name: str, index: int, size: int, mode: str) -> dict[str, list[list[int]]]:
    grid = _construct_input(seed, split_name, index, size)
    return {"input": grid, "output": solve(grid, mode)}


def generate_episode(seed: int, mode: str, demos: int, queries: int, program_solution: str) -> dict[str, object]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    train = [_pair(seed, "train", index, _TRAIN_SIZES[index], mode) for index in range(demos)]
    test = [_pair(seed, "test", index, _TEST_SIZES[index], mode) for index in range(queries)]
    fingerprints = {
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in [*train, *test]
    }
    if len(fingerprints) != demos + queries:
        raise RuntimeError("generated episode contains duplicate inputs")
    return {"train": train, "test": test, "program_solution": program_solution}
