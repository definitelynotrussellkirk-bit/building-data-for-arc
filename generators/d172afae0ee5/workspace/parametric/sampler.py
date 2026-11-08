"""Constructive matched-input banks for the d172 cue-orientation family."""
from __future__ import annotations

import hashlib
from random import Random

CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")


def _rng(seed, stream):
    data = f"d172afae0ee5/cue-family-v1/{stream}/{seed}".encode("ascii")
    return Random(int.from_bytes(hashlib.sha256(data).digest(), "big"))


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _orient(grid, corner):
    if corner == "top_left": return [list(row) for row in grid]
    if corner == "top_right": return _flip_lr(grid)
    if corner == "bottom_left": return _flip_ud(grid)
    if corner == "bottom_right": return _flip_ud(_flip_lr(grid))
    raise ValueError(corner)


def _crop(rng, h, w, body, cue, density):
    # A connected comb reaching both bottom and right bounds.  The unique cue is
    # at top-left before orientation; extra branches make large cases substantive.
    cells = {(r, 0) for r in range(h)} | {(0, c) for c in range(w)}
    available = [(r, c) for r in range(1, h) for c in range(1, w)]
    rng.shuffle(available)
    target = max(h + w - 1, density)
    while len(cells) < target:
        added = False
        for r, c in list(available):
            if any((r + dr, c + dc) in cells for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                cells.add((r, c)); available.remove((r, c)); added = True
                if len(cells) >= target: break
        if not added: break
    crop = [[0] * w for _ in range(h)]
    for r, c in cells: crop[r][c] = body
    crop[0][0] = cue
    return crop


def _scene(rng, size, dims, corner, colors, *, boundary=False, density=None):
    h, w = dims
    body, cue = colors
    crop = _orient(_crop(rng, h, w, body, cue, density or h + w + 2), corner)
    candidates = [(r, c) for r in range(size - h + 1) for c in range(size - w + 1)]
    if boundary:
        source = (0, 0)
        marker = (size - h, size - w)
    else:
        source = rng.choice(candidates)
        marker_choices = [(r, c) for r, c in candidates
                          if not (source[0] <= r <= source[0] + h - 1
                                  and source[1] <= c <= source[1] + w - 1)]
        marker = rng.choice(marker_choices)
    grid = [[0] * size for _ in range(size)]
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value: grid[source[0] + r][source[1] + c] = value
    grid[marker[0]][marker[1]] = 9
    return grid


def _bank(rng, specs):
    colors = rng.sample(range(1, 9), 8)
    result = []
    for index, (size, dims, corner, boundary, density) in enumerate(specs):
        body = colors[(2 * index) % len(colors)]
        cue = colors[(2 * index + 1) % len(colors)]
        if cue == body: cue = (cue % 8) + 1
        result.append(_scene(rng, size, dims, corner, (body, cue),
                             boundary=boundary, density=density))
    return result


def inputs(seed, demos=3, queries=4):
    for name, value, low, high in (("seed", seed, 0, 2**63 - 1),
                                   ("demos", demos, 2, 6),
                                   ("queries", queries, 1, 4)):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    demos_all = _bank(_rng(seed, "demos"), [
        (10, (3, 4), "top_right", False, 8),
        (12, (4, 3), "bottom_left", False, 9),
        (14, (4, 5), "top_left", False, 12),
        (17, (5, 4), "bottom_right", True, 14),
        (21, (6, 5), "top_right", False, 18),
        (25, (7, 6), "bottom_left", False, 22),
    ])
    queries_all = _bank(_rng(seed, "queries"), [
        (13, (4, 4), "bottom_right", False, 11),
        (18, (5, 6), "top_right", True, 17),
        (24, (7, 5), "bottom_left", False, 21),
        (30, (9, 8), "bottom_right", True, 30),
    ])
    return {"train": demos_all[:demos], "test": queries_all[:queries]}
