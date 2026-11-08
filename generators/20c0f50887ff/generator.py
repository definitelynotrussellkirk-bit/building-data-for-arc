"""Generator for arc_puzzle_bank_21_set18_bundle:medium_p06 — pivot cross until walls.

Rule: each non-bg, non-5 seed cell sends 4 cardinal rays in its color
until they hit a 5-wall or the edge. Output overlays seeds + rays.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, no_walls, seed_on_wall.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "20c0f50887ff"
VERSION = "2.0.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 2-3 non-{0,5} seed cells; no invalid cell values."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in {0, 5}]
    if len(seeds) < 2 or len(seeds) > 3:
        errs.append(f"expected 2-3 non-{{0,5}} seed cells, got {len(seeds)}")
    return errs
TASK_ID = "20c0f50887ff"
SUMMARY = (
    "0-bg grid (h~8-10, w~9-11) with: (a) 1-2 "
    "COLOR-5 (gray) WALL SEGMENTS as horizontal "
    "or vertical line segments (3-5 cells long) "
    "placed in the interior; (b) 2-3 single "
    "SEED CELLS in DISTINCT non-{0, 5} colors "
    "placed at random non-wall positions, "
    "non-4-touching each other. Rule: for EVERY "
    "non-{0, 5} SEED cell, emit 4 CARDINAL RAYS "
    "(up, down, left, right) in the SEED'S "
    "COLOR. Each ray walks from the seed until "
    "it hits a 5-wall cell, the grid EDGE, or "
    "the original grid boundary, painting "
    "every empty cell along the way. Walls "
    "STOP the ray (wall stays gray). Multiple "
    "seeds' rays may overlap — last-paint wins "
    "or order-independent depending on layout. "
    "Net: each colored seed sprouts a cardinal "
    "color-cross extending until walls/edges."
)

INVARIANTS = [
    "background is 0",
    "1-3 5-walls in the form of horizontal or vertical line segments",
    "2-3 single-cell seeds in distinct non-5 colors, not on a 5-cell",
    "seeds are not 4-touching each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "no_walls", "seed_on_wall")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "seeds_with_walls",
                       "valid": "seeds_with_walls"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    n_walls = rng.randint(1, 2)
    for _ in range(n_walls):
        for _ in range(20):
            if rng.random() < 0.5:
                # vertical
                c = rng.randint(2, w - 3)
                r1 = rng.randint(0, h - 3)
                r2 = rng.randint(r1 + 2, min(h - 1, r1 + 4))
                cells = [(r, c) for r in range(r1, r2 + 1)]
            else:
                r = rng.randint(2, h - 3)
                c1 = rng.randint(0, w - 3)
                c2 = rng.randint(c1 + 2, min(w - 1, c1 + 4))
                cells = [(r, c) for c in range(c1, c2 + 1)]
            if any(p in used for p in cells):
                continue
            for r, c in cells:
                g[r][c] = 5
            used |= set(cells)
            break
    n_seeds = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_seeds)
    for color in palette:
        cells = grow_blob(rng, h, w, used, 1, max_attempts=40)
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # Walls present but no seeds — rule has nothing to ray from.
        for r in range(2, 5): g[r][4] = 5
        return g
    if name == "no_walls":
        # Seeds but no walls — rays extend all the way to grid edges (no wall stops).
        g[3][3] = 4; g[5][6] = 6
        return g
    if name == "seed_on_wall":
        # Seed sits on a 5-wall cell — illegal per invariants.
        for r in range(2, 5): g[r][4] = 5
        g[3][4] = 4
        return g
    return g
