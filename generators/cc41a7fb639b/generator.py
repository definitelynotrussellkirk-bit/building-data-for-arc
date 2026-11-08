"""Generator for arc_additional_puzzles_21_set3:E15.

Rule: for each cell of color 2, set each of its 4 diagonal neighbors
to 6 if currently 0 and in-bounds.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seed_at_corner, seeds_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cc41a7fb639b"
VERSION = "2.1.0"
TASK_ID = "cc41a7fb639b"
SUMMARY = (
    "0-bg grid with several isolated color-2 cells scattered (≥3 "
    "cells), each separated by ≥2 Manhattan from another so their "
    "diagonal-painting regions don't overlap-conflict. Rule: for each "
    "color-2 cell at (r, c), paint the 4 diagonal neighbors at "
    "(r±1, c±1) with color 6 IF in-bounds AND currently 0. Color-2 "
    "cells preserved; non-bg cells already in place are preserved."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥3 cells of color 2",
    "no two 2-cells within Manhattan distance 2 (so diagonals don't conflict)",
]

PALETTE_KINDS = ("default", "sparse", "spread", "edge_safe")
DEGENERATE_TEXTURES = ("no_seeds", "seed_at_corner", "seeds_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 3..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _diag_neighbors(pt, h, w):
    r, c = pt
    out = set()
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            out.add((nr, nc))
    return out


def _seed_can_be_added(placed, pt, h, w):
    r, c = pt
    if r in (0, h - 1) and c in (0, w - 1):
        return False
    cand_diag = _diag_neighbors(pt, h, w)
    for pr, pc in placed:
        if abs(r - pr) + abs(c - pc) <= 2:
            return False
        if cand_diag & _diag_neighbors((pr, pc), h, w):
            return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 5, 6)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 5, 7)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    target = ctx.draw_int("n_seeds", 3, 4)
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if not (r in (0, h - 1) and c in (0, w - 1))]
    for _attempt in range(30):
        rng.shuffle(candidates)
        placed = []
        for r, c in candidates:
            if len(placed) >= target:
                break
            if _seed_can_be_added(placed, (r, c), h, w):
                placed.append((r, c))
        if len(placed) >= target:
            for r, c in placed:
                g[r][c] = 2
            return g
    raise ValueError("could not place isolated non-corner diagonal seeds")


def _draw_from_degenerate(name, rng):
    h, w = 6, 6
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # empty grid — no 2-cells, so the rule paints nothing
        return g
    if name == "seed_at_corner":
        # 2-cell at (0,0) → only 1 of 4 diagonal neighbors is in-bounds
        g[0][0] = 2
        g[h - 1][w - 1] = 2
        return g
    if name == "seeds_touching":
        # adjacent 2-cells → diagonal neighbor of one IS the other (collision)
        g[2][2] = 2; g[2][3] = 2; g[3][3] = 2
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    seeds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if len(seeds) < 3:
        errors.append("expected at least three color-2 seeds")
    for r, c in seeds:
        if r in (0, h - 1) and c in (0, w - 1):
            errors.append("default path placed a degenerate corner seed")
    for i, a in enumerate(seeds):
        for b in seeds[i + 1:]:
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) <= 2:
                errors.append("color-2 seeds are too close")
            if _diag_neighbors(a, h, w) & _diag_neighbors(b, h, w):
                errors.append("two seeds share a diagonal-paint target")
    return errors
