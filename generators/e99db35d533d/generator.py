"""Generator for additional_bank:E2.

Rule: blue components touching the top border are recolored to yellow.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_top_touching, all_top_touching, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e99db35d533d"
VERSION = "2.0.0"  # was rigid 1 fixed top-blob + 1 interior, with bbox-only separation that could let interior 4-touch the top blob (merge -> all recolored, contrast lost). Rewrite: MULTIPLE top-touching AND MULTIPLE interior blobs, varied shapes, full 8-halo separation guaranteeing distinct components
TASK_ID = "e99db35d533d"
SUMMARY = (
    "0-bg grid with several separated color-1 (blue) components: some touch "
    "row 0, some do not. Rule: every blue component with a cell in row 0 is "
    "recolored to 4 (yellow); interior components stay blue. Component count, "
    "shapes, positions and grid size vary; top-touching and interior counts "
    "both vary (>=1 of each guaranteed)."
)

INVARIANTS = [
    "background is 0",
    "source objects are color 1",
    ">=1 blue component touches row 0 (gets recolored to 4)",
    ">=1 blue component does NOT touch row 0 (stays blue)",
    "every component is 8-halo separated -> distinct 4-conn components (no merge)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_top_touching", "all_top_touching", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..15 by diff", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 7..16 by diff", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_top":          {"type": "int", "default": "rng 1..3 by diff", "valid": "1..4"},
    "n_interior":     {"type": "int", "default": "rng 1..4 by diff", "valid": "1..4"},
    "blob_size":      {"type": "int", "default": "rng 2..6 by diff", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "top_and_interior",
                       "valid": "top_and_interior"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _halo(cells):
    return {(r + dr, c + dc) for (r, c) in cells
            for dr in (-1, 0, 1) for dc in (-1, 0, 1)}


def _shape(rng, size):
    """A normalized connected blob of up to `size` cells (top-left at 0,0)."""
    side = size + 1
    blob = grow_blob(rng, side, side, set(), size)
    if not blob:
        return [(0, 0)]
    mr = min(r for r, _ in blob); mc = min(c for _, c in blob)
    return [(r - mr, c - mc) for r, c in blob]


def _place(g, rng, h, w, occupied, size, top_touch):
    """Place a halo-separated blob; top_touch -> includes a row-0 cell,
    else min-row >= 2 (no row-0 cell). Returns True on success."""
    for _ in range(60):
        norm = _shape(rng, size)
        bh = max(r for r, _ in norm) + 1
        bw = max(c for _, c in norm) + 1
        if bw > w or bh > h:
            continue
        c0 = rng.randint(0, w - bw)
        if top_touch:
            r0 = 0                                 # min-row cell lands in row 0
        else:
            if h - bh < 2:
                continue
            r0 = rng.randint(2, h - bh)            # entirely below row 0
        placed = {(r0 + r, c0 + c) for r, c in norm}
        if placed & occupied or _halo(placed) & occupied:
            continue
        for (r, c) in placed:
            g[r][c] = 1
        occupied |= placed
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 8, 7, 9
        t_lo, t_hi, i_lo, i_hi, s_lo, s_hi = 1, 2, 1, 2, 2, 4
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 11, 15, 12, 16
        t_lo, t_hi, i_lo, i_hi, s_lo, s_hi = 2, 3, 2, 4, 3, 6
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 11, 9, 12
        t_lo, t_hi, i_lo, i_hi, s_lo, s_hi = 1, 3, 2, 3, 3, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    n_top = int(overrides.get("n_top", ctx.draw_int("n_top", t_lo, t_hi)))
    n_int = int(overrides.get("n_interior", ctx.draw_int("n_interior", i_lo, i_hi)))
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    occupied = set()
    top_ok = 0
    for i in range(max(1, n_top)):
        sz = ctx.draw_int(f"ts{i}", s_lo, s_hi)
        if _place(g, rng, h, w, occupied, sz, top_touch=True):
            top_ok += 1
    int_ok = 0
    for i in range(max(1, n_int)):
        sz = ctx.draw_int(f"is{i}", s_lo, s_hi)
        if _place(g, rng, h, w, occupied, sz, top_touch=False):
            int_ok += 1
    # guarantee >=1 of each (small grids can fail a few attempts)
    if top_ok == 0:
        _place(g, rng, h, w, occupied, 2, top_touch=True)
    if int_ok == 0:
        _place(g, rng, h, w, occupied, 2, top_touch=False)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_top_touching":
        # all blue components in interior, none on row 0 → rule no-op, no contrast
        for r, c in [(3, 2), (3, 3), (4, 2)]:
            g[r][c] = 1
        for r, c in [(5, 5), (5, 6), (6, 6)]:
            g[r][c] = 1
        return g
    if name == "all_top_touching":
        # all blue components touch row 0 → rule recolors all to yellow, no contrast
        for r, c in [(0, 1), (1, 1), (0, 2)]:
            g[r][c] = 1
        for r, c in [(0, 5), (1, 5), (0, 6), (1, 6)]:
            g[r][c] = 1
        return g
    if name == "no_blobs":
        # empty grid → no objects to recolor, rule no-op
        return g
    return g
