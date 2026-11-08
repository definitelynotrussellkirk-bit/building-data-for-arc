"""Generator for arc_puzzle_bank_21_set16_s:S16_M1 — legend selects pair.

Rule: top-left (0,0) is a legend marker (5/6/other) which maps to a
target color (2/3/4). The two cells of that target color then get a
span drawn between them in 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_target_pair, axis_unaligned.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d5869f5c395e"
VERSION = "2.1.0"  # QUALITY: distractor pairs on harder difficulty (was always 3 pairs); AXES literals
TASK_ID = "d5869f5c395e"
SUMMARY = (
    "0-bg grid (h ∈ 9-12, w ∈ 10-14) "
    "with: (a) ONE LEGEND MARKER at "
    "FIXED position (0, 0) — value ∈ "
    "{4, 5, 6} (legend codes that map "
    "to a target color, e.g., 5→2, "
    "6→3, 4→4); (b) THREE COLOR-PAIRS "
    "scattered — for EACH color ∈ "
    "{2, 3, 4}: place 2 cells of that "
    "color at axis-aligned endpoints "
    "(horizontal or vertical, ≥3 "
    "cells apart, both cells initially "
    "0). All 3 pairs placed via "
    "_try_pair with non-overlap check. "
    "Rule (READ THE LEGEND AT (0, 0), "
    "MAP TO A TARGET COLOR, FIND THE "
    "PAIR OF THAT COLOR, DRAW A "
    "COLOR-8 SPAN BETWEEN THE TWO "
    "CELLS): READ the (0, 0) LEGEND. "
    "MAP legend → target color (per "
    "demos: 5→2, 6→3, 4→4, etc.). "
    "FIND the two cells of the "
    "TARGET color (axis-aligned). "
    "PAINT every cell on the line "
    "segment between them "
    "(inclusive of endpoints) with "
    "COLOR 8 (cyan). Other pairs "
    "stay as-is. The legend cell "
    "stays. Net: legend selects "
    "which color-pair to connect; "
    "that pair becomes a cyan line."
)

INVARIANTS = [
    "background is 0",
    "(0,0) holds a legend marker ∈ {5, 6, 4}",
    "each candidate color (2, 3, 4) appears exactly twice (so any pair is well-formed)",
    "the legend's selected target pair has 2 cells aligned horiz or vert",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_target_pair", "axis_unaligned")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "legend_corner_pairs_scattered",
                       "valid": "legend_corner_pairs_scattered"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_legend|no_target_pair|axis_unaligned"},
}


def _try_pair(g, color, rng):
    h, w = len(g), len(g[0])
    for _ in range(40):
        if rng.random() < 0.5:
            r = rng.randint(1, h - 1)
            c1 = rng.randint(1, w - 4)
            c2 = rng.randint(c1 + 3, w - 1)
            if g[r][c1] == 0 and g[r][c2] == 0:
                g[r][c1] = color
                g[r][c2] = color
                return True
        else:
            c = rng.randint(1, w - 1)
            r1 = rng.randint(1, h - 4)
            r2 = rng.randint(r1 + 3, h - 1)
            if g[r1][c] == 0 and g[r2][c] == 0:
                g[r1][c] = color
                g[r2][c] = color
                return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 14, 16)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 14)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    legend = rng.choice([5, 6, 4])
    g[0][0] = legend
    for color in (2, 3, 4):          # the 3 selectable target pairs (rule connects one)
        _try_pair(g, color, rng)
    # distractor pairs in non-target colors add clutter on harder difficulty;
    # the rule only connects the legend's target, so the output is unchanged.
    n_distract = {"easy": 0, "hard": rng.randint(2, 3)}.get(difficulty, rng.randint(0, 1))
    for color in rng.sample([1, 7, 9], min(n_distract, 3)):
        _try_pair(g, color, rng)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # Pairs but (0,0) is empty — rule's legend lookup fails.
        g[2][2] = 2; g[2][8] = 2
        g[5][3] = 3; g[5][9] = 3
        return g
    if name == "no_target_pair":
        # Legend selects a target color but no pair of that color
        # exists — rule's "find pair" finds nothing.
        g[0][0] = 5  # selector for color 2 (say)
        g[3][3] = 4; g[3][7] = 4
        g[6][2] = 3; g[6][9] = 3
        return g
    if name == "axis_unaligned":
        # Target pair exists but the two cells are not in the same
        # row or column — rule's span between them is undefined.
        g[0][0] = 5
        g[3][3] = 2; g[6][8] = 2
        return g
    return g
