"""Generator for arc_additional_puzzle_bank_volume15:E99.

Rule: two aligned blue markers with even separation get a red midpoint.

Combinatorial axes (8): grid_h, grid_w, palette_kind, orientation,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: single_marker, odd_separation, non_aligned.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "be3a57da2378"
VERSION = "1.3.0"  # rule's `pairs` only yields CONSECUTIVE row-major pairs; an extra marker sorting between the qualifying pair split it -> no hit -> identity. Ensure a consecutive qualifying pair survives; self_check now mirrors the consecutive-pair semantics.
TASK_ID = "be3a57da2378"
SUMMARY = (
    "0-bg grid with ≥2 blue (color-1) markers and optional decoration "
    "cells in other colors (the rule ignores them). Rule: enumerate "
    "all pairs of color-1 markers (in first-found order). For each "
    "pair (a, b), check if they share a row OR column AND their "
    "separation along that axis is EVEN and ≥2. The FIRST qualifying "
    "pair gets its midpoint cell set to color 2. All other cells "
    "preserved as-is."
)

# Rivals: 'output is input' refuted by demos with ≥1 qualifying pair.
# 'mark every aligned pair midpoint' refuted by demos with multiple
# pairs where only the first gets a midpoint. 'use color 1 for the
# midpoint' refuted by demos showing color 2. 'connect markers with
# a line, not just midpoint' refuted by demos showing only midpoint.
# 'use odd-separation pairs too' refuted by demos with odd pair
# staying inert. 'midpoint at average of all markers' refuted by
# demos with the midpoint at the actual pair midpoint. 3 demos with
# ≥2 markers and decoration cells pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 color-1 markers",
    "AT LEAST ONE pair of markers is row- or col-aligned with even ≥2 separation",
    "0..3 decoration cells in colors NOT 1 and NOT 2 (so the rule's output color 2 is unambiguous)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_marker", "odd_separation", "non_aligned")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..13", "valid": "3..20"},
    "grid_w":         {"type": "int", "default": "rng 7..13", "valid": "3..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "orientation":    {"type": "str", "default": "rng h|v", "valid": "h|v"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "row_or_col_aligned",
                       "valid": "row_or_col_aligned"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        n_extra_markers, n_decor = 0, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        n_extra_markers, n_decor = 2, 3
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        n_extra_markers, n_decor = 1, 2
    rng = ctx.draw_rng("placement")

    # The canonical rule's `pairs` enumerates only CONSECUTIVE pairs in row-major
    # (find-color) order, so the qualifying pair must remain ADJACENT in that order —
    # an extra marker sorting between them splits the pair and the rule fires nothing
    # (output == input). Retry until a consecutive qualifying pair survives.
    for _attempt in range(60):
        g = full_grid(h, w, 0)
        if rng.choice([False, True]):
            r = rng.randint(0, h - 1)
            c1 = rng.randint(0, w - 3)
            max_step = (w - 1 - c1) // 2
            c2 = c1 + 2 * rng.randint(1, max_step)
            g[r][c1] = 1; g[r][c2] = 1
        else:
            c = rng.randint(0, w - 1)
            r1 = rng.randint(0, h - 3)
            max_step = (h - 1 - r1) // 2
            r2 = r1 + 2 * rng.randint(1, max_step)
            g[r1][c] = 1; g[r2][c] = 1
        for _ in range(n_extra_markers):
            for _ in range(30):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] == 0:
                    g[r][c] = 1
                    break
        for _ in range(n_decor):
            for _ in range(30):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] == 0:
                    g[r][c] = rng.choice([3, 4, 5, 6, 7, 8, 9])
                    break
        if _has_consecutive_qualifying(g):
            return g
    # Fallback: just the qualifying pair (guaranteed consecutive, no splitters).
    g = full_grid(h, w, 0)
    r = rng.randint(0, h - 1); c1 = rng.randint(0, w - 3)
    c2 = c1 + 2 * rng.randint(1, max(1, (w - 1 - c1) // 2))
    g[r][c1] = 1; g[r][c2] = 1
    return g


def _has_consecutive_qualifying(grid):
    """Mirror the rule: scan color-1 points in row-major (find-color) order and test
    only CONSECUTIVE pairs for row/col alignment with even separation >= 2."""
    pts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    for (r1, c1), (r2, c2) in zip(pts, pts[1:]):
        if r1 == r2 and abs(c1 - c2) >= 2 and abs(c1 - c2) % 2 == 0:
            return True
        if c1 == c2 and abs(r1 - r2) >= 2 and abs(r1 - r2) % 2 == 0:
            return True
    return False


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "single_marker":
        # one blue → no second marker, no midpoint to compute
        g[3][4] = 1
        return g
    if name == "odd_separation":
        # markers separated by odd cells → no integer midpoint, rule undefined
        g[3][1] = 1; g[3][6] = 1  # separation 5 (odd)
        return g
    if name == "non_aligned":
        # markers not on same row/col → no axis defined
        g[2][2] = 1
        g[5][6] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h, w = len(grid), len(grid[0])
    ones = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    if len(ones) < 2:
        msgs.append("expected at least two color-1 markers")
    if any(v == 2 for row in grid for v in row):
        msgs.append("input should not pre-contain output color 2")
    decor = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 1, 2)]
    if len(decor) > 3:
        msgs.append("expected at most three decoration cells")
    # The rule only tests CONSECUTIVE row-major pairs, so the qualifying pair must be
    # adjacent in that order (a marker sorting between them would split it -> no hit).
    if not _has_consecutive_qualifying(grid):
        msgs.append("no CONSECUTIVE row/col-aligned even-separation marker pair "
                    "(a marker sorts between the pair in row-major order)")
    return msgs
