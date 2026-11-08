"""Generator for arc_puzzle_bank_21_set18_bundle:hard_p07 — parity wavefront from one seed.

Rule: one non-{0,5,8} seed sits inside a 5-wall boundary.  Shortest-path
distance through 0-cells is measured from the seed, blocked by 5-walls.  Even
distances take the seed color; odd distances take cyan 8.  Walls and the seed
are preserved.

Combinatorial axes: grid_h, grid_w, palette_kind, n_seeds, n_walls,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, walled_off, no_zero_room.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4a7168ef3ef1"
VERSION = "2.2.0"  # canonical parity wavefront: one non-8 seed, cyan(8) output-only, and 5-wall border prevents solid-8 collapse.
TASK_ID = "4a7168ef3ef1"

SUMMARY = (
    "0-background grid inside a color-5 boundary frame, with exactly one "
    "interior single-cell seed whose color is not 0, 5, or 8.  Optional "
    "interior color-5 walls are sparse and never adjacent to the seed.  "
    "The canonical rule measures shortest-path distance from the seed "
    "through 0-cells, blocked by 5-walls: even distances take the seed "
    "color, odd distances take cyan 8, while walls and the seed stay fixed."
)

INVARIANTS = [
    "background is 0",
    "exactly one single-cell seed in a non-{0, 5, 8} color",
    "color-5 wall border plus 0-4 optional interior wall cells",
    "seed is not adjacent to interior walls (so halos can spread)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "walled_off", "no_zero_room")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_seeds":        {"type": "int", "default": "1", "valid": "1..1"},
    "n_walls":        {"type": "int", "default": "rng 0..4 interior", "valid": "0..6"},
    "palette_size":   {"type": "int", "default": "3 (0,5,seed; 8 appears only in output)", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "seeds_with_sparse_walls",
                       "valid": "seeds_with_sparse_walls"},
    "n_distinct_colors": {"type": "int", "default": "3 input colors incl. 0/5/seed", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_seeds|walled_off|no_zero_room"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        n_seeds = 1
        n_walls = ctx.draw_int("n_walls", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 13)
        n_seeds = 1
        n_walls = ctx.draw_int("n_walls", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
        n_seeds = 1
        n_walls = ctx.draw_int("n_walls", 0, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        for rr in range(h):
            g[rr][0] = g[rr][w - 1] = 5
        for cc in range(w):
            g[0][cc] = g[h - 1][cc] = 5
        seed_colors = rng.sample([1, 2, 3, 4, 6, 7, 9], n_seeds)
        seed_pos = []
        ok = True
        for color in seed_colors:
            placed = False
            for _ in range(120):
                r = rng.randint(2, h - 3)
                c = rng.randint(2, w - 3)
                if g[r][c] != 0: continue
                if any(abs(r - sr) + abs(c - sc) < 3 for sr, sc in seed_pos): continue
                g[r][c] = color
                seed_pos.append((r, c))
                placed = True; break
            if not placed: ok = False; break
        if not ok:
            continue
        for _ in range(n_walls):
            for _t in range(40):
                r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
                if g[r][c] != 0: continue
                if any(abs(r - sr) + abs(c - sc) <= 1 for sr, sc in seed_pos): continue
                g[r][c] = 5
                break
        return g
    raise ValueError("could not realize hard_l21 layout")


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # Walls but no seeds — rule has no halos to project.
        for c in range(2, 5): g[3][c] = 5
        return g
    if name == "walled_off":
        # Seed surrounded by walls — halo cannot spread.
        g[4][4] = 4
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]: g[4 + dr][4 + dc] = 5
        return g
    if name == "no_zero_room":
        # Grid completely full of walls + seed — no 0-cells to color.
        for r in range(h):
            for c in range(w): g[r][c] = 5
        g[4][4] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate sparse seeds and non-adjacent walls for even-distance halos."""
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if not all(grid[0][c] == 5 and grid[h - 1][c] == 5 for c in range(w)) or not all(grid[r][0] == 5 and grid[r][w - 1] == 5 for r in range(h)):
        errs.append("normal instances should have a color-5 boundary frame")
    seeds = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
    if len(seeds) != 1:
        errs.append(f"expected exactly one seed, got {len(seeds)}")
    if any(v == 8 for _, _, v in seeds):
        errs.append("seed color must not be cyan 8; 8 is the odd-distance output color")
    for i, (r, c, _) in enumerate(seeds):
        if r in (0, h - 1) or c in (0, w - 1):
            errs.append("seeds should be interior")
        for rr, cc, _ in seeds[i + 1:]:
            if abs(r - rr) + abs(c - cc) < 3:
                errs.append("seeds must have Manhattan distance at least 3")
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 5:
                errs.append("walls must not be adjacent to seeds")
                return errs
    return errs
