"""Generator for e21d9049.

Rule: center row + center col with colored seq; rule cycles each
across entire row/col.

Combinatorial axes: grid_h/w, palette_kind, anchor_corner, n_h, n_v.
Degenerates: no_rows, no_cols, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "882c01c42710"
VERSION = "2.2.0"
TASK_ID = "882c01c42710"
SUMMARY = (
    "0-bg grid (h, w~12-16) with: (a) ONE HORIZONTAL "
    "SEED SEQUENCE at some center-ish row cr — 3-4 "
    "consecutive cells (starting at random col h_start) "
    "painted in distinct colors from a 4-color palette "
    "(palette colors used in order); (b) ONE VERTICAL "
    "SEED SEQUENCE at some center-ish col cc — 3-4 "
    "consecutive cells (starting at random row "
    "v_start) painted in the same palette order. Both "
    "sequences lie on the SAME center row/col axes. "
    "Rule: identify the row with the most non-bg "
    "cells (the H-axis center row) and the col with "
    "the most (the V-axis center col). For each axis, "
    "CYCLE the seed sequence across the ENTIRE "
    "row/col — extending the palette pattern (in "
    "order) to all cells of that row/col on both "
    "sides of the seeds. Net: a small seed sequence "
    "on each axis becomes a full periodic stripe "
    "spanning the row and column."
)

INVARIANTS = [
    "background is 0",
    "exactly one row has the most non-bg cells",
    "exactly one col has the most non-bg cells",
    "all non-bg cells lie on center_row OR center_col",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_rows", "no_cols", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_PALETTE_OPTIONS = {
    "warm": ((2, 4, 7, 1), (4, 2, 7, 3), (7, 4, 2, 1)),
    "cool": ((1, 5, 8, 9), (5, 1, 9, 8), (8, 5, 1, 9)),
    "primary": ((1, 2, 3, 4), (2, 3, 4, 1), (3, 4, 1, 2)),
}

AXES = {
    "grid_h":        {"type": "int", "default": "difficulty-aware rng 10..20", "valid": "10..20"},
    "grid_w":        {"type": "int", "default": "difficulty-aware rng 10..20", "valid": "10..20"},
    "palette_kind":  {"type": "str", "default": "rng helpful",
                      "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner": {"type": "bool", "default": "false|true",
                      "valid": "true|false"},
    "n_h":           {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "n_v":           {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "texture":       {"type": "str", "default": "alias for palette_kind",
                      "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}



def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = dict(overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        rng = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                      task_id=TASK_ID, difficulty=difficulty,
                      overrides=overrides).draw_rng("placement")
        return _draw_from_degenerate(texture, rng)
    if texture in HELPFUL_TEXTURES and "palette_kind" not in overrides:
        overrides["palette_kind"] = texture

    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    h = ctx.draw_int_diff("grid_h", 10, 20)
    w = ctx.draw_int_diff("grid_w", 10, 20)
    n_h = ctx.draw_int("n_h", 3, 5)
    n_v = ctx.draw_int("n_v", 3, 5)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    anchor_corner = ctx.draw_choice("anchor_corner", (False, True))
    if palette_kind == "broad":
        palette = ctx.draw_distinct_colors("palette", n=4, exclude={0})
    else:
        palette = ctx.draw_choice("palette", _PALETTE_OPTIONS[palette_kind])

    g = full_grid(h, w, 0)
    cr = rng.randint(h // 3, 2 * h // 3)
    cc = rng.randint(w // 3, 2 * w // 3)
    h_start = _choose_segment_start(rng, 2, w - n_h - 2, n_h,
                                    avoid=cc, anchor=anchor_corner)
    for i in range(n_h):
        g[cr][h_start + i] = palette[i % len(palette)]
    v_start = _choose_segment_start(rng, 2, h - n_v - 2, n_v,
                                    avoid=cr, anchor=anchor_corner)
    for i in range(n_v):
        g[v_start + i][cc] = palette[i % len(palette)]
    return g


def _choose_segment_start(rng, lo, hi, length, *, avoid, anchor=False):
    if hi < lo:
        raise ValueError("grid is too small for requested seed sequence")
    candidates = [s for s in range(lo, hi + 1) if not (s <= avoid < s + length)]
    if not candidates:
        candidates = list(range(lo, hi + 1))
    return candidates[0] if anchor else rng.choice(candidates)



def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    h, w = len(grid), len(grid[0])
    row_counts = [sum(1 for v in row if v != 0) for row in grid]
    col_counts = [sum(1 for r in range(h) if grid[r][c] != 0) for c in range(w)]
    rows = [i for i, x in enumerate(row_counts) if x == max(row_counts)]
    cols = [i for i, x in enumerate(col_counts) if x == max(col_counts)]
    if len(rows) != 1:
        errs.append(f"expected unique seed row, found {rows}")
    if len(cols) != 1:
        errs.append(f"expected unique seed col, found {cols}")
    if len(rows) == 1 and len(cols) == 1:
        cr, cc = rows[0], cols[0]
        off_axis = [(r, c) for r in range(h) for c in range(w)
                    if grid[r][c] != 0 and r != cr and c != cc]
        if off_axis:
            errs.append(f"non-bg cells off selected row/col: {off_axis[:3]}")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_rows":
        for r in range(2, 8):
            g[r][6] = 2
        return g
    if name == "no_cols":
        for c in range(2, 8):
            g[6][c] = 2
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 2
        return g
    return g
