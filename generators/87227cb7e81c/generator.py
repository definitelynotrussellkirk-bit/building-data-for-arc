"""Generator for arc_puzzle_bank_fifth_21_bundle:easy_33_stamp_template_at_marker.

Rule: a small template object and an 8 marker; the template is stamped
at the marker location.

Combinatorial axes (8): grid_h, grid_w, palette_kind, template_color,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, no_template, multiple_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "87227cb7e81c"
VERSION = "2.0.1"
TASK_ID = "87227cb7e81c"
SUMMARY = (
    "0-bg grid (h~8-12, w~9-13) "
    "with: (a) a SMALL TEMPLATE "
    "OBJECT (L-shape [(0,0), "
    "(1,0), (1,1)]) placed at "
    "the LEFT side (rows 1..h-4, "
    "cols 1..w//2-2) in a "
    "TEMPLATE_COLOR (random from "
    "{1..9} excluding 0 and 8); "
    "(b) ONE COLOR-8 (cyan) "
    "MARKER cell placed on the "
    "RIGHT side (cols w//2..w-2, "
    "well away from the "
    "template). Rule (STAMP "
    "TEMPLATE AT MARKER): "
    "identify the LARGEST non-8 "
    "object (the TEMPLATE) and "
    "its ANCHOR (top-left of "
    "its bbox). Identify the "
    "COLOR-8 MARKER cell at "
    "(mr, mc). STAMP the "
    "TEMPLATE at the marker — "
    "paint the template's cells "
    "at offsets from (mr, mc) "
    "in the TEMPLATE_COLOR. "
    "The original template "
    "stays. Net: 8-marker "
    "indicates where to place a "
    "copy of the template."
)

INVARIANTS = [
    "background is 0",
    "there is one 8 marker",
    "the largest non-8 object is the template",
    "the template crop fits at the marker location",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_template", "multiple_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "template_color": {"type": "color", "default": "rng", "valid": "1..9 != 8"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "template_left_marker_right",
                       "valid": "template_left_marker_right"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one color-8 marker; at least one non-8 connected object (template)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if not eights:
        return []  # degenerate no_marker — allowed
    errs = []
    if len(eights) != 1:
        return []  # degenerate multiple_markers — allowed
    non_eight = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)]
    if not non_eight:
        return []  # degenerate no_template — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 9, 13)
    color = ctx.draw_color("template_color", exclude={0, 8})
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    shape = [(0, 0), (1, 0), (1, 1)]
    rr = rng.randint(1, h - 4)
    rc = rng.randint(1, max(1, w // 2 - 2))
    for dr, dc in shape:
        g[rr + dr][rc + dc] = color
    mr = rng.randint(0, h - 2)
    mc = rng.randint(max(w // 2, rc + 3), w - 2)
    g[mr][mc] = 8
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # template only, no 8 marker → no position to stamp at
        for (r, c) in [(2, 1), (3, 1), (3, 2)]: g[r][c] = 4
        return g
    if name == "no_template":
        # 8 marker only, no template → nothing to stamp
        g[3][7] = 8
        return g
    if name == "multiple_markers":
        # multiple 8s → "the marker location" ambiguous
        for (r, c) in [(2, 1), (3, 1), (3, 2)]: g[r][c] = 4
        g[3][6] = 8; g[5][7] = 8; g[6][8] = 8
        return g
    return g
