"""Generator for 90c28cc7.

Rule: grid of colored blocks downscaled by detecting row/col transition
starts.

Combinatorial axes (8): rows, cols, palette_kind, max_band_h, max_band_w,
anchor_corner, asymmetry_force, palette_size.
Degenerates: single_block, no_blocks, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2c6ab8f41290"
VERSION = "2.1.0"  # keep varied macro rows/cols but restore canonical-scale 21x21 canvases with zero margins around the nonzero block bbox
TASK_ID = "2c6ab8f41290"
SUMMARY = "Canonical-scale 21x21 grid with a zero margin around a nonzero rectangle of solid colored blocks; rule downscales by detecting row/col transitions."

INVARIANTS = [
    "canvas is 21x21 with optional zero margin",
    "all cells in the nonzero bbox are nonzero block colors",
    "each macro-cell is a solid-color rectangle",
    "adjacent macro-cells differ in color along the probe row and column",
    "the output samples one representative cell from each block",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("single_block", "no_blocks", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "rows":           {"type": "int", "default": "3", "valid": "2..6"},
    "cols":           {"type": "int", "default": "3", "valid": "2..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "max_band_h":     {"type": "int", "default": "bbox composition", "valid": "1..12"},
    "max_band_w":     {"type": "int", "default": "bbox composition", "valid": "1..12"},
    "canvas_size":    {"type": "int", "default": "21", "valid": "18..24"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "5", "valid": "3..7"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _random_parts(total, n, rng):
    """Return n positive integer parts summing to total."""
    if n <= 1:
        return [total]
    cuts = sorted(rng.sample(range(1, total), n - 1))
    pts = [0] + cuts + [total]
    return [pts[i + 1] - pts[i] for i in range(n)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        rows = ctx.draw_int("rows", 2, 3)
        cols = ctx.draw_int("cols", 2, 3)
        bbox_lo, bbox_hi = 12, 17
    elif difficulty == "hard":
        rows = ctx.draw_int("rows", 4, 6)
        cols = ctx.draw_int("cols", 4, 6)
        bbox_lo, bbox_hi = 16, 21
    else:
        rows = ctx.draw_int("rows", 2, 5)
        cols = ctx.draw_int("cols", 2, 5)
        bbox_lo, bbox_hi = 14, 21
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    pool = _build_palette(palette_kind, rng)
    if len(pool) < 5:
        pool = pool + [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]
                       if c not in pool]
    colors = pool[:5]
    canvas = int(overrides.get("canvas_size", 21))
    canvas = max(18, min(24, canvas))
    bbox_h = int(overrides.get("bbox_h", rng.randint(max(rows, bbox_lo), min(canvas, bbox_hi))))
    bbox_w = int(overrides.get("bbox_w", rng.randint(max(cols, bbox_lo), min(canvas, bbox_hi))))
    bbox_h = max(rows, min(canvas, bbox_h))
    bbox_w = max(cols, min(canvas, bbox_w))
    heights = _random_parts(bbox_h, rows, rng)
    widths = _random_parts(bbox_w, cols, rng)
    top = rng.randint(0, canvas - bbox_h)
    left = rng.randint(0, canvas - bbox_w)

    g = full_grid(canvas, canvas, 0)
    r0 = top
    for r_idx, rh in enumerate(heights):
        c0 = left
        for c_idx, cw in enumerate(widths):
            color = colors[(r_idx * 2 + c_idx) % len(colors)]
            for r in range(r0, r0 + rh):
                for c in range(c0, c0 + cw):
                    g[r][c] = color
            c0 += cw
        r0 += rh
    return g

def _runs_by_change(values):
    if not values:
        return []
    starts = [0]
    for i in range(1, len(values)):
        if values[i] != values[i - 1]:
            starts.append(i)
    starts.append(len(values))
    return list(zip(starts, starts[1:]))


def _nonzero_bbox(grid):
    nz = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not nz:
        return None
    return (min(r for r, _ in nz), max(r for r, _ in nz),
            min(c for _, c in nz), max(c for _, c in nz))


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid is empty or not a 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    if h < 18 or w < 18:
        errs.append(f"generated canvas too small for canonical-scale task: {h}x{w}")
    values = {v for row in grid for v in row}
    bad_values = sorted(v for v in values if not isinstance(v, int) or v < 0 or v > 9)
    if bad_values:
        errs.append(f"cell values outside ARC palette: {bad_values}")
    bbox = _nonzero_bbox(grid)
    if bbox is None:
        return errs + ["normal block grid has no nonzero block bbox"]
    r0, r1, c0, c1 = bbox
    if any(grid[r][c] == 0 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
        errs.append("nonzero bbox contains background 0")
        return errs

    # Mirror the canonical rule's transition probes: use the row/column with the
    # most adjacent color changes inside the bbox.
    best_row = max(range(r0, r1 + 1),
                   key=lambda r: sum(grid[r][c] != grid[r][c - 1]
                                     for c in range(c0 + 1, c1 + 1)))
    best_col = max(range(c0, c1 + 1),
                   key=lambda c: sum(grid[r][c] != grid[r - 1][c]
                                     for r in range(r0 + 1, r1 + 1)))
    col_starts = [c for c in range(c0, c1 + 1)
                  if c == c0 or grid[best_row][c] != grid[best_row][c - 1]]
    row_starts = [r for r in range(r0, r1 + 1)
                  if r == r0 or grid[r][best_col] != grid[r - 1][best_col]]
    if not (2 <= len(row_starts) <= 6):
        errs.append(f"expected 2..6 row bands, found {len(row_starts)}")
    if not (2 <= len(col_starts) <= 6):
        errs.append(f"expected 2..6 column bands, found {len(col_starts)}")

    row_ends = row_starts[1:] + [r1 + 1]
    col_ends = col_starts[1:] + [c1 + 1]
    macro = []
    for rr, (rs, re) in enumerate(zip(row_starts, row_ends)):
        macro_row = []
        for cc, (cs, ce) in enumerate(zip(col_starts, col_ends)):
            color = grid[rs][cs]
            macro_row.append(color)
            if any(grid[r][c] != color for r in range(rs, re) for c in range(cs, ce)):
                errs.append(f"macro-cell ({rr},{cc}) is not solid")
                return errs
        macro.append(macro_row)
    for r in range(len(macro)):
        for c in range(len(macro[0]) - 1):
            if macro[r][c] == macro[r][c + 1]:
                errs.append("adjacent horizontal macro-cells share a color")
    for r in range(len(macro) - 1):
        for c in range(len(macro[0])):
            if macro[r][c] == macro[r + 1][c]:
                errs.append("adjacent vertical macro-cells share a color")
    return errs

def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 0]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    if name == "single_block":
        return full_grid(h, w, 2)
    if name == "no_blocks":
        return full_grid(h, w, 0)
    if name == "full_grid":
        return full_grid(h, w, 5)
    return full_grid(h, w, 0)
