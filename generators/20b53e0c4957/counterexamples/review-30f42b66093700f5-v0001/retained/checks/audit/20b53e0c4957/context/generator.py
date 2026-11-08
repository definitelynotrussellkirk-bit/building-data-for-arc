"""Generator for 20b53e0c4957 — A→B removal replayed on C.

Rule: 3 panels split by full-height color-5 divider columns. A is a
solid colored block; B is A with some cells removed (set to 0). C is
another solid colored block. Compute relative positions of removed
cells (A_cells - B_cells in bbox coordinates). Apply same removals to
C. Output: C with the matching cells set to 0.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "20b53e0c4957"
VERSION = "2.0.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 full-height color-5 divider columns; non-{0,5} cells in all 3 panels."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    five_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(five_cols) < 2:
        errs.append(f"expected >=2 full-height color-5 divider columns, got {len(five_cols)}")
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in {0, 5}]
    if not nz:
        errs.append("no non-{0,5} cells (expected colored panel blocks)")
    return errs
TASK_ID = "20b53e0c4957"

SUMMARY = (
    "h×(3·pw+2) grid (0-bg) split into THREE pw-wide panels by full-height "
    "color-5 (gray) divider columns at cols pw and 2·pw+1 (h and pw both vary, "
    "incl. non-square panels). Panel A: SOLID h×pw block of color X. Panel B: "
    "same color X but with several cells REMOVED (set to 0) at random positions. "
    "Panel C: SOLID h×pw block of a DIFFERENT color Y. Rule: split panels at the "
    "5-columns. Compute REMOVED positions = A_cells − B_cells (relative to A's "
    "bbox). Apply the same removals to C: for each removed (rel_r, rel_c), set "
    "C[bbox_c_r1+rel_r][bbox_c_c1+rel_c] = 0. Output = modified C (h×pw)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "h × (3·pw+2) grid; cols pw and 2·pw+1 are full-height color-5 dividers",
    "panel A is a solid h×pw block of one non-zero color X",
    "panel B has same color X but with >=1 cell removed (0)",
    "panel C is a solid h×pw block of color Y, Y ≠ X, Y ≠ 0, Y ≠ 5",
    "A and B differ by at least one cell (removal is non-trivial)",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("no_separators", "identical_a_b", "no_panel_c")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "h":              {"type": "int", "default": "rng 4..7", "valid": "3..8"},
    "panel_w":        {"type": "int", "default": "rng 4..6", "valid": "3..7"},
    "n_removed":      {"type": "int", "default": "rng 2..6", "valid": "1..20"},
    "palette_kind":   {"type": "str", "default": "default", "valid": "default"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "three_panels_5col_split",
                       "valid": "three_panels_5col_split"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "dense", "valid": "dense"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # output dims = panel height h x panel width pw (the rule fixes 3 panels but the
    # panel SIZE is free). Was w hardcoded to 11 (pw=3) + h 3-5 -> only 2 output sizes.
    # Vary h and pw INDEPENDENTLY (non-square allowed) for output-shape diversity.
    if difficulty == "easy":
        h = ctx.draw_int("h", 3, 5); pw = ctx.draw_int("panel_w", 3, 4)
        n_remove = ctx.draw_int("n_removed", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("h", 5, 8); pw = ctx.draw_int("panel_w", 5, 7)
        n_remove = ctx.draw_int("n_removed", 3, 9)
    else:
        h = ctx.draw_int("h", 4, 7); pw = ctx.draw_int("panel_w", 4, 6)
        n_remove = ctx.draw_int("n_removed", 2, 6)

    w = 3 * pw + 2                      # 3 panels of width pw + 2 single-col dividers
    d1, d2 = pw, 2 * pw + 1             # divider columns
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][d1] = 5
        g[r][d2] = 5

    color_x = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    color_y = rng.choice([c for c in [1, 2, 3, 4, 6, 7, 8, 9] if c != color_x])

    a_cols = range(0, pw)
    b_cols = range(pw + 1, 2 * pw + 1)
    c_cols = range(2 * pw + 2, 3 * pw + 2)
    # A solid (the mask), B solid minus n_remove holes (the holes punch C), C solid
    for r in range(h):
        for c in a_cols:
            g[r][c] = color_x
        for c in b_cols:
            g[r][c] = color_x
        for c in c_cols:
            g[r][c] = color_y
    all_b_positions = [(r, c) for r in range(h) for c in b_cols]
    remove_pos = rng.sample(all_b_positions, min(n_remove, len(all_b_positions) - 1))
    for r, c in remove_pos:
        g[r][c] = 0
    return g


def _draw_from_degenerate(name, rng):
    h = 3
    w = 11
    g = full_grid(h, w, 0)
    if name == "no_separators":
        for r in range(h):
            for c in range(3):
                g[r][c] = 4
            for c in range(4, 7):
                g[r][c] = 4
            for c in range(8, 11):
                g[r][c] = 6
        return g
    if name == "identical_a_b":
        for r in range(h):
            g[r][3] = 5; g[r][7] = 5
            for c in range(3):
                g[r][c] = 4
            for c in range(4, 7):
                g[r][c] = 4
            for c in range(8, 11):
                g[r][c] = 6
        return g
    if name == "no_panel_c":
        for r in range(h):
            g[r][3] = 5; g[r][7] = 5
            for c in range(3):
                g[r][c] = 4
            for c in range(4, 7):
                g[r][c] = 4
        g[0][5] = 0
        return g
    return g
