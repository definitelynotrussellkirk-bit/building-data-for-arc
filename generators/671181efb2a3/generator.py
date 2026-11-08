"""Generator for arc_puzzle_bank_21_set22_bundle:easy_p02.

Rule: same-color orthogonal clusters survive; isolated singletons drop.

Combinatorial axes (8): grid_h, grid_w, palette_kind, cluster_count,
singleton_count, palette_size, position_bias, n_distinct_colors,
density, texture.
Degenerates: all_singletons, all_clusters, mixed_color_pairs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "671181efb2a3"
VERSION = "2.0.1"
TASK_ID = "671181efb2a3"
SUMMARY = (
    "0-bg grid (h~7-10, w~8-12) with a MIX of "
    "(a) 2-3 same-color CLUSTERS (each = a 2-cell "
    "ORTHOGONAL pair: two cells of the same color "
    "placed horizontally or vertically adjacent); "
    "(b) 2-4 isolated SINGLETON noise cells in "
    "various colors, placed with no same-color "
    "orthogonal neighbor. Cluster cells and "
    "singletons are spaced so they don't touch "
    "each other. Rule: for every non-bg cell, "
    "check if it has at least one ORTHOGONAL "
    "neighbor of the SAME COLOR. If yes (cluster "
    "member), PRESERVE. If no (singleton), "
    "ERASE (set to 0). Net: same-color "
    "orthogonal pairs survive; all isolated "
    "color noise is wiped."
)

INVARIANTS = [
    "background is 0",
    "cluster cells have at least one same-color orthogonal neighbor",
    "singleton cells have no same-color orthogonal neighbor",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_singletons", "all_clusters", "mixed_color_pairs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cluster_count":  {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "singleton_count":{"type": "int", "default": "rng 2..4", "valid": "0..10"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "clusters_with_singleton_noise",
                       "valid": "clusters_with_singleton_noise"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 non-bg cluster cell with a same-color orthogonal neighbor."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    found_cluster = False
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 0:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == v:
                    found_cluster = True
                    break
    if not found_cluster:
        errs.append("no same-color orthogonal cluster cells found")
    return errs


def _clear_neighborhood(grid, cells):
    h = len(grid)
    w = len(grid[0])
    for r, c in cells:
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if grid[rr][cc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        cluster_count = ctx.draw_int("cluster_count", 2, 2)
        singleton_count = ctx.draw_int("singleton_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        cluster_count = ctx.draw_int("cluster_count", 3, 3)
        singleton_count = ctx.draw_int("singleton_count", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        cluster_count = ctx.draw_int("cluster_count", 2, 3)
        singleton_count = ctx.draw_int("singleton_count", 2, 4)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    anchors = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(anchors)
    placed = 0
    for r, c in anchors:
        if placed >= cluster_count:
            break
        orient = rng.choice([(0, 1), (1, 0)])
        cells = [(r, c), (r + orient[0], c + orient[1])]
        if not all(0 <= rr < h and 0 <= cc < w for rr, cc in cells):
            continue
        if not _clear_neighborhood(grid, cells):
            continue
        color = rng.choice(colors)
        for rr, cc in cells:
            grid[rr][cc] = color
        placed += 1

    rng.shuffle(anchors)
    placed = 0
    for r, c in anchors:
        if placed >= singleton_count:
            break
        if not _clear_neighborhood(grid, [(r, c)]):
            continue
        grid[r][c] = rng.choice(colors)
        placed += 1
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "all_singletons":
        # only isolated cells → rule erases everything, output is empty
        g[1][2] = 4; g[3][6] = 6; g[5][1] = 3; g[6][8] = 8
        return g
    if name == "all_clusters":
        # only same-color pairs → rule keeps everything, output equals input
        g[1][1] = 4; g[1][2] = 4
        g[4][5] = 6; g[4][6] = 6
        g[6][8] = 3; g[7][8] = 3
        return g
    if name == "mixed_color_pairs":
        # pairs are different colors next to each other → predicate "same-color neighbor" fails,
        # both cells treated as singletons, all dropped
        g[2][2] = 4; g[2][3] = 6
        g[5][5] = 3; g[5][6] = 8
        return g
    return g
