"""Generator for 5783df64.

Rule: 3*bh × 3*bw grid divided into 3×3 sub-blocks. Output is 3×3:
each cell = first non-zero in row-major scan of its sub-block.

Combinatorial axes (8): block_h, block_w, palette_kind,
n_cells_per_block, cell_position, decoy_density,
position_distribution, fg_density.
Degenerates: empty_grid, all_filled, single_block_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d1c037cda16e"
VERSION = "1.1.1"
TASK_ID = "d1c037cda16e"
SUMMARY = "3*bh × 3*bw grid; rule emits 3×3 of first non-zero per sub-block."

INVARIANTS = [
    "background is 0",
    "h % 3 == 0 and w % 3 == 0",
    "each of the 9 sub-blocks has >=1 non-zero cell",
    "the 9 sub-blocks reveal 9 different colors (so output is 9-colored)",
]

POSITION_DISTRIBUTIONS = ("random", "row_aligned", "diag", "first_cell",
                          "center", "scattered")
DEGENERATE_TEXTURES = ("empty_grid", "all_filled", "single_block_only")
HELPFUL_TEXTURES = POSITION_DISTRIBUTIONS

AXES = {
    "block_h":            {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "block_w":            {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "n_cells_per_block":  {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "position_distribution": {"type": "str", "default": "rng helpful",
                              "valid": "|".join(POSITION_DISTRIBUTIONS)},
    "palette_kind":       {"type": "str", "default": "rng all9|broad|small",
                           "valid": "all9|broad|small"},
    "fg_density":         {"type": "float", "default": "rng 0..0.05",
                           "valid": "0..0.1"},
    "decoy_density":      {"type": "float", "default": "0", "valid": "0..0.05"},
    "anchor_first":       {"type": "bool", "default": "false", "valid": "true|false"},
    "texture":            {"type": "str", "default": "alias for position_distribution",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: h%3==0 and w%3==0; each of the 9 sub-blocks has ≥1 non-zero cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    if h % 3 != 0:
        errs.append(f"grid height {h} is not divisible by 3")
    if w % 3 != 0:
        errs.append(f"grid width {w} is not divisible by 3")
    if errs:
        return errs
    bh, bw = h // 3, w // 3
    for bi in range(3):
        for bj in range(3):
            r0, c0 = bi * bh, bj * bw
            if not any(grid[r0 + dr][c0 + dc] != 0
                       for dr in range(bh) for dc in range(bw)):
                errs.append(f"sub-block ({bi},{bj}) is all-zero")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        bh_lo, bh_hi = 2, 2
    elif difficulty == "hard":
        bh_lo, bh_hi = 4, 6
    else:
        bh_lo, bh_hi = 2, 4
    bh = ctx.draw_int("block_h", bh_lo, bh_hi)
    bw = ctx.draw_int("block_w", bh_lo, bh_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], bh, bw, rng)
    h = 3 * bh
    w = 3 * bw
    pos_dist = (overrides.get("texture") or
                overrides.get("position_distribution")
                or ctx.draw_choice("position_distribution",
                                   list(POSITION_DISTRIBUTIONS)))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 ["all9", "broad", "small"]))
    if palette_kind == "all9":
        pal_pool = list(range(1, 10))
    elif palette_kind == "broad":
        pal_pool = [1, 2, 3, 4, 5, 6, 7, 8]
    else:
        pal_pool = [1, 2, 3, 4]
    pal = list(pal_pool)
    rng.shuffle(pal)
    if len(pal) < 9:
        extra = [c for c in range(1, 10) if c not in pal]
        rng.shuffle(extra)
        pal += extra
    pal = pal[:9]
    g = full_grid(h, w, 0)
    blocks = [(r0, c0) for r0 in range(0, h, bh) for c0 in range(0, w, bw)]
    for i, (r0, c0) in enumerate(blocks):
        dr, dc = _pick_block_pos(pos_dist, bh, bw, rng)
        g[r0 + dr][c0 + dc] = pal[i]
    if bool(overrides.get("anchor_first", False)):
        g[0][0] = pal[0]
    return g


def _pick_block_pos(dist, bh, bw, rng):
    if dist == "first_cell":
        return 0, 0
    if dist == "center":
        return bh // 2, bw // 2
    if dist == "diag":
        k = min(bh - 1, bw - 1)
        return rng.randint(0, k), rng.randint(0, k)
    if dist == "row_aligned":
        return 0, rng.randint(0, bw - 1)
    if dist == "scattered":
        return rng.randint(0, bh - 1), rng.randint(0, bw - 1)
    return rng.randint(0, bh - 1), rng.randint(0, bw - 1)


def _draw_from_degenerate(name, bh, bw, rng):
    h = 3 * bh
    w = 3 * bw
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        return g
    if name == "all_filled":
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "single_block_only":
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        g[0][0] = color
        return g
    return g
