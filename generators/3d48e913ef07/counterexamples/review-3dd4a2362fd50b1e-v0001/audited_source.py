"""Generator for arc_puzzle_bank_third_21_bundle:hard_18 — pack components by area with a palette.

Rule (verified from canonical Racket): COLUMN 0 holds a vertical PALETTE of colour
markers (cells in col 0 whose value is not 0 or 3), read top to bottom. The colour-3
OBJECTS are sorted by DESCENDING area; the largest takes the first palette colour,
the next the second, etc. Each object is cropped, recoloured to its palette colour,
and the results are vertically stacked (left-aligned, gap 1).

The previous body was the generic scatter template; it had no column-0 palette and
typically only one colour-3 object, so the packed output barely varied (distinct=4).
This rewrite CONSTRUCTS a column-0 palette plus several distinct-sized colour-3
objects, so the area ordering and recolouring produce varied stacked outputs.

Axes: object count, object sizes/shapes, palette colours + order, positions.
Degenerates: single_object, no_palette, equal_sizes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3d48e913ef07"
VERSION = "2.0.1"  # FIX: scatter template had no col-0 palette + one colour-3 object -> low diversity (distinct=4). Now a col-0 palette + several distinct-sized colour-3 objects.
TASK_ID = "3d48e913ef07"

SUMMARY = ("Column 0 is a top-to-bottom palette; the colour-3 objects are ordered by descending "
           "area, each recoloured to the next palette colour and vstacked. Object count, sizes, "
           "shapes and palette order vary.")

INVARIANTS = [
    "column 0 holds N palette markers (colours not in {0,3}), one per object",
    "N colour-3 objects of distinct sizes sit in columns 2+",
    "objects are separate connected components (1-cell halo)",
]

DEGENERATE_TEXTURES = ("single_object", "no_palette", "equal_sizes")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "grid_w":     {"type": "int", "default": "rng 12..16", "valid": "9..20"},
    "n_objs":     {"type": "int", "default": "2-3 easy / 3-4 hard", "valid": "2..5"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|single_object|no_palette|equal_sizes"},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: column 0 has palette markers (not 0 or 3), and >=1 color-3 object in cols 2+."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    palette_markers = [grid[r][0] for r in range(h) if grid[r][0] not in (0, 3)]
    if not palette_markers:
        errs.append("no palette markers found in column 0")
    threes = [(r, c) for r in range(h) for c in range(2, w) if grid[r][c] == 3]
    if not threes:
        errs.append("no color-3 objects found in columns 2+")
    return errs


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_PALETTE_COLORS = (1, 2, 4, 5, 6, 7, 8, 9)   # never 0 or 3


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _place(g, cells, r0, c0, color, occupied):
    h, w = len(g), len(g[0])
    abs_cells = [(r0 + r, c0 + c) for r, c in cells]
    for (r, c) in abs_cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (r + dr, c + dc) in occupied:
                    return False
    for (r, c) in abs_cells:
        g[r][c] = color
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                occupied.add((r + dr, c + dc))
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11); w = ctx.draw_int("grid_w", 12, 13)
        n = ctx.draw_int("n_objs", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14); w = ctx.draw_int("grid_w", 14, 16)
        n = ctx.draw_int("n_objs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 15)
        n = ctx.draw_int("n_objs", 2, 4)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    # column-0 palette: N markers at distinct rows, distinct colours, top to bottom
    pal_rows = sorted(rng.sample(range(h), n))
    pal_colors = rng.sample(_PALETTE_COLORS, n)
    for r, col in zip(pal_rows, pal_colors):
        g[r][0] = col

    # N colour-3 objects of distinct sizes, placed in columns 2+
    sizes = rng.sample(range(3, 3 + max(n + 3, 6)), n)   # distinct -> unambiguous area sort
    occupied = {(r, c) for r in range(h) for c in (0, 1)}  # keep cols 0,1 clear of objects
    placed = 0
    for sz in sizes:
        motif = _build_motif(rng, sz)
        bh = max(r for r, _ in motif) + 1; bw = max(c for _, c in motif) + 1
        for _ in range(200):
            r0 = rng.randint(0, max(0, h - bh)); c0 = rng.randint(2, max(2, w - bw))
            if _place(g, motif, r0, c0, 3, occupied):
                placed += 1
                break
    if placed < 2:                       # ensure a real multi-object pack
        return _draw_from_degenerate("equal_sizes", None)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 13
    g = full_grid(h, w, 0)
    if name == "no_palette":
        # objects but no column-0 palette -> nothing to recolour with -> [[0]]
        for r, c in [(2, 3), (2, 4), (3, 3)]:
            g[r][c] = 3
        for r, c in [(6, 6), (6, 7)]:
            g[r][c] = 3
        return g
    # one or two color-3 objects + a small palette
    g[1][0] = 5; g[5][0] = 6
    if name == "single_object":
        for r, c in [(2, 3), (2, 4), (3, 3), (3, 4)]:
            g[r][c] = 3
        return g
    # equal_sizes -> two objects of the same area (ambiguous ordering)
    for r, c in [(2, 3), (2, 4), (3, 3)]:
        g[r][c] = 3
    for r, c in [(7, 6), (7, 7), (8, 7)]:
        g[r][c] = 3
    return g
