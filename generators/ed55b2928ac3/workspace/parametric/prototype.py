#!/usr/bin/env python3
"""Two-setting sequential family for ed55b2928ac3.

A always clears the corner key, crops the content, and performs the keyed
transform.  In ``top_edge_to_8`` mode, B then reads the *transformed* top edge,
selects its leftmost nonzero color, and recolors every occurrence of that color
to 8.  Matched inputs are independent of the episode setting.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import random

TASK_ID = "ed55b2928ac3"
HOME = Path(__file__).resolve().parent
MODES = ("plain", "top_edge_to_8")
DEFAULT_MODE = "plain"


def _validate_mode(mode: str) -> None:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"finish_mode must be one of {MODES}, got {mode!r}")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def program_for(mode: str = DEFAULT_MODE) -> str:
    _validate_mode(mode)
    filename = "canonical.rkt" if mode == "plain" else "top-edge-to-8.rkt"
    return (HOME / filename).read_text()


def _rng(seed: int, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|v1|{seed}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _crop(grid):
    work = [row[:] for row in grid]
    work[0][0] = 0
    cells = [(r, c) for r, row in enumerate(work) for c, value in enumerate(row) if value != 0]
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in work[r0:r1 + 1]]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _flip_ud(grid):
    return [row[:] for row in grid[::-1]]


def _transform(grid, key: int):
    if key == 1:
        return _rotate_cw(grid)
    if key == 2:
        return _rotate_180(grid)
    if key == 3:
        return _flip_lr(grid)
    if key == 4:
        return _flip_ud(grid)
    return [row[:] for row in grid]


def _top_color(grid) -> int:
    for value in grid[0]:
        if value != 0:
            return value
    raise ValueError("transformed top row must contain a nonzero cell")


def _recolor(grid, source: int, target: int = 8):
    return [[target if value == source else value for value in row] for row in grid]


def python_mirror(grid, mode: str = DEFAULT_MODE):
    _validate_mode(mode)
    key = grid[0][0]
    intermediate = _transform(_crop(grid), key)
    if mode == "plain":
        return intermediate
    return _recolor(intermediate, _top_color(intermediate), 8)


def python_wrong_order(grid):
    """B reads/recolors the untransformed crop, then A transforms it."""
    key = grid[0][0]
    crop = _crop(grid)
    return _transform(_recolor(crop, _top_color(crop), 8), key)


def _sample_input(seed: int, index: int, *, stress: bool):
    rng = _rng(seed, index)
    key = 1 + index % 4
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 6)
    a, b, c, d, e, f = colors
    # The first nonzero top-edge color changes under every key 1..4, so the
    # correct and wrong-order sequential programs are observably different.
    crop = [
        [a, 0, b, 0],
        [a, c, b, d],
        [e, c, f, d],
    ]
    if stress:
        h = w = 30
    else:
        h = 8 + index % 6
        w = 9 + (index * 2) % 6
    row0 = 2 + rng.randrange(h - len(crop) - 1)
    col0 = 2 + rng.randrange(w - len(crop[0]) - 1)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    grid[0][0] = key
    for dr, row in enumerate(crop):
        for dc, value in enumerate(row):
            grid[row0 + dr][col0 + dc] = value
    if python_mirror(grid, "top_edge_to_8") == python_wrong_order(grid):
        raise AssertionError("sampler failed to expose sequential order")
    return grid


def generate_claims(seed: int, finish_mode: str = DEFAULT_MODE, *, demos: int = 3, queries: int = 4):
    _validate_seed(seed)
    _validate_mode(finish_mode)
    _validate_counts(demos, queries)
    total = demos + queries
    inputs = [_sample_input(seed, index, stress=(index == total - 1)) for index in range(total)]
    pairs = [{"input": grid, "output": python_mirror(grid, finish_mode)} for grid in inputs]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(finish_mode),
    }
