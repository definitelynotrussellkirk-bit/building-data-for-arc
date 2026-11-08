"""Generator for puzzle 6fa7a44f.

Rule: output is 2h × w with input as the top half and its UD mirror as
the bottom half — i.e., `vconcat g (flip-ud g)`.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "5cff884f1d16"
VERSION = "2.0.0"
TASK_ID = "5cff884f1d16"
SUMMARY = (
    "Colored grid (h~2-12, w~"
    "2-15) drawn with one of "
    "9 TEXTURE patterns "
    "(noise/sparse/blob/"
    "stripes/gradient/"
    "checkerboard/frame/ring/"
    "plus) from a palette of "
    "2-6 colors with bg_"
    "density 0..0.4 and "
    "noise_overlay 0..0.05. "
    "The grid is guaranteed "
    "NOT UD-SYMMETRIC (forced "
    "asymmetric: g[0][0] is "
    "perturbed if needed) and "
    "has ≥2 distinct colors. "
    "Rule (VCONCAT INPUT + "
    "UD-MIRROR): EMIT a "
    "(2h)×w OUTPUT GRID "
    "where TOP HALF (rows 0.."
    "h-1) = INPUT, and "
    "BOTTOM HALF (rows h.."
    "2h-1) = FLIP_UD(INPUT) "
    "— i.e., row h+k of "
    "output = row h-1-k of "
    "input. The shared edge "
    "(row h-1 vs row h) is "
    "the mirror axis. Net: "
    "input is reflected "
    "downward; output is "
    "input stacked above "
    "its vertical mirror "
    "image."
)

INVARIANTS = [
    "input dims ≤ (15, 30) so doubled output fits within ARC limits",
    "≥2 distinct colors so the mirror is visible",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("monochrome", "ud_symmetric", "single_row")

AXES = {
    "grid_h":         {"type": "int",   "default": "rng 2..12", "valid": "1..15"},
    "grid_w":         {"type": "int",   "default": "rng 2..15", "valid": "1..30"},
    "palette_size":   {"type": "int",   "default": "rng 2..6", "valid": "1..10"},
    "texture":        {"type": "str",   "default": "rng helpful",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "bg_density":     {"type": "float", "default": "rng 0..0.4", "valid": "0..0.95"},
    "noise_overlay":  {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
    "ud_asymmetric":  {"type": "bool",  "default": "true", "valid": "true|false"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 2, 5, 2, 8, 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 9, 12, 12, 15, 5, 8
    else:
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 2, 12, 2, 15, 2, 6
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
    if bool(overrides.get("ud_asymmetric", True)) and _is_ud_sym(g):
        g[0][0] = palette[1] if len(palette) > 1 else (g[0][0] + 1) % 10
    if len({v for row in g for v in row}) < 2:
        g[0][0] = palette[0]
        g[-1][-1] = palette[1] if len(palette) > 1 else (palette[0] + 1) % 10
    return g


def _is_ud_sym(g):
    h = len(g); w = len(g[0])
    return all(g[r][c] == g[h - 1 - r][c] for r in range(h) for c in range(w))


def self_check(grid, *, difficulty=None, meta=None):
    """Verify horizontal-mirror output invariants for 5cff884f1d16."""
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 15 or w > 30:
        errs.append(f"input dims {h}x{w} — doubled output would exceed ARC limits (15x30 max)")
    colors = {grid[r][c] for r in range(h) for c in range(w)}
    if len(colors) < 2:
        errs.append(f"only {len(colors)} distinct color(s) — mirror would be invisible")
    return errs


def _draw_from_degenerate(name, h, w, palette, rng):
    g = full_grid(h, w, palette[0])
    if name == "monochrome":
        c0 = rng.choice(palette)
        for r in range(h):
            for c in range(w):
                g[r][c] = c0
        return g
    if name == "ud_symmetric":
        for c in range(w):
            for r in range(h // 2):
                v = rng.choice(palette)
                g[r][c] = v
                g[h - 1 - r][c] = v
        return g
    if name == "single_row":
        for c in range(w):
            g[0][c] = rng.choice(palette)
        for r in range(1, h):
            for c in range(w):
                g[r][c] = g[0][c]
        return g
    return g
