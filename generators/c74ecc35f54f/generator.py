"""Generator for arc_additional_puzzles_21_set11_bundle:E75.

Rule: count all nonzero cells, then output a row that repeats the first
seen color that many times.

Combinatorial axes (8): grid_h/w, palette_kind, num_nonzero,
palette_size, position_bias, n_distinct_colors, first_color, texture.
Degenerates: only_one_nonzero, count_exceeds_width, monocolor_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c74ecc35f54f"
VERSION = "2.1.0"  # add self_check. all_background_output flag is a FALSE POSITIVE: this rule's OUTPUT is by definition a 1xn SOLID bar of the first-scanned colour (the canonical task outputs single-colour 1xn rows too). Output diversity (width n x colour) is high (distinct_out=24); generate() unchanged.
TASK_ID = "c74ecc35f54f"
SUMMARY = (
    "0-bg grid (h~5-8, w~6-9) with EXACTLY FIVE "
    "NON-ZERO CELLS placed at fixed positions: "
    "(0, 1), (1, w-2), (h//2, 2), (h-2, w//2), "
    "(h-1, w-1). Colors are drawn from a palette of "
    "3 distinct non-0 values C0, C1, C2 from {1..9} "
    "and assigned: position (0, 1) = C0 (the FIRST "
    "color in row-major scan order), positions "
    "(1, w-2) and (h-2, w//2) = C1, positions "
    "(h//2, 2) and (h-1, w-1) = C2. So C0 appears "
    "once and C1, C2 each appear twice — 5 cells "
    "total. Rule (COUNT ALL NONZERO CELLS, OUTPUT A "
    "ROW REPEATING THE FIRST-SEEN COLOR THAT MANY "
    "TIMES): COUNT n = total number of non-zero "
    "cells in the input. SCAN row-major to find the "
    "FIRST non-zero cell's color C0. PRODUCE a "
    "1-row × n output where every cell holds COLOR "
    "C0. Net: input has scattered colors; output is "
    "a horizontal bar of length n=count, all in "
    "the first-scanned color. Flagged intrinsic-low "
    "(uniq_out=9): output is one of 9 possible "
    "{color × length=5} bars."
)

INVARIANTS = [
    "there are at least four nonzero cells",
    "the first nonzero value appears before any distractor colors",
]

PALETTE_KINDS = ("default", "scattered", "clustered", "rainbow")
DEGENERATE_TEXTURES = ("only_one_nonzero", "count_exceeds_width", "monocolor_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "4..11"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "num_nonzero":    {"type": "int", "default": "5", "valid": "4..9"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "first_color":    {"type": "str", "default": "rng",
                       "valid": "any nonzero"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7); w = ctx.draw_int("grid_w", 6, 8); n_lo, n_hi = 2, 8
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 9, 12); n_lo, n_hi = 6, 22
    else:
        h = ctx.draw_int("grid_h", 6, 9); w = ctx.draw_int("grid_w", 7, 11); n_lo, n_hi = 3, 15
    rng = ctx.draw_rng("layout")
    # output = 1 x n bar of the FIRST (row-major) nonzero colour, where n = nonzero
    # count. Vary BOTH n (output width, was fixed at 5) and the colours -> output
    # width 1..n + colour both vary. n capped at 28 (ARC width) and grid capacity.
    n = ctx.draw_int("num_nonzero", n_lo, min(n_hi, 28, (h * w) // 2))
    n = max(2, n)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], rng.randint(2, 4))
    g = full_grid(h, w, 0)
    positions = rng.sample([(r, c) for r in range(h) for c in range(w)], n)
    for (r, c) in positions:
        g[r][c] = rng.choice(palette)
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """At least 2 non-zero cells, so the output 1xn bar (n = nonzero count) is a
    visible multi-cell row. (The single-colour bar OUTPUT is intrinsic to this
    rule, not a defect -- the all_background_output lint flag is a false
    positive.)"""
    nz = sum(1 for row in grid for v in row if v != 0)
    if nz < 2:
        return [f"only {nz} non-zero cell(s) -> degenerate output bar"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "only_one_nonzero":
        g[2][3] = 5
        return g
    if name == "count_exceeds_width":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3 if (r + c) % 2 == 0 else 0
        g[0][0] = 7
        return g
    if name == "monocolor_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
