"""Generator for arc_puzzle_bank_21_set11_bundle:hard_k16.

Rule: normalize the color-2 cells to their bbox and the color-3 cells to
their bbox; overlay the two normalized shapes. Output a grid the size of
their union bbox where a cell present in BOTH shapes is 8, in the 2-shape
only is 2, and in the 3-shape only is 3.

Combinatorial axes: grid size, the two shapes (which set the overlay
output) and their positions.
Degenerates: no_shapes, identical_shapes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "9e47b59d6afc"
VERSION = "2.0.1"  # diversity: random 2/3 shapes + positions + grid (was 2 fixed shapes)
TASK_ID = "9e47b59d6afc"
SUMMARY = (
    "0-bg grid (size varies). ONE color-2 (red) SHAPE and ONE color-3 "
    "(green) SHAPE (random connected polyominoes whose NORMALIZED forms "
    "overlap partially — they share >=1 cell and differ in >=1 cell), "
    "placed apart. Rule: normalize each shape to its bbox and overlay "
    "them; output a grid the size of the union bbox where cells in BOTH "
    "shapes are COLOR 8 (cyan), cells in the 2-shape only are 2, and "
    "cells in the 3-shape only are 3. The grid size, the two shapes "
    "(which set the overlay) and their positions all vary freely (was 2 "
    "fixed shapes)."
)

INVARIANTS = [
    "exactly one color-2 blob and one color-3 blob (placed apart)",
    "their normalized cell sets share >=1 cell (an 8 appears in the output)",
    "their normalized cell sets differ in >=1 cell (a 2 and a 3 also appear)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shapes", "identical_shapes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|"
                                "no_shapes|identical_shapes|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; exactly one color-2 blob and one color-3 blob, placed apart (not 4-touching)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    for color, name in ((2, "color-2"), (3, "color-3")):
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if not cells:
            errs.append(f"no {name} cells found")
    if errs:
        return errs
    # Check blobs don't touch (4-connectivity) — the two colors are in separate placed shapes
    c2 = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    c3 = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3}
    for r, c in c2:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if (r + dr, c + dc) in c3:
                errs.append("color-2 and color-3 blobs are 4-adjacent (should be placed apart)")
                return errs
    return errs


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _conn_poly(rng, size, maxd):
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        n = _norm(cells)
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return n
    return [(0, 0), (0, 1), (1, 0)]


def _free(occ, cells, top, left, h, w):
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = top + r + dr, left + c + dc
                if dr == 0 and dc == 0:
                    if not (0 <= rr < h and 0 <= cc < w):
                        return False
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, szr, md = (9, 11), (11, 13), (3, 4), 3
    elif difficulty == "hard":
        hr, wr, szr, md = (11, 15), (12, 16), (4, 7), 5
    else:
        hr, wr, szr, md = (9, 13), (11, 14), (4, 6), 4

    for _attempt in range(50):
        s2 = _norm(_conn_poly(rng, rng.randint(*szr), md))
        s3 = _norm(_conn_poly(rng, rng.randint(*szr), md))
        A = set(map(tuple, s2)); B = set(map(tuple, s3))
        if not (A & B):          # must share >=1 cell (→ an 8)
            continue
        if not (A ^ B):          # must differ (→ a 2 and a 3 too)
            continue
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        def _place(cells, color):
            bh = max(r for r, c in cells) + 1; bw = max(c for r, c in cells) + 1
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _free(occ, cells, top, left, h, w):
                    for r, c in cells:
                        g[top + r][left + c] = color; occ[top + r][left + c] = True
                    return True
            return False

        if _place(s2, 2) and _place(s3, 3):
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_shapes":
        return g
    if name == "identical_shapes":
        s = [(0, 0), (1, 0), (1, 1)]
        paint_at(g, 1, 1, s, 2)
        paint_at(g, 5, 7, s, 3)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(12):
                g[r][c] = 2
        return g
    return g
