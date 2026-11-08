"""Generator for 941d9a10.

Rule: color-5 grid has its top-left, center, and bottom-right cells
filled with blue, red, and green.

Combinatorial axes (8): grid_h/w, cell_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias, n_bands.
Degenerates: no_dividers, full_grid, single_band.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9dcdf3696b49"
VERSION = "2.1.0"
TASK_ID = "9dcdf3696b49"
SUMMARY = (
    "0-bg grid (h = sum(row_bands)+dividers, "
    "w = sum(col_bands)+dividers) with "
    "COLOR-5 (gray) DIVIDERS forming "
    "an odd 5×3, 3×5, or occasional 5×5 "
    "macro-cell lattice. Thin bands on the "
    "5-side keep color 5 as the majority "
    "like the canonical demos, so zero "
    "macro-cells are separate counted objects. "
    "Cell grid has odd row × col count "
    "so a CENTER macro-cell exists. Rule "
    "(FILL 3 "
    "DIAGONAL MACRO-CELLS): "
    "identify the 3×3 cell grid "
    "split by color-5 dividers. "
    "Fill the TOP-LEFT macro-"
    "cell's 0-cells with COLOR 1 "
    "(blue), the CENTER macro-"
    "cell with COLOR 2 (red), "
    "and the BOTTOM-RIGHT macro-"
    "cell with COLOR 3 (green). "
    "The 6 non-diagonal macro-"
    "cells stay 0. Dividers stay "
    "color 5. Net: 3×3 lattice "
    "of macro-cells with main "
    "diagonal filled "
    "blue/red/green."
)

INVARIANTS = [
    "background is color 0",
    "color 5 forms full divider rows and columns",
    "the cell grid has odd row and column counts so a center cell exists",
    "only zero cells inside the three diagonal macro-cells get recolored",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_dividers", "full_grid", "single_band")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..14", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 8..14", "valid": "7..18"},
    "cell_count":     {"type": "int", "default": "rng 5x3|3x5", "valid": "3|5"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "n_bands":        {"type": "int", "default": "rng 3|5", "valid": "3|5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_dividers|full_grid|single_band"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # Canonical demos are mostly 5-majority divider lattices: once 5 is
    # the majority/background, the zero macro-cells are counted as separate
    # objects (median 15).  The old fixed 3x3 lattice made zero the majority
    # almost always, so the input collapsed to one gray object under the
    # generic structural audit.  Keep odd dimensions for the center cell but
    # favor 5x3 / 3x5 layouts to match the canonical object structure.
    if difficulty == "hard" and rng.random() < 0.25:
        n_rows, n_cols = (5, 5)
    else:
        n_rows, n_cols = rng.choice([(5, 3), (3, 5)])
    ctx._record("cell_count", max(n_rows, n_cols), from_override=False)
    ctx._record("n_bands", max(n_rows, n_cols), from_override=False)

    def _bands(n):
        if n == 5:
            return [rng.choice([1, 1, 2]) for _ in range(n)]
        return [rng.randint(2, 4) for _ in range(n)]

    row_bands = _bands(n_rows)
    col_bands = _bands(n_cols)
    h = sum(row_bands) + (n_rows - 1)
    w = sum(col_bands) + (n_cols - 1)
    g = full_grid(h, w, 0)

    div_rows = []
    cursor = row_bands[0]
    for i in range(1, n_rows):
        div_rows.append(cursor)
        cursor += 1 + row_bands[i]
    div_cols = []
    cursor = col_bands[0]
    for i in range(1, n_cols):
        div_cols.append(cursor)
        cursor += 1 + col_bands[i]
    for r in div_rows:
        for c in range(w):
            g[r][c] = 5
    for c in div_cols:
        for r in range(h):
            g[r][c] = 5
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    if name == "no_dividers":
        return g
    if name == "single_band":
        for c in range(11):
            g[5][c] = 5
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(11):
                g[r][c] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify a color-5 divider lattice with odd macro-cell dimensions."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    div_rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    div_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if not div_rows:
        errs.append("no full-width color-5 divider row found")
    if not div_cols:
        errs.append("no full-height color-5 divider column found")

    def _ranges(size, divs):
        last = -1
        out = []
        for d in divs + [size]:
            if last + 1 <= d - 1:
                out.append((last + 1, d - 1))
            last = d
        return out

    row_ranges = _ranges(h, div_rows)
    col_ranges = _ranges(w, div_cols)
    if len(row_ranges) < 3 or len(col_ranges) < 3:
        errs.append(f"expected at least a 3x3 macro-cell lattice; got {len(row_ranges)}x{len(col_ranges)}")
    if len(row_ranges) % 2 == 0 or len(col_ranges) % 2 == 0:
        errs.append(f"macro-cell lattice must have odd dimensions; got {len(row_ranges)}x{len(col_ranges)}")
    if grid and max(sum(row.count(0) for row in grid), 1) > 2 * max(sum(row.count(5) for row in grid), 1):
        errs.append("zero cells dominate too strongly; divider lattice no longer resembles canonical 5-majority cases")
    return errs
