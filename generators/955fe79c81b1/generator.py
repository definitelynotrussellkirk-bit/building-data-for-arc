"""Generator for d37a1ef5.

Rule: a color-2 frame's interior filled with 2 while gray bbox region
is preserved.

Combinatorial axes (8): grid_h/w, frame_h, frame_w, gray_h, gray_w,
position_bias, palette_kind, anchor_corner.
Degenerates: no_gray, no_frame, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, fill_box, full_grid

GENERATOR_ID = "955fe79c81b1"
VERSION = "1.2.1"  # add self_check
TASK_ID = "955fe79c81b1"
SUMMARY = "Color-2 rectangular frame + interior color-5 (gray) bbox region. Rule fills all frame-interior cells outside the gray bbox with color 2; frame and gray bbox unchanged."

# Rivals: 'output is input' refuted by any demo (interior fills).
# 'fill gray region too' refuted by any demo (gray cells stay 5).
# 'use a different fill color' refuted by any demo (fill is 2).
# 'fill outside the frame too' refuted by any demo (outside stays 0).
# 3 demos with varied frame/gray sizes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is color 0",
    "color 2 forms one rectangular frame",
    "color 5 cells form a smaller interior bbox",
    "all frame interior cells outside the gray bbox become color 2",
]

POSITION_BIASES = ("centered", "corner", "near_edge", "scattered")
DEGENERATE_TEXTURES = ("no_gray", "no_frame", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 13..16", "valid": "11..20"},
    "grid_w":         {"type": "int", "default": "rng 13..16", "valid": "11..20"},
    "frame_h":        {"type": "int", "default": "9", "valid": "7..14"},
    "frame_w":        {"type": "int", "default": "9", "valid": "7..14"},
    "gray_h":         {"type": "int", "default": "2", "valid": "1..4"},
    "gray_w":         {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-2 (red) frame cell; ≥1 color-5 (gray) interior cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    has_2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    has_5 = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    if not has_2:
        errs.append("no color-2 (red) frame cells found")
    if not has_5:
        errs.append("no color-5 (gray) interior cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 11, 13
    elif difficulty == "hard":
        h_lo, h_hi = 16, 20
    else:
        h_lo, h_hi = 13, 16
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    if bias == "centered":
        r1 = max(1, (h - 9) // 2)
        c1 = max(1, (w - 9) // 2)
    elif bias == "corner":
        r1 = rng.choice([1, max(1, h - 11)])
        c1 = rng.choice([1, max(1, w - 11)])
    elif bias == "near_edge":
        if rng.random() < 0.5:
            r1 = rng.choice([1, max(1, h - 11)])
            c1 = rng.randint(1, max(1, w - 11))
        else:
            r1 = rng.randint(1, max(1, h - 11))
            c1 = rng.choice([1, max(1, w - 11)])
    else:
        r1 = 1 + rng.randint(0, max(0, h - 11))
        c1 = 1 + rng.randint(0, max(0, w - 11))
    r1 = max(1, min(r1, h - 11))
    c1 = max(1, min(c1, w - 11))
    r2 = r1 + 8
    c2 = c1 + 8
    if r2 >= h:
        r2 = h - 2
    if c2 >= w:
        c2 = w - 2
    draw_frame(g, r1, c1, r2, c2, 2)
    gh = int(overrides.get("gray_h", 2))
    gw = int(overrides.get("gray_w",
                           ctx.draw_int("gray_w", 3, 4)))
    gr1 = r1 + 3
    gc1 = c1 + 3
    if gr1 + gh - 1 < r2 and gc1 + gw - 1 < c2:
        fill_box(g, gr1, gc1, gr1 + gh - 1, gc1 + gw - 1, 5)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "no_gray":
        draw_frame(g, 2, 2, 11, 11, 2)
        return g
    if name == "no_frame":
        fill_box(g, 5, 5, 7, 8, 5)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g
