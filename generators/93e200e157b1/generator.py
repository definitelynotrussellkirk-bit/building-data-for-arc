"""Generator for ff28f65a.

Rule: count solid 2×2 blocks of any non-zero color; place 1s at the
first N positions of (0,0),(0,2),(1,1),(2,0),(2,2).

Combinatorial axes (8): grid_h/w, n_blocks, palette_size, palette_kind,
position_bias, block_color_distribution, anchor_corner, asymmetry_force.
Degenerates: no_blocks, all_blocks, single_color_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "93e200e157b1"
VERSION = "1.2.1"  # add self_check  # distinct=5: output is f(n)=first min(n,5) dots of a fixed 3x3 X-pattern, so distinct ceiling = 6 (n=0,1,2,3,4,>=5). Generator drew n_blocks 1..5 (missed n=0). Widen medium n_blocks to 0..6 -> distinct 5->6 (intrinsic ceiling; out_sh=1 is rule-fixed 3x3).
TASK_ID = "93e200e157b1"
SUMMARY = "0-6 solid 2x2 blocks; rule encodes count n (capped at 5) as a 3x3 X-pattern. Output is f(n): distinct ceiling is 6 (n in {0,1,2,3,4,>=5}); output is always 3x3 (rule-fixed)."

INVARIANTS = [
    "1-5 solid 2×2 non-bg blocks",
    "no two blocks overlap or touch (8-conn separation)",
    "no color 1 in input (rule writes 1 for output)",
]

POSITION_BIAS = ("center", "spread", "edge", "corners")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("no_blocks", "all_blocks", "single_color_only")
HELPFUL_TEXTURES = POSITION_BIAS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 6..14", "valid": "4..18"},
    "grid_w":            {"type": "int", "default": "rng 6..14", "valid": "4..18"},
    "n_blocks":          {"type": "int", "default": "rng 1..5", "valid": "0..7"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 1..3", "valid": "1..7"},
    "position_bias":     {"type": "str", "default": "rng helpful",
                          "valid": "|".join(POSITION_BIAS)},
    "block_color_distribution": {"type": "str", "default": "rng same|distinct",
                                 "valid": "same|distinct"},
    "anchor_corner":     {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "texture":           {"type": "str", "default": "alias for position_bias",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: no color-1 in input (rule writes 1); input is valid 0-bg grid."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    has_1 = any(grid[r][c] == 1 for r in range(h) for c in range(w))
    if has_1:
        return ["color 1 found in input (rule writes 1 for output; input should not have it)"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 4, 7
    elif difficulty == "hard":
        h_lo, h_hi = 12, 18
    else:
        h_lo, h_hi = 6, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_blocks = int(overrides.get("n_blocks",
                                 ctx.draw_int("n_blocks", 0, 6)))
    n_blocks = max(0, min(7, n_blocks))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [5, 7, 8]
    elif palette_kind == "small":
        pool = [2, 3]
    else:
        pool = [2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 1, 3)))
    palette = pool[:max(1, n_palette)]
    color_dist = overrides.get("block_color_distribution",
                               ctx.draw_choice("block_color_distribution",
                                               ["same", "distinct"]))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIAS)))
    g = full_grid(h, w, 0)
    occupied = [[False] * w for _ in range(h)]
    placed = 0
    for _ in range(n_blocks * 8):
        if placed >= n_blocks:
            break
        r, c = _pick_pos(bias, h, w, rng)
        if any(occupied[rr][cc]
               for rr in range(max(0, r - 1), min(h, r + 3))
               for cc in range(max(0, c - 1), min(w, c + 3))):
            continue
        if r + 1 >= h or c + 1 >= w:
            continue
        if color_dist == "distinct" and len(palette) > 1:
            color = palette[placed % len(palette)]
        else:
            color = palette[0]
        draw_rect(g, r, c, 2, 2, color)
        for rr in range(max(0, r - 1), min(h, r + 3)):
            for cc in range(max(0, c - 1), min(w, c + 3)):
                occupied[rr][cc] = True
        placed += 1
    return g


def _pick_pos(bias, h, w, rng):
    if bias == "center":
        return (h - 2) // 2 + rng.randint(-1, 1), (w - 2) // 2 + rng.randint(-1, 1)
    if bias == "edge":
        choices = [(0, rng.randint(0, w - 2)),
                   (h - 2, rng.randint(0, w - 2)),
                   (rng.randint(0, h - 2), 0),
                   (rng.randint(0, h - 2), w - 2)]
        return rng.choice(choices)
    if bias == "corners":
        return rng.choice([(0, 0), (0, w - 2), (h - 2, 0), (h - 2, w - 2)])
    return rng.randint(0, h - 2), rng.randint(0, w - 2)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    if name == "no_blocks":
        return g
    if name == "all_blocks":
        for r in range(0, h - 1, 4):
            for c in range(0, w - 1, 4):
                draw_rect(g, r, c, 2, 2, color)
        return g
    if name == "single_color_only":
        if h >= 4 and w >= 4:
            draw_rect(g, 1, 1, 2, 2, color)
            draw_rect(g, h - 3, w - 3, 2, 2, color)
        return g
    return g
