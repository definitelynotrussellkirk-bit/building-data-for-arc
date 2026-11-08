"""Generator for v0_original:easy_06.

Rule: isolated nonzero cells (no 4-neighbor of same component) recolor
to cyan; connected clusters remain unchanged.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, isolated, texture.
Degenerates: no_isolated, all_clusters, all_isolated.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f3a411af02b9"
VERSION = "2.1.0"  # shrink generated canvases toward the canonical 4x5..5x6 task scale; add stronger invariants
TASK_ID = "f3a411af02b9"

SUMMARY = ("0-bg grid with scattered ISOLATED single cells (no 4-neighbour) and "
           "several 4-CONNECTED CLUSTERS (random connected polyominoes, size 2-4), "
           "all in mixed non-0 colors and separated by a 1-cell ring. Rule: any "
           "cell with no non-0 orthogonal neighbour recolors to 8 (cyan); cells in "
           "a 4-connected cluster stay. (Was: 2 fixed tromino clusters.)")

INVARIANTS = [
    "background is 0",
    "some nonzero cells are 4-isolated",
    "some nonzero cells belong to components of size at least 2",
    "input avoids cyan isolated cells so recoloring is visible",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_isolated", "all_clusters", "all_isolated")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "easy 4..5 / medium 5..7 / hard 7..9", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "easy 5..7 / medium 6..9 / hard 8..11", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "isolated":       {"type": "int", "default": "easy 1..2 / medium 2..4 / hard 4..6", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng from fixed non-8 palette", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "scattered_isolated_and_clusters",
                       "valid": "scattered_isolated_and_clusters"},
    "n_distinct_colors": {"type": "int", "default": "varies by placed components", "valid": "2..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_isolated|all_clusters|all_isolated"},
}


def _free(g, cells):
    h, w = len(g), len(g[0])
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if g[rr][cc] != 0:
                    return False
    return True


def _rand_poly(rng, k):
    """Random 4-connected polyomino of k cells, normalized."""
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5); w = ctx.draw_int("grid_w", 5, 7)
        target = ctx.draw_int("isolated", 1, 2); ncl, csz = (1, 1), (2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 8, 11)
        target = ctx.draw_int("isolated", 4, 6); ncl, csz = (2, 3), (2, 4)
    else:
        h = ctx.draw_int("grid_h", 5, 7); w = ctx.draw_int("grid_w", 6, 9)
        target = ctx.draw_int("isolated", 2, 4); ncl, csz = (1, 2), (2, 3)
    rng = ctx.draw_rng("layout")
    colors = [1, 2, 3, 4, 5, 6, 7, 9]    # exclude 8 (the recolor target)
    g = full_grid(h, w, 0)

    # varied 4-connected clusters (>=2 cells -> stay)
    for _ in range(rng.randint(*ncl)):
        shape = _rand_poly(rng, rng.randint(*csz))
        bh = max(r for r, _ in shape) + 1; bw = max(c for _, c in shape) + 1
        if bh > h or bw > w:
            continue
        for _t in range(60):
            r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
            cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
            if _free(g, cells):
                col = rng.choice(colors)
                for r, c in cells:
                    g[r][c] = col
                break

    # isolated singletons (no neighbour -> recolor to 8)
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        r, c = rng.randrange(h), rng.randrange(w)
        if _free(g, [(r, c)]):
            g[r][c] = rng.choice(colors)
            placed += 1
    if _invariant_errors(g):
        return _draw_valid_fallback()
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            color = grid[sr][sc]
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _invariant_errors(grid):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    if any(v == 8 for row in grid for v in row):
        errs.append("input should exclude cyan 8 so isolated recolors are visible")
    comps = _components(grid)
    if not comps:
        errs.append("no non-bg cells found")
    if not any(len(cells) == 1 for cells in comps):
        errs.append("need at least one 4-isolated singleton")
    if not any(len(cells) >= 2 for cells in comps):
        errs.append("need at least one 4-connected cluster")
    return errs


def _draw_valid_fallback():
    g = full_grid(5, 7, 0)
    # one cluster that should stay
    g[0][0] = 4; g[0][1] = 4
    # another cluster to refute "all singletons"
    g[4][5] = 6; g[4][6] = 6
    # isolated cells that recolor to cyan
    g[2][3] = 7
    g[4][0] = 9
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_isolated":
        # Only multi-cell clusters, no isolated singletons — rule's
        # "isolated → cyan" branch never fires; output equals input.
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 6)]: g[r][c] = 6
        return g
    if name == "all_clusters":
        # Same as no_isolated, named differently — every component is
        # multi-cell.
        for r, c in [(2, 2), (3, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7)]: g[r][c] = 6
        return g
    if name == "all_isolated":
        # Every nonzero cell is isolated — rule's "kept cluster"
        # branch never fires; ALL non-bg cells become cyan,
        # eliminating color information from input.
        g[1][2] = 4; g[3][6] = 6; g[5][3] = 7; g[7][8] = 9
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """bg=0; at least one singleton fires, and at least one multi-cell cluster stays."""
    return _invariant_errors(grid)
