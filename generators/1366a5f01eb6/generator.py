"""Generator for arc_additional_puzzles_21_set4:E26.

Rule: find full-height 5-col `div`; for each non-{0,5} cell at
(r, c<div), mirror to (r, 2*div-c) if right side is 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_left_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, no_left_cells, right_side_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1366a5f01eb6"
VERSION = "3.0.1"  # unlock fixed w=9/div=4: vary width, divider column, height, and left-cell count (out_shapes 3 -> many)
TASK_ID = "1366a5f01eb6"
SUMMARY = (
    "0-bg grid (h~5-7, w=9) with: (a) FULL-HEIGHT "
    "GRAY (color 5) DIVIDER COLUMN at column 4 "
    "(the exact middle); (b) LEFT SIDE (cols 0..3) "
    "has 2-3 ISOLATED NON-{0, 5} CELLS placed at "
    "distinct random positions, each painted with "
    "a color drawn from {1, 2, 3, 4, 6, 7, 8, 9}; "
    "(c) RIGHT SIDE (cols 5..8) starts ENTIRELY "
    "bg-0. Left cells are constrained to fit so "
    "their right mirror lands in-bounds. Rule "
    "(MIRROR LEFT-SIDE COLORS ACROSS THE GRAY "
    "DIVIDER): identify the full-height GRAY "
    "(color 5) DIVIDER COLUMN at col div = 4. For "
    "EACH non-{0, 5} CELL at position (r, c) "
    "where c < div: COMPUTE the MIRROR position "
    "(r, 2*div - c) on the right side. IF the "
    "mirror cell is currently bg-0: PAINT it with "
    "the SAME COLOR as the source. If the mirror "
    "cell is already non-0, SKIP. The divider and "
    "the source left-side cells stay unchanged. "
    "Net: the left half's scattered colors are "
    "reflected across the gray divider to "
    "populate the right side, producing left-"
    "right mirror symmetry."
)

INVARIANTS = [
    "exactly 1 full-height col of 5s",
    "left side has 2-3 isolated non-{0,5} cells",
    "right side empty (so mirror is visible)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "no_left_cells", "right_side_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..12", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 9..16", "valid": "7..20"},
    "divider_col":    {"type": "int", "default": "rng central", "valid": "1..w-2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_left_cells":   {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "left_half", "valid": "left_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "density":        {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one full-height column of gray(5); left side has non-bg cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    # Find full-height gray divider column
    divider_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if not divider_cols:
        return errors  # degenerate (no_divider) — allowed
    if len(divider_cols) > 1:
        errors.append(f"multiple full-height gray columns: {divider_cols}")
    div = divider_cols[0]
    # Left of divider should have at least one non-bg, non-5 cell
    left_cells = [(r, c) for r in range(h) for c in range(div) if grid[r][c] not in (0, 5)]
    if not left_cells:
        return errors  # degenerate (no_left_cells) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7); w = ctx.draw_int("grid_w", 7, 11)
        nlo, nhi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 14); w = ctx.draw_int("grid_w", 12, 20)
        nlo, nhi = 4, 8
    else:
        h = ctx.draw_int("grid_h", 5, 12); w = ctx.draw_int("grid_w", 9, 16)
        nlo, nhi = 3, 6
    # Divider column `div`: need >=1 left col (div>=1) and the right mirror
    # zone 2*div-c (for the rightmost-usable left cell) to fit: 2*div-1 < w.
    # Keep div roughly central so left cells have room and mirrors land in-bounds.
    div_lo = 1
    div_hi = min(w - 2, (w - 1) // 2 + 1)  # ensures some in-bounds mirror room
    if div_hi < div_lo:
        div_hi = div_lo
    div = rng.randint(div_lo, div_hi)
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][div] = 5
    palette = [1, 2, 3, 4, 6, 7, 8, 9]
    # Left cells must have c < div AND their mirror 2*div-c be in-bounds (< w).
    # 2*div-c < w  =>  c > 2*div - w. Combined with 0 <= c < div.
    c_min = max(0, 2 * div - w + 1)
    if c_min >= div:
        c_min = div - 1  # at least column div-1 is usable
    n_cells = ctx.draw_int("n_left_cells", nlo, nhi)
    placed = 0
    for _ in range(n_cells * 12):
        if placed >= n_cells:
            break
        r = rng.randint(0, h - 1); c = rng.randint(c_min, div - 1)
        mc = 2 * div - c
        if g[r][c] == 0 and 0 <= mc < w and g[r][mc] == 0:
            g[r][c] = rng.choice(palette)
            placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # left cells but no full-height 5-col → mirror axis undefined
        for r, c in [(1, 1), (3, 2)]:
            g[r][c] = 4
        return g
    if name == "no_left_cells":
        # divider but nothing on left → rule has no source cells to mirror
        for r in range(h):
            g[r][4] = 5
        return g
    if name == "right_side_filled":
        # left cells + divider but right side already non-zero → "right empty" fails
        for r in range(h):
            g[r][4] = 5
        g[1][1] = 4; g[3][2] = 6
        g[1][7] = 9; g[3][6] = 8
        return g
    return g
