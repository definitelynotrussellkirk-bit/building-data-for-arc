"""Generator for arc_additional_puzzles_21_set13_bundle:E90.

Rule: for each non-bg cell at (r, c, v), paint the surrounding 8-cell
frame (all Moore-neighborhood cells except the center) with v on a fresh empty grid.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seed_at_corner, adjacent_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "df30a83a484e"
VERSION = "2.0.1"
TASK_ID = "df30a83a484e"
SUMMARY = (
    "0-bg grid (h~5-7, w~6-8) containing exactly 2-3 single SEED cells "
    "in distinct non-zero colors from {2..9}, placed at interior positions "
    "with Manhattan distance > 3 between any two seeds. Rule: build an empty "
    "output grid; for every seed at (r,c), paint the surrounding 8-cell frame "
    "(all neighbors in the 3x3 box except the center) with that seed's color. "
    "Out-of-bounds neighbors are silently dropped."
)

INVARIANTS = [
    "exactly 2-3 non-bg interior seeds",
    "seed colors are distinct",
    "no two seeds are within Manhattan distance 3",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "seed_at_corner", "adjacent_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "interior", "valid": "interior"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the seed-frame rule preconditions advertised by the generator."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    seeds = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    errs = []
    if not (2 <= len(seeds) <= 3):
        errs.append(f"expected 2-3 seeds; found {len(seeds)}")
    colors = [v for _, _, v in seeds]
    if len(set(colors)) != len(colors):
        errs.append("seed colors are not distinct")
    for r, c, _ in seeds:
        if not (1 <= r <= h - 2 and 1 <= c <= w - 2):
            errs.append(f"seed {(r, c)} is not interior")
    for i, (r, c, _) in enumerate(seeds):
        for pr, pc, _ in seeds[:i]:
            if abs(r - pr) + abs(c - pc) <= 3:
                errs.append(f"seeds {(pr, pc)} and {(r, c)} are too close")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 6, 8)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 3)
    n = rng.randint(2, 3)
    placed = []
    for _ in range(160):
        if len(placed) >= n:
            break
        r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
        if all(abs(r - pr) + abs(c - pc) > 3 for pr, pc in placed):
            g[r][c] = palette[len(placed)]
            placed.append((r, c))
    if len(placed) >= n:
        return g
    # Small canvases cannot always fit three separated seeds; emit a deterministic valid two-seed fallback.
    g = full_grid(h, w, 0)
    g[1][1] = palette[0]
    g[h - 2][w - 2] = palette[1]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 7
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # no source cells → no halos to draw, output is the empty grid
        return g
    if name == "seed_at_corner":
        # seed at (0,0) → up/left neighbors out of bounds, halo is partial
        g[0][0] = 4
        g[h - 1][w - 1] = 7
        return g
    if name == "adjacent_seeds":
        # seeds within distance 1 → their halos overwrite each other's source cells
        g[2][2] = 5
        g[2][3] = 6
        return g
    return g
