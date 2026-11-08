"""Generator for ARC task 62c24649.

Rule: 4-fold kaleidoscope — output is 2h × 2w with input mirrored into
all four quadrants around the input at top-left.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "36d9177c4b0a"
VERSION = "1.2.0"  # canonical-scale 3x3 defaults; larger mirrors remain opt-in/hard
TASK_ID = "36d9177c4b0a"
SUMMARY = "Canonical-scale colored grid; rule outputs 2h × 2w 4-fold kaleidoscope."

INVARIANTS = [
    "default/easy input is canonical-scale 3x3; hard rows are only modestly larger",
    "input dims ≤ (15, 15) so 2× kaleidoscope fits",
    "≥2 distinct colors so the kaleidoscope is informative",
    "default input is not already LR/UD symmetric, so mirroring is visible",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("monochrome", "lr_symmetric", "ud_symmetric")

AXES = {
    "grid_h":         {"type": "int",   "default": "3", "valid": "1..15"},
    "grid_w":         {"type": "int",   "default": "3", "valid": "1..15"},
    "palette_size":   {"type": "int",   "default": "4", "valid": "2..10"},
    "texture":        {"type": "str",   "default": "rng helpful",
                       "valid": "noise|sparse|blob|stripes|gradient|checkerboard|frame|ring|plus|monochrome|lr_symmetric|ud_symmetric"},
    "bg_density":     {"type": "float", "default": "rng 0..0.4", "valid": "0..0.95"},
    "noise_overlay":  {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    # The canonical task's train inputs are all dense 3x3 fields over colors 0/1/2/3.
    # Earlier defaults ranged up to 12x12 arbitrary textures; they passed parity, but they
    # trained a much broader "mirror any wallpaper" distribution than the actual task.
    # Keep normal rows canonical-scale, with only hard/explicit overrides widening modestly.
    if difficulty == "hard":
        h_lo, h_hi, c_lo, c_hi = 4, 5, 4, 5
    else:
        h_lo, h_hi, c_lo, c_hi = 3, 3, 4, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    n_colors = ctx.draw_int("palette_size", c_lo, c_hi)
    if "palette" in overrides:
        palette = ctx.draw_distinct_colors("palette", n=n_colors)
    else:
        base = (0, 1, 2, 3, 4)
        palette = base[:n_colors]
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, palette, rng)

    texture = overrides.get("texture")
    if texture is None:
        g = _random_asymmetric_field(h, w, palette, rng)
    else:
        g = fill_texture(texture, h, w, palette, rng)
        bg_d = float(overrides.get("bg_density", 0.0))
        if bg_d > 0.0:
            g = apply_bg_density(g, palette, rng, bg_d)
        no = float(overrides.get("noise_overlay", 0.0))
        if no > 0.0:
            g = apply_noise_overlay(g, palette, rng, no)
    _ensure_informative(g, palette)
    if _is_lr_sym(g):
        g[0][0] = _different_color(g[0][0], palette)
    if _is_ud_sym(g):
        g[-1][-1] = _different_color(g[-1][-1], palette)
    return g


def _is_lr_sym(g):
    return all(row == list(reversed(row)) for row in g)


def _is_ud_sym(g):
    return g == list(reversed(g))


def _different_color(color, palette):
    for c in palette:
        if c != color:
            return c
    return (color + 1) % 10


def _ensure_informative(g, palette):
    if len({v for row in g for v in row}) < 2:
        g[0][0] = palette[0]
        g[-1][-1] = _different_color(palette[0], palette)


def _random_asymmetric_field(h, w, palette, rng):
    for _ in range(100):
        g = [[rng.choice(palette) for _c in range(w)] for _r in range(h)]
        if len({v for row in g for v in row}) >= 2 and not _is_lr_sym(g) and not _is_ud_sym(g):
            return g
    g = [[palette[(r * 2 + c) % len(palette)] for c in range(w)] for r in range(h)]
    _ensure_informative(g, palette)
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

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 15 or w > 15:
        errs.append("input too large for 2x kaleidoscope")
    if h * w > 25:
        errs.append(f"default instance too large for canonical mirror task: {h}x{w}")
    if len({v for row in grid for v in row}) < 2:
        errs.append("grid should contain at least two colors")
    if _is_lr_sym(grid):
        errs.append("input is LR-symmetric, so the left/right mirror is hidden")
    if _is_ud_sym(grid):
        errs.append("input is UD-symmetric, so the top/bottom mirror is hidden")
    return errs
