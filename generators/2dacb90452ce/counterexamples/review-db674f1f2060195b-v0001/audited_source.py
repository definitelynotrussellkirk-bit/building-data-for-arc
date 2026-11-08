"""Generator for ARC task c59eb873.

Rule: `(rule! (lambda (g) (upscale g 2)))`.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "2dacb90452ce"
VERSION = "2.0.0"
TASK_ID = "2dacb90452ce"
SUMMARY = (
    "Small grid (h, w~2-15) "
    "drawn with one of 9 "
    "TEXTURE patterns "
    "(noise/sparse/blob/"
    "stripes/gradient/"
    "checkerboard/frame/"
    "ring/plus) from a "
    "palette of 2-9 colors, "
    "with bg_density 0..0.4 "
    "and noise_overlay "
    "0..0.05. Guaranteed "
    "≥2 distinct colors in "
    "the input (so upscale "
    "isn't trivially "
    "monochrome). Rule "
    "(2× UPSCALE): EMIT a "
    "(2h)×(2w) OUTPUT GRID "
    "where each input cell "
    "(r, c) with value v "
    "becomes a SOLID 2×2 "
    "BLOCK at output "
    "positions [2r..2r+1]"
    "×[2c..2c+1] all set to "
    "v. Net: each input "
    "cell expands to a "
    "2×2 block of the same "
    "color."
)

INVARIANTS = [
    "input dimensions are small so 2x upscale stays within ARC bounds",
    "input has at least two colors",
    "colors are sampled from a small palette",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("tiny_grid", "monochrome")

AXES = {
    "grid_h":       {"type": "int",   "default": "rng 2..15", "valid": "1..15"},
    "grid_w":       {"type": "int",   "default": "rng 2..15", "valid": "1..15"},
    "palette_size": {"type": "int",   "default": "rng 2..9",  "valid": "2..10"},
    "texture":      {"type": "str",   "default": "rng helpful",
                     "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "bg_density":   {"type": "float", "default": "rng 0..0.4", "valid": "0..0.95"},
    "noise_overlay": {"type": "float", "default": "rng 0..0.05", "valid": "0..0.5"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        lo, hi, c_lo, c_hi = 2, 5, 2, 3
    elif difficulty == "hard":
        lo, hi, c_lo, c_hi = 10, 15, 5, 9
    else:
        lo, hi, c_lo, c_hi = 2, 15, 2, 9

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
                               ctx.draw_rng("bg_density").uniform(0.0, 0.4)))
    if bg_d > 0.0:
        g = apply_bg_density(g, palette, rng, bg_d)
    no = float(overrides.get("noise_overlay",
                             ctx.draw_rng("noise_overlay").uniform(0.0, 0.05)))
    if no > 0.0:
        g = apply_noise_overlay(g, palette, rng, no)

    if len({v for row in g for v in row}) == 1:
        g[0][0] = palette[0]
        g[-1][-1] = palette[1] if len(palette) > 1 else palette[0]
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify upscale-by-2 input invariants for 2dacb90452ce."""
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 15 or w > 15:
        errs.append(f"input dims {h}x{w} exceed 15x15 (2x output would be too large)")
    colors = {grid[r][c] for r in range(h) for c in range(w)}
    if len(colors) < 2:
        errs.append(f"input has only {len(colors)} distinct color(s) — need >=2 for meaningful upscale")
    return errs


def _draw_from_degenerate(name, h, w, palette, rng):
    """Edge-case input where the 2x upscale is hard to read.

    tiny_grid  — 1×1 input becomes a 2×2 monochrome block, ambiguous
                 with "produce 2×2 of color X."
    monochrome — single-color input; upscale produces uniform output.
    """
    if name == "tiny_grid":
        return [[rng.choice(palette)]]
    if name == "monochrome":
        return full_grid(h, w, rng.choice(palette))
    return full_grid(h, w, palette[0])
