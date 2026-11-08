"""Generator for arc_puzzle_bank_21_set11_bundle:easy_k01.

Rule: sparse nonzero singleton cells are copied to their vertical
mirror positions.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seed_on_axis, mirror_target_occupied.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c4155b3fcecd"
VERSION = "1.2.0"  # exclude the vertical mirror axis from normal seeds so every marker has a distinct copy target.
TASK_ID = "c4155b3fcecd"
SUMMARY = "Sparse nonzero singleton cells are copied to their vertical mirror positions."

INVARIANTS = [
    "input cells are sparse nonzero singleton markers",
    "markers avoid duplicate mirror pairs",
    "background is zero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "seed_on_axis", "mirror_target_occupied")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "3..12"},
    "grid_w":         {"type": "int", "default": "rng 6..10", "valid": "3..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "left_half", "valid": "left_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "mixed", "valid": "mixed"},
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
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 6, 7)
        n = ctx.draw_int("n_seeds", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        n = ctx.draw_int("n_seeds", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 6, 10)
        n = ctx.draw_int("n_seeds", 2, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Use the strict left half only.  The previous `(w + 1) // 2` included
    # the central column for odd-width grids, producing axis seeds whose mirror
    # is themselves — the explicit degenerate case leaked into normal samples.
    positions = [(r, c) for r in range(h) for c in range(w // 2)]
    rng.shuffle(positions)
    colors = list(ctx.draw_distinct_colors("colors", n=min(n, 9), exclude={0}))
    for i, (r, c) in enumerate(positions[:n]):
        g[r][c] = colors[i % len(colors)]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 7
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # empty grid — no cells to mirror
        return g
    if name == "seed_on_axis":
        # seed sits on the central column → its mirror is itself (rule no-op)
        g[2][3] = 5
        g[4][3] = 7
        return g
    if name == "mirror_target_occupied":
        # left-half seed plus a pre-occupied mirror target → output cell already non-bg
        g[1][1] = 4
        g[1][w - 2] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    nonzero = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not nonzero:
        errors.append("expected at least one seed marker")
    for r, c in nonzero:
        if c >= w // 2:
            errors.append("normal seed is not in the strict left half")
            break
        if w % 2 == 1 and c == w // 2:
            errors.append("seed lies on the vertical mirror axis")
            break
        mc = w - 1 - c
        if grid[r][mc] != 0:
            errors.append("mirror target is already occupied")
            break
    return errors
