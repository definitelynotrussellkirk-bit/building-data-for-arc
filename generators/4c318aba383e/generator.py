"""Generator for puzzle 79cce52d.

Rule: square N×N input; row 0 has exactly one 2 in cols 1..n-1
(col-shift indicator), col 0 has exactly one 2 in rows 1..n-1
(row-shift indicator). Output is (n-1)×(n-1) interior shifted.

Combinatorial axes (8): grid_n, p_col_position, p_row_position,
palette_size, interior_density, interior_layout, palette_kind,
asymmetry_force.
Degenerates: missing_marker, multiple_markers, all_interior_zero.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4c318aba383e"
VERSION = "1.1.1"
TASK_ID = "4c318aba383e"
SUMMARY = "nxn grid; row 0 and col 0 each have one 2 marker; rule shifts interior."

INVARIANTS = [
    "input is square N×N (N in [5, 12])",
    "row 0 has exactly one 2 in cols 1..n-1",
    "col 0 has exactly one 2 in rows 1..n-1",
    "(0, 0) is 0",
    "interior (rows 1..n-1, cols 1..n-1) has >=2 non-bg cells",
]

INTERIOR_LAYOUTS = ("scattered", "blob", "diagonal", "checker",
                    "frame", "row_dominant", "col_dominant")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("missing_marker", "multiple_markers", "all_interior_zero")
HELPFUL_TEXTURES = INTERIOR_LAYOUTS

AXES = {
    "grid_n":             {"type": "int", "default": "rng 5..12", "valid": "4..14"},
    "p_col_position":     {"type": "int", "default": "rng 1..n-1",
                           "valid": "1..n-1"},
    "p_row_position":     {"type": "int", "default": "rng 1..n-1",
                           "valid": "1..n-1"},
    "palette_size":       {"type": "int", "default": "rng 2..5",
                           "valid": "1..7"},
    "interior_density":   {"type": "float", "default": "rng 0.3..0.7",
                           "valid": "0.1..1"},
    "interior_layout":    {"type": "str", "default": "rng helpful",
                           "valid": "|".join(INTERIOR_LAYOUTS)},
    "palette_kind":       {"type": "str", "default": "rng helpful",
                           "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":      {"type": "bool", "default": "false",
                           "valid": "true|false"},
    "texture":            {"type": "str", "default": "alias for interior_layout",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        n_lo, n_hi = 4, 6
    elif difficulty == "hard":
        n_lo, n_hi = 10, 14
    else:
        n_lo, n_hi = 5, 12
    n = ctx.draw_int("grid_n", n_lo, n_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], n, rng)
    p_col = int(overrides.get("p_col_position",
                              ctx.draw_int("p_col_position", 1, n - 1)))
    p_row = int(overrides.get("p_row_position",
                              ctx.draw_int("p_row_position", 1, n - 1)))
    p_col = max(1, min(n - 1, p_col))
    p_row = max(1, min(n - 1, p_row))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 5, 7, 8]
    elif palette_kind == "small":
        pool = [1, 3]
    else:
        pool = [1, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 2, 5)))
    palette = pool[:max(1, n_palette)]
    layout = (overrides.get("texture") or
              overrides.get("interior_layout")
              or ctx.draw_choice("interior_layout",
                                 list(INTERIOR_LAYOUTS)))
    density = float(overrides.get("interior_density",
                                  ctx.draw_rng("interior_density")
                                  .uniform(0.3, 0.7)))
    g = full_grid(n, n, 0)
    g[0][p_col] = 2
    g[p_row][0] = 2
    interior_cells = [(r, c) for r in range(1, n) for c in range(1, n)]
    cells = _layout_interior(layout, interior_cells, n - 1, rng)
    n_paint = max(2, int(len(interior_cells) * density))
    for i, (r, c) in enumerate(cells[:n_paint]):
        g[r][c] = palette[i % len(palette)]
    if bool(overrides.get("anchor_corner", False)):
        g[1][1] = palette[0]
    return g


def _layout_interior(layout, cells, side, rng):
    if layout == "blob":
        cr = rng.randint(1, side); cc = rng.randint(1, side)
        cells = sorted(cells, key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return cells
    if layout == "diagonal":
        diag = [(k, k) for k in range(1, side + 1)]
        rest = [c for c in cells if c not in diag]
        rng.shuffle(rest)
        return diag + rest
    if layout == "checker":
        even = [c for c in cells if (c[0] + c[1]) % 2 == 0]
        odd = [c for c in cells if (c[0] + c[1]) % 2 != 0]
        rng.shuffle(even); rng.shuffle(odd)
        return even + odd
    if layout == "frame":
        border = [c for c in cells if c[0] in (1, side) or c[1] in (1, side)]
        interior = [c for c in cells if c not in border]
        rng.shuffle(border); rng.shuffle(interior)
        return border + interior
    if layout == "row_dominant":
        chosen_rows = rng.sample(range(1, side + 1), min(2, side))
        first = [c for c in cells if c[0] in chosen_rows]
        rest = [c for c in cells if c not in first]
        rng.shuffle(rest)
        return first + rest
    if layout == "col_dominant":
        chosen_cols = rng.sample(range(1, side + 1), min(2, side))
        first = [c for c in cells if c[1] in chosen_cols]
        rest = [c for c in cells if c not in first]
        rng.shuffle(rest)
        return first + rest
    rng.shuffle(cells)
    return cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify square NxN with row-0 and col-0 shift markers."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    problems = []
    if h != w:
        problems.append(f"expected square grid, got {h}x{w}")
        return problems
    n = h
    # (0,0) must be 0
    if grid[0][0] != 0:
        problems.append(f"(0,0) should be 0, found {grid[0][0]}")
    # row 0 must have exactly one 2 in cols 1..n-1
    row0_twos = [c for c in range(1, n) if grid[0][c] == 2]
    if len(row0_twos) != 1:
        problems.append(f"row 0 should have exactly 1 color-2 marker in cols 1..n-1, found {len(row0_twos)}")
    # col 0 must have exactly one 2 in rows 1..n-1
    col0_twos = [r for r in range(1, n) if grid[r][0] == 2]
    if len(col0_twos) != 1:
        problems.append(f"col 0 should have exactly 1 color-2 marker in rows 1..n-1, found {len(col0_twos)}")
    return problems


def _draw_from_degenerate(name, n, rng):
    g = full_grid(n, n, 0)
    if name == "missing_marker":
        g[0][n // 2] = 2
        return g
    if name == "multiple_markers":
        g[0][1] = 2; g[0][n - 1] = 2
        g[1][0] = 2; g[n - 1][0] = 2
        return g
    if name == "all_interior_zero":
        g[0][1] = 2
        g[1][0] = 2
        return g
    return g
