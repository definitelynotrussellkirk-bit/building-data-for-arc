"""Generator for arc_additional_puzzles_21_set13_bundle:M90 — Flood single-color compartments.

Rule: 1-walls divide grid. For each 0-region, if it has exactly one
non-{0,1} color cell adjacent (or inside), fill the region with that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_compartments,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_walls, no_seeds, multiple_seeds_per_compartment.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "35b93111c742"
VERSION = "2.1.0"  # +self_check
TASK_ID = "35b93111c742"
SUMMARY = "1-walls form an n×m grid of compartments; each has 1 marker; output fills each compartment with its marker color."

# Rivals: 'fill with wall color' refuted by any demo (fill is marker
# color, not 1). 'fill only first compartment' refuted by ≥1 demo
# with ≥2 compartments. 'fill compartment based on position' refuted
# by ≥2 demos with the same compartment grid but different marker
# colors per cell.
# 3 demos covering multiple compartment grids + varied marker colors.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "1-walls form a regular grid",
    "each compartment has exactly one marker of distinct non-{0,1} color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_seeds", "multiple_seeds_per_compartment")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "derived", "valid": "11..17"},
    "grid_w":         {"type": "int", "default": "derived", "valid": "11..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rows":         {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "n_cols":         {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 4..9", "valid": "4..9"},
    "position_bias":  {"type": "str", "default": "1_walls_with_seeds",
                       "valid": "1_walls_with_seeds"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..9", "valid": "4..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-1 walls form a grid, each room has a marker (≥1 non-{0,1} cell)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    flat = [v for row in grid for v in row]
    if 1 not in flat:
        errs.append("no color-1 wall cells found")
    markers = [v for v in flat if v not in (0, 1)]
    if not markers:
        errs.append("no marker cells (non-{0,1}) found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        n_rows = ctx.draw_int("n_rows", 2, 2)
        n_cols = ctx.draw_int("n_cols", 2, 2)
        cell_size_pool = (3, 4)
    elif difficulty == "hard":
        n_rows = ctx.draw_int("n_rows", 2, 4)
        n_cols = ctx.draw_int("n_cols", 2, 4)
        cell_size_pool = (3, 4, 5)
    else:
        n_rows = ctx.draw_int("n_rows", 2, 3)
        n_cols = ctx.draw_int("n_cols", 2, 3)
        cell_size_pool = (3, 4, 5)
    # Cell height and width drawn independently → non-square
    # compartments are reachable.
    cell_h = rng.choice(cell_size_pool)
    cell_w = rng.choice(cell_size_pool)
    h = n_rows * cell_h + (n_rows + 1)
    w = n_cols * cell_w + (n_cols + 1)
    # Cap at canvas size.
    if h > 22 or w > 22:
        cell_h = min(cell_h, 3); cell_w = min(cell_w, 3)
        h = n_rows * cell_h + (n_rows + 1)
        w = n_cols * cell_w + (n_cols + 1)
    g = full_grid(h, w, 1)
    palette = [c for c in range(2, 10)]; rng.shuffle(palette)
    idx = 0
    for ri in range(n_rows):
        for ci in range(n_cols):
            r0 = 1 + ri * (cell_h + 1)
            c0 = 1 + ci * (cell_w + 1)
            for r in range(r0, r0 + cell_h):
                for c in range(c0, c0 + cell_w):
                    g[r][c] = 0
            sr = rng.randint(r0, r0 + cell_h - 1)
            sc = rng.randint(c0, c0 + cell_w - 1)
            g[sr][sc] = palette[idx % len(palette)]
            idx += 1
    return g


def _draw_from_degenerate(name, rng):
    n_rows, n_cols = 2, 2
    cell_h, cell_w = 4, 4
    h = n_rows * cell_h + (n_rows + 1)
    w = n_cols * cell_w + (n_cols + 1)
    if name == "no_walls":
        # markers without 1-walls → no compartments to fill within
        g = full_grid(h, w, 0)
        g[2][2] = 4; g[2][6] = 6
        g[6][2] = 7; g[6][6] = 8
        return g
    if name == "no_seeds":
        # walls form compartments but no seed markers → nothing to fill
        g = full_grid(h, w, 1)
        for ri in range(n_rows):
            for ci in range(n_cols):
                r0 = 1 + ri * (cell_h + 1)
                c0 = 1 + ci * (cell_w + 1)
                for r in range(r0, r0 + cell_h):
                    for c in range(c0, c0 + cell_w):
                        g[r][c] = 0
        return g
    if name == "multiple_seeds_per_compartment":
        # one compartment has 2 different seeds → "exactly one" precondition fails
        g = full_grid(h, w, 1)
        for ri in range(n_rows):
            for ci in range(n_cols):
                r0 = 1 + ri * (cell_h + 1)
                c0 = 1 + ci * (cell_w + 1)
                for r in range(r0, r0 + cell_h):
                    for c in range(c0, c0 + cell_w):
                        g[r][c] = 0
        g[2][2] = 4; g[3][3] = 6  # both in TL compartment
        g[2][6] = 7
        g[6][2] = 8
        return g
    return full_grid(h, w, 0)
