"""Generator for arc_additional_puzzles_21_set9:H59.

Rule: nested 8-frame rings get filled (outer-to-inner) using the colors
listed in the top row of the legend.

Combinatorial axes (8): grid_h/w, palette_kind, depth, palette_size,
position_bias, n_distinct_colors, legend_order, texture.
Degenerates: no_legend, only_one_frame, frames_collide.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "5e5205e54c96"
VERSION = "3.0.2"
TASK_ID = "5e5205e54c96"
SUMMARY = (
    "Variable-size grid with a top-row legend of 2-4 distinct nonzero colors "
    "and 2-4 nested hollow color-8 frames below it. Color 8 is lawful in the "
    "legend because frame discovery ignores row 0. The canonical rule keeps "
    "the frame borders and fills each annular interior, outer-to-inner, with "
    "the corresponding left-to-right legend color; the deepest color fills "
    "the innermost open region."
)

INVARIANTS = [
    "top-row nonzero cells are distinct outer-to-inner ring colors; color 8 is allowed",
    "all nested frame borders are color 8 and lie strictly below the legend row",
    "nested frames are separated by at least one zero cell so each is a distinct component",
    "the deepest legend color fills the innermost open region",
]

PALETTE_KINDS = ("default", "warm_legend", "cool_legend", "rainbow")
DEGENERATE_TEXTURES = ("no_legend", "only_one_frame", "frames_collide")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "15", "valid": "15"},
    "grid_w":         {"type": "int", "default": "15", "valid": "15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm_legend|cool_legend|rainbow"},
    "depth":          {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8"},
    "position_bias":  {"type": "str", "default": "centered", "valid": "centered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4",
                          "valid": "3..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm_legend|cool_legend|rainbow|no_legend|only_one_frame|frames_collide"},
}

_BOXES = [
    (2, 2, 14, 14),
    (5, 5, 11, 11),
    (7, 7, 9, 9),
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # rule reads rect-border frames + top-row legend dynamically (size-generic);
    # vary grid size + the outer frame's size/position, nest rings inset 3
    # (2-cell gap -> separate components), legend = one colour per ring.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 11, 14); max_depth = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 18, 26); w = ctx.draw_int("grid_w", 18, 26); max_depth = 4
    else:
        h = ctx.draw_int("grid_h", 13, 20); w = ctx.draw_int("grid_w", 13, 20); max_depth = 3
    g = full_grid(h, w, 0)
    fh = rng.randint(9, h - 1); fw = rng.randint(9, w - 1)
    r0 = rng.randint(1, h - fh); c0 = rng.randint(0, w - fw)
    r1 = r0 + fh - 1; c1 = c0 + fw - 1
    rings = []
    i = 0
    while len(rings) < max_depth:
        rr0, cc0, rr1, cc1 = r0 + 3 * i, c0 + 3 * i, r1 - 3 * i, c1 - 3 * i
        if rr1 - rr0 < 2 or cc1 - cc0 < 2:   # innermost must be >= 3x3
            break
        rings.append((rr0, cc0, rr1, cc1)); i += 1
    depth = len(rings)
    colors = rng.sample(list(range(1, 10)), depth)
    # Canonical examples include 8 as a legend value. Force deterministic
    # coverage instead of relying on chance so future audits retain that case.
    if sample_index % 4 == 0 and 8 not in colors:
        colors[-1] = 8
    for c, color in enumerate(colors):
        g[0][c] = color
    for box in rings:
        draw_frame(g, *box, 8)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Top row must have nonzero legend colors; body must have color-8 frames."""
    if not grid or not grid[0]:
        return ["grid is empty"]
    h, w = len(grid), len(grid[0])
    errors = []
    # The canonical grammar permits 8 in the legend. Row 0 is excluded when
    # discovering frame objects, so this does not merge with the body frames.
    legend = [grid[0][c] for c in range(w) if grid[0][c] != 0]
    if not legend:
        errors.append("top row has no legend colors")
    elif len(legend) != len(set(legend)):
        errors.append("legend colors must be distinct")
    # body must have color-8 frame cells
    has_frame = any(grid[r][c] == 8 for r in range(1, h) for c in range(w))
    if not has_frame:
        errors.append("no color-8 frame cells found below row 0")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 15, 0)
    if name == "no_legend":
        for box in _BOXES[:2]:
            draw_frame(g, *box, 8)
        return g
    if name == "only_one_frame":
        g[0][0] = 3
        draw_frame(g, *_BOXES[0], 8)
        return g
    if name == "frames_collide":
        g[0][0] = 3
        g[0][1] = 4
        draw_frame(g, 2, 2, 14, 14, 8)
        draw_frame(g, 3, 3, 13, 13, 8)
        return g
    return g
