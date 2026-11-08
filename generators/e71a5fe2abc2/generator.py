"""Generator for arc_puzzle_bank_21_set16_s:S16_E4.

Rule: two opposite rectangle corners imply the full rectangle border.

Combinatorial axes (8): height, width, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_corners, single_corner, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e71a5fe2abc2"
VERSION = "2.1.0"  # corners were fixed color 5 (canonical uses 1; rule paints the border color 8 from ANY nonzero corners -> corner color is rule-ignored). Vary corner color 1-9 (incl canonical's 1) + widen grid; doc fixed (border is 8)
TASK_ID = "e71a5fe2abc2"
SUMMARY = (
    "0-bg grid with EXACTLY TWO nonzero cells at OPPOSITE CORNERS of an "
    "axis-aligned rectangle (>=4x4). Rule: interpret them as opposite corners "
    "and paint the full rectangle BORDER with color 8 (the corner color is "
    "ignored -- any nonzero works; canonical uses 1). Corner color, rectangle "
    "size/position and grid size vary."
)

INVARIANTS = [
    "exactly two nonzero cells mark opposite corners of an axis-aligned rectangle",
    "the rectangle spans at least three rows and columns",
    "output paints the rectangle border",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_corners", "single_corner", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "width":          {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "random", "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 6, 9); w = ctx.draw_int("width", 6, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 11, 14); w = ctx.draw_int("width", 11, 14)
    else:
        h = ctx.draw_int("height", 8, 12); w = ctx.draw_int("width", 8, 12)
    rng = ctx.draw_rng("layout")
    r1 = rng.randint(0, h - 5)
    r2 = rng.randint(r1 + 3, h - 1)
    c1 = rng.randint(0, w - 5)
    c2 = rng.randint(c1 + 3, w - 1)
    color = rng.randint(1, 9)              # any nonzero (rule paints border 8 regardless); canonical uses 1
    g = full_grid(h, w, 0)
    if rng.random() < 0.5:
        g[r1][c1] = color; g[r2][c2] = color
    else:
        g[r1][c2] = color; g[r2][c1] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 0)
    if name == "no_corners":
        return g
    if name == "single_corner":
        g[1][1] = 5
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(8):
                g[r][c] = 5
        return g
    return g
