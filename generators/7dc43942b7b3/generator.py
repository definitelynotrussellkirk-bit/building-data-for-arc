"""Generator for arc_puzzle_bank_21_set9_s:S9_M4.

Rule: sort blobs ascending by area; recolor smallest=2, next=3, next=4.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "7dc43942b7b3"
VERSION = "2.0.1"
TASK_ID = "7dc43942b7b3"
SUMMARY = "Exactly 3 blobs of strictly distinct sizes in distinct (non-2/3/4) colors. Rule sorts blobs ascending by area and recolors them to 2 (smallest), 3 (middle), 4 (largest); positions preserved."

# Rivals: 'preserve original colors' refuted by any demo (all blobs
# get recolored). 'recolor by position (first-in-reading-order)'
# refuted by any demo where size order != reading order. 'recolor
# largest = 2' refuted by any demo where smallest gets 2. 'use bg
# for one blob' refuted by any demo. 3 demos with varied size orders
# cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 3 distinct-color blobs with strictly distinct sizes",
    "input colors aren't already 2/3/4 in size order (rule isn't identity)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "non_touching",
                       "valid": "non_touching"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥3 distinct nonzero colors present (three blobs)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    colors = {v for row in grid for v in row if v != 0}
    if len(colors) < 3:
        return [f"expected ≥3 distinct nonzero colors; found {len(colors)}: {sorted(colors)}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 11)
        size_pool = list(range(1, 6))
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 14, 18)
        size_pool = list(range(2, 11))
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 14)
        size_pool = list(range(2, 8))
    g = full_grid(h, w, 0)
    sizes = sorted(rng.sample(size_pool, 3))
    palette = rng.sample([5, 6, 7, 8, 9], 3)
    used: set[tuple[int, int]] = set()
    for size, color in zip(sizes, palette):
        cells = grow_blob(rng, h, w, used, size, max_attempts=80)
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # two blobs share size → rank tie, mapping ambiguous
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 5
        for r, c in [(5, 5), (5, 6)]: g[r][c] = 6
        for r, c in [(7, 1), (7, 2), (8, 1)]: g[r][c] = 7
        return g
    if name == "single_blob":
        # one blob → trivially recolored to 2, no rank progression
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 6
        return g
    if name == "no_blobs":
        # empty grid → no blobs to recolor
        return g
    return g
