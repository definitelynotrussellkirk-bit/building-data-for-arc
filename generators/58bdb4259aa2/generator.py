"""Generator for 11852cab.

Rule: find bbox center of all non-zero cells. For each non-zero cell,
paint at 4 rotated positions (0, 90, 180, 270) around the center.

Combinatorial axes (8): grid_n, n_cells, palette_size, palette_kind,
position_bias, anchor_corner, asymmetry_force, color_count.
Degenerates: full_grid, single_cell, all_in_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "58bdb4259aa2"
VERSION = "2.0.2"
TASK_ID = "58bdb4259aa2"
SUMMARY = (
    "0-bg SQUARE grid (n ∈ 7-14, h = w "
    "= n, by difficulty) with: "
    "N_CELLS ∈ 3-12 NON-ZERO CELLS in "
    "1-4 DISTINCT COLORS drawn per "
    "PALETTE_KIND ∈ {warm / cool / "
    "broad / primary}, placed per "
    "POSITION_BIAS ∈ {scattered "
    "(random in upper half) / tight "
    "(top-left corner) / diagonal "
    "(main diagonal) / row_aligned "
    "(one row)}. Cells lie in the "
    "upper half of the grid so the "
    "rotated copies fit. The bbox "
    "center of the non-zero cells is "
    "at integer coordinates. Rule "
    "(COMPUTE THE BBOX CENTER OF "
    "ALL NON-ZERO CELLS; FOR EACH "
    "NON-ZERO CELL, PAINT IT AT 4 "
    "ROTATED POSITIONS — 0°, 90°, "
    "180°, 270° — AROUND THE BBOX "
    "CENTER): COMPUTE bbox center "
    "(cr, cc). For EACH non-zero "
    "cell at (r, c) with color k: "
    "ROTATE (r - cr, c - cc) by "
    "0°, 90°, 180°, 270° → 4 "
    "(dr, dc) offsets. PAINT cells "
    "(cr + dr_i, cc + dc_i) = k "
    "for i ∈ 0..3 (in-bounds). "
    "Original cells preserved (as "
    "the i=0 rotation). Net: input "
    "pattern is replicated by 4-fold "
    "rotational symmetry around the "
    "bbox center."
)

INVARIANTS = [
    "h = w (square)",
    "5-10 non-zero cells (one or two distinct colors)",
    "cells lie in upper half so the rotated copies fit",
    "bbox center is at integer coordinates",
]

POSITION_BIASES = ("scattered", "tight", "diagonal", "row_aligned")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("full_grid", "single_cell", "all_in_corner")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_n":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "n_cells":        {"type": "int", "default": "rng 5..8", "valid": "3..12"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "warm|cool|broad|primary"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "scattered|tight|diagonal|row_aligned"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "color_count":    {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "scattered|tight|diagonal|row_aligned|full_grid|single_cell|all_in_corner"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        n_lo, n_hi = 7, 9
        nc_lo, nc_hi = 3, 5
        ps_lo, ps_hi = 1, 2
    elif difficulty == "hard":
        n_lo, n_hi = 11, 14
        nc_lo, nc_hi = 8, 12
        ps_lo, ps_hi = 3, 4
    else:
        n_lo, n_hi = 9, 11
        nc_lo, nc_hi = 5, 8
        ps_lo, ps_hi = 2, 3
    n = ctx.draw_int("grid_n", n_lo, n_hi)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette_size = int(overrides.get("palette_size",
                                     ctx.draw_int("palette_size",
                                                  ps_lo, ps_hi)))
    palette_size = max(1, min(4, palette_size))
    pal = _build_palette(palette_kind, palette_size, rng)
    n_cells = int(overrides.get("n_cells",
                                ctx.draw_int("n_cells", nc_lo, nc_hi)))
    n_cells = max(3, min(12, n_cells))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    for _attempt in range(30):
        g = full_grid(n, n, 0)
        placed = 0
        for _try in range(160):
            if placed >= n_cells:
                break
            r, c = _pick_cell(bias, n, rng)
            if g[r][c] == 0:
                g[r][c] = rng.choice(pal)
                placed += 1
        if placed >= 3 and _rotation_changes(g):
            return g
    return _fallback_nonidentity(n, pal, rng)


def _fallback_nonidentity(n, pal, rng):
    """Deterministic asymmetric pattern with integer bbox center."""
    g = full_grid(n, n, 0)
    ctr = min(max(3, n // 2), n - 3)
    offsets = [(-2, -1), (-2, 0), (-1, -2), (0, 1), (2, 2), (1, -1)]
    for i, (dr, dc) in enumerate(offsets):
        g[ctr + dr][ctr + dc] = pal[i % len(pal)] if pal else (i % 9) + 1
    return g


def _pick_cell(bias, n, rng):
    if bias == "tight":
        r = rng.randint(2, max(2, n // 3))
        c = rng.randint(2, max(2, n // 3))
    elif bias == "diagonal":
        i = rng.randint(2, max(2, n // 2))
        r, c = i, i
    elif bias == "row_aligned":
        r = rng.randint(2, max(2, n // 2))
        c = rng.randint(2, n - 3)
    else:
        r = rng.randint(2, max(2, n // 2 + 1))
        c = rng.randint(2, n - 3)
    return r, c


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _rotated_output(grid):
    h, w = len(grid), len(grid[0])
    cells = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not cells:
        return None
    rmin = min(r for r, _, _ in cells); rmax = max(r for r, _, _ in cells)
    cmin = min(c for _, c, _ in cells); cmax = max(c for _, c, _ in cells)
    if (rmin + rmax) % 2 or (cmin + cmax) % 2:
        return None
    cr = (rmin + rmax) // 2
    cc = (cmin + cmax) // 2
    out = [row[:] for row in grid]
    for r, c, color in cells:
        dr, dc = r - cr, c - cc
        for rr, cc2 in ((cr + dr, cc + dc), (cr - dc, cc + dr),
                        (cr - dr, cc - dc), (cr + dc, cc - dr)):
            if 0 <= rr < h and 0 <= cc2 < w and out[rr][cc2] == 0:
                out[rr][cc2] = color
    return out


def _rotation_changes(grid) -> bool:
    out = _rotated_output(grid)
    return out is not None and out != grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify that the 4-fold rotation rule is well-defined and non-identity."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs: list[str] = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h != w:
        errs.append(f"expected square grid, got {h}x{w}")
        return errs
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(nonzero) < 3:
        errs.append(f"expected at least 3 non-zero cells, found {len(nonzero)}")
    if _rotated_output(grid) is None:
        errs.append("bbox center is not at integer coordinates")
    elif not _rotation_changes(grid):
        errs.append("4-fold rotation leaves the input unchanged")
    return errs


def _draw_from_degenerate(name, rng):
    n = 9
    g = full_grid(n, n, 0)
    if name == "full_grid":
        for r in range(n):
            for c in range(n):
                g[r][c] = 2
        return g
    if name == "single_cell":
        g[3][3] = 2
        return g
    if name == "all_in_corner":
        for r in range(0, 2):
            for c in range(0, 2):
                g[r][c] = 2
        return g
    return g
