"""Generator for 60b1448d.

Rule: find first column entirely filled with one non-zero color
(axis_color). For each cell: if 0 and mirror cell != 0 != axis_color,
copy mirror; axis stays axis_color.

Combinatorial axes (8): grid_h/w, axis_color, axis_col, side, n_marks,
palette_kind, anchor_corner, asymmetry_force.
Degenerates: no_axis, two_axes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dd3fa53619d9"
VERSION = "1.2.0"
TASK_ID = "dd3fa53619d9"
SUMMARY = "Grid with one full-color axis column; rule mirrors non-zero cells across it."

INVARIANTS = [
    "exactly one column fully filled with a non-zero axis_color",
    "no other column is fully filled",
    "axis_color does not appear off the axis column",
    ">=1 non-zero off-axis cell whose mirror is 0",
]

SIDES = ("left", "right", "both")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_axis", "two_axes", "full_grid")
HELPFUL_TEXTURES = SIDES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "8..18"},
    "axis_color":     {"type": "color", "default": "rng",
                       "valid": "2|3|4|6|7|8|9"},
    "axis_col":       {"type": "int", "default": "rng",
                       "valid": "3..w-4"},
    "side":           {"type": "str", "default": "rng helpful",
                       "valid": "|".join(SIDES)},
    "n_marks":        {"type": "int", "default": "rng 5..9", "valid": "3..12"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for side",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 8, 8, 10
        nm_lo, nm_hi = 3, 5
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 12, 16, 14, 18
        nm_lo, nm_hi = 8, 12
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 12, 10, 14
        nm_lo, nm_hi = 5, 9
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pool = _build_pool(palette_kind, rng)
    axis_color = int(overrides.get("axis_color",
                                   rng.choice([c for c in pool if c in
                                               (2, 3, 4, 6, 7, 8, 9)] or [2])))
    axis_col = int(overrides.get("axis_col",
                                 rng.randint(3, max(3, w - 4))))
    axis_col = max(3, min(axis_col, w - 4))
    for r in range(h):
        g[r][axis_col] = axis_color
    palette = [c for c in pool if c not in (0, axis_color)]
    if not palette:
        palette = [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c != axis_color]
    side = (overrides.get("texture") or
            overrides.get("side")
            or ctx.draw_choice("side", list(SIDES)))
    n_marks = int(overrides.get("n_marks",
                                rng.randint(nm_lo, nm_hi)))
    n_marks = max(3, min(15, n_marks))
    for _ in range(n_marks):
        for _try in range(20):
            r = rng.randint(0, h - 1)
            if side == "left":
                c = rng.randint(0, axis_col - 1)
            elif side == "right":
                c = rng.randint(axis_col + 1, w - 1)
            else:
                c = rng.randint(0, w - 1)
            if c == axis_col or g[r][c] != 0:
                continue
            g[r][c] = rng.choice(palette)
            break
    if not _has_mirror_witness(g, axis_col, axis_color):
        # Guarantee at least one visible fill opportunity.  Random placements can
        # all land outside the mirrorable span or in already-symmetric pairs,
        # making the mirror rule look like an identity/no-op on rare seeds.
        for r in range(h):
            for c in list(range(axis_col - 1, -1, -1)) + list(range(axis_col + 1, w)):
                mc = 2 * axis_col - c
                if 0 <= mc < w and g[r][c] == 0 and g[r][mc] == 0:
                    g[r][c] = palette[0]
                    return g
    return g


def _has_mirror_witness(grid, axis_col, axis_color):
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if c == axis_col or grid[r][c] in (0, axis_color):
                continue
            mc = 2 * axis_col - c
            if 0 <= mc < w and grid[r][mc] == 0:
                return True
    return False


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    h, w = len(grid), len(grid[0])
    full_cols = []
    for c in range(w):
        color = grid[0][c]
        if color != 0 and all(grid[r][c] == color for r in range(h)):
            full_cols.append((c, color))
    if len(full_cols) != 1:
        errors.append(f"expected exactly one full nonzero axis column, got {full_cols}")
        return errors
    axis_col, axis_color = full_cols[0]
    if any(grid[r][c] == axis_color for r in range(h) for c in range(w) if c != axis_col):
        errors.append("axis color must not appear off the axis column")
    off_axis = [(r, c) for r in range(h) for c in range(w)
                if c != axis_col and grid[r][c] not in (0, axis_color)]
    if not off_axis:
        errors.append("expected off-axis marks to mirror")
    if not _has_mirror_witness(grid, axis_col, axis_color):
        errors.append("expected at least one off-axis mark with an empty in-bounds mirror cell")
    return errors


def _build_pool(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 8, 12
    g = full_grid(h, w, 0)
    if name == "no_axis":
        for _ in range(8):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        return g
    if name == "two_axes":
        for r in range(h):
            g[r][3] = 4
            g[r][w - 4] = 4
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 4
        return g
    return g
