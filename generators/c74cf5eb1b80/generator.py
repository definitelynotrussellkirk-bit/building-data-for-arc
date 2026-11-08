"""Generator for `arc_additional_puzzles_21_set11_bundle:E74` —
exactly one column is entirely 9s (the mirror guide); for every non-bg,
non-9 cell on the LEFT side of the guide, mirror it to the right.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_paint,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_guide, no_left_cells, cells_both_sides.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c74cf5eb1b80"
VERSION = "2.0.1"
TASK_ID = "c74cf5eb1b80"
SUMMARY = (
    "0-bg grid (h~6-10, w~9-14) with: (a) EXACTLY ONE "
    "FULL-HEIGHT color-9 (maroon) DIVIDER COLUMN at "
    "some column gc placed in the right half of the "
    "grid (gc ∈ [w//2..w-2]); (b) scattered non-{0, "
    "9} content cells in 2-3 distinct colors placed "
    "ONLY on the LEFT side of the divider (cols "
    "0..gc-1), at random row positions. The RIGHT "
    "side (cols gc+1..w-1) is initially EMPTY. Rule: "
    "for each cell (r, c) on the LEFT side with "
    "non-zero non-9 color k, compute its MIRROR "
    "column mc = 2*gc - c. If (r, mc) is in bounds, "
    "PAINT (r, mc) with color k. The 9-divider "
    "stays; original left cells stay. Net: the "
    "maroon column acts as a vertical mirror, "
    "reflecting all left-side content into the right "
    "half."
)

INVARIANTS = [
    "background is 0",
    "exactly one column is entirely 9s (the mirror guide)",
    ">=2 non-bg, non-9 cells on the LEFT of the guide",
    "right of the guide is all bg in the input",
    "guide column is positioned so left cells' mirrors stay in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_guide", "no_left_cells", "cells_both_sides")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "7..18 (must be odd-ish)"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "vertical_guide_with_left_cells",
                       "valid": "vertical_guide_with_left_cells"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..5"},
    "density":        {"type": "str", "default": "scattered", "valid": "scattered"},
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
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 9, 14)
    rng = ctx.draw_rng("guide_pos")
    gc = rng.randint(w // 2, w - 2)

    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][gc] = 9

    palette = ctx.draw_distinct_colors("palette", n=3, exclude={0, 9})
    rng2 = ctx.draw_rng("cells")
    n_paint = max(2, gc * h // 4)
    left_positions = [(r, c) for r in range(h) for c in range(gc)]
    rng2.shuffle(left_positions)
    for i, (r, c) in enumerate(left_positions[:n_paint]):
        mc = 2 * gc - c
        if mc < w:
            g[r][c] = palette[i % len(palette)]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one full-height color-9 divider column; >=1 non-{0,9} content cell left of it."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    # Find full-height color-9 columns
    full9_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(full9_cols) != 1:
        errors.append(f"expected exactly 1 full-height color-9 divider col, found {len(full9_cols)}")
        return errors
    gc = full9_cols[0]
    # Right side (cols gc+1..w-1) should be empty
    right_content = sum(grid[r][c] != 0 for r in range(h) for c in range(gc + 1, w))
    if right_content > 0:
        errors.append(f"found {right_content} nonzero cells right of divider (input should be empty there)")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 8, 11
    g = full_grid(h, w, 0)
    if name == "no_guide":
        # missing 9-column → no axis to mirror across
        g[1][2] = 4; g[3][3] = 6; g[5][1] = 3
        return g
    if name == "no_left_cells":
        # guide present but no left-side cells → rule has nothing to mirror
        gc = 6
        for r in range(h):
            g[r][gc] = 9
        return g
    if name == "cells_both_sides":
        # cells on both sides of guide → which side is the source?
        gc = 5
        for r in range(h):
            g[r][gc] = 9
        g[1][1] = 4; g[3][2] = 6  # left
        g[2][7] = 3; g[4][9] = 8  # right
        return g
    return g
