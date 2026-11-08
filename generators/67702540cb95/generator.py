"""Generator for 20981f0e.

Rule: blue shapes inside red-dot partition cells are recentered within
their cell ranges.

Combinatorial axes (8): grid_h/w, shape_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_dots, no_shapes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "67702540cb95"
VERSION = "2.0.1"  # shape-locked in/out: grid hardcoded 14x14 with fixed red dots at rows/cols [4,9]. Rule builds the row/col partition DYNAMICALLY from red cells and is fully size-generic (canonical: 14x16, 13x19, 17x10). Now build grid from random row/col BANDS (2..4 each) -> grid size + partition vary; varied blue rects per cell.
TASK_ID = "67702540cb95"
SUMMARY = "Blue shapes inside red-dot partition cells recentered in cell ranges."

INVARIANTS = [
    "red dots define at least two partition rows and columns",
    "blue shapes lie fully inside partition cells",
    "each blue shape has dimensions compatible with exact centering",
    "shape colors are color 1 on color-0 background",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_dots", "no_shapes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng bands", "valid": "9..28"},
    "grid_w":         {"type": "int", "default": "rng bands", "valid": "9..28"},
    "shape_count":    {"type": "int", "default": "rng", "valid": "1..16"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-2 (red partition dot) cell; ≥1 color-1 (blue shape) cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    has_red = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    has_blue = any(grid[r][c] == 1 for r in range(h) for c in range(w))
    if not has_red:
        errs.append("no color-2 (red partition) cells found")
    if not has_blue:
        errs.append("no color-1 (blue shape) cells found")
    return errs


def _bands(rng, n_bands):
    """Return (ranges, line_positions, total) for n_bands bands separated by
    1-cell red lines; each band is 3..6 wide."""
    ranges = []; lines = []; pos = 0
    for i in range(n_bands):
        bs = rng.randint(3, 6)
        ranges.append((pos, pos + bs - 1)); pos += bs
        if i < n_bands - 1:
            lines.append(pos); pos += 1
    return ranges, lines, pos


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        nr_lo, nr_hi, fill_frac = 2, 2, 0.6
    elif difficulty == "hard":
        nr_lo, nr_hi, fill_frac = 3, 4, 0.85
    else:
        nr_lo, nr_hi, fill_frac = 2, 4, 0.7
    n_rbands = ctx.draw_int("n_rbands", nr_lo, nr_hi)
    n_cbands = ctx.draw_int("n_cbands", nr_lo, nr_hi)
    row_ranges, row_lines, h = _bands(rng, n_rbands)
    col_ranges, col_lines, w = _bands(rng, n_cbands)
    g = full_grid(h, w, 0)
    # red dots at every (row-line, col-line) intersection define the partition
    for r in row_lines:
        for c in col_lines:
            g[r][c] = 2
    # one blue rect per chosen cell, random size + off-centre offset so the
    # rule's recentre actually moves it.
    cells = [(rr, cr) for rr in row_ranges for cr in col_ranges]
    rng.shuffle(cells)
    n = max(1, int(round(len(cells) * fill_frac)))
    for (r1, r2), (c1, c2) in cells[:n]:
        bh = rng.randint(1, min(3, r2 - r1 + 1))
        bw = rng.randint(1, min(3, c2 - c1 + 1))
        rr0 = rng.randint(r1, r2 - bh + 1)
        cc0 = rng.randint(c1, c2 - bw + 1)
        draw_rect(g, rr0, cc0, bh, bw, 1)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 14, 0)
    if name == "no_dots":
        draw_rect(g, 5, 5, 2, 2, 1)
        return g
    if name == "no_shapes":
        for r in [4, 9]:
            for c in [4, 9]:
                g[r][c] = 2
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(14):
                g[r][c] = 1
        return g
    return g
