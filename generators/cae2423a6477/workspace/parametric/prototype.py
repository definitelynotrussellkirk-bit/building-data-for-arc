"""Exact frame selection followed optionally by global selected-barrier filling.

The sampler is constructive.  Its two core demonstrations teach geometry,
connectivity, and composition before independently sampled private queries.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
import hashlib
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
MODES = ("border", "enclosed")
FOUR = ((-1, 0), (0, -1), (0, 1), (1, 0))


def _mode(settings):
    if type(settings) is not dict or set(settings) != {"completion_mode"}:
        raise ValueError("settings must contain exactly completion_mode")
    value = settings["completion_mode"]
    if type(value) is not str or value not in MODES:
        raise ValueError("completion_mode must be border or enclosed")
    return value


def _validate(grid, values=(0, 3)):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be 1..30")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(v) is not int or v not in values for v in row) for row in grid):
        raise ValueError("expected a rectangular exact-integer grid in the declared palette")
    return len(grid), width


def _components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3}
    found = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = [start]
        for r, c in queue:
            for dr, dc in FOUR:
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    queue.append(p)
        cells = set(queue)
        r1, r2 = min(r for r, c in cells), max(r for r, c in cells)
        c1, c2 = min(c for r, c in cells), max(c for r, c in cells)
        exact = (r2-r1 >= 2 and c2-c1 >= 2 and
                 len(cells) == 2 * (r2-r1+c2-c1) and
                 all(r in (r1, r2) or c in (c1, c2) for r, c in cells))
        found.append({"box": [r1, c1, r2, c2], "cells": sorted(cells), "selected": exact})
    return found


def first_stage(grid):
    """Recognize 4-connected exact green rectangular outlines, then paint 7."""
    _validate(grid)
    out = [row[:] for row in grid]
    for obj in _components(grid):
        if obj["selected"]:
            for r, c in obj["cells"]:
                out[r][c] = 7
    return out


def _outside(stage):
    h, w = len(stage), len(stage[0])
    reached = {(r, c) for r in range(h) for c in range(w)
               if (r in (0, h-1) or c in (0, w-1)) and stage[r][c] != 7}
    queue = deque(sorted(reached))
    while queue:
        r, c = queue.popleft()
        for dr, dc in FOUR:
            nr, nc = r+dr, c+dc
            if (0 <= nr < h and 0 <= nc < w and stage[nr][nc] != 7 and
                    (nr, nc) not in reached):
                reached.add((nr, nc))
                queue.append((nr, nc))
    return reached


def second_stage(intermediate):
    """Fill unreachable zeros; only selected orange cells obstruct 4-connectivity."""
    h, w = _validate(intermediate, (0, 3, 7))
    outside = _outside(intermediate)
    return [[2 if intermediate[r][c] == 0 and (r, c) not in outside else intermediate[r][c]
             for c in range(w)] for r in range(h)]


def mirror(grid, settings):
    mode = _mode(settings)
    stage = first_stage(grid)
    return stage if mode == "border" else second_stage(stage)


def analyze(grid, settings):
    mode = _mode(settings)
    stage = first_stage(grid)
    objects = _components(grid)
    output = stage if mode == "border" else second_stage(stage)
    return {"components": objects,
            "selected_boxes": [o["box"] for o in objects if o["selected"]],
            "intermediate": stage,
            "fill_cells": [[r, c] for r in range(len(grid)) for c in range(len(grid[0]))
                           if stage[r][c] == 0 and output[r][c] == 2],
            "output": output}


def program(settings):
    mode = _mode(settings)
    return (HOME / ("canonical.rkt" if mode == "border" else "enclosed.rkt")).read_text()


def transform(grid, turns=0, flip=False):
    """Clockwise quarter turns after an optional horizontal reflection."""
    out = [row[::-1] if flip else row[:] for row in grid]
    for _ in range(turns % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def _rng(seed, stream):
    digest = hashlib.sha256(f"cae2423a6477/native-v1/{seed}/{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _blank(h, w):
    return [[0]*w for _ in range(h)]


def _frame(g, top, left, h, w):
    for r in range(h):
        for c in range(w):
            if r in (0, h-1) or c in (0, w-1):
                g[top+r][left+c] = 3


def _solid(g, top, left, h, w):
    for r in range(top, top+h):
        for c in range(left, left+w):
            g[r][c] = 3


def _place(g, tile, top, left):
    for r, row in enumerate(tile):
        for c, v in enumerate(row):
            if v:
                if g[top+r][left+c]:
                    raise AssertionError("constructive placement overlap")
                g[top+r][left+c] = v


def _reflect(g, rng):
    out = [row[:] for row in g]
    if rng.getrandbits(1):
        out = [row[::-1] for row in out]
    if rng.getrandbits(1):
        out.reverse()
    return out


def _tiles(rng):
    result = []
    # Four exact frames jointly seal a central 3x3 pocket under 4-connectivity.
    g = _blank(9, 9)
    for r, c in ((0, 3), (3, 0), (3, 6), (6, 3)):
        _frame(g, r, c, 3, 3)
    result.append(g)
    # Detached green content is passable for reachability and survives filling.
    g = _blank(9, 9)
    _frame(g, 0, 0, 9, 9); _frame(g, 3, 3, 3, 3); g[2][2] = 3
    result.append(g)
    # A closed degree-two stepped loop, plus thin and solid distractors.
    g = _blank(9, 9)
    cells = ({(0, c) for c in range(3)} | {(1, c) for c in range(2, 6)} |
             {(r, 0) for r in range(5)} | {(r, 5) for r in range(1, 5)} |
             {(4, c) for c in range(6)})
    for r, c in cells: g[r][c] = 3
    _solid(g, 7, 0, 1, 5); _solid(g, 6, 7, 2, 2)
    result.append(g)
    # A complete border with an outward branch is not an exact outline object.
    g = _blank(9, 9)
    _frame(g, 0, 0, 5, 5); g[2][5] = 3
    _solid(g, 7, 0, 2, 3); _solid(g, 6, 8, 3, 1); g[6][5] = 3
    result.append(g)
    # Missing border cell plus attached interior cell spoofs perimeter size.
    g = _blank(9, 9)
    _frame(g, 0, 0, 5, 7); g[0][rng.randrange(1, 6)] = 0
    _frame(g, 6, 0, 3, 4); g[6][1] = 0; g[7][1] = 3
    _solid(g, 6, 6, 2, 2)
    result.append(g)
    # Inward branch and diagonal contacts separate object connectivity rules.
    g = _blank(9, 9)
    _frame(g, 0, 0, 5, 5); g[1][2] = 3
    _frame(g, 6, 6, 3, 3); g[5][5] = 3
    result.append(g)
    result = [transform(g, rng.randrange(4), bool(rng.getrandbits(1))) for g in result]
    rng.shuffle(result)
    return result


def _small(rng, inactive=False):
    g = _blank(9, 11)
    _frame(g, 2, 0, 3, 11)
    _frame(g, 6, 0, 3, 3)
    _solid(g, 6, 4, 3, 3)
    _frame(g, 6, 8, 3, 3); g[6][9] = 0
    _solid(g, 0, rng.randrange(3, 6), 1, 3)
    if inactive:
        g[3][rng.randrange(1, 10)] = 3
        g[7][1] = 3
    return _reflect(g, rng)


def _large_core(rng):
    g = _blank(29, 29)
    for i, tile in enumerate(_tiles(rng)):
        _place(g, tile, (i//2)*10, (i%2)*10)
    _frame(g, 0, 22, 29, 3)
    return _reflect(g, rng)


def _mosaic(h, w, rng):
    g = _blank(h, w)
    for i, tile in enumerate(_tiles(rng)):
        _place(g, tile, (i//3)*10, (i%3)*10)
    lower = h-20
    _frame(g, 20, 0, lower, 9)
    _frame(g, 20, 10, lower, 9); g[20][rng.randrange(11, 18)] = 0
    _frame(g, 20, 20, lower, w-20)
    return _reflect(g, rng)


def _general(h, w, rng):
    if h >= 23 and w >= 29:
        return _mosaic(h, w, rng)
    g = _blank(h, w)
    for r, c in ((0, 3), (3, 0), (3, 6), (6, 3)):
        _frame(g, r, c, 3, 3)
    _frame(g, 0, 11, max(7, h-10), w-11)
    g[2][13] = 3
    if h >= 17:
        _frame(g, h-5, 0, 5, 7); g[h-5][rng.randrange(1, 6)] = 0
        _frame(g, h-6, w-6, 5, 6); g[h-5][w-4] = 3
    else:
        _solid(g, h-2, 0, 2, 5)
    _frame(g, h-3, 8, 3, 3)
    return _reflect(g, rng)


def _key(grid):
    return tuple(tuple(row) for row in grid)


@lru_cache(maxsize=64)
def _inputs(seed):
    seen = set()

    def novel(make, stream):
        rng = _rng(seed, stream)
        for _ in range(64):
            g = make(rng)
            key = _key(g)
            if key not in seen:
                seen.add(key)
                return key
        raise RuntimeError("bounded constructive uniqueness search exhausted")

    core = [novel(_small, "core-small"), novel(_large_core, "core-large")]
    extras = [novel(lambda rng, h=h, w=w: _general(h, w, rng), f"demo-{i}")
              for i, (h, w) in enumerate(((13, 17), (17, 21), (23, 27), (27, 29)))]
    queries = [novel(lambda rng: _small(rng, bool(rng.getrandbits(1))), "query-small")]
    queries += [novel(lambda rng, h=h, w=w: _general(h, w, rng), f"query-{i}")
                for i, (h, w) in enumerate(((17, 21), (25, 29), (30, 30)))]
    _rng(seed, "query-order").shuffle(queries)
    return tuple(core+extras), tuple(queries)


def generate(seed, settings, demos=3, queries=4):
    _mode(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    train, test = _inputs(seed)

    def label(key):
        grid = [list(row) for row in key]
        return {"input": grid, "output": mirror(grid, settings)}

    return {"train": [label(k) for k in train[:demos]],
            "test": [label(k) for k in test[:queries]],
            "program_solution": program(settings)}
