"""Generator for arc_additional_puzzle_bank_volume6:H37.

Rule: BFS the cardinal distance from the color-2 seeds through cells that
are 0 or 2 (any other color is a wall). Recolor each reachable cell by its
distance mod 3 (0->3, 1->4, 2->5); unreachable cells keep their color.

This generator scatters color-2 seeds on a 0 field with optional wall
obstacles, producing concentric distance bands.

Combinatorial axes: grid size, the seed positions/count, and the wall
obstacles.
Degenerates: no_walls, no_seed, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9199b47fab1e"
VERSION = "2.0.1"
TASK_ID = "9199b47fab1e"
SUMMARY = (
    "0-bg grid (size varies) with 1-N color-2 SEEDS and optional wall "
    "obstacles (any non-0/2 color). Rule: BFS the distance from the seeds "
    "through 0/2 cells and recolor reachable cells by distance mod 3 "
    "(0->3, 1->4, 2->5). The grid size, seed positions/count and wall "
    "obstacles vary freely (was a fixed setup, ~24 distinct)."
)

INVARIANTS = [
    "color-2 seeds are the BFS sources; any non-0/2 color is a wall",
    "reachable cells are recolored by cardinal distance mod 3 (3/4/5)",
    "the seeds are placed so a non-trivial region is reachable",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_seed", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 color-2 seed cell present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_walls", "no_seed", "full_grid"):
        return errs
    if not any(grid[r][c] == 2 for r in range(h) for c in range(w)):
        errs.append("no color-2 BFS seed cells found")
    return errs


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..20"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..22"},
    "n_seeds":        {"type": "int", "default": "varies", "valid": "1..3"},
    "n_walls":        {"type": "int", "default": "varies", "valid": "0..4"},
    "wall_color":     {"type": "color", "default": "rng {6,7,8,9}", "valid": "6|7|8|9"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_walls|no_seed|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, sd, wl = (10, 12), (10, 13), (1, 1), (0, 1)
    elif difficulty == "hard":
        hr, wr, sd, wl = (15, 20), (16, 22), (2, 3), (2, 4)
    else:
        hr, wr, sd, wl = (12, 16), (12, 18), (1, 2), (0, 3)

    wall = rng.choice([6, 7, 8, 9])
    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occupied = set()
        # wall obstacles: short bars
        for _ in range(rng.randint(*wl)):
            wl_len = rng.randint(2, max(2, min(h, w) // 2))
            vert = rng.random() < 0.5
            if vert:
                r0 = rng.randint(0, h - wl_len); c0 = rng.randint(0, w - 1)
                cells = [(r0 + i, c0) for i in range(wl_len)]
            else:
                r0 = rng.randint(0, h - 1); c0 = rng.randint(0, w - wl_len)
                cells = [(r0, c0 + i) for i in range(wl_len)]
            for (r, c) in cells:
                g[r][c] = wall; occupied.add((r, c))
        # seeds
        placed = 0
        for _ in range(rng.randint(*sd)):
            for _t in range(20):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if (r, c) not in occupied:
                    g[r][c] = 2; occupied.add((r, c)); placed += 1; break
        if placed >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    g[5][5] = 2
    if name == "no_seed":
        g[5][5] = 0
        return g
    if name == "no_walls":
        return g
    if name == "full_grid":
        return full_grid(11, 11, 7)
    for r in range(2, 9):
        g[r][3] = 7
    return g
