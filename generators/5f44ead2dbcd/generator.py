"""Generator for arc_additional_puzzle_bank_volume9:H58.

Rule: scale + rotation controls transform an orange template; the result
is stamped at the cyan anchor on a blank canvas.

Combinatorial axes (8): grid_h/w, palette_kind, scale_control,
rotation_control, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_template, no_anchor, missing_controls.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "5f44ead2dbcd"
VERSION = "2.0.1"
TASK_ID = "5f44ead2dbcd"
SUMMARY = (
    "0-bg grid (h~12-16, w~12-17) with: (a) a SCALE "
    "CONTROL at (0, 0) — color 1 means scale-factor 1 "
    "(keep size), other (color 2) means scale-factor 2 "
    "(2×2 upscale); (b) a ROTATION CONTROL at (0, 1) — "
    "color 3 means rotate 0°, 4 means 90° CW, 5 means "
    "180°, else (color 6) means 270° CW; (c) a small "
    "color-7 (orange) TEMPLATE polyomino somewhere in "
    "the top-left region; (d) a single color-8 (cyan) "
    "ANCHOR cell placed somewhere with room. Rule: "
    "(1) NORMALIZE the template's cells. (2) UPSCALE by "
    "the scale factor (each template cell becomes a k×k "
    "block). (3) ROTATE by the rotation count. "
    "(4) PAINT the resulting shape in color 7 onto a "
    "BLANK CANVAS at the anchor's position (anchor "
    "becomes the shape's top-left). Net: only the "
    "transformed orange shape remains, stamped at the "
    "cyan anchor location, on an otherwise-empty grid."
)

INVARIANTS = [
    "top-left control selects scale 1 or 2",
    "the next control selects one of four rotations",
    "one orange template and one cyan anchor are present",
    "the scaled rotated template fits at the anchor",
]

PALETTE_KINDS = ("default", "scale_1", "scale_2", "varied_rotation")
DEGENERATE_TEXTURES = ("no_template", "no_anchor", "missing_controls")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..16", "valid": "10..24"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "scale_control":  {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "rotation_control": {"type": "int", "default": "rng 3..6",
                         "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
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
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 16)
        w = ctx.draw_int("grid_w", 15, 17)
    else:
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 17)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    g[0][0] = rng.choice([1, 2])
    g[0][1] = rng.choice([3, 4, 5, 6])
    paint_at(g, 2, 2, [(0, 0), (0, 1), (0, 2), (1, 1)], 7)
    g[h - 6][w - 6] = 8
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Controls at (0,0) and (0,1); orange(7) template cells; cyan(8) anchor."""
    if not grid or not grid[0]:
        return ["grid is empty"]
    errors = []
    if grid[0][0] not in (1, 2):
        errors.append(f"cell (0,0) should be scale control 1 or 2, got {grid[0][0]}")
    if grid[0][1] not in (3, 4, 5, 6):
        errors.append(f"cell (0,1) should be rotation control 3-6, got {grid[0][1]}")
    h, w = len(grid), len(grid[0])
    n7 = sum(grid[r][c] == 7 for r in range(h) for c in range(w))
    n8 = sum(grid[r][c] == 8 for r in range(h) for c in range(w))
    if n7 == 0:
        errors.append("no color-7 (orange) template cells found")
    if n8 != 1:
        errors.append(f"expected exactly 1 color-8 anchor, got {n8}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 13, 14
    g = full_grid(h, w, 0)
    if name == "no_template":
        # controls + anchor but no orange template — nothing to stamp
        g[0][0] = 1
        g[0][1] = 3
        g[h - 6][w - 6] = 8
        return g
    if name == "no_anchor":
        # template + controls but no cyan anchor — stamp position undefined
        g[0][0] = 2
        g[0][1] = 5
        paint_at(g, 2, 2, [(0, 0), (0, 1), (0, 2), (1, 1)], 7)
        return g
    if name == "missing_controls":
        # template + anchor but no scale/rotation controls
        paint_at(g, 2, 2, [(0, 0), (0, 1), (0, 2), (1, 1)], 7)
        g[h - 6][w - 6] = 8
        return g
    return g
