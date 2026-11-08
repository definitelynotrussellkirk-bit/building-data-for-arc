"""Generator for arc_puzzle_bank_21_set11_bundle:easy_k02.

Rule: each nonzero seed paints its full row and full column with its color.

Combinatorial axes (8): grid_h/w, palette_kind, n_seeds, palette_size,
position_bias, n_distinct_colors, seed_density, texture.
Degenerates: no_seeds, seeds_share_row, full_grid_seeded.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5b790b7416e1"
VERSION = "1.2.0"  # normal path now uses 2..3 seeds so demos teach multi-cross composition
TASK_ID = "5b790b7416e1"
SUMMARY = "Each nonzero seed paints its full row and full column with its color."

INVARIANTS = [
    "seed cells are sparse and nonzero",
    "seed rows and columns are distinct",
    "background is zero",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_seeds", "seeds_share_row", "full_grid_seeded")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "3..12"},
    "grid_w":         {"type": "int", "default": "rng 5..8", "valid": "3..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..9"},
    "seed_density":   {"type": "str", "default": "mixed", "valid": "mixed"},
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
        w = ctx.draw_int("grid_w", 5, 6)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 5, 8)
    # Normal samples should show composition of multiple crosshairs.  A single
    # seed is a useful degenerate/override, but it hides the multi-seed rule in
    # default training examples (roughly a third of v1.1.0 samples).
    n = min(ctx.draw_int("n_seeds", 2, 3), h, w)
    rng = ctx.draw_rng("layout")
    rows = list(range(h))
    cols = list(range(w))
    rng.shuffle(rows)
    rng.shuffle(cols)
    colors = list(ctx.draw_distinct_colors("colors", n=n, exclude={0}))
    g = full_grid(h, w, 0)
    for i in range(n):
        g[rows[i]][cols[i]] = colors[i]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the normal crosshair-seed samples."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if not (5 <= h <= 8 and 5 <= w <= 8):
        errors.append(f"normal grid size should be 5..8 in each axis, got {h}x{w}")
    seeds = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not (2 <= len(seeds) <= 3):
        errors.append(f"expected 2..3 nonzero seed cells in normal samples, found {len(seeds)}")
        return errors
    rows = [r for r, _, _ in seeds]
    cols = [c for _, c, _ in seeds]
    colors = [v for _, _, v in seeds]
    if len(rows) != len(set(rows)):
        errors.append("seed rows must be distinct so row-painting is unambiguous")
    if len(cols) != len(set(cols)):
        errors.append("seed columns must be distinct so column-painting is unambiguous")
    if len(colors) != len(set(colors)):
        errors.append("seed colors must be distinct in the normal path")
    if any(v < 1 or v > 9 for v in colors):
        errors.append("seed colors must be ARC colors 1..9")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # empty grid — no crosshairs to paint
        return g
    if name == "seeds_share_row":
        # two seeds in same row — invariant violated, ambiguous painting
        g[2][3] = 4
        g[2][5] = 7  # same row → which color wins for row 2?
        return g
    if name == "full_grid_seeded":
        # seed at every cell — rule's effect is identity (already filled)
        for r in range(h):
            for c in range(w):
                g[r][c] = ((r + c) % 7) + 2
        return g
    return g
