"""Generator for b71a7747 — extract the largest paired two-color block.

Rule: for each color, take the rows/cols where it appears (its support); if
that support submatrix is >=2x2 and contains EXACTLY two colors, it is a
candidate. Two candidates are "paired" when they have the same two-color
value-set (within a single 2-color block, its two colors pair each other).
Output = the submatrix of the largest paired candidate.

v2.0.0 drew ONE fixed {2,3} checkerboard at size 3/4 -> only 2 distinct
outputs (ERR gate). Now place several disjoint-color 2-color blocks of varied
size/colors/phase; each block is internally paired, and the rule outputs the
LARGEST -> output varies by that block's size, colors and pattern.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b277da396290"
VERSION = "3.0.0"  # ERR gate (distinct 2): drew one fixed 2/3 checkerboard. Rule outputs the largest paired 2-color block; now place K disjoint-color blocks of varied size/colors/phase -> output (the largest) varies widely.
TASK_ID = "b277da396290"
SUMMARY = ("0-bg grid with several disjoint-color 2-color blocks (each fills "
           "its rectangle with two colors, both present in every row & col so "
           "each color's support = the block). Rule crops to the largest such "
           "paired block.")

INVARIANTS = [
    "background is 0",
    "each block fills a rectangle with exactly two colors, both in every row and col",
    "blocks use mutually disjoint colors and have non-overlapping bounding rectangles",
    "the largest block is unique (strictly bigger area) so the output is well-defined",
]

DEGENERATE_TEXTURES = ("no_matrix", "full_grid", "single_color")
HELPFUL_TEXTURES = ()

AXES = {
    "grid_h":    {"type": "int", "default": "by difficulty", "valid": "10..24"},
    "grid_w":    {"type": "int", "default": "by difficulty", "valid": "10..24"},
    "n_blocks":  {"type": "int", "default": "by difficulty", "valid": "1..3"},
    "texture":   {"type": "str", "default": "none",
                  "valid": "|".join(DEGENERATE_TEXTURES)},
}


def _fill_block(g, r0, c0, bh, bw, x, y, phase):
    # checkerboard with the given phase -> both colors appear in every row and
    # column (for bh,bw >= 2), so each color's row/col support spans the block.
    for r in range(bh):
        for c in range(bw):
            g[r0 + r][c0 + c] = x if (r + c + phase) % 2 == 0 else y


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 10, 13)
        n_blocks = ctx.draw_int("n_blocks", 1, 2); smax = 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 24); w = ctx.draw_int("grid_w", 16, 24)
        n_blocks = ctx.draw_int("n_blocks", 2, 3); smax = 7
    else:
        h = ctx.draw_int("grid_h", 12, 20); w = ctx.draw_int("grid_w", 12, 20)
        n_blocks = ctx.draw_int("n_blocks", 1, 3); smax = 6

    g = full_grid(h, w, 0)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(colors)
    ci = 0
    placed = []           # (r1, c1, r2, c2) bounding rectangles
    areas = []
    for _ in range(n_blocks * 30):
        if len(placed) >= n_blocks or ci + 2 > len(colors):
            break
        bh = rng.randint(2, smax); bw = rng.randint(2, smax)
        if bh > h or bw > w:
            continue
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        r1, c1 = r0 + bh - 1, c0 + bw - 1
        # non-overlapping rectangles with >=1 gap so each color's row/col support
        # rectangle contains only its own block.
        if any(r0 <= p2 + 1 and p0 <= r1 + 1 and c0 <= p3 + 1 and p1 <= c1 + 1
               for p0, p1, p2, p3 in placed):
            continue
        if (bh * bw) in areas:        # keep the largest unique (avoid ties)
            continue
        x, y = colors[ci], colors[ci + 1]; ci += 2
        _fill_block(g, r0, c0, bh, bw, x, y, rng.randint(0, 1))
        placed.append((r0, c0, r1, c1)); areas.append(bh * bw)
    if not placed:                    # safety: one block
        _fill_block(g, 1, 1, 3, 3, colors[0], colors[1], 0)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_matrix":
        return g
    if name == "full_grid":
        _fill_block(g, 0, 0, 9, 9, 2, 3, 0)
        return g
    if name == "single_color":
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = 4          # only one color -> no valid 2-color candidate
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """bg=0; ≥2 distinct non-bg colors (blocks with two colors each)."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    fg = {grid[r][c] for r in range(h) for c in range(w)} - {0}
    if len(fg) < 2:
        errs.append(f"need ≥2 distinct fg colors for the 2-color blocks, got {len(fg)}")
    return errs
