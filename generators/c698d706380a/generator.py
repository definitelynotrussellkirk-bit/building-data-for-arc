"""Generator for arc_puzzle_bank_twentyfirst21:M142 — legend key -> stamp queries.

Rule (verified from canonical Racket): row 0 holds KEY colors at some columns; the
two cells directly below each key (rows 1-2 of that column) form that key's 2x1
STAMP. In the body (rows >= 3), every cell holding a key color is replaced by that
key's stamp pasted at the cell's position. Output starts blank; only stamps appear.

The previous body was a generic "6 panels / find pair" layout (a different task) with
no row-0 legend and no body query cells, so the lookup produced nothing. This rewrite
CONSTRUCTS the legend (keys + 2x1 stamps) plus body query cells.

Axes: grid size, key count, stamp patterns, query count/positions.
Degenerates: no_legend, no_queries, single_key.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c698d706380a"
VERSION = "2.1.0"  # WRONG-TASK: gen was a generic '6 panels' layout; the rule reads a row-0 legend (key + 2x1 stamp below each) and replaces every body key-cell (rows>=3) with its stamp. Now construct the legend + body query cells.
TASK_ID = "c698d706380a"
SUMMARY = ("Row 0 holds key colors; the 2 cells below each form its 2x1 stamp. Body "
           "cells (rows>=3) holding a key color are replaced by that key's stamp.")

INVARIANTS = [
    "row 0 holds >=1 key color, each with a 2x1 stamp directly below (rows 1-2)",
    "body region (rows >= 3) holds query cells in key colors",
    "output is blank except where stamps are pasted at query positions",
]

DEGENERATE_TEXTURES = ("no_legend", "no_queries", "single_key")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":   {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":   {"type": "int", "default": "rng 7..12", "valid": "6..16"},
    "n_keys":   {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "n_query":  {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                    "valid": "default|warm|cool|varied"},
    "density":  {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":  {"type": "str", "default": "alias for palette_kind",
                 "valid": "default|warm|cool|varied|no_legend|no_queries|single_key"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 7, 9)
        n_keys = ctx.draw_int("n_keys", 2, 2); n_q = ctx.draw_int("n_query", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 10, 16)
        n_keys = ctx.draw_int("n_keys", 3, 5); n_q = ctx.draw_int("n_query", 4, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 12); w = ctx.draw_int("grid_w", 8, 12)
        n_keys = ctx.draw_int("n_keys", 2, 4); n_q = ctx.draw_int("n_query", 3, 6)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_keys = min(n_keys, max(1, w - 1))
    # Canonical rule slices each key stamp as (subgrid g 1 c 2 (+ c 1));
    # a key in the final column makes (+ c 1) out of bounds in Racket.
    key_cols = sorted(rng.sample(range(w - 1), n_keys))
    keys = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_keys)
    stamp_palette = [0] + [c for c in range(1, 10)]
    for kc, key in zip(key_cols, keys):
        g[0][kc] = key
        # 2x1 stamp below the key (rows 1-2); >=1 nonzero cell so it's visible
        s1 = rng.choice([key, key, rng.choice(stamp_palette)])
        s2 = rng.choice([key, 0, rng.choice(stamp_palette)])
        if s1 == 0 and s2 == 0:
            s1 = key
        g[1][kc] = s1; g[2][kc] = s2
    # body query cells (rows 3..h-2 so the 2x1 stamp fits) in key colors
    body = [(r, c) for r in range(3, h - 1) for c in range(w - 1)]
    rng.shuffle(body)
    placed = 0
    for (r, c) in body:
        if placed >= n_q:
            break
        if g[r][c] == 0 and g[r + 1][c] == 0:        # leave room for the 2x1 stamp readout
            g[r][c] = rng.choice(keys)
            placed += 1
    if placed == 0 and h - 1 > 3:
        g[3][0] = keys[0]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    key_cols = [c for c in range(w) if grid[0][c] != 0]
    if not key_cols:
        errs.append("expected at least one nonzero key in row 0")
    if any(c >= w - 1 for c in key_cols):
        errs.append("row-0 key in final column makes canonical stamp subgrid out of bounds")
    keys = {grid[0][c] for c in key_cols}
    for c in key_cols:
        if h < 3 or grid[1][c] == 0 and grid[2][c] == 0:
            errs.append(f"key at col {c} has blank 2x1 stamp")
            break
    body_queries = [(r, c) for r in range(3, max(3, h - 1)) for c in range(max(0, w - 1))
                    if grid[r][c] in keys]
    if not body_queries:
        errs.append("expected at least one body query cell in a key color within canonical scan range")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 0)
    # legend: key 2 (stamp [2,0]) at col0, key 3 (stamp [3,3]) at col3
    g[0][0] = 2; g[1][0] = 2; g[2][0] = 0
    g[0][3] = 3; g[1][3] = 3; g[2][3] = 3
    if name == "no_legend":
        g2 = full_grid(8, 8, 0); g2[4][2] = 2; g2[4][5] = 3
        return g2
    if name == "no_queries":
        return g                                      # legend only
    # single_key
    g3 = full_grid(8, 8, 0)
    g3[0][1] = 4; g3[1][1] = 4; g3[2][1] = 0
    g3[4][3] = 4; g3[5][3] = 4
    return g3
