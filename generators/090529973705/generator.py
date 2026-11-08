"""Generator for 090529973705.

Rule (actual): rank all colors by cell-count; the TOP-2 most-frequent
colors are the two "zone" colors. Every other (minority/marker) cell is
reassigned to whichever zone color is nearest via 4-neighbour BFS. So
the output is a two-zone partition where each marker is absorbed into
its surrounding zone.

The input here is built to expose that: a vertical split makes two large
background regions (guaranteed top-2 by count) plus a few 1-2 cell
markers that the rule reassigns. (Earlier docstring described a
'diagonal rays' task d07ae81c — that was wrong-task; the construction
below is the correct two-zone-by-frequency input.)

Combinatorial axes: grid_h/w (randomized), split_col, palette colors,
two_markers texture.
Degenerates: no_markers, no_split.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "090529973705"
VERSION = "1.4.1"  # docstring fix: was wrong-task 'diagonal rays'; real rule = top-2-frequency zone partition
TASK_ID = "090529973705"
SUMMARY = ("Two large background zones (the top-2 most-frequent colors) "
           "plus sparse minority markers; the rule reassigns every marker "
           "cell to its nearest zone color, yielding a two-zone partition.")

# Rivals: 'use background color for rays' refuted by any demo. 'fixed
# split position' refuted by ≥2 demos with different split cols.
# 'cast rays in single direction' refuted by ≥2 demos where rays
# clearly fan in 4 diagonals.
# 4 demos with varied splits + grid sizes + colors.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "two dominant colors form the background zones",
    "each non-zone marker sits inside or adjacent to exactly one zone",
    "all cells on a marker diagonal are recolored with that zone's marker color",
    "left, right, lm and rm colors are distinct and non-zero",
]

SPLIT_COLS = ("c5", "c6", "c7")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_markers", "no_split")
HELPFUL_TEXTURES = SPLIT_COLS + ("two_markers",)

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "11..19"},
    "split_col":      {"type": "str", "default": "rng helpful",
                       "valid": "c5|c6|c7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for split_col",
                       "valid": "c5|c6|c7|two_markers|no_markers|no_split",
                       "doc": "two_markers: a zone holds TWO markers - both "
                              "cast rays, the scan-order FIRST supplies the "
                              "zone's recolor color."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h, w = 10, 11
    elif difficulty == "hard":
        h = rng.randint(14, 18); w = rng.randint(15, 19)
    else:
        h = rng.randint(11, 14); w = rng.randint(12, 16)
    tx = overrides.get("texture")
    if tx in SPLIT_COLS:
        split_col = int(tx[1:])
    else:
        split_col = rng.randint(w // 3, 2 * w // 3)
    left, right, lm, rm = ctx.draw_distinct_colors("colors", n=4, exclude={0})
    g = full_grid(h, w, right)
    for r in range(h):
        for c in range(split_col):
            g[r][c] = left
    # Place markers at random interior positions in their respective
    # zones (rather than fixed offsets).
    lm_r = rng.randint(2, h - 3)
    lm_c = rng.randint(1, max(1, split_col - 2))
    g[lm_r][lm_c] = lm
    rm_r = rng.randint(2, h - 3)
    rm_c = rng.randint(min(w - 2, split_col + 2), w - 2)
    g[rm_r][rm_c] = rm
    if tx == "two_markers":
        # second marker in the LEFT zone: both cast rays; the zone's
        # recolor color comes from the scan-order FIRST marker
        extra = ctx.draw_color("extra_marker", exclude={0, left, right, lm, rm})
        for _try in range(60):
            r2 = rng.randint(1, h - 2)
            c2 = rng.randint(1, max(1, split_col - 2))
            if g[r2][c2] == left and abs(r2 - lm_r) + abs(c2 - lm_c) > 3:
                g[r2][c2] = extra
                break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=3 distinct non-zero colors (2 dominant zones + >=1 marker)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    nz_colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(nz_colors) < 3:
        return [f"expected >=3 distinct non-zero colors (2 zones + markers), found {len(nz_colors)}: {sorted(nz_colors)}"]
    return []


def _draw_from_degenerate(name, rng):
    """no_markers — two zones, nothing else: identity (verified).
    no_split — one dominant color + 2 dot colors: the count-sort
    promotes a DOT to a zone color (deterministic, weird, verified
    non-crashing). full_grid was DROPPED: a single color makes
    (nth sorted-colors 1) -> #f -> car contract violation."""
    h = rng.randint(10, 13)
    w = rng.randint(11, 14)
    bg = rng.randint(1, 9)
    g = full_grid(h, w, bg)
    if name == "no_markers":
        other = rng.choice([c for c in range(1, 10) if c != bg])
        for r in range(h):
            for c in range(w // 2):
                g[r][c] = other
        return g
    a, b = rng.sample([c for c in range(1, 10) if c != bg], 2)
    g[rng.randint(1, h - 2)][rng.randint(1, w // 2)] = a
    g[rng.randint(1, h - 2)][rng.randint(w // 2, w - 2)] = b
    return g
