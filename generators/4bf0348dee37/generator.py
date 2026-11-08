"""Generator for arc_additional_puzzles_21_set16_bundle:H110 — Connect 2-cells via 3-elbow with color-2 path.

Rule: two 2-cells (endpoints) + one 3-cell (elbow). Draw L-shaped path
in color 2 (corner painted as well). 5-cells block path drawing.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_endpoints,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_endpoints, no_elbow, single_endpoint.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4bf0348dee37"
VERSION = "2.0.1"
TASK_ID = "4bf0348dee37"
SUMMARY = (
    "0-bg grid (h, w~8-10) "
    "with: (a) TWO "
    "ENDPOINT CELLS in "
    "COLOR 2 at distinct "
    "interior positions "
    "with different rows "
    "AND different cols; "
    "(b) ONE ELBOW CELL "
    "in COLOR 3 at a "
    "distinct interior "
    "position with row "
    "matching one endpoint "
    "and col matching the "
    "other endpoint; (c) "
    "TWO COLOR-5 (gray) "
    "OBSTACLE CELLS at "
    "(0, w-2) and (0, "
    "w-1) (top-right "
    "corner). Rule (DRAW "
    "L-SHAPED PATH IN "
    "COLOR 2 CONNECTING "
    "ENDPOINTS VIA ELBOW, "
    "BLOCKED BY 5-WALLS): "
    "identify the 2 "
    "COLOR-2 ENDPOINTS A "
    "and B and the 1 "
    "COLOR-3 ELBOW E. "
    "The ELBOW is at "
    "(A.row, B.col) or "
    "(B.row, A.col). "
    "DRAW an L-PATH: "
    "from A → E → B "
    "via straight "
    "horizontal then "
    "vertical (or vice "
    "versa) segments, "
    "PAINTING each "
    "intermediate cell "
    "and the elbow with "
    "COLOR 2 (overwriting "
    "the elbow's 3). "
    "The path is BLOCKED "
    "by color-5 cells "
    "(skip those). "
    "Endpoints stay. Net: "
    "the L-path connects "
    "the 2 endpoints "
    "through the elbow "
    "in color 2."
)

INVARIANTS = [
    "exactly 2 cells of color 2",
    "exactly 1 cell of color 3",
    "endpoints not in same row/col as elbow trivially",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_endpoints", "no_elbow", "single_endpoint")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_endpoints":    {"type": "int", "default": "2", "valid": "2..2"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "two_endpoints_with_elbow",
                       "valid": "two_endpoints_with_elbow"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_endpoints|no_elbow|single_endpoint"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    while True:
        a = (rng.randint(1, h - 2), rng.randint(1, w - 2))
        b = (rng.randint(1, h - 2), rng.randint(1, w - 2))
        e = (rng.randint(1, h - 2), rng.randint(1, w - 2))
        if a != b and a != e and b != e and a[0] != b[0] and a[1] != b[1] \
           and a[0] != e[0] and b[1] != e[1]:
            break
    g[a[0]][a[1]] = 2
    g[b[0]][b[1]] = 2
    g[e[0]][e[1]] = 3
    g[0][w - 2] = 5
    g[0][w - 1] = 5
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify L-path endpoints and elbow invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    problems = []
    flat = [v for row in grid for v in row]
    count2 = flat.count(2)
    count3 = flat.count(3)
    if count2 != 2:
        problems.append(f"expected exactly 2 color-2 endpoint cells, found {count2}")
    if count3 != 1:
        problems.append(f"expected exactly 1 color-3 elbow cell, found {count3}")
    return problems


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_endpoints":
        # only elbow, no 2-endpoints → no path source/target
        g[3][4] = 3
        return g
    if name == "no_elbow":
        # endpoints but no 3-elbow → no corner location for L-path
        g[2][2] = 2
        g[6][6] = 2
        return g
    if name == "single_endpoint":
        # only one endpoint → can't define a path
        g[2][2] = 2
        g[5][5] = 3
        return g
    return g
