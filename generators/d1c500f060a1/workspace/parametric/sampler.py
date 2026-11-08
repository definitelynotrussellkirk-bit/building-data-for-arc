"""Matched constructive banks for transformed-accent piece ordering."""
from __future__ import annotations

import hashlib
from random import Random


def _rng(seed, stream):
    data = f"d1c500f060a1/accent-order-v1/{stream}/{seed}".encode("ascii")
    return Random(int.from_bytes(hashlib.sha256(data).digest(), "big"))


def _rotate_cw(grid): return [list(row) for row in zip(*grid[::-1])]
def _flip_lr(grid): return [list(reversed(row)) for row in grid]
def _flip_ud(grid): return [list(row) for row in reversed(grid)]


def _orient(grid, corner):
    if corner == "top_left": return [list(row) for row in grid]
    if corner == "top_right": return _flip_lr(grid)
    if corner == "bottom_left": return _flip_ud(grid)
    if corner == "bottom_right": return _flip_ud(_flip_lr(grid))
    raise ValueError(corner)


def _transform(grid, code):
    if code == 1: return _rotate_cw(grid)
    if code == 2: return _rotate_cw(_rotate_cw(grid))
    if code == 3: return _rotate_cw(_rotate_cw(_rotate_cw(grid)))
    if code == 4: return _flip_lr(grid)
    if code == 5: return _flip_ud(grid)
    raise ValueError(code)


def _key(piece, accent):
    r, c = next((r, c) for r, row in enumerate(piece) for c, value in enumerate(row)
                if value == accent)
    return r, c, len(piece), len(piece[0])


def _crop(rng, h, w, body, accent, density):
    cells = {(r, 0) for r in range(h)} | {(0, c) for c in range(w)}
    candidates = [(r, c) for r in range(1, h) for c in range(1, w)]
    rng.shuffle(candidates)
    target = max(h + w - 1, density)
    while len(cells) < target:
        changed = False
        for r, c in list(candidates):
            if any((r + dr, c + dc) in cells for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                cells.add((r, c)); candidates.remove((r, c)); changed = True
                if len(cells) >= target: break
        if not changed: break
    crop = [[0] * w for _ in range(h)]
    for r, c in cells: crop[r][c] = body
    crop[0][0] = accent
    return crop


def _scene(rng, dims, motif_dims, corner, colors, density, *, boundary=False):
    h, w = dims
    mh, mw = motif_dims
    body, accent = colors
    crop = _orient(_crop(rng, mh, mw, body, accent, density), corner)
    codes = rng.sample(range(1, 6), 4)
    keys = {code: _key(_transform(crop, code), accent) for code in codes}
    if codes == sorted(codes, key=keys.__getitem__):
        codes[0], codes[1] = codes[1], codes[0]
    columns = sorted(rng.sample(range(w), len(codes)))
    if boundary:
        r0, c0 = h - mh, w - mw
    else:
        r0, c0 = rng.randint(2, h - mh), rng.randint(0, w - mw)
    grid = [[0] * w for _ in range(h)]
    for col, code in zip(columns, codes): grid[0][col] = code
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value: grid[r0 + r][c0 + c] = value
    return grid


def _bank(rng, specs):
    palette = [(6, 8), (7, 9), (4, 6), (5, 7), (8, 3), (9, 4)]
    result = []
    for index, (dims, motif_dims, corner, density, boundary) in enumerate(specs):
        result.append(_scene(rng, dims, motif_dims, corner,
                             palette[index % len(palette)], density, boundary=boundary))
    return result


def inputs(seed, demos=3, queries=4):
    for name, value, low, high in (("seed", seed, 0, 2**63 - 1),
                                   ("demos", demos, 2, 6),
                                   ("queries", queries, 1, 4)):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    demos_all = _bank(_rng(seed, "demos"), [
        ((9, 12), (3, 4), "top_left", 8, False),
        ((11, 15), (4, 5), "top_right", 12, False),
        ((13, 17), (5, 4), "bottom_left", 14, True),
        ((16, 20), (4, 6), "bottom_right", 16, False),
        ((20, 24), (6, 5), "top_left", 20, False),
        ((24, 27), (5, 6), "top_right", 22, True),
    ])
    queries_all = _bank(_rng(seed, "queries"), [
        ((10, 14), (3, 5), "bottom_left", 10, False),
        ((15, 18), (5, 4), "bottom_right", 15, True),
        ((23, 25), (6, 5), "top_right", 21, False),
        ((30, 30), (5, 6), "bottom_right", 18, True),
    ])
    return {"train": demos_all[:demos], "test": queries_all[:queries]}
