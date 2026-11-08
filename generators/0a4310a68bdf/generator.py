"""Generator for ARC task 9172f3a0.

Rule: `(rule! (lambda (g) (upscale g 3)))`.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "0a4310a68bdf"
VERSION = "1.3.1"
TASK_ID = "0a4310a68bdf"
SUMMARY = (
    "Small random grid (up to 10×10) with ≥2 distinct colors. Rule: "
    "upscale by 3 — each cell becomes a 3×3 block of the same color. "
    "Output dimensions are (3H × 3W). Equivalent to "
    "output[r][c] = input[r//3][c//3]."
)

# Rivals: 'output is input' refuted by demos (output is 3× larger).
# 'upscale by 2' refuted by demos showing 3× dims. 'upscale only some
# cells' refuted by demos with all cells upscaled. 'fill with a single
# color' refuted by demos with multiple colors. 'output is fixed size'
# refuted by demos with varying input dims. 3 demos with varied input
# sizes pin the 3× scaling.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input dimensions are at most 10x10 so 3x upscale stays within ARC bounds",
    "input has at least two colors",
    "colors are sampled from a small palette",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("tiny_grid", "monochrome")

AXES = {
    "grid_h":       {"type": "int",   "default": "rng 2..10", "valid": "1..10"},
    "grid_w":       {"type": "int",   "default": "rng 2..10", "valid": "1..10"},
    "palette_size": {"type": "int",   "default": "rng 2..9",  "valid": "2..10"},
    "texture":      {"type": "str",   "default": "rng helpful",
                     "valid": "noise|sparse|blob|stripes|gradient|"
                              "checkerboard|frame|ring|plus|"
                              "tiny_grid|monochrome"},
    "bg_density":   {"type": "float", "default": "rng 0..0.3", "valid": "0..0.95"},
    "noise_overlay": {"type": "float", "default": "rng 0..0.05", "valid": "0..0.5"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        lo, hi, c_lo, c_hi = 2, 4, 2, 3
    elif difficulty == "hard":
        lo, hi, c_lo, c_hi = 7, 10, 5, 9
    else:
        lo, hi, c_lo, c_hi = 2, 10, 2, 9

    h = ctx.draw_int("grid_h", lo, hi)
    w = ctx.draw_int("grid_w", lo, hi)
    n_colors = ctx.draw_int("palette_size", c_lo, c_hi)
    palette = ctx.draw_distinct_colors("palette", n=n_colors)
    rng = ctx.draw_rng("cells")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, palette, rng)

    if "texture" in overrides:
        texture = overrides["texture"]
    else:
        texture = ctx.draw_choice("texture", list(HELPFUL_TEXTURES))
    g = fill_texture(texture, h, w, palette, rng)

    bg_d = float(overrides.get("bg_density",
                               ctx.draw_rng("bg_density").uniform(0.0, 0.3)))
    if bg_d > 0.0:
        g = apply_bg_density(g, palette, rng, bg_d)
    no = float(overrides.get("noise_overlay",
                             ctx.draw_rng("noise_overlay").uniform(0.0, 0.05)))
    if no > 0.0:
        g = apply_noise_overlay(g, palette, rng, no)

    # Invariant: ≥2 distinct colors visible.
    if len({v for row in g for v in row}) == 1:
        g[0][0] = palette[0]
        g[-1][-1] = palette[1] if len(palette) > 1 else palette[0]
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify upscale-by-3 input invariants for 0a4310a68bdf."""
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 10 or w > 10:
        errs.append(f"input dims {h}x{w} exceed 10x10 (3x output would exceed 30x30)")
    colors = {grid[r][c] for r in range(h) for c in range(w)}
    if len(colors) < 2:
        errs.append(f"input has only {len(colors)} distinct color(s) — need >=2 for meaningful upscale")
    return errs


def _draw_from_degenerate(name, h, w, palette, rng):
    """Edge-case input where the 3x upscale is hard to read.

    tiny_grid  — 1×1 input; output is a 3×3 monochrome block, easily
                 confused with "fill with color X" rules.
    monochrome — single color repeated; upscale produces a uniform 3x grid.
    """
    if name == "tiny_grid":
        g = [[rng.choice(palette)]]
        return g
    if name == "monochrome":
        color = rng.choice(palette)
        return full_grid(h, w, color)
    return full_grid(h, w, palette[0])
