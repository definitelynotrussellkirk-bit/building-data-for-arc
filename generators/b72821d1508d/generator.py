"""Generator for puzzle 1d0a4b61.

Rule: zeros in a periodic 3x3 color tile are filled from matching
period positions.

Combinatorial axes (8): grid_size, n_holes, tile_kind, palette_kind,
hole_distribution, anchor_corner, asymmetry_force, period.
Degenerates: no_holes, all_holes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b72821d1508d"
# 1.2.0: period was FIXED at 3 (3x3 tile) and grid always SQUARE. Rule searches
# period 2..25 generically, so vary the period (2-5) and use non-square grids.
VERSION = "1.3.0"
TASK_ID = "b72821d1508d"
SUMMARY = (
    "A p x p periodic color TILE (period p in 2..5) tiled over a grid (rows "
    "and cols may differ), with some cells punched to 0 (holes). The first p "
    "rows keep the full tile so the period is recoverable. Rule: detect the "
    "period p, then fill each 0-cell from the matching periodic position. "
    "Output is the fully restored periodic grid."
)

INVARIANTS = [
    "grid repeats a p×p nonzero tile for p in 2..5",
    "top p rows preserve the full tile with no holes",
    "1+ holes appear in repeated copies below the preserved tile rows",
    "each hole has nonzero value at the same period position",
]

TILE_KINDS = ("digits", "warm", "cool", "primary", "broad")
HOLE_DISTRIBUTIONS = ("scattered", "clustered", "row_focus",
                     "col_focus", "diagonal")
DEGENERATE_TEXTURES = ("no_holes", "all_holes", "full_grid")
HELPFUL_TEXTURES = HOLE_DISTRIBUTIONS

AXES = {'grid_h': {'type': 'int', 'default': 'rng 18..25', 'valid': '12..25'},
 'grid_w': {'type': 'int', 'default': 'rng 18..25', 'valid': '12..25'},
 'period': {'type': 'int', 'default': 'rng 2..4', 'valid': '2..5'},
 'n_holes': {'type': 'int', 'default': 'rng 3..8', 'valid': '1..20'},
 'tile_kind': {'type': 'str',
               'default': 'rng helpful',
               'valid': 'digits|warm|cool|primary|broad'},
 'hole_distribution': {'type': 'str',
                       'default': 'rng helpful',
                       'valid': 'scattered|clustered|row_focus|col_focus|diagonal'},
 'texture': {'type': 'str',
             'default': 'alias for hole_distribution',
             'valid': 'scattered|clustered|row_focus|col_focus|diagonal|no_holes|all_holes|full_grid'}}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, p_lo, p_hi = 14, 18, 14, 18, 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, p_lo, p_hi = 22, 25, 22, 25, 3, 5
    else:
        h_lo, h_hi, w_lo, w_hi, p_lo, p_hi = 18, 25, 18, 25, 2, 4
    period = int(overrides.get("period", ctx.draw_int("period", p_lo, p_hi)))
    period = max(2, min(5, period))
    H = int(overrides.get("grid_h", ctx.draw_int("grid_h", h_lo, h_hi)))
    W = int(overrides.get("grid_w", ctx.draw_int("grid_w", w_lo, w_hi)))
    H = max(period + 2, H); W = max(period + 1, W)
    n_holes = int(overrides.get("n_holes",
                                ctx.draw_int("n_holes", 3, 8)))
    n_holes = max(1, min(20, n_holes))
    tile_kind = overrides.get("tile_kind",
                              ctx.draw_choice("tile_kind",
                                              list(TILE_KINDS)))
    distribution = (overrides.get("texture") or
                    overrides.get("hole_distribution")
                    or ctx.draw_choice("hole_distribution",
                                       list(HOLE_DISTRIBUTIONS)))
    tile = _build_tile(tile_kind, rng, period)
    g = full_grid(H, W, 0)
    for r in range(H):
        for c in range(W):
            g[r][c] = tile[r % period][c % period]
    # keep the first `period` rows intact so the period is unambiguous
    candidates = _hole_candidates(distribution, H, W, rng)
    candidates = [(r, c) for r, c in candidates if r >= period]
    if len(candidates) < n_holes:
        seen = set(candidates)
        fallback = [(r, c) for r in range(period, H) for c in range(W)
                    if (r, c) not in seen]
        rng.shuffle(fallback)
        candidates.extend(fallback)
    rng.shuffle(candidates)
    for r, c in candidates[:n_holes]:
        g[r][c] = 0
    return g


def _build_tile(kind, rng, period):
    """Return a period x period tile (all cells non-zero)."""
    if kind == "warm":
        base = [2, 3, 4, 6, 9]
    elif kind == "cool":
        base = [1, 5, 7, 8]
    elif kind == "primary":
        base = [1, 2, 3, 4]
    else:
        base = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    need = period * period
    pool = list(base)
    rng.shuffle(pool)
    while len(pool) < need:
        pool += rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 9)
    return [[pool[r * period + c] for c in range(period)] for r in range(period)]


def _hole_candidates(distribution, H, W, rng):
    if distribution == "clustered":
        cr = rng.randint(0, H - 1); cc = rng.randint(0, W - 1)
        cells = [(r, c) for r in range(H) for c in range(W)]
        cells.sort(key=lambda p: abs(p[0] - cr) + abs(p[1] - cc))
        return cells
    if distribution == "row_focus":
        rs = rng.sample(range(0, H), min(2, H))
        cells = [(r, c) for r in rs for c in range(W)]
        rng.shuffle(cells)
        return cells
    if distribution == "col_focus":
        cs = rng.sample(range(W), min(2, W))
        cells = [(r, c) for c in cs for r in range(0, H)]
        rng.shuffle(cells)
        return cells
    if distribution == "diagonal":
        diag = [(i, i) for i in range(min(H, W))]
        anti = [(i, W - 1 - i) for i in range(min(H, W))]
        cells = list(set(diag + anti))
        rng.shuffle(cells)
        return cells
    cells = [(r, c) for r in range(H) for c in range(W)]
    rng.shuffle(cells)
    return cells


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the variable-period tile-with-holes structure."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    H, W = len(grid), len(grid[0])
    if any(len(row) != W for row in grid):
        return ["ragged grid"]

    def period_ok(p):
        if H <= p or W < p:
            return False
        for r in range(p):
            for c in range(W):
                if grid[r][c] == 0:
                    return False
        for r in range(H):
            for c in range(W):
                v = grid[r][c]
                tv = grid[r % p][c % p]
                if tv == 0:
                    return False
                if v != 0 and v != tv:
                    return False
        return True

    periods = [p for p in range(2, 6) if period_ok(p)]
    if not periods:
        errs.append("no period 2..5 explains all non-zero cells from a non-zero top tile")
        period = None
    else:
        period = periods[0]

    holes = [(r, c) for r in range(H) for c in range(W) if grid[r][c] == 0]
    if not holes:
        errs.append("no holes to fill")
    elif period is not None:
        above = [(r, c) for r, c in holes if r < period]
        if above:
            errs.append("hole appears in preserved top tile rows")
    return errs


def _draw_from_degenerate(name, rng):
    size = 9
    g = full_grid(size, size, 0)
    tile = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    for r in range(size):
        for c in range(size):
            g[r][c] = tile[r % 3][c % 3]
    # (period-3 tile retained for these illustrative degenerates)
    if name == "no_holes":
        return g
    if name == "all_holes":
        for r in range(3, size):
            for c in range(size):
                g[r][c] = 0
        return g
    if name == "full_grid":
        for r in range(size):
            for c in range(size):
                g[r][c] = tile[r % 3][c % 3]
        return g
    return g
