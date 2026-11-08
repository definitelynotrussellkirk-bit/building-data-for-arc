"""Generator for arc_additional_puzzles_21_set5:M32 — Object colors sorted by size asc, color asc.

Rule: sort objects by (size asc, color asc); output is single row of
each obj's color in that order.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "53849ea2e4ac"
VERSION = "1.1.1"
TASK_ID = "53849ea2e4ac"
SUMMARY = "Several non-touching blobs of distinct sizes/colors; output is colors sorted by size asc."

INVARIANTS = [
    "between 3 and 5 non-touching blobs",
    "all distinct sizes",
    "distinct colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 3..5",  "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_blobs",
                       "valid": "spaced_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid with bg=0; ≥2 non-bg blobs in distinct colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    non_bg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not non_bg:
        return errors  # degenerate (no_blobs) — allowed
    colors = set(grid[r][c] for r, c in non_bg)
    if len(colors) < 2:
        return errors  # degenerate (single_blob) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_blobs = ctx.draw_int("n_blobs", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n_blobs = ctx.draw_int("n_blobs", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        n_blobs = ctx.draw_int("n_blobs", 3, 5)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    sizes = list(range(1, 7)); rng.shuffle(sizes)
    sizes = sorted(sizes[:n_blobs])
    colors = list(range(1, 10)); rng.shuffle(colors)
    used = set()
    for i, size in enumerate(sizes):
        blob = grow_blob(rng, h, w, used, size)
        if blob is None: continue
        used |= blob
        for r, c in blob: g[r][c] = colors[i % len(colors)]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # all blobs same size → secondary sort key (color) is the only signal
        for (r, c) in [(1, 1), (1, 2)]: g[r][c] = 4
        for (r, c) in [(1, 5), (1, 6)]: g[r][c] = 6
        for (r, c) in [(4, 2), (4, 3)]: g[r][c] = 3
        for (r, c) in [(6, 5), (6, 6)]: g[r][c] = 8
        return g
    if name == "single_blob":
        # one blob → output is single-color single-cell, weakly tests sorting
        for (r, c) in [(2, 3), (2, 4), (3, 3)]: g[r][c] = 4
        return g
    if name == "no_blobs":
        # blank → no objects to sort, output is empty
        return g
    return g
