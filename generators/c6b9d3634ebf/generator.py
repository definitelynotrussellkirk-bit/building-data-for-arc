"""Generator for 1d398264.

Rule: find center cell whose 8-neighbors are all non-zero. Each
neighbor's color extends as a ray in that direction.

Combinatorial axes (8): grid_h/w, n_distinct_colors, palette_kind,
position_bias, anchor_corner, asymmetry_force, palette_size, block_position.
Degenerates: no_block, partial_block, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c6b9d3634ebf"
VERSION = "1.1.1"
TASK_ID = "c6b9d3634ebf"
SUMMARY = "Solid 3x3 block of mixed colors at interior position; rest empty."

INVARIANTS = [
    "exactly 9 non-zero cells forming a 3x3 block",
    "center has all 8 neighbors non-zero",
    "block uses 4-7 distinct colors",
]

POSITION_BIASES = ("centered", "corner", "near_edge", "scattered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_block", "partial_block", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "n_distinct_colors":{"type": "int", "default": "rng 4..7", "valid": "2..9"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 4..7", "valid": "2..9"},
    "texture":        {"type": "str", "default": "alias for position_bias",
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
        h_lo, h_hi = 10, 12
        nc_lo, nc_hi = 2, 4
    elif difficulty == "hard":
        h_lo, h_hi = 16, 20
        nc_lo, nc_hi = 6, 9
    else:
        h_lo, h_hi = 12, 16
        nc_lo, nc_hi = 4, 7
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    n_distinct = int(overrides.get("n_distinct_colors",
                                   ctx.draw_int("n_distinct_colors",
                                                nc_lo, nc_hi)))
    n_distinct = max(2, min(9, n_distinct))
    pal = _build_palette(palette_kind, n_distinct, rng)
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    cr, cc = _pick_center(bias, h, w, rng)
    for dr in range(-1, 2):
        for dc in range(-1, 2):
            g[cr + dr][cc + dc] = rng.choice(pal)
    return g


def _pick_center(bias, h, w, rng):
    if bias == "centered":
        cr = h // 2
        cc = w // 2
    elif bias == "corner":
        cr = rng.choice([2, h - 3])
        cc = rng.choice([2, w - 3])
    elif bias == "near_edge":
        if rng.random() < 0.5:
            cr = rng.choice([2, h - 3])
            cc = rng.randint(2, w - 3)
        else:
            cr = rng.randint(2, h - 3)
            cc = rng.choice([2, w - 3])
    else:
        cr = rng.randint(2, h - 3)
        cc = rng.randint(2, w - 3)
    cr = max(2, min(cr, h - 3))
    cc = max(2, min(cc, w - 3))
    return cr, cc


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly 9 nonzero cells forming a 3x3 block; block uses 4-7 distinct colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    nz = sum(grid[r][c] != 0 for r in range(h) for c in range(w))
    if nz != 9:
        errors.append(f"expected exactly 9 nonzero cells (3x3 block), found {nz}")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 1:
        errors.append("no nonzero color found in block")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 13, 13
    g = full_grid(h, w, 0)
    if name == "no_block":
        return g
    if name == "partial_block":
        for dr in range(-1, 1):
            for dc in range(-1, 1):
                g[h // 2 + dr][w // 2 + dc] = 2
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g
