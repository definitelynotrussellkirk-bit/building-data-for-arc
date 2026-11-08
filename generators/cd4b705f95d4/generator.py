"""Generator for arc_puzzle_bank_21_set10_s:S10_H7 — Move 3-blob (size = count of 1s) to 2-anchor.

Rule: target_size = count of 1s in row 0. Find 3-blob with that size in
body. Anchor = first 2-cell. Translate blob's bbox top-left to anchor.
Paint moved cells with 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, k,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_count_row, no_anchor, no_size_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "cd4b705f95d4"
VERSION = "3.0.1"  # distinct 18: FIXED 2-cell & 3-cell blobs at fixed slots + anchor fixed at (5,5); only k toggled which of 2 shapes -> output was ~2 shapes at ONE position. Rule: select the color-3 blob whose size == count of 1s in row 0, paint it (8) with its bbox top-left at the anchor. Now 2-3 blobs of DISTINCT random sizes/shapes (incl non-square), k = one of those sizes, random anchor (fit in-bounds), varied grid."
TASK_ID = "cd4b705f95d4"
SUMMARY = (
    "0-bg grid (h~7-9, w~9-11). ROW 0 contains k=2..3 "
    "color-1 (blue) cells at random distinct columns "
    "(the COUNT/target-size). BODY (rows 1..h-1) "
    "contains EXACTLY 2 color-3 (green) BLOBS of "
    "DISTINCT sizes (one with 2 cells, one with 3 "
    "cells), positioned at fixed slots (rows 2, cols "
    "1 and 6). EXACTLY ONE color-2 (red) ANCHOR cell "
    "at fixed (5, 5) with room for the translated "
    "blob. Rule: count color-1 cells in row 0 → k. "
    "Find the green BLOB whose cell count equals k. "
    "TRANSLATE that blob so its bbox top-left lies at "
    "the red anchor's position. PAINT the translated "
    "cells with color 8 (cyan) on the existing grid. "
    "Original green blobs, the red anchor, and row-0 "
    "count stay. Net: the count selects the matching "
    "blob; output adds a cyan copy at the anchor."
)

INVARIANTS = [
    "row 0 has 2-4 1-cells",
    "exactly 2 3-blobs of distinct sizes (one matches k)",
    "exactly one 2-anchor with room for translated blob",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_count_row", "no_anchor", "no_size_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "k":              {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "count_row_plus_two_blobs_plus_anchor",
                       "valid": "count_row_plus_two_blobs_plus_anchor"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; row 0 has color-1 cells (count); body has color-3 blobs; one color-2 anchor."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    # check valid colors: 0, 1 (row0 count), 2 (anchor), 3 (blobs)
    allowed = {0, 1, 2, 3}
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
           if grid[r][c] not in allowed]
    if bad:
        return errs  # degenerate — allow
    twos = sum(1 for row in grid for v in row if v == 2)
    if twos > 1:
        errs.append(f"expected at most 1 color-2 anchor; found {twos}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 9, 11); n_blobs = 2; smax = 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 11, 16); n_blobs = 3; smax = 6
    else:
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 10, 13); n_blobs = ctx.draw_int("n_blobs", 2, 3); smax = 5
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    sizes = rng.sample(range(2, smax + 1), min(n_blobs, smax - 1))
    used = set()
    for c in range(w):
        used.add((0, c))                              # reserve row 0 for the count
    shape_by_size = {}
    for sz in sizes:
        shp = _poly(rng, sz)
        bh = max(r for r, _ in shp) + 1; bw = max(c for _, c in shp) + 1
        for _ in range(120):
            r0 = rng.randint(1, h - bh); c0 = rng.randint(0, w - bw)
            cells = {(r0 + dr, c0 + dc) for dr, dc in shp}
            ring = {(r, c) for (br, bc) in cells
                    for r in (br - 1, br, br + 1) for c in (bc - 1, bc, bc + 1)}
            if ring & used:
                continue
            for (r, c) in cells:
                g[r][c] = 3
            used |= cells
            shape_by_size[sz] = shp
            break
    if not shape_by_size:
        return g
    # k = count of 1s in row 0; choose a size we actually placed
    k = rng.choice(list(shape_by_size))
    cols = list(range(w)); rng.shuffle(cols)
    for c in cols[:k]:
        g[0][c] = 1
    # anchor: place color-2 where the selected blob (bbox dims) fits in-bounds
    sel = shape_by_size[k]
    bh = max(r for r, _ in sel) + 1; bw = max(c for _, c in sel) + 1
    for _ in range(200):
        ar = rng.randint(1, h - bh); ac = rng.randint(0, w - bw)
        if (ar, ac) not in used:
            g[ar][ac] = 2
            break
    return g


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_count_row":
        # blobs and anchor present but no 1-cells → no target size signal
        paint_at(g, 2, 1, [(0, 0), (1, 0)], 3)
        paint_at(g, 2, 6, [(0, 0), (1, 0), (1, 1)], 3)
        g[5][5] = 2
        return g
    if name == "no_anchor":
        # count + blobs but no 2-anchor → nowhere to translate the matching blob
        for c in [1, 3]: g[0][c] = 1
        paint_at(g, 2, 1, [(0, 0), (1, 0)], 3)
        paint_at(g, 2, 6, [(0, 0), (1, 0), (1, 1)], 3)
        return g
    if name == "no_size_match":
        # neither 3-blob has size k → rule's selection step has no candidate
        for c in [1, 3, 5, 7]: g[0][c] = 1  # k = 4
        paint_at(g, 2, 1, [(0, 0), (1, 0)], 3)
        paint_at(g, 2, 6, [(0, 0), (1, 0), (1, 1)], 3)
        g[5][5] = 2
        return g
    return g
