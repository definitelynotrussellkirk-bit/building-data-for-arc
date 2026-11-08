"""Input-pure native proposal: optional 8→2 merge before per-color ranking."""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

MODES = ("ignore", "merge")
DEFAULT = {"bridge_mode": "ignore"}
NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"bridge_mode"} or settings["bridge_mode"] not in MODES:
        raise ValueError("settings must contain only bridge_mode='ignore' or 'merge'")
    return settings["bridge_mode"]


def program(settings):
    mode = _settings(settings)
    canonical = Path(__file__).with_name("canonical.rkt").read_text()
    if mode == "ignore":
        return canonical
    # Reuse the exact canonical callable; only the input grid is different.
    callable_source = canonical[len("(rule! "):-1]
    return "(rule! (lambda (grid)\n  (define merged (map-grid grid\n    (lambda (r c v) (if (= v 8) 2 v))))\n  (" + callable_source + " merged)))"


def _grid(grid):
    if type(grid) is not list or not grid or len(grid) > 30:
        raise ValueError("grid needs 1..30 rows")
    if any(type(row) is not list or not row for row in grid):
        raise ValueError("grid rows must be nonempty lists")
    if len(grid[0]) > 30 or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid needs a rectangular width 1..30")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be exact ARC integers")


def components(grid, connectivity=4):
    _grid(grid)
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    directions = NEIGHBORS if connectivity == 4 else tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)
    h, w = len(grid), len(grid[0])
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            cells, stack = {(r, c)}, [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in directions:
                    cell = nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and cell not in seen and grid[nr][nc] == color:
                        seen.add(cell)
                        cells.add(cell)
                        stack.append(cell)
            result.append({"color": color, "cells": sorted(cells), "size": len(cells)})
    return result


def preprocess(grid, settings):
    mode = _settings(settings)
    _grid(grid)
    return [[2 if v == 8 and mode == "merge" else v for v in row] for row in grid]


def mirror(grid, settings):
    intermediate = preprocess(grid, settings)
    parts = components(intermediate)
    out = [[0] * len(grid[0]) for _ in grid]
    for color, target in ((2, 4), (3, 1)):
        candidates = [o for o in parts if o["color"] == color]
        if not candidates:
            raise ValueError("both red and green are required")
        winner = max(candidates, key=lambda o: o["size"])
        for r, c in winner["cells"]:
            out[r][c] = target
    return out


def analyze(grid):
    errors = []
    try:
        _grid(grid)
    except ValueError as e:
        return {"errors": [str(e)]}
    states = {}
    for mode in MODES:
        parts = components(preprocess(grid, {"bridge_mode": mode}))
        sizes = {str(color): sorted((o["size"] for o in parts if o["color"] == color), reverse=True) for color in (2, 3)}
        for color, values in sizes.items():
            if not values or (len(values) > 1 and values[0] == values[1]):
                errors.append(f"{mode} color {color} requires a unique maximum")
        states[mode] = {"sizes": sizes, "components": parts}
    return {"errors": errors, "height": len(grid), "width": len(grid[0]),
            "foreground": sum(v != 0 for row in grid for v in row), "states": states}


def transform(grid, symmetry):
    if type(symmetry) is not int or not 0 <= symmetry < 8:
        raise ValueError("symmetry must be 0..7")
    out = [row[:] for row in grid]
    if symmetry >= 4:
        out = [row[::-1] for row in out]
    for _ in range(symmetry % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def _rng(seed, role, index):
    digest = hashlib.sha256(f"6afe10b621e4:bridge-v1:{seed}:{role}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _grow(h, w, size, rng, *, root=None, spread=False):
    if not 1 <= size <= h * w:
        raise ValueError(f"shape size {size} does not fit {h}x{w}")
    if root is None:
        root = (rng.randrange(h), rng.randrange(w))
    cells = {root}
    while len(cells) < size:
        frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in NEIGHBORS
                           if 0 <= r + dr < h and 0 <= c + dc < w and (r + dr, c + dc) not in cells})
        def score(cell):
            trial = cells | {cell}
            area = (max(r for r, _ in trial) - min(r for r, _ in trial) + 1) * (max(c for _, c in trial) - min(c for _, c in trial) + 1)
            return area if spread else -area
        scores = [score(x) for x in frontier]
        best = max(scores)
        cells.add(rng.choice([x for x, s in zip(frontier, scores) if s == best]))
    return cells


def _scene(seed, role, index, profile):
    h, w, control = profile
    rng = _rng(seed, role, index)
    rs = [(0, h // 2), (h // 2 + 1, h)]
    cs = [(0, w // 2), (w // 2 + 1, w)]
    slots = [(r0, c0, r1 - r0, c1 - c0) for r0, r1 in rs for c0, c1 in cs]
    core = role == "train" and index < 2
    if core:
        # Same global symmetry, opposite winner corners across the two demos.
        # This defeats fixed-position selectors constructively, without retries.
        order = (0, 3, 1, 2) if index == 0 else (1, 0, 2, 3)
        slots = [slots[k] for k in order]
    else:
        rng.shuffle(slots)
    min_h, min_w = min(x[2] for x in slots), min(x[3] for x in slots)
    q = max(1, min(min_h * min_w // 30,
                   (min_h // 2) * min_w // 12,
                   (min_h - min_h // 2 - 1) * min_w // 10))
    grid = [[0] * w for _ in range(h)]

    def paint(slot, cells, color, offset=(0, 0)):
        r0, c0, _, _ = slot
        for r, c in cells:
            rr, cc = r0 + r + offset[0], c0 + c + offset[1]
            if grid[rr][cc]:
                raise AssertionError("constructive regions overlap")
            grid[rr][cc] = color

    # A bridge joins 3q and 4q red fragments into 8q cells after preprocessing.
    a = slots[0]
    ah, aw = a[2:]
    mid = aw // 2
    row = rng.randrange(ah - q + 1)
    paint(a, _grow(ah, mid, 3 * q, rng, root=(row, mid - 1), spread=True), 2)
    paint(a, _grow(ah, aw - mid - 1, 4 * q, rng, root=(row + q - 1, 0), spread=bool(index % 2)), 2, (0, mid + 1))
    paint(a, {(row + k, mid) for k in range(q)}, 8)

    # An independent 6q red object wins before merging; diagonal red is excluded.
    b = slots[1]
    bh, bw = b[2:]
    paint(b, _grow(bh - 1, bw - 1, 6 * q, rng, root=(bh - 2, bw - 2)), 2)
    paint(b, {(bh - 1, bw - 1)}, 2)

    # Both rankings matter. The sparse green decoy also challenges bbox area.
    c = slots[2]
    ch, cw = c[2:]
    cut = ch // 2
    green_main, green_decoy = (12 * q, 10 * q) if control else (4 * q, 3 * q)
    if role == "train" and index == 0:
        # Eight occupied cells in a 3x3 box beat a seven-cell 4x4 L, despite
        # smaller bbox area, either side, bbox perimeter and exposed perimeter.
        dense = {(r, c) for r in range(3) for c in range(3)} - {(0, 0)}
        sparse = {(0, c) for c in range(4)} | {(1, 0), (2, 0), (3, 0)}
        if rng.randrange(2):
            sparse = {(r, 3 - c) for r, c in sparse}
        paint(c, dense, 3, (rng.randrange(cut - 2), rng.randrange(cw - 2)))
        paint(c, sparse, 3, (cut + 1 + rng.randrange(ch - cut - 4), rng.randrange(cw - 3)))
    else:
        paint(c, _grow(cut, cw, green_main, rng), 3)
        paint(c, _grow(ch - cut - 1, cw, green_decoy, rng, spread=True), 3, (cut + 1, 0))

    # The control has a standalone color-8 winner. All 8s merge, not just bridges.
    d = slots[3]
    dh, dw = d[2:]
    eight_root = (dh - 2, dw - 2) if core and index == 1 else None
    paint(d, _grow(dh - 1, dw - 1, (9 if control else 2) * q, rng, root=eight_root), 8)
    if core and index == 1:
        # A diagonal-only 8 is erased even after merging; 8-connectivity would
        # incorrectly add it to the winning component. Both edge neighbors stay 0.
        paint(d, {(dh - 1, dw - 1)}, 8)
    extras = rng.sample([1, 4, 5, 6, 7, 9], min(4, dw))
    if rng.randrange(2) and not (core and index == 1):
        extras[0] = 2
    if rng.randrange(2):
        extras[2] = 3
    rng.shuffle(extras)
    for k, color in enumerate(extras):
        paint(d, {(dh - 1, k)}, color)
    # Boundary noise is lawful and ignored by both exact settings; it guarantees
    # true full-canvas contact while substantial objects carry the size stress.
    for r, c in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
        if grid[r][c] == 0:
            grid[r][c] = rng.choice([1, 4, 5, 6, 7, 9])
    symmetry = _rng(seed, "core-symmetry", 0).randrange(8) if core else rng.randrange(8)
    grid = transform(grid, symmetry)
    errors = analyze(grid)["errors"]
    if errors:
        raise AssertionError(errors)
    return grid


def generate(seed, settings, demos=3, queries=4):
    _settings(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    demo_profiles = [(19, 19, False), (13, 13, True), (17, 23, False),
                     (21, 17, True), (25, 27, False), (28, 26, True)]
    query_profiles = [(11, 13, False), (19, 23, True), (30, 30, True), (25, 29, False)]
    _rng(seed, "query-order", 0).shuffle(query_profiles)
    def pairs(role, profiles):
        result = []
        for i, profile in enumerate(profiles):
            g = _scene(seed, role, i, profile)
            result.append({"input": g, "output": mirror(g, settings)})
        return result
    train, test = pairs("train", demo_profiles[:demos]), pairs("test", query_profiles[:queries])
    inputs = [p["input"] for p in train + test]
    if len({repr(g) for g in inputs}) != demos + queries:
        raise AssertionError("duplicate input")
    return {"train": train, "test": test, "program_solution": program(settings)}
