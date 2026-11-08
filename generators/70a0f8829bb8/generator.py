"""Generator for arc_puzzle_bank_21_set23_s:S23_H3 — tile-lattice majority overlay.

Rule (verified from canonical Racket): full color-9 rows/cols split the grid into a
LATTICE of equal-size tiles. Output is one tile-sized grid where cell (r,c) = 8 iff at
least 3 of the tiles have a nonzero cell at (r,c), else 0 (a >=3 majority overlay).

The previous body was a MISLABELLED "multi-motif gallery pack" that scattered motifs
with NO color-9 dividers, so the grid was a single tile and the overlay (count >= 3)
was almost never met -> output near-constant (distinct=9). This rewrite builds a real
tile lattice (>=4 tiles separated by color-9 rows/cols), each tile a random pattern.

Axes: tile size, lattice dimensions, per-tile patterns.
Degenerates: no_dividers, all_same_tile, single_tile.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "70a0f8829bb8"
VERSION = "2.1.0"  # all_background fix: random tiles occasionally yielded a DEGENERATE >=3-overlay -- all-0 (too sparse, no cell shared by >=3 tiles) or all-8 (too dense, every cell in >=3 tiles), both single-colour outputs. Now resample the tile patterns until the overlay is PARTIAL (>=1 eight and >=1 zero), keeping the original tile distribution.
TASK_ID = "70a0f8829bb8"

SUMMARY = "Color-9 dividers split the grid into a lattice of equal tiles; output is the tile-sized grid with 8 where >=3 tiles have a nonzero cell."

INVARIANTS = [
    "full color-9 divider rows/cols split the grid into equal tiles",
    "there are at least 4 tiles (so the >=3-majority overlay is meaningful)",
    "each tile carries a random nonzero pattern",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "all_same_tile", "single_tile")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "tile_size":      {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "tile_rows":      {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "tile_cols":      {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _fill_tile(g, top, left, K, rng):
    """Random nonzero pattern in a K x K tile (>=1 cell)."""
    spots = [(r, c) for r in range(K) for c in range(K)]
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])   # never 9 (divider colour)
    for r, c in rng.sample(spots, rng.randint(1, K * K)):
        g[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        K = ctx.draw_int("tile_size", 2, 3); tr = 2; tc = 2
    elif difficulty == "hard":
        K = ctx.draw_int("tile_size", 3, 5)
        tr = ctx.draw_int("tile_rows", 2, 3); tc = ctx.draw_int("tile_cols", 2, 4)
    else:
        K = ctx.draw_int("tile_size", 2, 4)
        tr = ctx.draw_int("tile_rows", 2, 3); tc = ctx.draw_int("tile_cols", 2, 3)
    rng = ctx.draw_rng("layout")

    h = tr * K + (tr - 1)
    w = tc * K + (tc - 1)
    tiles_xy = [(ti, tj) for ti in range(tr) for tj in range(tc)]

    def _overlay_count(gg):
        """# of local cells where >=3 tiles are nonzero (the rule's 8-count)."""
        n8 = 0
        for r in range(K):
            for c in range(K):
                cnt = sum(1 for ti, tj in tiles_xy
                          if gg[ti * (K + 1) + r][tj * (K + 1) + c] != 0)
                if cnt >= 3:
                    n8 += 1
        return n8

    # Resample the per-tile patterns until the >=3-overlay is PARTIAL (neither
    # all-0 nor all-8), so the output is never a degenerate single colour.
    g = full_grid(h, w, 0)
    for _attempt in range(60):
        g = full_grid(h, w, 0)
        for ti in range(tr):
            for tj in range(tc):
                _fill_tile(g, ti * (K + 1), tj * (K + 1), K, rng)
        if 0 < _overlay_count(g) < K * K:
            break
    # full color-9 divider rows/cols between tiles
    for ti in range(1, tr):
        rr = ti * (K + 1) - 1
        for c in range(w):
            g[rr][c] = 9
    for tj in range(1, tc):
        cc = tj * (K + 1) - 1
        for r in range(h):
            g[r][cc] = 9
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """The color-9 lattice must hold >=4 equal tiles and the >=3-majority
    overlay must be PARTIAL (>=1 eight and >=1 zero), else the output is a
    degenerate single colour (all-0 or all-8)."""
    h, w = len(grid), len(grid[0])
    drows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    dcols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not drows or not dcols:
        return ["no full color-9 divider rows/cols -> single tile"]

    def bands(seps, n):
        res, start = [], 0
        for s in seps + [n]:
            if start < s:
                res.append((start, s - 1))
            start = s + 1
        return res

    rb, cb = bands(drows, h), bands(dcols, w)
    if len(rb) * len(cb) < 4:
        return [f"only {len(rb) * len(cb)} tiles (<4)"]
    th = rb[0][1] - rb[0][0] + 1
    tw = cb[0][1] - cb[0][0] + 1
    n8 = 0
    for lr in range(th):
        for lc in range(tw):
            cnt = sum(1 for (r0, _) in rb for (c0, _) in cb
                      if grid[r0 + lr][c0 + lc] != 0)
            if cnt >= 3:
                n8 += 1
    if n8 == 0:
        return ["empty >=3-majority overlay -> all-0 output"]
    if n8 == th * tw:
        return ["full >=3-majority overlay -> all-8 output"]
    return []


def _draw_from_degenerate(name, rng):
    K = 3
    if name == "no_dividers":
        # one tile, no color-9 dividers -> overlay (count >= 3) never met
        g = full_grid(K, K, 0)
        g[0][0] = 4; g[1][1] = 4
        return g
    h = 2 * K + 1; w = 2 * K + 1
    g = full_grid(h, w, 0)
    for ti in range(2):
        for tj in range(2):
            if name == "all_same_tile":
                for r in range(K):
                    g[ti * (K + 1) + r][tj * (K + 1) + r] = 4   # identical diagonal tiles
            else:  # single_tile -> only one non-empty tile
                if (ti, tj) == (0, 0):
                    g[0][0] = 4; g[1][1] = 4
    for c in range(w):
        g[K][c] = 9
    for r in range(h):
        g[r][K] = 9
    return g
