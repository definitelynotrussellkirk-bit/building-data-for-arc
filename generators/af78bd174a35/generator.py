"""Generator for arc_additional_puzzle_bank_volume14:M98.

Rule: aligned equal-color pairs with empty gaps are bridged in their own
color (the gap cells get filled).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, pairs_adjacent, mismatched_pair_alignment.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "af78bd174a35"
VERSION = "1.2.0"
TASK_ID = "af78bd174a35"
SUMMARY = "2-4 horizontally-aligned equal-color pairs with empty cells between."

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "paired markers are aligned horizontally on the same row",
    "the cells between each pair are empty (so the bridge fill is visible)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "pairs_adjacent", "mismatched_pair_alignment")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..24"},
    "grid_w":         {"type": "int", "default": "rng 8..14", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "horizontal_pairs",
                       "valid": "horizontal_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        n_pairs = ctx.draw_int("n_pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
        n_pairs = ctx.draw_int("n_pairs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 14)
        n_pairs = ctx.draw_int("n_pairs", 2, 4)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    colors = list(range(1, 10))
    rng.shuffle(colors)
    rows = rng.sample(range(h), min(n_pairs, h))
    for i, r in enumerate(rows):
        c1 = rng.randint(0, w - 5)
        c2 = rng.randint(c1 + 3, w - 1)
        g[r][c1] = colors[i]
        g[r][c2] = colors[i]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # singletons only → no pair bridges to draw
        g[2][3] = 4
        g[5][7] = 6
        return g
    if name == "pairs_adjacent":
        # endpoints touch → the bridge is empty (already fully connected)
        g[2][3] = 4; g[2][4] = 4
        g[5][6] = 6; g[5][7] = 6
        return g
    if name == "mismatched_pair_alignment":
        # two cells of same color on different rows AND cols → not a valid pair
        g[2][3] = 4; g[5][7] = 4
        g[3][1] = 6; g[6][8] = 6
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    from collections import defaultdict
    msgs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    locs = defaultdict(list)
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                locs[v].append((r, c))
    if not locs:
        msgs.append("no active marker pairs")
    for color, cells in locs.items():
        if len(cells) != 2:
            msgs.append(f"color {color} appears {len(cells)} times, expected exactly twice")
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        if r1 != r2:
            msgs.append(f"color {color} pair is not horizontally aligned")
        elif abs(c2 - c1) < 3:
            msgs.append(f"color {color} pair is too close to show bridge gap")
        elif any(grid[r1][c] != 0 for c in range(c1 + 1, c2)):
            msgs.append(f"color {color} bridge corridor is blocked")
    return msgs
