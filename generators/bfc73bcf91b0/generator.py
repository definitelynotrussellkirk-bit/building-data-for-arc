"""Generator for arc_puzzle_bank_sixth_21_bundle:easy_36_diagonal_rays_from_seeds.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, no_blockers, seeds_on_diagonal.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bfc73bcf91b0"
VERSION = "1.1.1"
TASK_ID = "bfc73bcf91b0"

SUMMARY = "Red seeds cast cyan rays along all diagonals until gray blockers."

INVARIANTS = [
    "background is 0",
    "seed color is 2",
    "blocker color is 5",
    "diagonal rays stop at blockers or grid edges",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "no_blockers", "seeds_on_diagonal")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "n_blockers":     {"type": "int", "default": "rng 2..6", "valid": "0..30"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "seeds_off_diagonal_with_blockers",
                       "valid": "seeds_off_diagonal_with_blockers"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has red seed cells (2) and gray blocker cells (5)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    blockers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not seeds:
        errs.append("no red seed cells (color 2) found")
    if not blockers:
        errs.append("no gray blocker cells (color 5) found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        seed_count = ctx.draw_int("n_seeds", 2, 2)
        blocker_count = ctx.draw_int("n_blockers", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
        seed_count = ctx.draw_int("n_seeds", 3, 4)
        blocker_count = ctx.draw_int("n_blockers", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        seed_count = ctx.draw_int("n_seeds", 2, 4)
        blocker_count = ctx.draw_int("n_blockers", 2, 6)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    seeds: list[tuple[int, int]] = []
    candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    rng.shuffle(candidates)
    for r, c in candidates:
        if len(seeds) >= seed_count:
            break
        if any(abs(r - rr) == abs(c - cc) for rr, cc in seeds):
            continue
        g[r][c] = 2
        seeds.append((r, c))
    empty = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
    rng.shuffle(empty)
    for r, c in empty[:blocker_count]:
        g[r][c] = 5
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # blockers without seeds → no rays to cast
        for r, c in [(2, 3), (4, 6), (6, 2)]:
            g[r][c] = 5
        return g
    if name == "no_blockers":
        # seeds without blockers → rays span entire grid (no stopping)
        g[3][3] = 2
        g[6][6] = 2
        return g
    if name == "seeds_on_diagonal":
        # 2 seeds share a diagonal → their rays overlap (rule's "rays stop at seeds" ambiguous)
        g[2][2] = 2; g[5][5] = 2  # both on main diagonal
        g[3][6] = 5
        return g
    return g
