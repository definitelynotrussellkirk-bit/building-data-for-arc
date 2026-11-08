"""Generator for arc_additional_puzzle_bank_volume7:M48.

Rule: an anchored green/red source shape rotates by blue-dot count and
stamps at the cyan target.

Combinatorial axes (8): grid_h/w, palette_kind, n_blue_dots,
palette_size, position_bias, n_distinct_colors, target_pos, texture.
Degenerates: no_anchor, no_target, no_blue_dots.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3431b0a2e5ac"
VERSION = "1.1.0"
TASK_ID = "3431b0a2e5ac"
SUMMARY = "An anchored green/red source shape rotates by blue-dot count and stamps at cyan."

INVARIANTS = [
    "background is 0",
    "there is one red anchor connected to green source cells",
    "there is one cyan target",
    "the number of blue dots is between one and four",
]

PALETTE_KINDS = ("default", "rot_1", "rot_2", "rot_3_or_4")
DEGENERATE_TEXTURES = ("no_anchor", "no_target", "no_blue_dots")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "8..24"},
    "grid_w":         {"type": "int", "default": "rng 11..15", "valid": "8..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blue_dots":    {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "target_pos":     {"type": "str", "default": "fixed", "valid": "fixed"},
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
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 15)
        w = ctx.draw_int("grid_w", 14, 15)
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 11, 15)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    anchor = (3, 3)
    g[anchor[0]][anchor[1]] = 2
    for dr, dc in [(0, 1), (1, 0), (2, 0), (2, 1)]:
        g[anchor[0] + dr][anchor[1] + dc] = 3
    target = (h - 5, w - 5)
    g[target[0]][target[1]] = 8
    k = rng.randint(1, 4)
    for i in range(k):
        g[0][i] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 13, 13
    g = full_grid(h, w, 0)
    if name == "no_anchor":
        # green cells exist but no red anchor → rotation pivot undefined
        for dr, dc in [(0, 1), (1, 0), (2, 0), (2, 1)]:
            g[3 + dr][3 + dc] = 3
        g[h - 5][w - 5] = 8
        g[0][0] = 1; g[0][1] = 1
        return g
    if name == "no_target":
        # source + dots but no cyan target → no stamp position
        g[3][3] = 2
        for dr, dc in [(0, 1), (1, 0), (2, 0), (2, 1)]:
            g[3 + dr][3 + dc] = 3
        g[0][0] = 1
        return g
    if name == "no_blue_dots":
        # source + target but zero rotation count → ambiguous
        g[3][3] = 2
        for dr, dc in [(0, 1), (1, 0), (2, 0), (2, 1)]:
            g[3 + dr][3 + dc] = 3
        g[h - 5][w - 5] = 8
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0]:
        return ["empty grid"]
    msgs = []
    red = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    green = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    blue = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    cyan = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    if len(red) != 1:
        msgs.append(f"expected one red anchor, found {len(red)}")
    if len(cyan) != 1:
        msgs.append(f"expected one cyan target, found {len(cyan)}")
    if not (1 <= len(blue) <= 4):
        msgs.append(f"expected 1-4 blue rotation dots, found {len(blue)}")
    if not green:
        msgs.append("expected green source cells")
    if red and green:
        ar, ac = red[0]
        if not any(abs(ar - r) + abs(ac - c) == 1 for r, c in green):
            msgs.append("red anchor is not 4-connected to the green source")
    if blue:
        rows = {r for r, _ in blue}
        cols = sorted(c for _, c in blue)
        if rows != {0} or cols != list(range(len(blue))):
            msgs.append("blue dots should be a visible count on the top row")
    return sorted(set(msgs))
