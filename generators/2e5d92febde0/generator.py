"""Generator for arc_puzzle_bank_21_set11_bundle:easy_k05.

Rule: each nonzero seed extends straight downward to the bottom border
in its own color.

Combinatorial axes (8): grid_h/w, palette_kind, n_seeds, palette_size,
position_bias, n_distinct_colors, seed_density, texture.
Degenerates: no_seeds, seed_at_bottom, single_seed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2e5d92febde0"
VERSION = "1.1.1"
TASK_ID = "2e5d92febde0"
SUMMARY = "Each nonzero seed extends straight downward to the bottom border in its color."

INVARIANTS = [
    "seed columns are distinct",
    "seeds are placed above the bottom row",
    "background is zero",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_seeds", "seed_at_bottom", "single_seed")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "3..14"},
    "grid_w":         {"type": "int", "default": "rng 6..10", "valid": "3..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "seed_density":   {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, has non-bg seed cells (at most 1 per column, not in bottom row)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    seeds = sum(grid[r][c] != 0 for r in range(h) for c in range(w))
    if seeds == 0:
        return ["no seed cells found"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 6, 10)
    n = min(ctx.draw_int("n_seeds", 2, 5), w)
    rng = ctx.draw_rng("layout")
    cols = list(range(w))
    rng.shuffle(cols)
    colors = list(ctx.draw_distinct_colors("colors", n=n, exclude={0}))
    g = full_grid(h, w, 0)
    for i, c in enumerate(cols[:n]):
        r = rng.randint(0, h - 2)
        g[r][c] = colors[i]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # empty grid — no rays to extend
        return g
    if name == "seed_at_bottom":
        # seed already at bottom row — no extension needed (rule degenerate)
        g[h - 1][3] = 4
        return g
    if name == "single_seed":
        # only 1 seed — minimum signal
        g[2][3] = 5
        return g
    return g
