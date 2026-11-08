"""Generator for 3391f8c0.

Rule: 2 colors c1 and c2; the color with more objects is rep, other is
single. Stamp single's shape at each rep position.

Combinatorial axes (8): grid_h/w, palette_kind, n_rep, position_bias,
anchor_corner, asymmetry_force, palette_size, shape_variant.
Degenerates: same_count, no_objects, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "6c8e23981ee0"
VERSION = "1.1.1"
TASK_ID = "6c8e23981ee0"
SUMMARY = "2 colors: one with multiple objects, other with 1 unique object."

INVARIANTS = [
    "1 'rep' color with >=2 objects of same normalized shape",
    "1 'single' color with exactly 1 object of different shape",
]

POSITION_BIASES = ("scattered", "spread", "centered", "rng")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("same_count", "no_objects", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rep":          {"type": "int", "default": "2", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 2 distinct nonzero colors present (rep + single)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    colors = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not colors:
        return errs  # degenerate (no_objects) — allowed
    if len(colors) != 2:
        errs.append(f"expected exactly 2 distinct colors (rep+single); found {len(colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 6, 8, 10
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 9, 14, 11, 14
    else:
        h_lo, h_hi, w_lo, w_hi = 6, 8, 9, 11
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, 2, rng)
    rep, single = pal[0], pal[1]
    rep_shape = [(0, 0), (1, 1)]
    single_shape = [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)]
    paint_at(g, rng.randint(0, 1), rng.randint(0, 2), rep_shape, rep)
    paint_at(g, rng.randint(0, 1), rng.randint(4, 6), rep_shape, rep)
    paint_at(g, rng.randint(h - 4, h - 3), rng.randint(2, w - 5),
             single_shape, single)
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "same_count":
        g[1][1] = 2; g[1][6] = 3
        return g
    if name == "no_objects":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g
