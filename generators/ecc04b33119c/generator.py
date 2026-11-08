"""Generator for ARC task 00576224.

Rule: output is 3h × 3w. For tile row block (r // h): if even, use
input as-is; else, use input's LR mirror. Effect: 3-row vertical
tiling with alternating LR mirror.

Combinatorial axes: grid_h/w, palette_size, texture, lr_asymmetric.
Degenerates: monochrome, lr_symmetric (mirror invisible), single_pixel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "ecc04b33119c"
VERSION = "2.1.0"  # add self_check + canonical-scale default 2..4 tiles
TASK_ID = "ecc04b33119c"
SUMMARY = "Small LR-ASYMMETRIC multicolor tile (w>=2); rule tiles 3x3, with the MIDDLE row-block LR-mirrored (top/bottom straight). Output is 3h x 3w. Asymmetry is enforced so the middle (mirrored) block differs from the straight blocks -- the rule's distinguishing feature stays visible."

INVARIANTS = [
    "input dims ≤ (9, 9) so 3 × output fits the 30-canvas",
    "width >= 2 (w=1 is always LR-symmetric -> mirror invisible)",
    "≥2 colors so the mirror is visible",
    "input is NOT LR-symmetric (else the mirrored middle block looks identical)",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("monochrome", "lr_symmetric", "single_pixel")

AXES = {
    "grid_h":         {"type": "int",   "default": "rng 2..9 by diff", "valid": "1..9"},
    "grid_w":         {"type": "int",   "default": "rng 2..9 by diff", "valid": "2..9"},
    "palette_size":   {"type": "int",   "default": "rng 2..8 by diff", "valid": "1..10"},
    "texture":        {"type": "str",   "default": "rng helpful",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "bg_density":     {"type": "float", "default": "rng 0..0.4", "valid": "0..0.95"},
    "noise_overlay":  {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
    "lr_asymmetric":  {"type": "bool",  "default": "true", "valid": "true|false"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 2, 3, 2, 3, 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 5, 9, 5, 9, 5, 8
    else:
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 2, 4, 2, 4, 2, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)   # w>=2: w=1 is always LR-symmetric
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
    # Robustly force LR-asymmetry so the mirrored middle block differs from the
    # straight top/bottom blocks (the rule's distinguishing feature). The old
    # single-cell g[0][0] poke could leave the tile symmetric (e.g. w=2).
    if bool(overrides.get("lr_asymmetric", True)):
        _force_lr_asym(g, palette, rng)
    return g


def _is_lr_sym(g):
    h = len(g); w = len(g[0])
    return all(g[r][c] == g[r][w - 1 - c] for r in range(h) for c in range(w))


def _force_lr_asym(g, palette, rng):
    h = len(g); w = len(g[0])
    if w < 2:
        return
    pool = list(palette) if len(palette) > 1 else [0, 1, 2, 3, 4]
    for _ in range(60):
        if not _is_lr_sym(g):
            return
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w // 2 - 1)        # a cell strictly left of its mirror
        mirror = g[r][w - 1 - c]
        alt = [v for v in pool if v != mirror]
        if alt:
            g[r][c] = rng.choice(alt)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the tile is a non-degenerate LR-asymmetric input for 3x tiling."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 9 or w > 9:
        errs.append(f"input {h}x{w} would exceed 30x30 after 3x tiling")
    if w < 2:
        errs.append("width < 2 makes LR mirror invisible")
    if len({v for row in grid for v in row}) < 2:
        errs.append("monochrome tile makes mirror invisible")
    if _is_lr_sym(grid):
        errs.append("LR-symmetric tile makes the mirrored middle band identical")
    return errs


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
    if name == "single_pixel":
        rr = rng.randint(0, h - 1); rc = rng.randint(0, w - 1)
        g[rr][rc] = palette[1] if len(palette) > 1 else palette[0]
        return g
    return g
