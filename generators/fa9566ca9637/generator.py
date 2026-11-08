"""Generator for arc_puzzle_bank_eighth21:M51 — prototype stamp at anchors.

Rule: 3-blob = prototype shape. 1-cells are anchors. Output: empty grid
+ prototype stamped (in 3) at each 1-anchor (anchor at top-left of stamp).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_anchors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_prototype, no_anchors, prototype_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "fa9566ca9637"
VERSION = "3.0.0"  # any non-1 prototype color (rule stamps in proto's own color, not locked to 3) + bigger grids/prototype/more anchors
TASK_ID = "fa9566ca9637"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) "
    "with: (a) ONE CONNECTED "
    "COLOR-3 (green) BLOB of "
    "2-4 cells (the "
    "PROTOTYPE) at a random "
    "interior position; (b) "
    "1-3 SINGLE COLOR-1 (blue) "
    "ANCHOR cells placed so "
    "that stamping the "
    "PROTOTYPE (with anchor "
    "as top-left of stamp's "
    "bbox) stays in-bounds and "
    "doesn't overlap existing "
    "non-0 cells. Rule (STAMP "
    "PROTOTYPE IN COLOR 3 AT "
    "EACH 1-ANCHOR): identify "
    "the 3-BLOB PROTOTYPE "
    "(its normalized cell "
    "offsets). For EACH "
    "1-ANCHOR at (ar, ac), "
    "STAMP the prototype's "
    "cells in COLOR 3 with "
    "(ar, ac) as the bbox "
    "top-left. EMIT a clean "
    "0-grid with only the "
    "stamps (and the original "
    "prototype, or output may "
    "drop it). Net: each blue "
    "anchor sprouts a copy of "
    "the green prototype "
    "shape."
)

INVARIANTS = [
    "background is 0",
    "exactly one 3-blob (prototype) of size 2-4",
    "1-3 single 1-cells with room for the stamp without OOB",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_prototype", "no_anchors", "prototype_only")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8-11 easy / 11-15 med / 14-20 hard", "valid": "7..22"},
    "grid_w":         {"type": "int", "default": "9-12 easy / 12-17 med / 16-22 hard", "valid": "8..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_anchors":      {"type": "int", "default": "1-3 easy / 2-5 med / 3-7 hard", "valid": "1..7"},
    "proto_color":    {"type": "color", "default": "rng non-1 (2..9)", "valid": "2..9"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "prototype_plus_anchors",
                       "valid": "prototype_plus_anchors"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
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
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 9, 12)
        n_anchors = ctx.draw_int("n_anchors", 1, 3); psz = (2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 16, 22)
        n_anchors = ctx.draw_int("n_anchors", 3, 7); psz = (3, 6)
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 12, 17)
        n_anchors = ctx.draw_int("n_anchors", 2, 5); psz = (2, 6)
    rng = ctx.draw_rng("layout")
    # Prototype color is the proto object's own color -> any non-1 color (rule stamps it).
    proto_color = int(overrides.get("proto_color",
                                    rng.choice([2, 3, 4, 5, 6, 7, 8, 9])))
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    template = grow_blob(rng, h, w, used, rng.randint(*psz), max_attempts=100)
    if template is None:
        return g
    rs = sorted(r for r, _ in template)
    cs = sorted(c for _, c in template)
    tpl_h = rs[-1] - rs[0] + 1
    tpl_w = cs[-1] - cs[0] + 1
    for r, c in template:
        g[r][c] = proto_color
    used |= template
    for _ in range(n_anchors):
        for _ in range(40):
            ar = rng.randint(0, h - tpl_h)
            ac = rng.randint(0, w - tpl_w)
            stamp = {(ar + (r - rs[0]), ac + (c - cs[0])) for r, c in template}
            if any(g[r][c] != 0 for r, c in stamp):
                continue
            g[ar][ac] = 1
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_prototype":
        # 1-anchors but no 3-blob → nothing to stamp
        g[3][3] = 1
        g[6][7] = 1
        return g
    if name == "no_anchors":
        # prototype only, no 1-anchors → nowhere to stamp
        g[1][1] = 3; g[1][2] = 3; g[2][1] = 3
        return g
    if name == "prototype_only":
        # prototype only (same as no_anchors but explicit) → no work to do
        g[2][2] = 3; g[3][2] = 3; g[3][3] = 3
        return g
    return g
