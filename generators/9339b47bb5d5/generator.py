"""Generator for arc_puzzle_bank_21_set24_bundle:easy_p07.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seed_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_walls, no_seeds, multiple_seeds_per_compartment.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9339b47bb5d5"
VERSION = "1.3.2"  # enforce one seed per wall compartment
TASK_ID = "9339b47bb5d5"
SUMMARY = "Color-5 walls + non-{0,5} seed cells. Rule: from each seed, cast 4 cardinal rays through 0-bg cells, painting them with the seed's color. A ray stops at the first 5-wall or grid edge. Seeds and walls stay; opposite-side cells (across a wall) are NOT painted."

# Rivals: 'output is input' refuted by any demo (rays fill).
# 'paint all bg cells from any seed' refuted by ≥1 demo where two
# seeds in different compartments don't bleed across the wall.
# 'rays pass through walls' refuted by any demo where a 5-wall
# stops a ray. 'rays go diagonal too' refuted by demos with empty
# diagonal cells. 3 demos with ≥2 seeds in distinct compartments cover.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "wall color is 5",
    "each compartment contains at most one non-wall seed",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_seeds", "multiple_seeds_per_compartment")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "6..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_count":     {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "cross_walls_with_seeds",
                       "valid": "cross_walls_with_seeds"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _zero_compartments(grid):
    """Connected non-wall compartments; color-5 cells are barriers."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 5:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 5:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify walls plus at most one seed per color-5-bounded compartment."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if not any(grid[r][c] == 5 for r in range(h) for c in range(w)):
        errs.append("no color-5 wall cells found")
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
    if not seeds:
        errs.append("no seed cells (non-{0,5}) found")
    comps = _zero_compartments(grid)
    seeded_comps = 0
    for idx, cells in enumerate(comps):
        n = sum(1 for r, c in cells if grid[r][c] not in (0, 5))
        if n:
            seeded_comps += 1
        if n > 1:
            errs.append(f"compartment {idx} contains {n} seeds; expected at most one")
    if seeds and seeded_comps < min(2, len(comps)):
        errs.append("fewer than two wall compartments contain seeds; cross-wall branch is weak")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(7, 9); w = rng.randint(8, 11)
        wall_kind = rng.choice(["row", "col", "cross"])
        seed_count = rng.randint(2, 3)
    elif difficulty == "hard":
        h = rng.randint(12, 16); w = rng.randint(13, 18)
        wall_kind = rng.choice(["cross", "double_cross", "L"])
        seed_count = rng.randint(4, 6)
    else:
        h = rng.randint(9, 12); w = rng.randint(11, 14)
        wall_kind = rng.choice(["cross", "row", "col", "L"])
        seed_count = rng.randint(3, 5)

    grid = full_grid(h, w, 0)

    def paint_row(r):
        for c in range(w):
            grid[r][c] = 5
    def paint_col(c):
        for r in range(h):
            grid[r][c] = 5

    if wall_kind == "row":
        wall_r = rng.randint(2, h - 3)
        paint_row(wall_r)
    elif wall_kind == "col":
        wall_c = rng.randint(2, w - 3)
        paint_col(wall_c)
    elif wall_kind == "L":
        wall_r = rng.randint(2, h - 3)
        wall_c = rng.randint(2, w - 3)
        # Half-row + half-col
        if rng.random() < 0.5:
            for c in range(wall_c):
                grid[wall_r][c] = 5
        else:
            for c in range(wall_c, w):
                grid[wall_r][c] = 5
        if rng.random() < 0.5:
            for r in range(wall_r):
                grid[r][wall_c] = 5
        else:
            for r in range(wall_r, h):
                grid[r][wall_c] = 5
    elif wall_kind == "double_cross":
        wall_r1 = rng.randint(2, h // 2)
        wall_r2 = rng.randint(h // 2 + 1, h - 3)
        wall_c = rng.randint(3, w - 4)
        paint_row(wall_r1)
        paint_row(wall_r2)
        paint_col(wall_c)
    else:  # cross
        wall_r = rng.randint(2, h - 3)
        wall_c = rng.randint(2, w - 3)
        paint_row(wall_r)
        paint_col(wall_c)

    # Place at most one seed in each color-5-bounded compartment.  The
    # previous random-cell placement often put several seeds in the same
    # compartment, leaking the declared multiple_seeds_per_compartment
    # degenerate into normal generation.
    comps = [cells for cells in _zero_compartments(grid) if cells]
    rng.shuffle(comps)
    colors_pool = [1, 2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(colors_pool)
    for placed, cells in enumerate(comps[:min(seed_count, len(comps))]):
        r, c = rng.choice(cells)
        grid[r][c] = colors_pool[placed % len(colors_pool)]
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_walls":
        # seeds without crosshair walls → no compartment boundaries to bound rays within
        g[1][1] = 4
        g[3][5] = 6
        g[6][7] = 7
        return g
    if name == "no_seeds":
        # walls alone, no seeds → no rays to cast
        for c in range(w):
            g[4][c] = 5
        for r in range(h):
            g[r][5] = 5
        return g
    if name == "multiple_seeds_per_compartment":
        # 2 seeds in one compartment → "at most one seed" precondition fails
        for c in range(w):
            g[4][c] = 5
        for r in range(h):
            g[r][5] = 5
        g[1][1] = 4
        g[2][2] = 6  # both in TL compartment
        g[7][8] = 7
        return g
    return g
