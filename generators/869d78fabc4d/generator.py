"""Generator for b3a901da.

Rule: 9-line splits grid; rule applies gravity-down to each half.

Combinatorial axes (8): grid_h/w, palette_kind, position_bias, n_left,
n_right, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_divider, no_cells, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "869d78fabc4d"
VERSION = "2.0.0"
TASK_ID = "869d78fabc4d"
SUMMARY = (
    "0-bg grid (h~6-8, w~7-9) "
    "with: (a) ONE FULL-"
    "HEIGHT COLOR-9 (maroon) "
    "DIVIDER COLUMN at col "
    "w//2 splitting the grid "
    "into LEFT and RIGHT "
    "halves; (b) 2-3 SCATTERED "
    "CELLS in the LEFT half "
    "(cols 0..div-1) in color "
    "C_L from a palette (warm/"
    "cool/broad/primary); (c) "
    "2-3 SCATTERED CELLS in "
    "the RIGHT half (cols "
    "div+1..w-1) in a DISTINCT "
    "color C_R. Rule (GRAVITY-"
    "DOWN PER HALF): identify "
    "the FULL 9-DIVIDER. "
    "For EACH HALF "
    "INDEPENDENTLY: APPLY "
    "GRAVITY DOWNWARD — every "
    "non-0, non-9 cell falls "
    "to the BOTTOM of its "
    "column within its half "
    "(stacking on the floor "
    "or on cells already at "
    "the bottom). Empty cells "
    "stay 0. The 9-divider "
    "stays. Net: both halves "
    "gravity-fall to the "
    "bottom independently."
)

INVARIANTS = [
    "exactly one full-column 9-divider",
    "scattered cells in both halves (gravitate to bottom)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_divider", "no_cells", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng",
                       "valid": "scattered|spread|rng"},
    "n_left":         {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "n_right":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
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
        h_lo, h_hi, w_lo, w_hi = 5, 6, 5, 7
        nl_lo, nl_hi = 1, 2
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 9, 12, 10, 14
        nl_lo, nl_hi = 3, 5
    else:
        h_lo, h_hi, w_lo, w_hi = 6, 8, 7, 9
        nl_lo, nl_hi = 2, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    div = w // 2
    for r in range(h):
        g[r][div] = 9
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, rng)
    color_l = pal[0] if pal else 2
    color_r = pal[1] if len(pal) > 1 else 6
    n_l = int(overrides.get("n_left",
                            ctx.draw_int("n_left", nl_lo, nl_hi)))
    n_r = int(overrides.get("n_right",
                            ctx.draw_int("n_right", nl_lo, nl_hi)))
    placed = 0
    while placed < n_l:
        r = rng.randint(0, h - 1); c = rng.randint(0, div - 1)
        if g[r][c] == 0:
            g[r][c] = color_l; placed += 1
        if placed > n_l + 30:
            break
    placed = 0
    while placed < n_r:
        r = rng.randint(0, h - 1); c = rng.randint(div + 1, w - 1)
        if g[r][c] == 0:
            g[r][c] = color_r; placed += 1
        if placed > n_r + 30:
            break
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8]
    pool = [c for c in pool if c != 9]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "no_divider":
        g[2][2] = 2
        g[3][6] = 6
        return g
    if name == "no_cells":
        for r in range(h):
            g[r][4] = 9
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 9
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not (5 <= h <= 12 and 5 <= w <= 14):
        msgs.append("grid dimensions outside generated range")
    divs = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(divs) != 1:
        msgs.append("expected exactly one full-height color-9 divider")
        return msgs
    div = divs[0]
    if div == 0 or div == w - 1:
        msgs.append("divider must split non-empty left and right halves")
    extra9 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9 and c != div]
    if extra9:
        msgs.append("color 9 appears outside the divider")
    left = [(r, c) for r in range(h) for c in range(div) if grid[r][c] not in (0, 9)]
    right = [(r, c) for r in range(h) for c in range(div + 1, w) if grid[r][c] not in (0, 9)]
    if not left or not right:
        msgs.append("both halves need at least one movable cell")
    lcols = {grid[r][c] for r, c in left}
    rcols = {grid[r][c] for r, c in right}
    if lcols and rcols and lcols & rcols:
        msgs.append("left/right movable colors should be distinct")
    return msgs
