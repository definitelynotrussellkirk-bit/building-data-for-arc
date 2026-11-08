"""Generator for `arc_additional_puzzles_21_set17_bundle:E119` —
output is a 1xN row of color values, each color repeated by its cell
count, sorted by descending count (ties broken by ascending color).

Concept membership: 2 puzzles share this rule.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_colors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: monochrome, equal_counts, no_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "75ac106ed6a9"
VERSION = "2.0.1"
TASK_ID = "75ac106ed6a9"
SUMMARY = (
    "0-bg grid (h, w ~7-10) with 3-5 distinct non-bg "
    "colors, each occupying a DISTINCT cell count drawn "
    "from {2..7}, scattered uniformly. Total non-bg "
    "cells ≤ 30. Rule: collect (color, count) for each "
    "distinct non-bg color. Sort by DESCENDING count, "
    "ties broken by ASCENDING color value. Output is a "
    "1×N row (N = total non-bg cell count) where each "
    "color appears CONSECUTIVELY repeated by its count, "
    "in sorted order. So a histogram-as-1D-bar-chart "
    "concatenated by frequency rank."
)

INVARIANTS = [
    "background is 0",
    "3-5 distinct non-bg colors",
    "the colors have distinct cell counts",
    "total non-bg cells <= 30 (so output 1xN fits)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("monochrome", "equal_counts", "no_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_colors":       {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "uniform_scatter",
                       "valid": "uniform_scatter"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|monochrome|equal_counts|no_colors"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n_colors = ctx.draw_int("n_colors", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        n_colors = ctx.draw_int("n_colors", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        n_colors = ctx.draw_int("n_colors", 3, 5)
    palette = ctx.draw_distinct_colors("palette", n=n_colors, exclude={0})
    rng = ctx.draw_rng("placement")

    counts = rng.sample(range(2, 8), n_colors)  # distinct counts in [2, 7]
    if sum(counts) > 30:
        counts = [min(c, 6) for c in counts]
    g = full_grid(h, w, 0)
    positions = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(positions)
    idx = 0
    for color, cnt in zip(palette, counts):
        for _ in range(cnt):
            if idx >= len(positions): break
            r, c = positions[idx]; idx += 1
            g[r][c] = color
    return g




def self_check(grid, *, difficulty=None, meta=None):
    from collections import Counter
    counts = Counter(v for row in grid for v in row if v != 0)
    expected = {"easy": (3, 4), "hard": (4, 5)}.get(difficulty, (3, 5))
    errors = []
    if not (expected[0] <= len(counts) <= expected[1]):
        errors.append(f"expected {expected[0]}-{expected[1]} non-bg colors, got {len(counts)}")
    if len(counts.values()) != len(set(counts.values())):
        errors.append(f"color counts should be distinct to avoid tie ambiguity, got {dict(counts)}")
    return errors

def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "monochrome":
        # Only one non-bg color — rule output is a single-color 1xN.
        for i, (r, c) in enumerate([(1, 1), (1, 2), (1, 3), (2, 1)]):
            g[r][c] = 5
        return g
    if name == "equal_counts":
        # All colors have same count — sort tie-break is ambiguous.
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 3
        for r, c in [(2, 1), (2, 2)]: g[r][c] = 4
        for r, c in [(3, 1), (3, 2)]: g[r][c] = 5
        return g
    if name == "no_colors":
        # All-bg input — rule has no colors to count.
        return g
    return g
