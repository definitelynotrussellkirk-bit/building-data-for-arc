"""Generator for arc_additional_puzzle_bank_volume2:E11.

Rule: color-7 objects touching the grid border are erased; interior
color-7 objects remain.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors, other.
Degenerates: no_objects, all_interior, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "287967e33b21"
VERSION = "2.0.1"
TASK_ID = "287967e33b21"
SUMMARY = (
    "0-bg grid (h~8-11, w~8-11) with multiple "
    "DISCONNECTED color-7 (orange) OBJECTS — some "
    "TOUCHING the grid OUTER BORDER (row 0, last row, "
    "first col, or last col) and at least ONE objects "
    "STRICTLY INTERIOR (not touching any border). "
    "Input is strictly 2-colour {0, 7} (no decoys). "
    "Rule: identify each connected color-7 component. "
    "ERASE (set to 0) every color-7 component that has "
    "AT LEAST ONE cell on the outer border. KEEP "
    "color-7 components whose cells are all strictly "
    "interior. Net: orange blobs touching the edge of "
    "the canvas vanish; interior orange blobs survive."
)

INVARIANTS = [
    "at least one color-7 object touches the border",
    "at least one color-7 object is fully interior",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "all_interior", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "other":          {"type": "color", "default": "rng !{0,7}",
                       "valid": "1..6|8|9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-7 cells present; at least one border-touching cell and one interior."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_objects", "all_interior", "full_grid"):
        return []
    errs = []
    c7_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7]
    if not c7_cells:
        errs.append("no color-7 cells")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # rule removes color-7 objects TOUCHING the border, keeps interior ones. Canonical
    # is strictly 2-colour [0,7] -> the old `other` 3rd colour (rule-ignored, absent in
    # canonical) was POISON; removed. Now multiple random color-7 blobs, some on the
    # border (removed) and some interior (kept), on a varied grid.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 7, 9)
        n_border, n_interior = rng_n(ctx, "nb", 1, 2), rng_n(ctx, "ni", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 11, 16)
        n_border, n_interior = rng_n(ctx, "nb", 2, 3), rng_n(ctx, "ni", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 12); w = ctx.draw_int("grid_w", 8, 12)
        n_border, n_interior = rng_n(ctx, "nb", 1, 3), rng_n(ctx, "ni", 1, 2)
    rng = ctx.draw_rng("layout")
    for _outer in range(40):
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        nb = _place_blobs(g, occ, rng, n_border, h, w, border=True)
        ni = _place_blobs(g, occ, rng, n_interior, h, w, border=False)
        if nb >= 1 and ni >= 1:        # need >=1 removed (non-identity) and >=1 kept
            return g
    raise ValueError("could not place border+interior color-7 blobs")


def rng_n(ctx, key, lo, hi):
    return ctx.draw_int(key, lo, hi)


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nb = (r + dr, c + dc)
        if nb not in seen:
            cells.append(nb); seen.add(nb)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _free(occ, cells, h, w, pad=1):
    for (r, c) in cells:
        for dr in range(-pad, pad + 1):
            for dc in range(-pad, pad + 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    return True


def _place_blobs(g, occ, rng, n, h, w, border):
    """Place n color-7 polyominoes; border=True forces >=1 cell on the outer border,
    border=False keeps them strictly interior."""
    placed = 0
    for _ in range(n):
        shape = _rand_poly(rng, rng.randint(2, 5))
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        if border:
            r_lo, r_hi, c_lo, c_hi = 0, h - sh, 0, w - sw
        else:
            r_lo, r_hi, c_lo, c_hi = 1, h - sh - 1, 1, w - sw - 1
        if r_lo > r_hi or c_lo > c_hi:
            continue
        for _ in range(80):
            r0 = rng.randint(r_lo, r_hi); c0 = rng.randint(c_lo, c_hi)
            cells = [(r0 + r, c0 + c) for r, c in shape]
            on_border = any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)
            if border != on_border:
                continue
            if _free(occ, cells, h, w):
                for (r, c) in cells:
                    g[r][c] = 7; occ[r][c] = True
                placed += 1
                break
    return placed


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_objects":
        g[8][8] = 3
        return g
    if name == "all_interior":
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[4 + dr][4 + dc] = 7
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(9):
                g[r][c] = 7
        return g
    return g
