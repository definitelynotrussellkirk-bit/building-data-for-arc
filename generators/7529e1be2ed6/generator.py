"""Generator for arc_puzzle_bank_21_set12_s:S12_M5.

Rule: components touching at least two distinct neighbor colors are
selected on a blank canvas.

Combinatorial axes (8): grid_h, grid_w, palette_kind, neighbor_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: single_neighbor, no_central, all_isolated.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7529e1be2ed6"
VERSION = "2.2.0"  # add executable two-neighbor predicate witnesses
TASK_ID = "7529e1be2ed6"
SUMMARY = (
    "0-bg grid (h~9-12, w~11-15) with: (a) one CENTRAL "
    "color-3 (green) cell at random interior position "
    "(r, c); (b) 2-3 NEIGHBOR cells adjacent to it in "
    "distinct colors {2, 4, 6} (above/right/below the "
    "center); (c) 2 DISTRACTOR singletons (color 7, 8) "
    "elsewhere with no neighbors. Rule: extract all "
    "4-conn non-bg components. For each, find its "
    "neighbor components (any 4-adjacent non-bg cell of "
    "a different color). KEEP components whose set of "
    "neighbor colors has SIZE ≥ 2; output them on a "
    "blank canvas (same dims). Drop components with "
    "<2 distinct neighbor colors."
)

INVARIANTS = [
    "background is 0",
    "one central component touches two or three differently colored neighbors",
    "neighbor components each touch only the central component",
    "distractor components do not satisfy the two-neighbor-color predicate",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_neighbor", "no_central", "all_isolated")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..15"},
    "grid_w":         {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "neighbor_count": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "central_with_neighbors",
                       "valid": "central_with_neighbors"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        neighbor_count = ctx.draw_int("neighbor_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 15)
        neighbor_count = ctx.draw_int("neighbor_count", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 15)
        neighbor_count = ctx.draw_int("neighbor_count", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    r = rng.randint(3, h - 4)
    c = rng.randint(3, w - 4)
    g[r][c] = 3
    neighbors = [
        (r - 1, c, 2),
        (r, c + 1, 4),
        (r + 1, c, 6),
    ]
    for rr, cc, color in neighbors[:neighbor_count]:
        g[rr][cc] = color

    # Isolated singleton distractors; keep them non-adjacent so they never
    # become one component touching multiple colors.
    g[h - 2][1] = 7
    g[h - 2][w - 2] = 8
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "single_neighbor":
        # central touches only one neighbor color → predicate (≥2) fails, output empty
        g[5][6] = 3
        g[4][6] = 2
        g[h - 2][w - 4] = 7; g[h - 2][w - 3] = 8
        return g
    if name == "no_central":
        # only neighbors, no central component → predicate has no candidate
        g[4][5] = 2; g[5][6] = 4; g[6][5] = 6
        return g
    if name == "all_isolated":
        # all components are singletons not touching any others → predicate fails everywhere
        g[2][3] = 4; g[5][7] = 6; g[7][2] = 8
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    selected = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3:
                continue
            neigh = {grid[nr][nc]
                     for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                     if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] not in (0, 3)}
            if len(neigh) >= 2:
                selected.append((r, c, tuple(sorted(neigh))))
    if len(selected) != 1:
        errs.append(f"expected one central color-3 component with >=2 neighbor colors, found {len(selected)}")
    if difficulty == "hard" and selected and len(selected[0][2]) < 3:
        errs.append("hard samples should expose three neighbor colors")
    for color in (7, 8):
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if len(cells) != 1:
            errs.append(f"expected one color-{color} singleton distractor, found {len(cells)}")
            continue
        r, c = cells[0]
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if (dr or dc) and 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0:
                    errs.append(f"color-{color} distractor is not isolated")
                    return errs
    return errs
