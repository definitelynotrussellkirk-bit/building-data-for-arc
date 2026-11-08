#!/usr/bin/env python3
"""Two-setting sequential family for 1713e09a3132.

A renders all rectangle borders using the canonical reading-order overwrite
policy.  In ``paint_enclosed`` mode, B consumes that combined rendered grid and
recolors zero cells that have nonzero support in all four cardinal directions
to 8.  This makes the intermediate outline state necessary.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import random

TASK_ID = "1713e09a3132"
HOME = Path(__file__).resolve().parent
MODES = ("outline", "paint_enclosed")
DEFAULT_MODE = "outline"


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
    filename = "canonical.rkt" if mode == "outline" else "paint-enclosed.rkt"
    return (HOME / filename).read_text()


def _rng(seed: int, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|v1|{seed}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _reading_colors(grid):
    seen = []
    for row in grid:
        for value in row:
            if value != 0 and value not in seen:
                seen.append(value)
    return seen


def render_outlines(grid):
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for color in _reading_colors(grid):
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(cells) < 2:
            raise ValueError(f"color {color} needs two corner cells")
        (ra, ca), (rb, cb) = cells[:2]
        r0, r1 = sorted((ra, rb))
        c0, c1 = sorted((ca, cb))
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    out[r][c] = color
    return out


def paint_enclosed(grid):
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            left = any(grid[r][cc] != 0 for cc in range(c))
            right = any(grid[r][cc] != 0 for cc in range(c + 1, w))
            up = any(grid[rr][c] != 0 for rr in range(r))
            down = any(grid[rr][c] != 0 for rr in range(r + 1, h))
            if left and right and up and down:
                out[r][c] = 8
    return out


def python_mirror(grid, mode: str = DEFAULT_MODE):
    _validate_mode(mode)
    intermediate = render_outlines(grid)
    return intermediate if mode == "outline" else paint_enclosed(intermediate)


def python_wrong_order(grid):
    """Apply B to sparse corner markers before A renders the outlines."""
    return render_outlines(paint_enclosed(grid))


def _sample_input(seed: int, index: int, *, stress: bool):
    rng = _rng(seed, index)
    if stress:
        h = w = 30
        boxes = [
            ((1, 1, 21, 21), True),
            ((8, 8, 28, 28), False),
            ((2, 23, 15, 29), True),
        ]
    else:
        h = 12 + index % 3
        w = 13 + (index * 2) % 2
        boxes = [
            ((1, 1, h - 3, min(w - 4, 10)), True),
            ((3, 3, h - 2, w - 2), False),
            ((0, w - 5, 5, w - 1), True),
        ]
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], len(boxes))
    grid = [[0 for _ in range(w)] for _ in range(h)]
    occupied = set()
    for color, (box, positive) in zip(colors, boxes):
        r0, c0, r1, c1 = box
        points = ((r0, c0), (r1, c1)) if positive else ((r0, c1), (r1, c0))
        if any(point in occupied for point in points):
            raise AssertionError("corner collision")
        for r, c in points:
            grid[r][c] = color
            occupied.add((r, c))
    if paint_enclosed(grid) != grid:
        raise AssertionError("wrong-order B must see no enclosure in sparse input")
    if python_mirror(grid, "paint_enclosed") == python_wrong_order(grid):
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
