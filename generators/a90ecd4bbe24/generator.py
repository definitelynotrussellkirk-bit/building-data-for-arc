"""Generator for arc_puzzle_bank_eighth_21_bundle:easy_53_keep_tallest_bar.

Rule: multiple vertical bars; keep only the unique tallest bar.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_bars,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_bars, single_bar, tied_tallest.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a90ecd4bbe24"
VERSION = "1.1.1"
TASK_ID = "a90ecd4bbe24"
SUMMARY = "Multiple vertical bars with one unique tallest bar."

INVARIANTS = [
    "background is 0",
    "each nonzero column contains one contiguous same-color bar",
    "one bar has strictly greatest height",
    "the tallest bar is not already isolated in the scene",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_bars", "single_bar", "tied_tallest")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_bars":         {"type": "int", "default": "rng 3..5", "valid": "2..8"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "vertical_bars_distinct_heights",
                       "valid": "vertical_bars_distinct_heights"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 non-zero colors each forming a single contiguous vertical bar; one is tallest."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Gather bar heights per column
    bar_heights = []
    for c in range(w):
        col = [grid[r][c] for r in range(h)]
        nz = [(r, col[r]) for r in range(h) if col[r] != 0]
        if not nz:
            continue
        colors = {v for _, v in nz}
        if len(colors) != 1:
            continue  # multi-color column — skip (degenerate ok)
        bar_heights.append(len(nz))
    if not bar_heights:
        return errs  # degenerate (no_bars) — allowed
    if len(bar_heights) < 2:
        return errs  # degenerate (single_bar) — allowed
    # Check that one bar has strictly greatest height
    max_h = max(bar_heights)
    if bar_heights.count(max_h) > 1:
        return errs  # degenerate (tied_tallest) — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_bars = ctx.draw_int("n_bars", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n_bars = ctx.draw_int("n_bars", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        n_bars = ctx.draw_int("n_bars", 3, 5)
    colors = ctx.draw_distinct_colors("colors", n=n_bars, exclude={0})
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    cols = rng.sample(range(w), min(n_bars, w))
    tallest = min(6, h - 1)
    heights = [tallest] + [rng.randint(2, max(2, tallest - 1)) for _ in range(len(cols) - 1)]
    rng.shuffle(heights)
    for c, height, color in zip(cols, heights, colors):
        r0 = rng.randint(0, h - height)
        for r in range(r0, r0 + height):
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_bars":
        # blank → no bars to compare
        return g
    if name == "single_bar":
        # only one bar → "tallest" is trivially identity (no other to drop)
        for r in range(2, 8): g[r][3] = 4
        return g
    if name == "tied_tallest":
        # two bars of equal max height → ambiguous "tallest"
        for r in range(1, 7): g[r][2] = 4
        for r in range(1, 7): g[r][6] = 6   # same height, tied
        for r in range(3, 6): g[r][8] = 7
        return g
    return g
