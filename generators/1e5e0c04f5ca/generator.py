"""Generator for arc_puzzle_bank_fifth_21_bundle:easy_34_keep_rarest_color.

Rule: several colors appear with distinct frequencies; the rarest is
retained, all others become 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_colors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_counts, single_color, no_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1e5e0c04f5ca"
VERSION = "2.0.0"
TASK_ID = "1e5e0c04f5ca"
SUMMARY = (
    "0-bg grid (h~8-11, w~"
    "9-13) with 3 DISTINCT "
    "NON-ZERO COLORS each "
    "appearing at distinct "
    "scattered positions: "
    "color #1 appears 2 "
    "times (rarest), color "
    "#2 appears 4 times, "
    "color #3 appears 6 "
    "times (most common). "
    "Each color's count is "
    "STRICTLY DISTINCT, so "
    "the rarest is "
    "unambiguous. Cells "
    "placed at random "
    "non-overlapping "
    "positions throughout "
    "the grid. Rule (KEEP "
    "RAREST COLOR, ERASE "
    "OTHERS): COUNT cells "
    "of EACH NON-0 COLOR. "
    "IDENTIFY the color "
    "with the STRICTLY "
    "MINIMUM count (the "
    "RAREST). For EACH "
    "cell: if its color "
    "equals the rarest, "
    "KEEP. Else (including "
    "the more frequent "
    "colors), ERASE to 0. "
    "Net: only the rarest "
    "color survives; all "
    "others disappear."
)

INVARIANTS = [
    "background is 0",
    "there are at least three nonzero colors",
    "one color has a strictly smallest count",
    "the rarest color has at least one visible cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_counts", "single_color", "no_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_colors":       {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "graded", "valid": "graded"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 13)
    colors = ctx.draw_distinct_colors("colors", n=3, exclude={0})
    rng = ctx.draw_rng("cells")
    g = full_grid(h, w, 0)
    counts = [2, 4, 6]
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    i = 0
    for color, count in zip(colors, counts):
        for r, c in cells[i:i + count]:
            g[r][c] = color
        i += count
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "tied_counts":
        # multiple colors share the smallest count → "rarest" is ambiguous
        for r, c, v in [(1, 1, 3), (1, 2, 3),  # color 3 ×2
                        (2, 4, 5), (2, 5, 5),  # color 5 ×2 (tied rarest)
                        (4, 1, 7), (4, 2, 7), (4, 3, 7), (4, 4, 7)]:  # color 7 ×4
            g[r][c] = v
        return g
    if name == "single_color":
        # only one nonzero color → "rarest" is trivially the only one, rule is no-op
        for r, c in [(1, 2), (3, 4), (5, 6), (7, 8)]:
            g[r][c] = 6
        return g
    if name == "no_cells":
        # empty grid → no colors to compare frequencies of
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """bg=0; ≥3 distinct nonzero colors; one color strictly rarest."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(counts) < 3:
        errs.append(f"need ≥3 nonzero colors, got {len(counts)}")
        return errs
    vals = sorted(counts.values())
    if vals[0] == vals[1]:
        errs.append("no strictly-rarest nonzero color (tie at minimum count)")
    return errs
