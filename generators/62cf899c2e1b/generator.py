"""Generator for 7953d61e.

Rule: output is 2N × 2N: TL=g, TR=rotate-ccw, BL=rotate-180, BR=rotate-cw.

Combinatorial axes (8): grid_n, palette_size, texture, fg_density,
asymmetry_force, anchor_corner, noise_overlay, bg_density.
Degenerates: monochrome, full_4fold_sym, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "62cf899c2e1b"
VERSION = "2.0.1"
TASK_ID = "62cf899c2e1b"
SUMMARY = (
    "Small SQUARE input grid (N×N, N=3..8) using ≥2 distinct "
    "non-zero colors. Grid is NOT 4-fold rotationally symmetric "
    "(so all 4 rotations are visibly different). Various textures "
    "(noise, sparse, blob, stripes, gradient, checker, frame, "
    "ring, plus) provide visual diversity. Rule: build 2N × 2N "
    "output as a 2×2 collage of rotations: TL=identity, "
    "TR=rotate-270° CW (=rotate-90° CCW), BL=rotate-180°, "
    "BR=rotate-90° CW. Each quadrant is an N×N rotated copy of "
    "the input."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is square (h == w), N in [3, 8]",
    "2N ≤ 16 (output fits within typical ARC limits)",
    "input is NOT 4-fold rotationally symmetric (so all 4 quadrants differ)",
    "≥2 distinct colors in input (rotations are visible)",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("monochrome", "full_4fold_sym", "single_cell")

AXES = {
    "grid_n":         {"type": "int", "default": "rng 4..7", "valid": "3..8"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "2..7"},
    "texture":        {"type": "str", "default": "rng helpful",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "fg_density":     {"type": "float", "default": "rng 0.4..0.7",
                       "valid": "0.1..1"},
    "bg_density":     {"type": "float", "default": "rng 0..0.3",
                       "valid": "0..0.7"},
    "noise_overlay":  {"type": "float", "default": "rng 0..0.05",
                       "valid": "0..0.2"},
    "asymmetry_force": {"type": "bool", "default": "true",
                        "valid": "true|false"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid is square, N in [3,8], has non-zero cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    if h != w:
        errs.append(f"grid not square: {h}x{w}")
    elif not (3 <= h <= 8):
        errs.append(f"N={h} out of range [3,8]")
    nonzero = any(grid[r][c] != 0 for r in range(h) for c in range(w))
    if not nonzero:
        errs.append("no non-zero cells in grid")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        n_lo, n_hi, c_lo, c_hi = 3, 4, 2, 3
    elif difficulty == "hard":
        n_lo, n_hi, c_lo, c_hi = 6, 8, 4, 7
    else:
        n_lo, n_hi, c_lo, c_hi = 4, 7, 2, 5
    n = ctx.draw_int("grid_n", n_lo, n_hi)
    n_colors = ctx.draw_int("palette_size", c_lo, c_hi)
    palette = list(ctx.draw_distinct_colors("palette", n=max(2, n_colors)))
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], n, palette, rng)
    texture = overrides.get("texture",
                            ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    g = fill_texture(texture, n, n, palette, rng)
    bg_d = float(overrides.get("bg_density",
                               ctx.draw_rng("bg_density").uniform(0.0, 0.3)))
    if bg_d > 0:
        g = apply_bg_density(g, palette, rng, bg_d)
    no = float(overrides.get("noise_overlay",
                             ctx.draw_rng("noise_overlay").uniform(0.0, 0.05)))
    if no > 0:
        g = apply_noise_overlay(g, palette, rng, no)
    if bool(overrides.get("asymmetry_force", True)):
        if _is_4fold_sym(g, n) and len(palette) > 1:
            other = next((c for c in palette if c != g[0][0]), None)
            if other is not None and n >= 2:
                g[0][n - 1] = other
    if bool(overrides.get("anchor_corner", False)):
        g[0][0] = palette[0]
    if len({v for row in g for v in row}) < 2:
        g[0][n - 1] = palette[1] if len(palette) > 1 else (palette[0] + 1) % 10
    return g


def _is_4fold_sym(g, n):
    for r in range(n):
        for c in range(n):
            v = g[r][c]
            if g[c][n - 1 - r] != v:
                return False
            if g[n - 1 - r][n - 1 - c] != v:
                return False
            if g[n - 1 - c][r] != v:
                return False
    return True


def _draw_from_degenerate(name, n, palette, rng):
    g = full_grid(n, n, palette[0])
    if name == "monochrome":
        c = rng.choice(palette)
        return [[c] * n for _ in range(n)]
    if name == "full_4fold_sym":
        for r in range((n + 1) // 2):
            for c in range((n + 1) // 2):
                v = rng.choice(palette)
                g[r][c] = v
                g[c][n - 1 - r] = v
                g[n - 1 - r][n - 1 - c] = v
                g[n - 1 - c][r] = v
        return g
    if name == "single_cell":
        g[n // 2][n // 2] = palette[1] if len(palette) > 1 else (palette[0] + 1) % 10
        return g
    return g
