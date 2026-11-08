"""Generator for ARC task a59b95c0.

Rule: n = number of distinct colors in input. Output is (h*n) × (w*n)
where each cell is g[r mod h][c mod w]. Tile the input n × n times.

Combinatorial axes: grid_h/w, color_count (n), texture, color_distribution.
Degenerates: monochrome (n=1, output equals input), max_colors,
single_color_per_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "a70bcf3f2c88"
VERSION = "1.1.1"
TASK_ID = "a70bcf3f2c88"
SUMMARY = "Small multicolor grid; rule tiles n × n times where n = number of distinct colors."

INVARIANTS = [
    "(h * n) ≤ 30 and (w * n) ≤ 30 so tiled output fits",
    "≥2 distinct colors so the tiling factor is informative",
    "all colors appear ≥ once",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("monochrome", "max_colors", "single_pixel_per_color")

AXES = {
    "grid_h":         {"type": "int", "default": "rng 3..6", "valid": "2..7"},
    "grid_w":         {"type": "int", "default": "rng 3..6", "valid": "2..7"},
    "color_count":    {"type": "choice", "default": "rng 2|3|4|5", "valid": "2|3|4|5"},
    "texture":        {"type": "str", "default": "rng helpful",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "bg_density":     {"type": "float", "default": "rng 0..0.3", "valid": "0..0.95"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 distinct colors; h*n ≤ 30 and w*n ≤ 30 (n = distinct color count)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    all_colors = {v for row in grid for v in row}
    n = len(all_colors)
    if n < 2:
        return errs  # degenerate (monochrome) — allowed
    if h * n > 30:
        errs.append(f"h*n={h*n} > 30 — tiled output would not fit")
    if w * n > 30:
        errs.append(f"w*n={w*n} > 30 — tiled output would not fit")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, c_choices = 3, 4, [2, 3]
    elif difficulty == "hard":
        h_lo, h_hi, c_choices = 5, 6, [4, 5]
    else:
        h_lo, h_hi, c_choices = 3, 6, [2, 3, 4, 5]
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    n = ctx.draw_choice("color_count", c_choices)
    # Output is h*n × w*n — must fit in 30. Cap n if too big.
    while h * n > 30 or w * n > 30:
        n -= 1
    if n < 1:
        n = 1
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, n, rng)
    palette = list(ctx.draw_distinct_colors("palette", n=max(1, n), exclude={0}))
    texture = overrides.get("texture",
                            ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    g = fill_texture(texture, h, w, palette, rng)
    bg_d = float(overrides.get("bg_density",
                               ctx.draw_rng("bg_density").uniform(0.0, 0.3)))
    if bg_d > 0.0:
        g = apply_bg_density(g, palette, rng, bg_d)
    # Force exactly n distinct colors. Place each palette color at least once.
    for i, color in enumerate(palette):
        rr = i % h; rc = (i // h) % w
        g[rr][rc] = color
    # Verify n is actually the distinct color count.
    actual_n = len({v for row in g for v in row})
    if actual_n != n:
        # Adjust: either remove extras or add missing.
        if actual_n > n:
            # Reduce by replacing rarer colors with palette[0].
            counts = {}
            for r in range(h):
                for c in range(w):
                    counts[g[r][c]] = counts.get(g[r][c], 0) + 1
            keep = sorted(counts, key=lambda k: -counts[k])[:n]
            for r in range(h):
                for c in range(w):
                    if g[r][c] not in keep:
                        g[r][c] = keep[0]
    return g


def _draw_from_degenerate(name, h, w, n, rng):
    palette = list(range(1, 10))
    rng.shuffle(palette)
    g = full_grid(h, w, palette[0])
    if name == "monochrome":
        c0 = palette[0]
        for r in range(h):
            for c in range(w):
                g[r][c] = c0
        return g
    if name == "max_colors":
        # Use 5 distinct colors so n=5; output is (h*5) × (w*5) → fits if h,w ≤6.
        if h * 5 > 30 or w * 5 > 30:
            h = w = 5
            g = full_grid(h, w, palette[0])
        used = palette[:5]
        for i, color in enumerate(used):
            rr = i % h; rc = (i // h) % w
            g[rr][rc] = color
        return g
    if name == "single_pixel_per_color":
        # Spread n distinct colors thinly.
        used = palette[:max(1, n)]
        for i, color in enumerate(used):
            rr = i % h; rc = (i // h) % w
            g[rr][rc] = color
        return g
    return g
