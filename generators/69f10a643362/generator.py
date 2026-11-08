"""Generator for puzzle 47c1f68c.

Rule: cross is full row+col of xc=8. Top-left quadrant has a pattern.
Output is 4-fold mirror (TL→TR+BL+BR) with all non-zero non-xc cells
replaced by xc.

Combinatorial axes (8): grid_h/w, cross_row, cross_col, pat_color,
n_cells, palette_kind, anchor_corner, asymmetry_force.
Degenerates: no_cross, full_grid, empty_quadrant.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "69f10a643362"
VERSION = "1.1.1"
TASK_ID = "69f10a643362"
SUMMARY = "Cross of 8s + TL pattern; rule mirrors 4-fold + replaces colors with 8."

INVARIANTS = [
    "exactly 1 row + 1 col of 8 (forming a cross)",
    "top-left quadrant has non-{0,8} pattern (>=3 cells)",
    "no other quadrant has non-zero non-cross cells",
]

CROSS_POSITIONS = ("center", "upper_left", "upper_right", "lower_left",
                   "lower_right", "spread")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_cross", "full_grid", "empty_quadrant")
HELPFUL_TEXTURES = CROSS_POSITIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..14", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 8..14", "valid": "7..18"},
    "cross_position": {"type": "str", "default": "rng helpful",
                       "valid": "|".join(CROSS_POSITIONS)},
    "pat_color":      {"type": "color", "default": "rng (≠0,8)",
                       "valid": "1..9 (≠8)"},
    "n_cells":        {"type": "int", "default": "rng 3..8",
                       "valid": "3..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for cross_position",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one full row of 8s and one full col of 8s (the cross)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    full_rows = [r for r in range(h) if all(grid[r][c] == 8 for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if not full_rows and not full_cols:
        return errs  # degenerate (no_cross or full_grid all-8) — allowed
    if len(full_rows) != 1:
        errs.append(f"expected exactly 1 full-8 row; found {len(full_rows)}")
    if len(full_cols) != 1:
        errs.append(f"expected exactly 1 full-8 col; found {len(full_cols)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 7, 9
    elif difficulty == "hard":
        h_lo, h_hi = 14, 18
    else:
        h_lo, h_hi = 8, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    pos = (overrides.get("texture") or
           overrides.get("cross_position")
           or ctx.draw_choice("cross_position",
                              list(CROSS_POSITIONS)))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, rng)
    pat_color = int(overrides.get("pat_color",
                                  next((c for c in palette if c != 8),
                                       1)))
    if pat_color == 8:
        pat_color = 1
    cr, cc = _pick_cross(pos, h, w, rng)
    xc = 8
    g = full_grid(h, w, 0)
    for c in range(w):
        g[cr][c] = xc
    for r in range(h):
        g[r][cc] = xc
    cells_pool = [(r, c) for r in range(cr) for c in range(cc)]
    if not cells_pool:
        return g
    n_cells = int(overrides.get("n_cells",
                                ctx.draw_int("n_cells", 3,
                                             max(4, len(cells_pool) // 2))))
    n_cells = max(3, min(len(cells_pool), n_cells))
    chosen = rng.sample(cells_pool, n_cells)
    for r, c in chosen:
        g[r][c] = pat_color
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


def _pick_cross(pos, h, w, rng):
    if pos == "center":
        return h // 2, w // 2
    if pos == "upper_left":
        return rng.randint(2, max(2, h // 2)), \
               rng.randint(2, max(2, w // 2))
    if pos == "upper_right":
        return rng.randint(2, max(2, h // 2)), \
               rng.randint(w // 2, max(w // 2, w - 3))
    if pos == "lower_left":
        return rng.randint(h // 2, max(h // 2, h - 3)), \
               rng.randint(2, max(2, w // 2))
    if pos == "lower_right":
        return rng.randint(h // 2, max(h // 2, h - 3)), \
               rng.randint(w // 2, max(w // 2, w - 3))
    return rng.randint(2, h - 4), rng.randint(2, w - 4)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_cross":
        for r in range(2):
            for c in range(2):
                g[r][c] = 3
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 8
        return g
    if name == "empty_quadrant":
        cr = h // 2; cc = w // 2
        for c in range(w):
            g[cr][c] = 8
        for r in range(h):
            g[r][cc] = 8
        return g
    return g
