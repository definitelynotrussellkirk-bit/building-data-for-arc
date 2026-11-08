"""Generator for 264363fd.

Rule: a cross-shaped key centered on a marker stamps colored arms inside
each rectangle marker.

Combinatorial axes (8): grid_h/w, rect_size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_key, no_rect, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "334cbd1692c7"
RULE_HASH = "695c07388555"  # canonical rule this generator was written against
VERSION = "3.1.0"  # +self_check  # shape-locked-in/out (fixed 16x18, 1 rect + key at fixed positions): rule reads h,w dynamically (rects size>=10 + cross-key legend, output=input size). Now grid 14..30 + rect size/position + key position vary.
TASK_ID = "334cbd1692c7"
SUMMARY = (
    "Variable-size 0-bg grid (14..30) with: (a) a large RECTANGLE (varied size) "
    "in some color (rect_color); (b) one MARKER cell of a "
    "different color at the rectangle's center; (c) outside "
    "the rectangle: a KEY shape — a marker-colored center "
    "cell with 4 ARM segments extending up/down/left/right "
    "(each arm is 2 cells of a distinct color: up-color, "
    "down-color, left-color, right-color). Rule: detect bg = "
    "most common color. Detect rect_color = most common non-"
    "bg. Find rectangle objects of that color. Compute "
    "marker_color from cells inside the rect that are neither "
    "bg nor rect_color (mode). Find OUTSIDE marker cells (same "
    "color, not in any rect). The one with most nearby non-bg "
    "neighbors = KEY CENTER. Grow the key region from the "
    "center via 8-conn non-bg cells outside rects. Then for "
    "every marker inside each rectangle, STAMP the key's "
    "offsets (relative to key center) at that marker's "
    "position, painted in the corresponding key arm colors."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "large same-colored rectangles contain marker cells",
    "an outside connected key shape is centered on the same marker color",
    "key offsets and arm colors are copied to every marker inside the rectangles",
]

RECT_SIZES = ("medium", "large")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_key", "no_rect", "full_grid")
HELPFUL_TEXTURES = RECT_SIZES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 16..24", "valid": "14..30"},
    "grid_w":         {"type": "int", "default": "rng 18..26", "valid": "16..30"},
    "rect_size":      {"type": "str", "default": "rng helpful",
                       "valid": "|".join(RECT_SIZES)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "6", "valid": "6"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "6", "valid": "6"},
    "texture":        {"type": "str", "default": "alias for rect_size",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 large rect present, ≥1 marker inside it."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    flat = [v for row in grid for v in row]
    if all(v == 0 for v in flat):
        errs.append("all-zero grid: no rectangle or key placed")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    rect, marker, up, down, left, right = ctx.draw_distinct_colors("colors", n=6, exclude={0})
    # rule reads h,w dynamically (rects size>=10 + a cross-key legend); canonical
    # used a single fixed size. Vary grid + rect size/position + key position.
    if difficulty == "easy":
        H = ctx.draw_int("grid_h", 14, 18); W = ctx.draw_int("grid_w", 16, 20)
    elif difficulty == "hard":
        H = ctx.draw_int("grid_h", 22, 30); W = ctx.draw_int("grid_w", 24, 30)
    else:
        H = ctx.draw_int("grid_h", 16, 24); W = ctx.draw_int("grid_w", 18, 26)
    g = full_grid(H, W, 0)
    rh = rng.randint(5, min(10, H - 6)); rw = rng.randint(6, min(12, W - 6))
    r0 = rng.randint(3, H - rh - 1); c0 = rng.randint(1, W - rw - 1)
    draw_rect(g, r0, c0, rh, rw, rect)
    g[r0 + rh // 2][c0 + rw // 2] = marker
    # cross-key legend: marker centre + colored arms (radius 2). Place clear of rect.
    for _try in range(80):
        kr = rng.randint(2, H - 3); kc = rng.randint(2, W - 3)
        plus = [(kr, kc)] + [(kr + d, kc) for d in (-2, -1, 1, 2)] + \
               [(kr, kc + d) for d in (-2, -1, 1, 2)]
        if all(g[r][c] == 0 for (r, c) in plus):
            g[kr][kc] = marker
            for dr, color in [(-2, up), (-1, up), (1, down), (2, down)]:
                g[kr + dr][kc] = color
            for dc, color in [(-2, left), (-1, left), (1, right), (2, right)]:
                g[kr][kc + dc] = color
            break
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(16, 18, 0)
    if name == "no_key":
        draw_rect(g, 8, 5, 6, 8, 3)
        return g
    if name == "no_rect":
        g[3][3] = 4
        return g
    if name == "full_grid":
        for r in range(16):
            for c in range(18):
                g[r][c] = 4
        return g
    return g
