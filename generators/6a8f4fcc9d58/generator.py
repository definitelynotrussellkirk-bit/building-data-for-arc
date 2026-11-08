"""Generator for arc_additional_puzzle_bank_volume14:M97: colors sorted by component size.

Rule: disconnected nonzero components have unique sizes; output lists
their colors largest-first.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_components,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes, single_component, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6a8f4fcc9d58"
VERSION = "2.0.1"
TASK_ID = "6a8f4fcc9d58"
SUMMARY = (
    "0-bg grid (h~9-12, w~10-14) with 3-5 ISOLATED 4-conn "
    "components, each in a distinct non-bg color and with "
    "a STRICTLY DISTINCT cell count (sizes drawn from "
    "{1..7}). Components are separated by background. "
    "Rule: extract all 4-conn non-bg components. Sort "
    "them by size DESCENDING (with each size unique by "
    "construction). Output is a 1×N row where N = number "
    "of components, each cell = the color of the "
    "corresponding component in size-rank order. Net: a "
    "histogram-by-rank single-row encoding."
)
INVARIANTS = [
    "components are 4-connected and separated by background",
    "component sizes are unique",
    "component colors are nonzero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "single_component", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "6..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_components":   {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "spread_distinct_sizes",
                       "valid": "spread_distinct_sizes"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; >=2 distinct non-zero colors (components to sort by size)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    colors = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not colors:
        return errs  # degenerate blank — allowed
    if len(colors) < 2:
        errs.append(f"only {len(colors)} distinct color(s); need >=2 to sort by size")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        n = ctx.draw_int("n_components", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 14)
        n = ctx.draw_int("n_components", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        n = ctx.draw_int("n_components", 3, 5)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    sizes = list(range(1, 8))
    rng.shuffle(sizes)
    sizes = sorted(sizes[:n], reverse=True)
    colors = list(ctx.draw_distinct_colors("colors", n=n, exclude={0}))
    used = set()
    for i, size in enumerate(sizes):
        cells = grow_blob(rng, h, w, used, size)
        if cells is None:
            continue
        used |= cells
        for r, c in cells:
            g[r][c] = colors[i]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # multiple components share max size → "largest" is ambiguous, sort order undefined
        for (r, c) in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4   # size 3
        for (r, c) in [(5, 6), (5, 7), (6, 6)]: g[r][c] = 6   # size 3
        for (r, c) in [(8, 2), (8, 3), (9, 2)]: g[r][c] = 3   # size 3
        return g
    if name == "single_component":
        # one component → no comparison, output trivially that color
        for (r, c) in [(3, 4), (3, 5), (4, 4), (4, 5), (5, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # multiple components, all same color → output is a single repeated color, no contrast
        for (r, c) in [(1, 1), (1, 2)]: g[r][c] = 4
        for (r, c) in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 4
        for (r, c) in [(8, 8), (8, 9), (9, 8), (9, 9)]: g[r][c] = 4
        return g
    return g
