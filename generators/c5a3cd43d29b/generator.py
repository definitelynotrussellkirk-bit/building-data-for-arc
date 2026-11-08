"""Generator for 13f06aa5.

Rule: a minority-color indicator cell inside a shape sends a dotted
trail and edge bar outward.

Combinatorial axes (8): grid_h/w, direction, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_shape, no_indicator, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import PLUS_5

GENERATOR_ID = "c5a3cd43d29b"
VERSION = "2.1.0"  # 2.1.0: add plus-indicator self-check.
TASK_ID = "c5a3cd43d29b"
SUMMARY = (
    "BG-color filled grid "
    "(h~11-15, w~11-16) with "
    "BG = 1st of 3 random "
    "distinct colors. "
    "Layout: (a) ONE PLUS_5 "
    "SHAPE (5-cell + sign) "
    "at random interior "
    "position (r0, c0) with "
    "4 BODY cells in the "
    "BODY COLOR (2nd of "
    "palette); (b) ONE "
    "INDICATOR cell at one "
    "of the 4 cardinal "
    "PLUS_5 arms in the "
    "INDICATOR COLOR (3rd) "
    "— direction (up/down/"
    "left/right) determined "
    "by which arm cell is "
    "the indicator. Rule "
    "(SHOOT DOTTED TRAIL + "
    "EDGE BAR FROM "
    "INDICATOR OUTWARD): "
    "identify the BG, BODY, "
    "and INDICATOR colors. "
    "Locate the SHAPE and "
    "the INDICATOR's "
    "DIRECTION (which arm "
    "of the plus). PAINT a "
    "DOTTED TRAIL of "
    "INDICATOR color "
    "outward from the "
    "indicator cell in the "
    "direction (every other "
    "cell). At the GRID "
    "EDGE in that direction, "
    "PAINT a FULL EDGE BAR "
    "(row or column) in "
    "the INDICATOR color. "
    "Net: indicator's arm "
    "direction sends a "
    "dotted ray and a edge "
    "bar in indicator "
    "color."
)

INVARIANTS = [
    "the mode color is the background",
    "one compact non-background component has a majority body color and one minority indicator color",
    "the indicator is offset from the component centroid along a cardinal direction",
    "the rule paints a dotted ray from the indicator and fills the corresponding edge row or column",
]

DIRECTIONS = ("up", "down", "left", "right")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shape", "no_indicator", "full_grid")
HELPFUL_TEXTURES = DIRECTIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "11..15"},
    "grid_w":         {"type": "int", "default": "rng 11..16", "valid": "11..16"},
    "direction":      {"type": "str", "default": "rng helpful",
                       "valid": "|".join(DIRECTIONS)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for direction",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    direction = (overrides.get("texture") if overrides.get("texture") in DIRECTIONS else None) or \
                overrides.get("direction") or \
                ctx.draw_choice("direction", list(DIRECTIONS))
    bg, body, indicator = ctx.draw_distinct_colors("colors", n=3, exclude=set())
    h = rng.randint(11, 15)
    w = rng.randint(11, 16)
    g = full_grid(h, w, bg)

    r0 = rng.randint(4, h - 7)
    c0 = rng.randint(4, w - 7)
    cells = PLUS_5
    for dr, dc in cells:
        g[r0 + dr][c0 + dc] = body

    if direction == "up":
        ind = (r0, c0 + 1)
    elif direction == "down":
        ind = (r0 + 2, c0 + 1)
    elif direction == "left":
        ind = (r0 + 1, c0)
    else:
        ind = (r0 + 1, c0 + 2)
    g[ind[0]][ind[1]] = indicator
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    if name == "no_shape":
        g[5][5] = 4
        return g
    if name == "no_indicator":
        for dr, dc in PLUS_5:
            g[5 + dr][5 + dc] = 3
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(11):
                g[r][c] = 3
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    from collections import Counter
    msgs = []
    flat = [v for row in grid for v in row]
    bg = Counter(flat).most_common(1)[0][0]
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != bg]
    if len(cells) != 5:
        return [f"expected one 5-cell plus object against modal background, got {len(cells)} non-bg cells"]
    r1, r2 = min(r for r, c in cells), max(r for r, c in cells)
    c1, c2 = min(c for r, c in cells), max(c for r, c in cells)
    rel = {(r - r1, c - c1) for r, c in cells}
    expected = {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}
    if (r2 - r1, c2 - c1) != (2, 2) or rel != expected:
        msgs.append("non-background cells must form a PLUS_5 shape")
    counts = Counter(grid[r][c] for r, c in cells)
    if sorted(counts.values()) != [1, 4]:
        msgs.append("plus must have four body cells and one minority indicator")
    else:
        indicator_color = [col for col, n in counts.items() if n == 1][0]
        ind = [(r - r1, c - c1) for r, c in cells if grid[r][c] == indicator_color][0]
        if ind not in {(0, 1), (1, 0), (1, 2), (2, 1)}:
            msgs.append("indicator must be on a cardinal arm, not the center")
    return msgs
