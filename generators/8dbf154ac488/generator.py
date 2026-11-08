"""Generator for ARC task 794b24be.

Rule: count the color-1 (blue) cells, n. Output a 3x3 grid where the first
min(n,4) positions of a fixed fill order [(0,0),(0,1),(0,2),(1,1)] are 2,
the rest 0 -- a small count display.

This generator scatters n blue cells (plus optional ignored decoy colors)
on a grid of varying size.

Combinatorial axes: the blue count, the blue/decoy positions, decoy
colors, and grid size.
Degenerates: zero_ones, dense_ones, decoy_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8dbf154ac488"
VERSION = "2.2.0"  # all_background fix: n=0 blue cells -> an all-0 3x3 output, but the canonical task never shows the empty count display (its outputs all have >=2 twos). Force blue_count>=1 so the output always shows a count. distinct_out drops 5->4 (the lost output was the degenerate empty grid); the <=5 ceiling is INTRINSIC (output is a fixed 3x3 count display), so DEGENERATE status is unavoidable.
TASK_ID = "8dbf154ac488"
SUMMARY = (
    "0-bg grid (size varies) with n scattered blue(1) cells plus optional "
    "ignored decoy-color cells. Rule: output a 3x3 count display -- the "
    "first min(n,4) positions of a fixed T-order are colored 2. The blue "
    "count, blue/decoy positions, decoy colors and grid size vary freely "
    "(was a fixed setup, ~23 distinct). Output is a 3x3 count display, so "
    "distinct OUTPUTS are bounded (~5: n=0..4+); distinct INPUTS are large."
)

INVARIANTS = [
    "the output encodes min(blue-count, 4) in a fixed 3x3 fill order",
    "decoy colors (not 1) are ignored by the count",
    "the output is 3x3 regardless of input size",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("zero_ones", "dense_ones", "decoy_only")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "5..14"},
    "blue_count":     {"type": "int", "default": "varies", "valid": "1..6"},
    "n_decoys":       {"type": "int", "default": "varies", "valid": "0..4"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|zero_ones|dense_ones|decoy_only"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    # output = f(min(blue_count, 4)); blue_count>=1 so the output always shows a
    # count (n=0 gives an off-distribution all-0 display the canonical never has).
    if difficulty == "easy":
        sr, br, dr = (5, 8), (1, 3), (0, 1)
    elif difficulty == "hard":
        sr, br, dr = (10, 14), (1, 6), (2, 4)
    else:
        sr, br, dr = (7, 11), (1, 5), (0, 3)

    h = rng.randint(*sr); w = rng.randint(*sr)
    n_blue = rng.randint(*br)
    n_decoy = rng.randint(*dr)
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    if n_blue + n_decoy > len(cells):
        n_blue = min(n_blue, len(cells)); n_decoy = 0

    g = full_grid(h, w, 0)
    for (r, c) in cells[:n_blue]:
        g[r][c] = 1
    for (r, c) in cells[n_blue:n_blue + n_decoy]:
        g[r][c] = rng.choice([3, 4, 5, 6, 7, 8, 9])
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """At least one blue(1) cell, so the 3x3 count display is non-empty (n=0
    yields an off-distribution all-0 output). The <=5 distinct-output ceiling is
    intrinsic to this fixed 3x3 count-display rule."""
    n_blue = sum(1 for row in grid for v in row if v == 1)
    if n_blue < 1:
        return ["no blue(1) cell -> empty 3x3 count display (off-distribution)"]
    return []


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "zero_ones":
        g[3][3] = 5
        return g
    if name == "dense_ones":
        for r in range(7):
            for c in range(7):
                g[r][c] = 1
        return g
    if name == "decoy_only":
        g[1][1] = 3; g[2][2] = 4
        return g
    g[1][1] = 1; g[2][3] = 1
    return g
