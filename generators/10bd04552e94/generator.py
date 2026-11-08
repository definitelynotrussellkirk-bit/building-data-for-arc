"""Generator for arc_puzzle_bank_21_set22_bundle:medium_p01.

Rule: pick the largest connected non-zero blob, crop to its bbox.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_largest, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "10bd04552e94"
VERSION = "1.2.1"  # +self_check
TASK_ID = "10bd04552e94"
SUMMARY = "3-4 distinct-color blobs of strictly distinct sizes; rule crops the largest."

INVARIANTS = [
    "background is 0",
    "3 distinct-color blobs with strictly distinct sizes",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_largest", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "palette_size":   {"type": "int", "default": "= n_blobs", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "non_touching",
                       "valid": "non_touching"},
    "n_distinct_colors": {"type": "int", "default": "= n_blobs", "valid": "3..4"},
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
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        size_pool = range(2, 8)
        n_blobs = ctx.draw_int("n_blobs", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 14)
        size_pool = range(3, 13)
        n_blobs = ctx.draw_int("n_blobs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 9, 13)
        size_pool = range(2, 11)
        n_blobs = ctx.draw_int("n_blobs", 3, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # strictly distinct sizes so the largest is unambiguous (rule tie-breaks by
    # bbox but we keep sizes distinct to match the canonical 'biggest wins' demo)
    sizes = rng.sample(list(size_pool), n_blobs)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_blobs)
    used: set[tuple[int, int]] = set()
    for size, color in zip(sizes, palette):
        cells = grow_blob(rng, h, w, used, size, max_attempts=120)
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least 2 distinct non-zero colors (blobs); largest is unique in count."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(len(grid)) for c in range(len(grid[0]))
                     if grid[r][c] != 0)
    errors = []
    if len(counts) < 2:
        errors.append(f"need >=2 distinct blob colors, got {len(counts)}")
        return errors
    vals = sorted(counts.values(), reverse=True)
    if vals[0] == vals[1]:
        errors.append("two blobs share the maximum size — largest not unique for cropping")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "tied_largest":
        # two blobs share the maximum size → which one to crop ambiguous
        for r, c in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 3
        for r, c in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 5
        for r, c in [(7, 1), (7, 2)]: g[r][c] = 7
        return g
    if name == "single_blob":
        # one blob → trivially largest, no comparison
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 6
        return g
    if name == "no_blobs":
        # empty grid → no blob to crop
        return g
    return g
