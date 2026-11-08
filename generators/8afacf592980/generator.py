"""Generator for arc_additional_puzzles_21_set14_bundle:E96 — Most-frequent color, repeated total-count times in 1 row.

Rule: count all non-bg cells. Find most-frequent color. Output single
row with that color repeated total-count times (length = total cells).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_colors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_frequencies, single_color, all_bg.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8afacf592980"
VERSION = "2.0.0"  # dup37%: total cell count N stayed in a tiny range (counts 1-4) so the 1xN majority-color output had few distinct (N,color) values. Widen the majority count (3-9) and distractor counts + full color range + larger grids -> output width N and color vary.
TASK_ID = "8afacf592980"
SUMMARY = "Scattered cells of 2-4 colors where one color is uniquely most-frequent. Rule outputs a single row of length N (total nonzero cells) all in the majority color. Total count N (output width), the majority color, and grid size all vary."

INVARIANTS = [
    "≥2 distinct non-bg colors",
    "≥1 color is uniquely most-frequent",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_frequencies", "single_color", "all_bg")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_colors":       {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "scattered_distinct_freqs",
                       "valid": "scattered_distinct_freqs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 6); w = ctx.draw_int("grid_w", 6, 8)
        maj_lo, maj_hi, nc_lo, nc_hi = 3, 5, 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 10); w = ctx.draw_int("grid_w", 9, 12)
        maj_lo, maj_hi, nc_lo, nc_hi = 6, 10, 3, 4
    else:
        h = ctx.draw_int("grid_h", 5, 8); w = ctx.draw_int("grid_w", 7, 10)
        maj_lo, maj_hi, nc_lo, nc_hi = 4, 8, 2, 4
    rng = ctx.draw_rng("layout")
    n_colors = rng.randint(nc_lo, nc_hi)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_colors)
    maj_count = rng.randint(maj_lo, maj_hi)
    # distractor colors get strictly fewer cells -> palette[0] is uniquely top
    counts = [maj_count] + [rng.randint(1, maj_count - 1) for _ in range(n_colors - 1)]
    total = sum(counts)
    g = full_grid(h, w, 0)
    cells = [(r, c) for r in range(h) for c in range(w)]
    if total > len(cells):                 # shouldn't happen, but guard
        return g
    rng.shuffle(cells)
    idx = 0
    for color, cnt in zip(palette, counts):
        for _ in range(cnt):
            r, c = cells[idx]; idx += 1
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 7
    g = full_grid(h, w, 0)
    if name == "tied_frequencies":
        # 2 colors with equal counts → "most-frequent" is ambiguous
        g[0][0] = 4; g[0][1] = 4; g[0][2] = 4
        g[1][0] = 6; g[1][1] = 6; g[1][2] = 6
        return g
    if name == "single_color":
        # only 1 color → trivial: output is that color repeated N times
        g[0][0] = 4; g[1][2] = 4; g[2][3] = 4; g[3][1] = 4
        return g
    if name == "all_bg":
        # blank → no colors at all, total count 0
        return g
    return g
