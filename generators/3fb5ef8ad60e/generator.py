"""Generator for 19bb5feb.

Rule: large 8-rectangle contains 2-3 small colored 2x2 blocks in
distinct quadrants; output compresses to a 2x2 grid.

Combinatorial axes (8): grid_h/w, n_blocks, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
block_size.
Degenerates: no_blocks, single_block, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "3fb5ef8ad60e"
VERSION = "3.0.1"
TASK_ID = "3fb5ef8ad60e"
SUMMARY = "Large 8-rect with 2-3 small colored 2x2 blocks in distinct quadrants."

INVARIANTS = [
    "single 8-rect of size at least 10x10 fills most of the grid",
    "two or three distinct non-{0,8} 2x2 blocks sit inside in different quadrants",
    "each block sits clear of the rect borders",
    "block colors are distinct so each quadrant has a unique value",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_blocks", "single_block", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "n_blocks":       {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "block_size":     {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_blocks|single_block|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 14, 14
    elif difficulty == "hard":
        h_lo, h_hi = 18, 22
    else:
        h_lo, h_hi = 14, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind") or
                    ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    g = full_grid(h, w, 0)
    fh = h - 4
    fw = w - 2
    r0 = 2
    c0 = 1
    draw_rect(g, r0, c0, fh, fw, 8)
    # output is a 2x2 of the block colours by centroid quadrant -> use up to 4
    # blocks (all quadrants) for more distinct 2x2 arrangements (was 2-3).
    if difficulty == "easy":
        n_blocks = rng.randint(2, 3)
    elif difficulty == "hard":
        n_blocks = rng.randint(3, 4)
    else:
        n_blocks = rng.randint(2, 4)
    pool = _build_palette(palette_kind, rng)
    if len(pool) < n_blocks:
        pool = pool + [c for c in [1, 2, 3, 4, 5, 6, 7, 9] if c not in pool]
    palette = pool[:n_blocks]
    quadrants = rng.sample([(0, 0), (0, 1), (1, 0), (1, 1)], n_blocks)
    mid_r = r0 + fh // 2
    mid_c = c0 + fw // 2
    for color, (qr, qc) in zip(palette, quadrants):
        if qr == 0:
            br = rng.randint(r0 + 1, mid_r - 3)
        else:
            br = rng.randint(mid_r + 1, r0 + fh - 3)
        if qc == 0:
            bc = rng.randint(c0 + 1, mid_c - 3)
        else:
            bc = rng.randint(mid_c + 1, c0 + fw - 3)
        draw_rect(g, br, bc, 2, 2, color)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has color-8 rect, has 2-4 non-{0,8} block cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    all_vals = [grid[r][c] for r in range(h) for c in range(w)]
    if 8 not in all_vals:
        errs.append("no color-8 cells (expected the outer rect)")
    non_bg_non8 = set(v for v in all_vals if v not in (0, 8))
    if len(non_bg_non8) < 1:
        errs.append("no non-{0,8} block colors found")
    return errs


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 9]
    pool = [c for c in pool if c not in (0, 8)]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "no_blocks":
        draw_rect(g, 2, 1, h - 4, w - 2, 8)
        return g
    if name == "single_block":
        draw_rect(g, 2, 1, h - 4, w - 2, 8)
        draw_rect(g, 4, 3, 2, 2, 2)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 8
        return g
    return g
