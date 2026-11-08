"""Generator for puzzle 65daed9b.

Rule: find the column containing 8-cells (mirror axis). For 0-cells:
if mirror cell is non-zero, copy it. Axis col becomes all 8.

Combinatorial axes (8): grid_h/w, axis_col, n_marks, side, n_cells,
palette_kind, anchor_corner, asymmetry_force.
Degenerates: no_axis, no_cells, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b7d1baa57fb4"
VERSION = "2.0.1"
TASK_ID = "b7d1baa57fb4"
SUMMARY = (
    "0-bg grid (h~8-14, w~"
    "10-16) with: (a) ONE "
    "MIRROR AXIS COLUMN at "
    "axis_col (3..w-4) — 1-3 "
    "COLOR-8 (cyan) CELLS "
    "placed at random rows "
    "on this column (NOT a "
    "full 8-column, just "
    "markers); (b) 5-10 "
    "SCATTERED NON-ZERO "
    "CELLS in colors from "
    "palette (warm/cool/"
    "broad/primary) on ONE "
    "SIDE of the axis "
    "(left OR right). Cells "
    "are not on the axis "
    "column. Rule (IDENTIFY "
    "8-AXIS, MIRROR NON-ZERO "
    "CELLS, FILL AXIS): "
    "identify the AXIS COLUMN "
    "(unique col containing "
    "≥1 color-8). For EACH "
    "0-cell at (r, c) with "
    "c ≠ axis_col: COMPUTE "
    "MIRROR position "
    "(r, 2*axis_col - c). If "
    "the MIRROR cell is non-"
    "zero, COPY it to (r, c). "
    "AXIS COLUMN becomes "
    "ENTIRELY COLOR-8 (every "
    "cell on the axis col is "
    "filled with 8). Net: "
    "scattered cells reflect "
    "across the 8-axis; axis "
    "column becomes solid "
    "cyan."
)

INVARIANTS = [
    "background is 0",
    ">=1 cell of color 8 on the axis column",
    "no other 8-cells outside axis",
    ">=1 non-zero cell whose mirror is 0",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
SIDES = ("left", "right", "rng")
DEGENERATE_TEXTURES = ("no_axis", "no_cells", "full_grid")
HELPFUL_TEXTURES = SIDES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "axis_col":       {"type": "int", "default": "rng 3..w-4",
                       "valid": "1..w-2"},
    "n_marks":        {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "side":           {"type": "str", "default": "rng helpful",
                       "valid": "|".join(SIDES)},
    "n_cells":        {"type": "int", "default": "rng 5..10", "valid": "1..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for side",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: all color-8 cells (axis column markers) occupy a single column."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    cols_with_8 = {c for r in range(h) for c in range(w) if grid[r][c] == 8}
    if len(cols_with_8) > 1:
        return [f"color-8 (axis) cells span multiple columns: {sorted(cols_with_8)}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 6, 9
    elif difficulty == "hard":
        h_lo, h_hi = 14, 18
    else:
        h_lo, h_hi = 8, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo + 2, h_hi + 4)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    axis_col = int(overrides.get("axis_col",
                                 rng.randint(3, max(3, w - 4))))
    axis_col = max(1, min(w - 2, axis_col))
    n_marks = int(overrides.get("n_marks",
                                ctx.draw_int("n_marks", 1, 3)))
    n_marks = max(1, min(5, min(h, n_marks)))
    side = (overrides.get("texture") or
            overrides.get("side")
            or ctx.draw_choice("side", list(SIDES)))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, rng)
    n_cells = int(overrides.get("n_cells",
                                ctx.draw_int("n_cells", 5, 10)))
    g = full_grid(h, w, 0)
    mark_rows = rng.sample(range(h), n_marks)
    for r in mark_rows:
        g[r][axis_col] = 8
    if side == "left":
        side_dir = -1
    elif side == "right":
        side_dir = 1
    else:
        side_dir = rng.choice([-1, 1])
    placed_payload = 0
    for _ in range(n_cells * 4):
        if placed_payload >= n_cells:
            break
        r = rng.randint(0, h - 1)
        if side_dir == -1:
            lo = max(0, 2 * axis_col - (w - 1))
            hi = axis_col - 1
        else:
            lo = axis_col + 1
            hi = min(w - 1, 2 * axis_col)
        if lo > hi:
            continue
        c = rng.randint(lo, hi)
        if g[r][c] == 0:
            g[r][c] = rng.choice(palette)
            placed_payload += 1
    if placed_payload == 0:
        # Fallback: put one payload cell in the nearest mirror-safe slot.
        c = axis_col - 1 if axis_col > 0 else axis_col + 1
        g[h // 2][c] = rng.choice(palette)
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 9]
    rng.shuffle(pool)
    return pool




def self_check(grid, *, difficulty=None, meta=None):
    h, w = len(grid), len(grid[0])
    axis_cols = [c for c in range(w) if any(grid[r][c] == 8 for r in range(h))]
    errors = []
    if len(axis_cols) != 1:
        return [f"expected exactly one cyan axis column, got {axis_cols}"]
    axis = axis_cols[0]
    payload = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)]
    if not payload:
        errors.append("no payload cells to mirror")
    sides = {-1 if c < axis else 1 for _r, c in payload}
    if len(sides) != 1:
        errors.append("payload appears on both sides of the axis; examples should show one-sided completion")
    for _r, c in payload:
        mc = 2 * axis - c
        if not (0 <= mc < w):
            errors.append("payload cell mirrors out of bounds")
            break
    return errors

def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_axis":
        for r in range(2, 5):
            g[r][2] = rng.choice([1, 2, 3, 4])
        return g
    if name == "no_cells":
        axis_col = w // 2
        for r in range(h // 2):
            g[r][axis_col] = 8
        return g
    if name == "full_grid":
        axis_col = w // 2
        for r in range(h):
            for c in range(w):
                if c == axis_col:
                    g[r][c] = 8
                else:
                    g[r][c] = rng.choice([1, 2, 3, 4])
        return g
    return g
