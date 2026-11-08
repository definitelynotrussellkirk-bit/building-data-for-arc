"""Generator for puzzle 37ce87bb.

Rule: bg=7. Two vertical bars at the bottom: one of color 8, one of 2.
Compute |height_8 - height_2| = h_diff. Place 5-cells in column
(last_bar_col + 2), spanning the bottom h_diff rows.

Combinatorial axes (8): grid_h/w, col_8_position, col_2_position,
bar_h_8, bar_h_2, bg_color, anchor_corner, asymmetry_force.
Degenerates: equal_heights, no_8_bar, single_bar.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b34d330a5426"
VERSION = "2.1.1"  # guard left_first col_2 hi (easy w=6 inverted randint(3, w-4))
TASK_ID = "b34d330a5426"
SUMMARY = (
    "Grid (h~6-10, w~7-12) with bg = 7 (orange). At the BOTTOM "
    "there are exactly TWO vertical BARS: one in col col_8 of "
    "color 8 (cyan), one in col col_2 of color 2 (red). Each "
    "bar's height = how many cells from the bottom up are "
    "non-7 in that column. Bars have DIFFERENT heights. (col_2 "
    "+ 2) must be in-bounds. Rule: scan bottom row to find "
    "bar columns. Compute height_8 and height_2 by counting "
    "non-7 cells in each bar's column. gray_h = |height_8 - "
    "height_2|. new_col = (rightmost bar col) + 2. Paint a "
    "color-5 (gray) bar in column new_col, occupying the "
    "bottom gray_h rows. All other cells preserved."
)

# Rivals: '5-bar height = sum of bars' or 'max of bars' refuted by ≥2
# demos with different (h_8, h_2) where |h_8 - h_2| is observably
# distinct from sum/max. 'always make 5-bar height N' refuted by ≥2
# demos with different |diff|. 'use a different color for the new bar'
# refuted by any demo (always 5). 'place the new bar in a fixed
# column' refuted by ≥2 demos with last_bar_col varied.
# 4 demos to span the |diff| arithmetic + bar-position variation.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "bg = 7",
    "exactly one column with bottom-cell = 8 (8-bar)",
    "exactly one column with bottom-cell = 2 (2-bar)",
    "8-bar height != 2-bar height",
    "(2-bar col + 2) is in-bounds",
]

POSITION_BIASES = ("close", "far", "left_first", "right_first", "centered")
DEGENERATE_TEXTURES = ("equal_heights", "no_8_bar", "single_bar")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "6..16"},
    "col_8":          {"type": "int", "default": "rng 1..3", "valid": "0..w-5"},
    "col_2":          {"type": "int", "default": "rng col_8+2..w-4",
                       "valid": "col_8+2..w-3"},
    "bar_h_8":        {"type": "int", "default": "rng 2..h-1",
                       "valid": "1..h-1"},
    "bar_h_2":        {"type": "int", "default": "rng 2..h-1 (≠bar_h_8)",
                       "valid": "1..h-1"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "close|far|left_first|right_first|centered"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "close|far|left_first|right_first|centered|equal_heights|no_8_bar|single_bar"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=7; exactly 1 col with bottom-cell=8 and 1 col with bottom-cell=2;
    those two bar heights are strictly different."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Find bar columns by their bottom cell
    col_8s = [c for c in range(w) if grid[h - 1][c] == 8]
    col_2s = [c for c in range(w) if grid[h - 1][c] == 2]
    if len(col_8s) != 1:
        errs.append(f"expected exactly 1 col with bottom-cell=8; found {col_8s}")
    if len(col_2s) != 1:
        errs.append(f"expected exactly 1 col with bottom-cell=2; found {col_2s}")
    if len(col_8s) == 1 and len(col_2s) == 1:
        c8, c2 = col_8s[0], col_2s[0]
        h8 = sum(1 for r in range(h) if grid[r][c8] == 8)
        h2 = sum(1 for r in range(h) if grid[r][c2] == 2)
        if h8 == h2:
            errs.append(f"bar heights must differ; both are {h8}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 5, 7
    elif difficulty == "hard":
        h_lo, h_hi = 10, 14
    else:
        h_lo, h_hi = 6, 10
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo + 1, h_hi + 2)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    g = full_grid(h, w, 7)
    col_8, col_2 = _pick_positions(bias, w, rng)
    if "col_8" in overrides:
        col_8 = int(overrides["col_8"])
    if "col_2" in overrides:
        col_2 = int(overrides["col_2"])
    col_8 = max(0, min(w - 5, col_8))
    col_2 = max(col_8 + 2, min(w - 3, col_2))
    bar_h_8 = int(overrides.get("bar_h_8",
                                ctx.draw_int("bar_h_8", 2, max(2, h - 1))))
    bar_h_2 = int(overrides.get("bar_h_2",
                                ctx.draw_int("bar_h_2", 2, max(2, h - 1))))
    bar_h_8 = max(1, min(h - 1, bar_h_8))
    bar_h_2 = max(1, min(h - 1, bar_h_2))
    while bar_h_2 == bar_h_8:
        bar_h_2 = max(1, min(h - 1, bar_h_2 + 1 if bar_h_2 < h - 1 else bar_h_2 - 1))
    for r in range(h - bar_h_8, h):
        g[r][col_8] = 8
    for r in range(h - bar_h_2, h):
        g[r][col_2] = 2
    return g


def _pick_positions(bias, w, rng):
    if bias == "close":
        col_8 = rng.randint(1, max(1, w - 6))
        col_2 = col_8 + 2
        return col_8, col_2
    if bias == "far":
        col_8 = 1
        col_2 = w - 4
        return col_8, col_2
    if bias == "left_first":
        col_8 = 1
        # max() guard like the sibling branches: the easy band allows w=6
        # (w = randint(6,9)), where w-4 = 2 < 3 and the un-guarded randint(3, 2)
        # threw randrange(3,3). Flooring the hi at 3 gives col_2=3 (=w-3 at w=6);
        # the downstream `col_2 = max(col_8+2, min(w-3, col_2))` clamp keeps it
        # in-bounds and (col_2+2)=5=w-1 still fits. Wider grids keep w-4, so
        # every non-w=6 seed stays byte-identical.
        col_2 = rng.randint(3, max(3, w - 4))
        return col_8, col_2
    if bias == "right_first":
        col_8 = rng.randint(1, max(1, w - 6))
        col_2 = w - 4
        return col_8, col_2
    if bias == "centered":
        mid = w // 2
        return max(1, mid - 2), min(w - 4, mid + 1)
    col_8 = rng.randint(1, max(1, w - 6))
    col_2 = rng.randint(col_8 + 2, max(col_8 + 2, w - 4))
    return col_8, col_2


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 7)
    if name == "equal_heights":
        # Equal heights → no 5-bar in output
        col_8 = 1; col_2 = w - 4
        bar_h = h // 2
        for r in range(h - bar_h, h):
            g[r][col_8] = 8
            g[r][col_2] = 2
        return g
    if name == "no_8_bar":
        # Only the 2-bar → rule has no 8 to compare
        col_2 = 2
        for r in range(h - 3, h):
            g[r][col_2] = 2
        return g
    if name == "single_bar":
        # Only the 8-bar
        col_8 = 1
        for r in range(h - 3, h):
            g[r][col_8] = 8
        return g
    return g
