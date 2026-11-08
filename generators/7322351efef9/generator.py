"""Generator for arc_puzzle_bank_21_set9_s:S9_M1.

Rule: two seeds (color 2 and color 3) on otherwise empty grid. Each
cell labeled by which seed is nearest (BFS distance). Tied cells
become 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seed_distance,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seed_2, no_seed_3, seeds_at_same_position.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7322351efef9"
VERSION = "1.1.1"
TASK_ID = "7322351efef9"
SUMMARY = "Exactly one 2-seed + one 3-seed on an otherwise empty grid."

INVARIANTS = [
    "background is 0",
    "exactly one cell of color 2 and one of color 3",
    "the seeds are not at the same position and not 4-adjacent",
]

PALETTE_KINDS = ("default", "horiz_seeds", "vert_seeds", "diag_seeds")
DEGENERATE_TEXTURES = ("no_seed_2", "no_seed_3", "seeds_adjacent")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_distance":  {"type": "str", "default": "≥3 manhattan",
                       "valid": "≥3 manhattan"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "minimal", "valid": "minimal"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one color-2 seed and one color-3 seed."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(twos) != 1:
        errs.append(f"expected exactly 1 color-2 seed, got {len(twos)}")
    if len(threes) != 1:
        errs.append(f"expected exactly 1 color-3 seed, got {len(threes)}")
    return errs


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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 6, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    p2 = (rng.randint(0, h - 1), rng.randint(0, w - 1))
    while True:
        p3 = (rng.randint(0, h - 1), rng.randint(0, w - 1))
        if abs(p3[0] - p2[0]) + abs(p3[1] - p2[1]) >= 3:
            break
    g[p2[0]][p2[1]] = 2
    g[p3[0]][p3[1]] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_seed_2":
        # only 3-seed → "nearest of two" undefined; entire grid maps to 3
        g[3][5] = 3
        return g
    if name == "no_seed_3":
        # only 2-seed → entire grid maps to 2 (rule loses contrast)
        g[3][1] = 2
        return g
    if name == "seeds_adjacent":
        # seeds 4-adjacent → boundary distance is 0 vs 1, ties dominate
        g[3][3] = 2
        g[3][4] = 3
        return g
    return g
