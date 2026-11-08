"""Generator for arc_puzzle_bank_twentieth21:M134.

A full wall of 8s receives straight shadows from every colored cell on one
side of the wall.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, orientation, texture.
Degenerates: no_wall, no_objects, both_sides.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6a8c2662e37c"
# 1.4.0: defect-lint identity_demo + axis-honesty — a right/below-side shape could
# sit FLUSH against the wall (no zeros to fill -> output == input); it now keeps a
# >=1 gap like the left/top side always did. AXES grid ranges made honest.
VERSION = "1.4.1"  # no_wall degenerate raised NameError (_BLOB undefined); inline the blob cells (defect-lint texture-crash)
TASK_ID = "6a8c2662e37c"
SUMMARY = "Non-wall colored cells cast horizontal or vertical shadows to an 8-wall row/column."

# Rivals: 'cast in only one direction regardless of wall orientation'
# refuted by ≥2 demos with different wall orientations. 'use wall
# color for shadow' refuted by any demo (shadow uses source colors).
# 'recolor object' refuted by any demo (object preserved).
# 'shadow only the first cell' refuted by ≥1 demo with multi-cell
# objects (all cast shadows).
# 4 demos with varied wall orientations + sides + colors.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "there is exactly one full row or column of color 8",
    "all nonzero non-8 cells lie on one side of the wall",
    "the wall and original object cells are preserved",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_wall", "no_objects", "both_sides")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7-9 easy / 8-11 med / 11-14 hard", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "7-9 easy / 8-12 med / 12-15 hard", "valid": "7..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "orientation":    {"type": "int", "default": "rng 0..1",
                       "valid": "0 vertical, 1 horizontal"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "wall_with_one_side_blob",
                       "valid": "wall_with_one_side_blob"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_wall|no_objects|both_sides"},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify one full 8-wall and at least one colored source object entirely
    on one side of that wall."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    full_rows_8 = [r for r in range(h) if all(grid[r][c] == 8 for c in range(w))]
    full_cols_8 = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    n_walls = len(full_rows_8) + len(full_cols_8)
    if n_walls != 1:
        errs.append(f"expected exactly one full-8 row/col wall, found {n_walls}")
        return errs
    objects = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)]
    if not objects:
        errs.append("no colored source cells to cast shadows")
        return errs
    if full_cols_8:
        wall = full_cols_8[0]
        sides = {"left" if c < wall else "right" if c > wall else "on_wall" for _r, c in objects}
    else:
        wall = full_rows_8[0]
        sides = {"above" if r < wall else "below" if r > wall else "on_wall" for r, _c in objects}
    if "on_wall" in sides or len(sides) != 1:
        errs.append("all colored source cells must lie strictly on one side of the wall")
    return errs


_SHAPES = [
    [(0, 0), (1, 0), (1, 1), (2, 1)],                       # S-tet (original)
    [(0, 0), (0, 1), (1, 0)],                               # L-tromino
    [(0, 0), (0, 1), (0, 2), (1, 1)],                       # T-tet
    [(0, 0), (1, 0), (2, 0), (2, 1)],                       # J-tet
    [(0, 0), (0, 1), (1, 1), (1, 2)],                       # Z-tet
    [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)],               # zigzag
    [(0, 0), (0, 1), (0, 2), (0, 3)],                       # I4
    [(0, 0), (1, 0), (1, 1), (2, 0)],                       # T-rot
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 7, 9, 7, 9
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 11, 14, 12, 15
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 11, 8, 12
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    orientation = ctx.draw_int("orientation", 0, 1)
    g = full_grid(h, w, 0)
    # Palette now includes colors 1, 6, 7, 9 (was {2,3,4,5} only); avoid 0 (bg) and 8 (wall).
    color_pool = [1, 2, 3, 4, 5, 6, 7, 9]

    # The wall sits at randint(s+1, dim-s-2): for that range to be non-empty the
    # grid must satisfy dim >= 2*s+3 along the cross axis (s = footprint width
    # for a vertical wall, height for a horizontal one). The wide I4 shape (sw=4)
    # needs w>=11 — impossible on the easy band's 7..9 grids — so it gave an
    # empty randint. Restrict the shape draw to the footprints that actually fit
    # the drawn orientation + grid (fall back to all shapes for tiny overrides).
    def _fits(s):
        ssh = max(r for r, _ in s) + 1
        ssw = max(c for _, c in s) + 1
        if orientation == 0:
            return w >= 2 * ssw + 3 and h >= ssh
        return h >= 2 * ssh + 3 and w >= ssw
    feasible = [s for s in _SHAPES if _fits(s)] or _SHAPES
    shape = rng.choice(feasible)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    rng.shuffle(color_pool)
    if orientation == 0:
        # vertical wall
        wall = rng.randint(sw + 1, max(sw + 1, w - sw - 2))
        for r in range(h):
            g[r][wall] = 8
        side_left = rng.choice([True, False])
        top = rng.randint(0, max(0, h - sh))
        if side_left:
            left = rng.randint(0, max(0, wall - sw - 1))
        else:
            # >=1 empty column between wall and shape, else there is nothing
            # for the rule to fill (identity demo).
            left = rng.randint(min(wall + 2, w - sw), max(wall + 2, w - sw))
        for i, (dr, dc) in enumerate(shape):
            g[top + dr][left + dc] = color_pool[i % len(color_pool)]
    else:
        # horizontal wall
        wall = rng.randint(sh + 1, max(sh + 1, h - sh - 2))
        for c in range(w):
            g[wall][c] = 8
        side_top = rng.choice([True, False])
        if side_top:
            top = rng.randint(0, max(0, wall - sh - 1))
        else:
            # >=1 empty row between wall and shape (see vertical-wall note).
            top = rng.randint(min(wall + 2, h - sh), max(wall + 2, h - sh))
        left = rng.randint(0, max(0, w - sw))
        for i, (dr, dc) in enumerate(shape):
            g[top + dr][left + dc] = color_pool[i % len(color_pool)]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_wall":
        # Object but no 8-wall — rule has no shadow target row/column.
        for dr, dc in ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)):
            g[2 + dr][2 + dc] = 4
        return g
    if name == "no_objects":
        # Wall but no colored cells — rule has nothing to project shadows
        # from.
        for r in range(h): g[r][4] = 8
        return g
    if name == "both_sides":
        # 8-wall with colored cells on BOTH sides — rule's "all on one
        # side" precondition fails; shadow direction is ambiguous.
        for r in range(h): g[r][4] = 8
        g[2][1] = 4; g[2][2] = 5
        g[5][6] = 6; g[5][7] = 7
        return g
    return g
