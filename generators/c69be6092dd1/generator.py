"""Generator for arc_puzzle_bank_eighth21:H53 — row/col threshold staircase.

Rule (verified from canonical Racket): row 0 holds a per-column threshold
g[0][c]; column 0 holds a per-row threshold g[r][0]. The interior cell (r,c)
(r>=1, c>=1) becomes 8 iff g[r][0] >= c AND g[0][c] >= r — i.e. the intersection
staircase of the two threshold bars. Row 0 and column 0 of the output are blank.

The previous body was a generic "gallery pack" (a different task); it placed
random motifs, so the row-0/col-0 threshold bars were arbitrary. This rewrite
CONSTRUCTS proper threshold vectors on row 0 and column 0.

Axes: grid size, the two threshold vectors.
Degenerates: no_thresholds, all_max, single_col.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c69be6092dd1"
VERSION = "2.1.0"  # WRONG-TASK + distinct 15: gen was a generic 'gallery pack' but the rule reads row-0 as per-column thresholds and col-0 as per-row thresholds and fills the intersection STAIRCASE with 8. Now construct random threshold vectors on row 0 + column 0 (interior blank).
TASK_ID = "c69be6092dd1"
SUMMARY = ("Row 0 holds per-column thresholds and column 0 per-row thresholds; the "
           "rule fills interior cell (r,c) with 8 where both thresholds are met (a "
           "staircase intersection of the two bars).")

INVARIANTS = [
    "row 0 (cols >=1) holds per-column threshold values >=1",
    "column 0 (rows >=1) holds per-row threshold values >=1",
    "the interior (r>=1, c>=1) is background in the input",
]

DEGENERATE_TEXTURES = ("no_thresholds", "all_max", "single_col")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":   {"type": "int", "default": "rng 5..9", "valid": "4..10"},
    "grid_w":   {"type": "int", "default": "rng 5..9", "valid": "4..10"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                    "valid": "default|warm|cool|varied"},
    "density":  {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":  {"type": "str", "default": "alias for palette_kind",
                 "valid": "default|warm|cool|varied|no_thresholds|all_max|single_col"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7); w = ctx.draw_int("grid_w", 5, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 8, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 9); w = ctx.draw_int("grid_w", 6, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # row 0: per-column threshold = how far DOWN the column fills (1..h-1, capped 9)
    for c in range(1, w):
        g[0][c] = rng.randint(1, min(9, h - 1))
    # column 0: per-row threshold = how far RIGHT the row fills (1..w-1, capped 9)
    for r in range(1, h):
        g[r][0] = rng.randint(1, min(9, w - 1))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 6
    g = full_grid(h, w, 0)
    if name == "no_thresholds":
        return g                                  # no bars -> empty output
    if name == "all_max":
        for c in range(1, w):
            g[0][c] = h - 1
        for r in range(1, h):
            g[r][0] = w - 1
        return g
    if name == "single_col":
        g[0][1] = h - 1                           # only one column has a threshold
        for r in range(1, h):
            g[r][0] = 1
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h < 4 or w < 4 or any(len(row) != w for row in grid):
        return ["grid must be rectangular and at least 4x4"]
    if any(grid[0][c] < 1 for c in range(1, w)):
        errs.append("row 0 must carry a positive threshold for every interior column")
    if any(grid[r][0] < 1 for r in range(1, h)):
        errs.append("column 0 must carry a positive threshold for every interior row")
    if any(grid[r][c] != 0 for r in range(1, h) for c in range(1, w)):
        errs.append("input interior must be blank before threshold fill")
    fired = sum(1 for r in range(1, h) for c in range(1, w)
                if grid[r][0] >= c and grid[0][c] >= r)
    if fired < 1:
        errs.append("threshold intersection produces an empty output")
    return errs
