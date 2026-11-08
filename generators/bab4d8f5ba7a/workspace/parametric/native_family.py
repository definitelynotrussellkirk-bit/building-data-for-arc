"""Recolor row markers, optionally recomputing the largest resulting component."""
from __future__ import annotations
import hashlib
from pathlib import Path
import random

TASK_ID = "bab4d8f5ba7a"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"mode": ["row", "largest"]}
DEFAULT = {"mode": "row"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
assert CANONICAL.startswith("(rule!") and CANONICAL.endswith(")")
STAGE_EXPRESSION = CANONICAL[len("(rule!"):-1].strip()
STAGE_BINDING = "(stage " + STAGE_EXPRESSION + ")"
RENDER = "(grid-from-fn hh ww (lambda (r c) (if (member? (list r c) cells) (obj-color chosen) 0)))"
ALTERNATIVE = """(rule! (let* (BINDING (comps (objects stage 0)))
  (if (empty? comps) (list (list 0))
    (let* ((ordered (sort comps (lambda (a b)
               (if (= (obj-size a) (obj-size b))
                 (cell< (first (sort (obj-cells a) cell<)) (first (sort (obj-cells b) cell<)))
                 (> (obj-size a) (obj-size b))))))
           (chosen (first ordered))
           (cells (normalize-cells (obj-cells chosen)))
           (hh (+ 1 (apply max (map first cells))))
           (ww (+ 1 (apply max (map second cells)))))
      RENDER))))""".replace("BINDING", STAGE_BINDING).replace("RENDER", RENDER)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    if type(settings["mode"]) is not str or settings["mode"] not in PARAMETERS["mode"]:
        raise ValueError("mode must be row or largest")
    return settings["mode"]


def program(settings):
    return CANONICAL if _setting(settings) == "row" else ALTERNATIVE


def _validate_grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("need a nonempty list of nonempty lists")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid axes must be 1..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be exact integer colors0..9")


def normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def recolor(grid):
    _validate_grid(grid)
    return [[row[0] if c > 0 and v == 8 and row[0] != 0 else v
             for c, v in enumerate(row)] for row in grid]


def components(grid):
    """Same-color, nonzero four-components of the supplied state (no recoloring)."""
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            color = grid[r][c]
            cells, stack = {(r, c)}, [(r, c)]
            seen.add((r, c))
            while stack:
                y, x = stack.pop()
                for point in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    py, px = point
                    if 0 <= py < h and 0 <= px < w and point not in seen and grid[py][px] == color:
                        seen.add(point); cells.add(point); stack.append(point)
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def selected(grid):
    """Select in the supplied state; ties compare the first actual occupied cell."""
    objects = components(grid)
    return min(objects, key=lambda obj: (-len(obj["cells"]), obj["cells"][0])) if objects else None


def _mask(obj):
    if obj is None:
        return [[0]]
    cells = set(normalize(obj["cells"]))
    return [[obj["color"] if (r, c) in cells else 0 for c in range(max(c for _, c in cells) + 1)]
            for r in range(max(r for r, _ in cells) + 1)]


def solve(grid, mode="row"):
    _setting({"mode": mode})
    stage = recolor(grid)
    return stage if mode == "row" else _mask(selected(stage))


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


_PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)


def _core0(rng):
    # Source-derived from the current independently executed design probe.
    a, b, color = rng.sample(_PALETTE, 3)
    grid = [[0] * 17 for _ in range(15)]
    for r in range(1, 6):
        grid[r][0] = a
        for c in range(3, 8):
            if r in (1, 5) or c in (3, 7):
                grid[r][c] = a if (r - 1 + c - 3) % 2 == 0 else 8
    grid[1][1], grid[1][2] = 8, a
    grid[3][5] = grid[6][8] = a
    for c in range(10, 17):
        grid[7][c] = b
    for r in range(8, 14):
        grid[r][16] = b
    for r in (0, 2, 4, 6):
        for c in (10, 12, 14):
            grid[r][c] = b
    grid[0][0], grid[0][5] = b, 8
    grid[2][4] = color
    grid[6][2] = grid[6][3] = 8
    grid[14][0], grid[14][2], grid[14][3] = color, 8, 8
    if rng.randrange(2):
        grid.reverse()
    return grid


def _core1(rng):
    low, color = rng.sample(range(1, 8), 2)
    grid = [[0] * 18 for _ in range(14)]
    for r in range(1, 6):
        for c in range(2, 7):
            if r in (1, 5) or c in (2, 6):
                grid[r][c] = 8
    grid[0][0] = low
    for c in range(2, 7):
        grid[0][c] = 8
    for r in range(8, 12):
        for c in range(1, 5):
            grid[r][c] = low
    for c in range(9, 17):
        grid[1][c] = 9
    for r in range(2, 10):
        grid[r][9] = 9
    grid[3][4] = grid[6][7] = 8
    grid[2][3] = low
    grid[13][0], grid[13][3], grid[13][4] = color, 8, 8
    return grid


def _small(h, w, rng):
    palette = rng.sample(_PALETTE, 3)
    grid = [[rng.choice([0, 0, 0, 8, *palette]) for _ in range(w)] for _ in range(h)]
    for row in grid:
        row[0] = rng.choice([0, 8, *palette])
    grid[0][0], grid[0][-1] = palette[0], 8
    grid[1][0], grid[1][-1] = 0, 8
    grid[2][0], grid[2][1] = palette[1], palette[2]
    return grid


def _dense(h, w, rng, tooth_adjust=0):
    """Balanced merged comb, plus a dense field fragmented by alternating colors."""
    a, b, color = rng.sample(_PALETTE, 3)
    sh, sw = h - 4, w // 2 - 3
    count = sh // 2 + 1 + tooth_adjust
    middle = sh // 2
    first_count = (count - 2) // 2
    full = {0, sh - 1} | set(rng.sample(range(1, middle), first_count))
    full.update(rng.sample(range(middle, sh - 1), count - 2 - first_count))
    grid = [[0] * w for _ in range(h)]
    for r in range(2, h - 2):
        grid[r][0] = a
        for c in range(2, sw + 2):
            if c == 2 or r - 2 in full:
                grid[r][c] = a if (r + c) % 2 == 0 else 8
    start = sw + 4
    for r in range(h):
        for c in range(start, w):
            grid[r][c] = b if (r + c) % 2 == 0 else color
    bh, bw = max(2, sh // 2 - 1), min(4, w - start)
    row, col = rng.randrange(h - bh + 1), rng.randrange(start, w - bw + 1)
    for r in range(row, row + bh):
        for c in range(col, col + bw):
            grid[r][c] = b
    grid[0][0], grid[0][4] = b, 8
    grid[-1][0], grid[-1][5] = color, 8
    return grid


def input_bank(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    d, q = _rng(seed, "demos"), _rng(seed, "queries")
    demos = [_core0(d), _core1(d), [[d.randrange(10)]], _small(6, 9, d),
             _dense(21, 26, d), _dense(30, 30, d)]
    queries = [_small(4, 7, q), _dense(14, 19, q), _dense(23, 27, q), _dense(30, 30, q, -1)]
    q.shuffle(queries)
    return demos, queries


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"mode": _rng(seed, "settings").choice(PARAMETERS["mode"])}
    mode = _setting(settings)
    train, test = input_bank(seed)
    def pairs(grids):
        return [{"input": grid, "output": solve(grid, mode)} for grid in grids]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
