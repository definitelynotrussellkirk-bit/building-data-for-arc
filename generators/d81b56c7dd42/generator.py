"""Generator for ARC task 0c786b71.

Rule: `(rule! (lambda (g) (kaleidoscope (rotate-180 g))))`. The output
is a 2H × 2W kaleidoscope of the (rotated) input — four reflected copies.

Combinatorial axes:
  * grid_h / grid_w        — outer canvas size (small; output is 2x)
  * palette_size           — number of distinct colors
  * texture                — per-cell pattern (noise/sparse/blob/...)
  * bg_density             — bias toward more / fewer bg cells
  * noise_overlay          — small perturbation
  * caller-opt-in degenerates: rot180_symmetric (kaleidoscope no-op-ish),
                               monochrome (uniform output), single_pixel
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "d81b56c7dd42"
VERSION = "1.1.0"  # bumped: deeper combinatorial axes added
TASK_ID = "d81b56c7dd42"
SUMMARY = "Small multicolor seed grid; rule rotates 180° and applies a 4-quadrant kaleidoscope."

INVARIANTS = [
    "input dimensions are small (output is 2× each axis, must be ≤30)",
    "≥3 colors so the kaleidoscope output is rich",
    "input is not 180°-symmetric (else the rotate is invisible)",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("rot180_symmetric", "monochrome", "single_pixel")

AXES = {
    "grid_h":         {"type": "int",   "default": "rng 2..7",  "valid": "1..15"},
    "grid_w":         {"type": "int",   "default": "rng 3..7",  "valid": "1..15"},
    "palette_size":   {"type": "int",   "default": "rng 3..6",  "valid": "2..10"},
    "texture":        {"type": "str",   "default": "rng helpful",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "bg_density":     {"type": "float", "default": "rng 0..0.3", "valid": "0..0.9"},
    "noise_overlay":  {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 2, 4, 3, 4, 3, 4
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 6, 7, 6, 7, 5, 6
    else:
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 2, 7, 3, 7, 3, 6

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    n_colors = ctx.draw_int("palette_size", c_lo, c_hi)
    palette = ctx.draw_distinct_colors("palette", n=n_colors)
    rng = ctx.draw_rng("cells")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, palette, rng)

    texture = overrides.get(
        "texture",
        ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    g = fill_texture(texture, h, w, palette, rng)

    bg_d = float(overrides.get(
        "bg_density",
        ctx.draw_rng("bg_density").uniform(0.0, 0.3)))
    if bg_d > 0.0:
        g = apply_bg_density(g, palette, rng, bg_d)
    no = float(overrides.get(
        "noise_overlay",
        ctx.draw_rng("noise_overlay").uniform(0.0, 0.05)))
    if no > 0.0:
        g = apply_noise_overlay(g, palette, rng, no)

    # Some helpful textures plus bg-density can collapse to bg + one foreground
    # color.  That makes the four-quadrant kaleidoscope visually impoverished,
    # so force at least three visible colors in the normal path.
    while len({v for row in g for v in row}) < 3:
        used = {v for row in g for v in row}
        missing = [c for c in palette if c not in used]
        if not missing:
            break
        counts = {}
        for row in g:
            for v in row:
                counts[v] = counts.get(v, 0) + 1
        candidates = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row)
                      if counts.get(v, 0) > 1]
        if not candidates:
            candidates = [(r, c) for r in range(h) for c in range(w)]
        rr, cc = rng.choice(candidates)
        g[rr][cc] = missing[0]

    # Force 180°-asymmetry by toggling a corner if needed.
    if _is_rot180_symmetric(g):
        g[0][0] = palette[1] if len(palette) > 1 else (g[0][0] + 1) % 10
        if _is_rot180_symmetric(g):
            g[0][min(w - 1, 1)] = palette[2] if len(palette) > 2 else palette[0]
    return g


def _is_rot180_symmetric(g):
    h, w = len(g), len(g[0])
    return all(g[r][c] == g[h - 1 - r][w - 1 - c]
               for r in range(h) for c in range(w))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if 2 * h > 30 or 2 * w > 30:
        errs.append(f"kaleidoscope output would exceed 30x30: input {h}x{w}")
    colors = {v for row in grid for v in row}
    if len(colors) < 3:
        errs.append(f"default path should expose at least 3 colors, found {len(colors)}")
    if _is_rot180_symmetric(grid):
        errs.append("input is 180-degree symmetric, hiding the rotate-180 step")
    return errs


def _draw_from_degenerate(name, h, w, palette, rng):
    """Edge-case where the kaleidoscope/rotate signature is hidden.

    rot180_symmetric — input is its own rotation; the 180° step is invisible.
    monochrome       — uniform input → uniform output.
    single_pixel     — one non-bg cell; kaleidoscope produces a sparse
                       symmetric pattern that's hard to read.
    """
    g = full_grid(h, w, palette[0])
    if name == "rot180_symmetric":
        for _ in range(rng.randint(2, 4)):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            color = rng.choice(palette[1:]) if len(palette) > 1 else palette[0]
            g[r][c] = color
            g[h - 1 - r][w - 1 - c] = color
        return g
    if name == "monochrome":
        color = palette[1] if len(palette) > 1 else palette[0]
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "single_pixel":
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if r == h - 1 - r and c == w - 1 - c and h > 1:
            r = max(0, r - 1)
        g[r][c] = palette[1] if len(palette) > 1 else palette[0]
        return g
    return g
