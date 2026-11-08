"""Generator for puzzle 67e8384a.

Rule: 4-fold kaleidoscope — output is 2h × 2w with 4-quadrant mirror
(input + LR-mirror | UD-mirror + 180°-rot). Same shape as 3af2c5a8.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "8725a034f163"
VERSION = "2.2.0"  # keep normal examples near the canonical 3x3 task scale
TASK_ID = "8725a034f163"
SUMMARY = (
    "Multicolor grid (h, w ∈ 2-6, by "
    "difficulty), palette of 2-6 "
    "distinct colors drawn at random, "
    "filled by dense TEXTURE ∈ {noise / "
    "stripes / gradient / checkerboard} via fill_texture. After "
    "base fill: apply_bg_density "
    "(0-40%) adds sparsity; "
    "apply_noise_overlay (0-5%) flips "
    "cells. ≥2 distinct colors "
    "guaranteed (if monochrome after "
    "all transforms, force corners "
    "to different palette colors). "
    "Rule (4-FOLD KALEIDOSCOPE — "
    "OUTPUT IS 2H × 2W WITH 4 "
    "QUADRANTS: TOP-LEFT = INPUT, "
    "TOP-RIGHT = LR-MIRROR OF INPUT, "
    "BOTTOM-LEFT = UD-MIRROR OF "
    "INPUT, BOTTOM-RIGHT = 180°-"
    "ROTATION OF INPUT): For an h×w "
    "input g, BUILD output of size "
    "(2h) × (2w). For positions "
    "(r, c): TOP-LEFT (r < h, c < w) "
    "= g[r][c]; TOP-RIGHT (r < h, "
    "c ≥ w) = g[r][2w-1-c]; "
    "BOTTOM-LEFT (r ≥ h, c < w) = "
    "g[2h-1-r][c]; BOTTOM-RIGHT "
    "(r ≥ h, c ≥ w) = g[2h-1-r]"
    "[2w-1-c]. Net: input is "
    "reflected into a 4-quadrant "
    "symmetric pattern."
)

INVARIANTS = [
    "input dims ≤ (15, 15) so 2× kaleidoscope fits",
    "≥2 distinct colors so the kaleidoscope is informative",
]

HELPFUL_TEXTURES = (
    "noise", "stripes", "gradient", "checkerboard",
)
DEGENERATE_TEXTURES = ("monochrome", "lr_symmetric", "ud_symmetric")

AXES = {
    "grid_h":         {"type": "int",   "default": "rng 2..6", "valid": "1..15"},
    "grid_w":         {"type": "int",   "default": "rng 2..6", "valid": "1..15"},
    "palette_size":   {"type": "int",   "default": "rng 2..5", "valid": "1..10"},
    "texture":        {"type": "str",   "default": "rng helpful",
                       "valid": "noise|stripes|gradient|checkerboard|monochrome|lr_symmetric|ud_symmetric"},
    "bg_density":     {"type": "float", "default": "rng 0..0.4", "valid": "0..0.95"},
    "noise_overlay":  {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: dims ≤ 15 (2x output fits), ≥2 distinct colors."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h > 15 or w > 15:
        errors.append(f"grid {h}x{w} > 15x15 (2x kaleidoscope would exceed 30x30)")
    if h > 6 or w > 6:
        errors.append(f"default grid {h}x{w} is far from the canonical 3x3 kaleidoscope scale")
    colors = set(grid[r][c] for r in range(h) for c in range(w))
    if len(colors) < 2:
        errors.append("normal generation should contain at least two colors")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, c_lo, c_hi = 2, 3, 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, c_lo, c_hi = 4, 6, 3, 5
    else:
        h_lo, h_hi, c_lo, c_hi = 2, 5, 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
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
