"""Generator for arc_puzzle_bank_twentyfirst21:M146 — recolor shapes by size-rank to top-row legend.

Rule: row 0 holds K legend colors (left-aligned, with 0 gaps).
Below row 0: K connected shapes in distinct non-legend colors and
distinct sizes. Output recolors each shape: rank-i shape (sorted by
size ASC) becomes legend[i]. Row 0 is cleared.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes (≥2 shapes share size → "rank-i" is ambiguous,
tie-break decides), no_legend (row 0 is empty → rule's size→color map
is empty, all shapes stay their original colors), missing_shape (one
size slot has no shape → rule's rank-by-size has a gap, mapping
mismatched).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "914cf1c42d85"
VERSION = "2.1.1"
TASK_ID = "914cf1c42d85"
SUMMARY = (
    "0-bg grid (h~5-7, w~7-10) with: (a) ROW 0 "
    "containing a LEGEND of K=3 colors placed "
    "left-aligned at fixed columns 0, 2, 4 "
    "(with 0-gaps between them); (b) BELOW row 0: "
    "K=3 CONNECTED SHAPES at distinct positions, "
    "each in a DIFFERENT non-legend color, each "
    "with a DISTINCT SIZE drawn from sizes "
    "{1, 2, 4} (one 1-cell, one 2-cell line, one "
    "4-cell L-shape). Shapes don't touch each "
    "other or row 0. Rule: SORT the 3 shapes by "
    "size ASCENDING. RECOLOR shape with rank-i "
    "(0-indexed by size) to LEGEND[i] (the i-th "
    "row-0 color). CLEAR row 0 (set to 0). Net: "
    "shapes get repainted with legend colors "
    "according to size-rank; the legend itself "
    "is erased."
)

INVARIANTS = [
    "background is 0",
    "row 0 holds 3 legend colors at columns 0, 2, 4",
    "below row 0: a 1-cell, a 2-cell line, and a 4-cell L (each at a distinct location)",
    "shapes use 3 distinct colors disjoint from the legend",
    "shapes don't touch each other or row 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "no_legend", "missing_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 5..7", "valid": "5..10"},
    "grid_w":            {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "position_bias":     {"type": "str", "default": "row0_legend_plus_ranked_shapes",
                          "valid": "row0_legend_plus_ranked_shapes"},
    "n_distinct_colors": {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|tied_sizes|no_legend|missing_shape"},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 non-zero in row 0 (legend) and >=1 non-zero in rows 2+."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("tied_sizes", "no_legend", "missing_shape"):
        return errs
    if not any(grid[0][c] != 0 for c in range(w)):
        errs.append("no legend cells (non-zero) in row 0")
    if h > 2 and not any(grid[r][c] != 0 for r in range(2, h) for c in range(w)):
        errs.append("no shape cells (non-zero) in rows 2+")
    return errs


_SIZE2 = [[(0, 0), (0, 1)], [(0, 0), (1, 0)]]
_SIZE4 = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 10)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    legend = list(random_palette(rng, 3))
    g[0][0] = legend[0]
    g[0][2] = legend[1]
    g[0][4] = legend[2]
    shape_palette = list(random_palette(rng, 3, exclude=set(legend)))
    placed: list[tuple[int, int, int, int]] = [(0, 0, 0, w - 1)]
    for _ in range(80):
        r0 = rng.randint(2, h - 2)
        c0 = rng.randint(0, w - 1)
        bb = (r0 - 1, c0 - 1, r0 + 1, c0 + 1)
        if any(bbox_overlaps(bb, p) for p in placed): continue
        g[r0][c0] = shape_palette[0]
        placed.append((r0, c0, r0, c0))
        break
    for size_set, color in [(_SIZE2, shape_palette[1]),
                             (_SIZE4, shape_palette[2])]:
        # Placement below row 0 needs r0∈[2, h-sh-1] non-empty (sh ≤ h-3) and
        # c0∈[0, w-sw] (sw ≤ w). The 3-tall L (sh=3) can't fit easy's h=5 →
        # randint(2,1) raised "randrange(2,2)". Pick from the grid-feasible
        # subset so the 4-cell slot still gets a 4-cell shape that fits.
        feasible = [s for s in size_set
                    if (max(c[0] for c in s) + 1) <= h - 3
                    and (max(c[1] for c in s) + 1) <= w] or size_set
        shape = rng.choice(feasible)
        sh = max(c[0] for c in shape) + 1
        sw = max(c[1] for c in shape) + 1
        for _ in range(80):
            r0 = rng.randint(2, h - sh - 1)
            c0 = rng.randint(0, w - sw)
            bb = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
            if any(bbox_overlaps(bb, p) for p in placed): continue
            paint_at(g, r0, c0, shape, color)
            placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # Two shapes share size 2 — "rank-i" by size is ambiguous;
        # tie-break decides which legend slot each gets.
        g[0][0] = 4; g[0][2] = 5; g[0][4] = 6
        g[2][1] = 7; g[2][2] = 7  # 2-cell
        g[4][1] = 8; g[4][2] = 8  # 2-cell tied
        return g
    if name == "no_legend":
        # Row 0 is empty — rule's size→color map empty; shapes keep
        # original colors.
        g[2][1] = 3
        g[3][3] = 7; g[3][4] = 7
        g[4][6] = 8; g[4][7] = 8; g[5][6] = 8; g[5][7] = 8
        return g
    if name == "missing_shape":
        # Legend has 3 entries but only 2 shapes — rule's rank-by-size
        # has a gap; rank-3 is undefined.
        g[0][0] = 4; g[0][2] = 5; g[0][4] = 6
        g[2][1] = 7
        g[4][3] = 8; g[4][4] = 8
        return g
    return g
