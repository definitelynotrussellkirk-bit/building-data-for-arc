"""Generator for arc_puzzle_bank_21_next:easy_c04 — fill 0 in a 2x2 with 3 same-color cells.

Rule (single pass over the original grid): for each 2x2 window with exactly 3
cells of one non-0 color and 1 zero, set the zero to that color.

Prior coverage: the generator placed 2-3 isolated L-trominoes (a 2x2 minus one
cell) on tiny 5-8 grids. This version uses eroded monochrome BLOCKS of varied
size (2x2 up to 5x6) — a solid rectangle with a Chebyshev-spaced independent set
of cells removed, so EVERY hole sits in a 2x2 with the other 3 filled and heals
in the single pass (a 2x2-minus-one is exactly the old L-tromino). Bigger grids,
more blocks, full palette.

Rule-safe diversity: grid size, block count/size, erosion, colors, positions.
Degenerates: no_l_pattern, all_complete_squares, mixed_color_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f4d60fd96dde"
VERSION = "2.0.1"  # eroded blocks of varied size (subsumes L-trominoes) + bigger grids (was 2-3 tiny L's, 5-8 grid)
TASK_ID = "f4d60fd96dde"
SUMMARY = (
    "0-bg grid (size varies) with several solid monochrome RECTANGLES (2x2 up to "
    "5x6) in full 1-9 palette, each with a few cells ERODED (a Chebyshev-spaced "
    "independent set) so every hole sits in a 2x2 with 3 same-color neighbours. "
    "Blocks are separated by a 1-cell halo. Rule: fill any 2x2 with 3-same + "
    "1-zero (single pass). Net: each eroded block heals to a solid rectangle. "
    "(Was: 2-3 isolated L-trominoes on a tiny grid.)"
)

INVARIANTS = [
    "background is 0",
    ">=1 eroded monochrome rectangle (>=2x2)",
    "each block's removed cells are pairwise Chebyshev-distance >=2 (so each heals)",
    "blocks separated by a 1-cell halo (no cross-block 2x2 window)",
    "at least one cell eroded (output differs from input)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_l_pattern", "all_complete_squares", "mixed_color_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":   {"type": "int", "default": "6-9 easy / 9-13 med / 12-18 hard", "valid": "4..20"},
    "grid_w":   {"type": "int", "default": "7-10 easy / 11-15 med / 14-20 hard", "valid": "5..22"},
    "n_blocks": {"type": "int", "default": "2-3 easy / 3-4 med / 4-6 hard", "valid": "1..7"},
    "block_max":{"type": "int", "default": "rect dims 3 / 4 / 5", "valid": "2..6"},
    "n_distinct_colors": {"type": "int", "default": "up to 9", "valid": "1..9"},
    "density":  {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":  {"type": "str", "default": "alias for palette_kind",
                 "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _erode(rng, cells):
    order = cells[:]; rng.shuffle(order)
    removed = []
    for (r, c) in order:
        if all(max(abs(r - rr), abs(c - cc)) >= 2 for rr, cc in removed):
            removed.append((r, c))
    cap = max(1, min(len(removed), len(cells) - 1, (len(cells) + 1) // 2))
    return set(removed[:cap])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  task_id=TASK_ID, version=VERSION,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])
    if difficulty == "easy":
        hr, wr, nr, dmax = (6, 9), (7, 10), (2, 3), 3
    elif difficulty == "hard":
        hr, wr, nr, dmax = (12, 18), (14, 20), (4, 6), 5
    else:
        hr, wr, nr, dmax = (9, 13), (11, 15), (3, 4), 4
    rng = ctx.draw_rng("layout")
    h = rng.randint(*hr); w = rng.randint(*wr)
    g = full_grid(h, w, 0)
    occ = [[False] * w for _ in range(h)]
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]; rng.shuffle(colors)
    target = rng.randint(*nr)
    placed = 0
    any_eroded = False
    for k in range(target * 6):
        if placed >= target:
            break
        bh = rng.randint(2, dmax); bw = rng.randint(2, dmax)
        if bh > h or bw > w:
            continue
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        if any(occ[r][c]
               for r in range(max(0, r0 - 1), min(h, r0 + bh + 1))
               for c in range(max(0, c0 - 1), min(w, c0 + bw + 1))):
            continue
        color = colors[placed % len(colors)]
        cells = [(r0 + dr, c0 + dc) for dr in range(bh) for dc in range(bw)]
        for r, c in cells:
            g[r][c] = color
        for r, c in _erode(rng, cells):
            g[r][c] = 0
            any_eroded = True
        for r in range(r0, r0 + bh):
            for c in range(c0, c0 + bw):
                occ[r][c] = True
        placed += 1
    if not any_eroded:                       # fallback: one L-tromino
        g = full_grid(8, 9, 0)
        g[2][2] = 4; g[2][3] = 4; g[3][2] = 4
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the 2x2-completion rule.

    A valid default instance must contain at least one zero cell that participates
    in a 2x2 window with the other three cells all equal and non-zero; otherwise
    the rule is invisible.  This deliberately avoids overfitting to the generator
    internals while catching the historical all-complete/no-L regressions.
    """
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]
    bad = sorted({v for row in grid for v in row if not isinstance(v, int) or v < 0 or v > 9})
    if bad:
        errs.append(f"colors outside 0..9: {bad}")
    if not any(v != 0 for row in grid for v in row):
        errs.append("no non-zero cells")
    fillable = 0
    for r in range(h - 1):
        for c in range(w - 1):
            vals = [grid[r][c], grid[r+1][c], grid[r][c+1], grid[r+1][c+1]]
            zeros = vals.count(0)
            nz = [v for v in vals if v != 0]
            if zeros == 1 and len(nz) == 3 and len(set(nz)) == 1:
                fillable += 1
    if fillable == 0:
        errs.append("no fillable 2x2 window with exactly 3 same-color cells and one zero")
    return errs


def _draw_from_degenerate(name):
    g = full_grid(6, 7, 0)
    if name == "no_l_pattern":
        return g
    if name == "all_complete_squares":
        for r, c in [(1, 1), (1, 2), (2, 1), (2, 2)]: g[r][c] = 4
        for r, c in [(1, 4), (1, 5), (2, 4), (2, 5)]: g[r][c] = 6
        return g
    if name == "mixed_color_l":
        g[1][1] = 4; g[1][2] = 6; g[2][1] = 7
        return g
    return g
