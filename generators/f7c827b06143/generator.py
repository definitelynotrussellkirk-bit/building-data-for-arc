"""Generator for arc_additional_puzzles_21_set6:E37 — Fill 2x2 windows with 3 same.

Rule: iterate to a fixed point; whenever a 2x2 window has exactly 3 cells of one
non-zero color and 1 zero, fill the zero with that color. Filling can complete a
neighbouring window, so the effect CASCADES — eroded monochrome blocks heal back
to solid rectangles.

Rule-safe diversity (this version): grid size, number of blocks, block SIZE
(2x2 up to ~5x6), how many cells are eroded, and full 1-9 palette. Each block is
a solid monochrome rectangle with a Chebyshev-spaced independent set of cells
removed — every removed cell sits in a 2x2 with the other 3 filled, so the rule
refills the whole block (a 2x2-minus-one is exactly the old L-tromino case).
Degenerates: no_l, full_2x2, length_2_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f7c827b06143"
VERSION = "2.1.0"  # add executable self_check for the cascade-fill 2x2 invariant; literal AXES for lint
TASK_ID = "f7c827b06143"
SUMMARY = (
    "0-bg grid (size varies). Several solid monochrome RECTANGLES (2x2 up to "
    "~5x6) in colors from the full 1-9 palette, each with a few cells ERODED "
    "(removed to 0) as a Chebyshev-spaced independent set so every hole has 3 "
    "same-color neighbours in some 2x2. Blocks are separated by a 1-cell halo. "
    "Rule: iteratively fill any 2x2 with 3 same + 1 zero (cascades). Net: each "
    "eroded block heals back to a solid rectangle. (Was: 2-3 isolated single "
    "L-trominoes that each fill one corner.)"
)

INVARIANTS = [
    "background is 0",
    ">=1 eroded monochrome rectangle (>=2x2)",
    "each block's removed cells are pairwise Chebyshev-distance >=2 (so each refills)",
    "blocks are separated by a 1-cell halo (no cross-block 2x2 windows)",
    "at least one cell is eroded somewhere (output differs from input)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_l", "full_2x2", "length_2_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7-9 easy / 9-13 med / 12-18 hard", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "8-11 easy / 11-15 med / 14-20 hard", "valid": "6..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_shapes":       {"type": "int", "default": "2-3 easy / 3-4 med / 4-6 hard", "valid": "1..7"},
    "block_max":      {"type": "int", "default": "rect dims 2..3 easy / 2..4 med / 2..5 hard", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "per-block colors", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "separated_eroded_blocks",
                       "valid": "separated_eroded_blocks"},
    "n_distinct_colors": {"type": "int", "default": "up to 9", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_l|full_2x2|length_2_l"},
}


def _erode(rng, cells):
    """Remove a non-empty Chebyshev-spaced independent set from a block's cells."""
    order = cells[:]; rng.shuffle(order)
    removed = []
    for (r, c) in order:
        if all(max(abs(r - rr), abs(c - cc)) >= 2 for rr, cc in removed):
            removed.append((r, c))
    # keep ~half at most, and never remove every cell
    cap = max(1, min(len(removed), len(cells) - 1, (len(cells) + 1) // 2))
    return set(removed[:cap])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, nr, dmax = (7, 9), (8, 11), (2, 3), 3
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
        # require a 1-cell halo free of other blocks
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
    if not any_eroded:
        # deterministic fallback: a single 2x2 missing one corner (L-tromino)
        g = full_grid(8, 9, 0)
        g[2][2] = 4; g[2][3] = 4; g[3][2] = 4
    return g


def _fillable_windows(grid):
    hits = []
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            coords = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
            vals = [grid[rr][cc] for rr, cc in coords]
            zeros = [p for p, v in zip(coords, vals) if v == 0]
            nonzeros = [v for v in vals if v != 0]
            if len(zeros) == 1 and len(nonzeros) == 3 and len(set(nonzeros)) == 1:
                hits.append((zeros[0], nonzeros[0]))
    return hits


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Normal examples must visibly exercise the 3-of-4 2x2 fill rule."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(v not in range(10) for row in grid for v in row):
        return ["colors must be ARC digits 0..9"]
    if not any(v != 0 for row in grid for v in row):
        return ["normal example has no colored cells"]
    if not _fillable_windows(grid):
        return ["no 2x2 window has exactly three same nonzero cells and one zero"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_l":
        # blank → no shapes to complete
        return g
    if name == "full_2x2":
        # 2x2 already complete → no missing 4th to fill
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 4
        return g
    if name == "length_2_l":
        # 2-cell groups → not 3-of-4, rule won't fire
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 4
        for r, c in [(5, 5), (6, 5)]: g[r][c] = 6
        return g
    return g
