"""Generator for arc_puzzle_bank_21_set9_e:medium_i09 — recolor by area rank.

Rule: sort blobs by ascending area, recolor by palette[i] (e.g. 2/3/4).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "bc72c2d915c9"
VERSION = "2.0.1"  # add self_check
TASK_ID = "bc72c2d915c9"
SUMMARY = (
    "0-bg grid with N (3-5) connected blobs in distinct non-zero "
    "colors. Each blob has a strictly distinct size from all others "
    "(so the size-rank is unambiguous). Blobs are placed with ≥1-cell "
    "buffer so they don't 4-touch. Rule: sort all 4-connected non-bg "
    "components by (size ASC, then top-row ASC, then left-col ASC). "
    "Recolor the i-th component to palette[i] where palette = [2, 3, "
    "4, 6, 7, 8, 9]. Output: same shapes, new colors based on size-rank."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "3-5 connected blobs in distinct non-zero colors",
    "blobs have strictly distinct sizes (so size-rank is unambiguous)",
    "blobs don't 4-touch (separated components)",
    "input colors should NOT all match the rank palette (so recolor is visible)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..18"},
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
    """Verify: bg=0; >=2 distinct nonzero colors (blobs with distinct sizes)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not colors:
        return errs  # degenerate no_blobs
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct blob colors, got {len(colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        n_blobs = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        n_blobs = ctx.draw_int("n_blobs", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        n_blobs = ctx.draw_int("n_blobs", 3, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    sizes = rng.sample(range(1, 9), n_blobs)
    palette = rng.sample([1, 5, 6, 7, 8, 9], n_blobs)
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
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # two blobs same size → rank-based recolor mapping is ambiguous
        for r, c in [(1, 1), (2, 1)]:
            g[r][c] = 5
        for r, c in [(5, 5), (5, 6)]:
            g[r][c] = 7
        for r, c in [(6, 1), (6, 2), (7, 1)]:
            g[r][c] = 9
        return g
    if name == "single_blob":
        # only one blob → smallest = largest, ranking is degenerate
        for r, c in [(3, 3), (3, 4), (4, 3)]:
            g[r][c] = 6
        return g
    if name == "no_blobs":
        # empty grid → no blobs to recolor
        return g
    return g
