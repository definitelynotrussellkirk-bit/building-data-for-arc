"""Generator for puzzle 3af2c5a8.

Rule: 4-fold kaleidoscope — output is 2h × 2w with the input mirrored
into all four quadrants around the input at top-left.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "346d774eda9b"
VERSION = "1.1.1"
TASK_ID = "346d774eda9b"
SUMMARY = "Any colored grid; rule emits a 4-fold kaleidoscope (2h × 2w) of the input."

INVARIANTS = [
    "input dims ≤ (6, 8) by default so 2× kaleidoscope stays canonical-like",
    "≥2 distinct colors so the kaleidoscope is informative",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("monochrome", "lr_symmetric", "ud_symmetric")

AXES = {
    "grid_h":         {"type": "int",   "default": "rng 3..5 (easy 3, hard 4..6)", "valid": "1..15"},
    "grid_w":         {"type": "int",   "default": "rng 4..7 (easy 4, hard 5..8)", "valid": "1..15"},
    "palette_size":   {"type": "int",   "default": "rng 2..6", "valid": "1..10"},
    "texture":        {"type": "str",   "default": "rng helpful",
                       "valid": "noise|sparse|blob|stripes|gradient|checkerboard|frame|ring|plus|monochrome|lr_symmetric|ud_symmetric"},
    "bg_density":     {"type": "float", "default": "rng 0..0.4", "valid": "0..0.95"},
    "noise_overlay":  {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 3, 3, 4, 4, 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 4, 6, 5, 8, 3, 5
    else:
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 3, 5, 4, 7, 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    n_colors = ctx.draw_int("palette_size", c_lo, c_hi)
    palette = ctx.draw_distinct_colors("palette", n=n_colors)
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, palette, rng)
    texture = overrides.get("texture",
                            ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    g = fill_texture(texture, h, w, palette, rng)
    bg_d = float(overrides.get("bg_density",
                               ctx.draw_rng("bg_density").uniform(0.0, 0.4)))
    if bg_d > 0.0:
        g = apply_bg_density(g, palette, rng, bg_d)
    no = float(overrides.get("noise_overlay",
                             ctx.draw_rng("noise_overlay").uniform(0.0, 0.05)))
    if no > 0.0:
        g = apply_noise_overlay(g, palette, rng, no)
    if len({v for row in g for v in row}) < 2:
        g[0][0] = palette[0]
        g[-1][-1] = palette[1] if len(palette) > 1 else (palette[0] + 1) % 10
    return g


def _draw_from_degenerate(name, h, w, palette, rng):
    g = full_grid(h, w, palette[0])
    if name == "monochrome":
        c0 = rng.choice(palette)
        for r in range(h):
            for c in range(w):
                g[r][c] = c0
        return g
    if name == "lr_symmetric":
        for r in range(h):
            for c in range(w // 2):
                v = rng.choice(palette)
                g[r][c] = v
                g[r][w - 1 - c] = v
        return g
    if name == "ud_symmetric":
        for c in range(w):
            for r in range(h // 2):
                v = rng.choice(palette)
                g[r][c] = v
                g[h - 1 - r][c] = v
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Default kaleidoscope inputs must be small, non-empty, and informative."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    msgs = []
    if h * w > 48:
        msgs.append(f"default input area {h*w} is too large for this canonical 3x4-style task")
    if 2 * h > 30 or 2 * w > 30:
        msgs.append(f"2x kaleidoscope output would exceed ARC bounds: input {h}x{w}")
    if len({v for row in grid for v in row}) < 2:
        msgs.append("input has <2 colors; kaleidoscope would be visually uninformative")
    return msgs
