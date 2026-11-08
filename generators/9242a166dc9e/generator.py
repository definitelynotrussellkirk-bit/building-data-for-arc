"""Generator for arc_puzzle_bank_21_set16_bundle:easy_p01.

Matching diagonal endpoints with a single zero between them are completed by
filling the middle cell.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_gaps,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_gaps, no_zero_between, axis_aligned_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9242a166dc9e"
VERSION = "2.0.1"  # add self_check
TASK_ID = "9242a166dc9e"
SUMMARY = (
    "0-bg grid (h, w~7-10) "
    "with 2-4 DIAGONAL "
    "ENDPOINT PAIRS — each "
    "pair: TWO SAME-COLOR "
    "cells at diagonal "
    "offset ±1 from a "
    "MIDPOINT (r, c), at "
    "(r-dr, c-dc) and "
    "(r+dr, c+dc) where "
    "(dr, dc) ∈ {(1, 1), "
    "(1, -1)}. Midpoint "
    "is initially 0. "
    "Pairs are DISTINCT "
    "colors from {1..9}, "
    "placed non-touching "
    "(3×3 neighborhood "
    "padding). Rule "
    "(FILL MIDPOINT OF "
    "EACH DIAGONAL "
    "ENDPOINT PAIR): For "
    "EACH PAIR of same-"
    "color cells at "
    "(r1, c1) and (r2, "
    "c2) with |r2-r1| == "
    "|c2-c1| == 2 and "
    "the midpoint cell "
    "(r1+r2)//2, "
    "(c1+c2)//2 == 0: "
    "PAINT the midpoint "
    "with the pair's "
    "color. Endpoints "
    "stay. Net: each "
    "diagonal endpoint "
    "pair becomes a "
    "filled 3-cell "
    "diagonal."
)

INVARIANTS = [
    "background is 0",
    "each motif has two matching diagonal endpoints",
    "the midpoint is zero",
    "motif neighborhoods are separated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_gaps", "no_zero_between", "axis_aligned_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_gaps":         {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "diagonal_endpoint_pairs",
                       "valid": "diagonal_endpoint_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _block(r, c):
    return {(rr, cc) for rr in range(r - 1, r + 2) for cc in range(c - 1, c + 2)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 pair of same-color cells at diagonal offset |dr|=|dc|=2 with 0 midpoint."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    from collections import defaultdict
    color_cells: dict = defaultdict(list)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                color_cells[grid[r][c]].append((r, c))
    pairs = []
    for color, cells in color_cells.items():
        if len(cells) == 2:
            (r1, c1), (r2, c2) = cells
            if abs(r2 - r1) == 2 and abs(c2 - c1) == 2:
                mr, mc = (r1 + r2) // 2, (c1 + c2) // 2
                if 0 <= mr < h and 0 <= mc < w and grid[mr][mc] == 0:
                    pairs.append(color)
    if not pairs:
        return ["expected ≥1 diagonal endpoint pair with zero midpoint; found none"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        gap_count = ctx.draw_int("gap_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        gap_count = ctx.draw_int("gap_count", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        gap_count = ctx.draw_int("gap_count", 2, 4)
    colors = ctx.draw_distinct_colors("colors", n=gap_count, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    occupied = set()
    for color in colors:
        for _ in range(300):
            r = rng.randint(1, h - 2)
            c = rng.randint(1, w - 2)
            dr, dc = rng.choice([(1, 1), (1, -1)])
            block = _block(r, c)
            if not (block & occupied):
                g[r - dr][c - dc] = color
                g[r + dr][c + dc] = color
                occupied |= block
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_gaps":
        # blank → no diagonal endpoint pairs to bridge
        return g
    if name == "no_zero_between":
        # diagonal pair with already-filled midpoint → rule is identity
        g[1][1] = 4; g[2][2] = 4; g[3][3] = 4
        return g
    if name == "axis_aligned_pair":
        # endpoints share row or col → not diagonal, rule won't fire
        g[3][1] = 4; g[3][5] = 4
        return g
    return g
