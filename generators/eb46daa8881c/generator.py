"""Generator for arc_puzzle_bank_fourth21:E22.

Rule: each 5-cell plus motif has its center highlighted.

Combinatorial axes (8): grid_h, grid_w, palette_kind, pluses,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pluses, partial_pluses, dense_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eb46daa8881c"
VERSION = "2.2.0"  # faithful (pluses only; canonical has no decoys); widen pluses 1-8 + bigger grids
TASK_ID = "eb46daa8881c"
SUMMARY = (
    "0-bg grid (h, w~7-10) "
    "with 1-3 SAME-COLOR "
    "5-CELL PLUS MOTIFS — "
    "each at an interior "
    "center (r, c) with "
    "1 ≤ r ≤ h-2 and 1 ≤ "
    "c ≤ w-2, occupying "
    "the 5 cells {(r, c), "
    "(r-1, c), (r+1, c), "
    "(r, c-1), (r, c+1)} "
    "all painted in a "
    "RANDOM non-{0, 8} "
    "color from {1, 2, 3, "
    "4, 5, 6, 7, 9}. "
    "Pluses are SEPARATED "
    "by ≥1-cell padding "
    "(no shared cells in "
    "the 3×3 footprint "
    "guard). Rule "
    "(HIGHLIGHT EACH PLUS "
    "CENTER WITH CYAN 8)"
    ": For EACH 5-CELL "
    "PLUS-PATTERN of "
    "color C — i.e., a "
    "cell (r, c) with "
    "(r-1, c), (r+1, c), "
    "(r, c-1), (r, c+1) "
    "all equal to C: "
    "RECOLOR the CENTER "
    "cell (r, c) from C "
    "to COLOR 8 (cyan). "
    "Arms stay at C. "
    "Net: each plus "
    "becomes a cross of "
    "color C with a "
    "cyan dot in the "
    "middle."
)

INVARIANTS = [
    "background is 0",
    "each active motif is a five-cell plus",
    "the plus center and four cardinal arms share one non-8 color",
    "motif footprints are separated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pluses", "partial_pluses", "dense_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "pluses":         {"type": "int", "default": "rng 1..8 by diff", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "interior_pluses",
                       "valid": "interior_pluses"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_CARDINAL = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        target = ctx.draw_int("pluses", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        target = ctx.draw_int("pluses", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        target = ctx.draw_int("pluses", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    placed = 0

    def try_place(r, c):
        nonlocal placed
        cells = {(r, c)} | {(r + dr, c + dc) for dr, dc in _CARDINAL}
        # Reserve the 3x3 center neighborhood.  The previous expansion around
        # every arm cell reserved most of a 5x5 square and made hard targets
        # underfill despite ample non-overlapping plus locations.
        guard = {
            (rr, cc)
            for rr in range(r - 1, r + 2)
            for cc in range(c - 1, c + 2)
        }
        if guard & reserved:
            return False
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
        for rr, cc in cells:
            g[rr][cc] = color
        reserved.update(guard)
        placed += 1
        return True

    for _ in range(500):
        if placed >= target:
            break
        try_place(rng.randint(1, h - 2), rng.randint(1, w - 2))
    if placed < target:
        centers = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
        rng.shuffle(centers)
        for r, c in centers:
            if placed >= target:
                break
            try_place(r, c)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_pluses":
        # blank grid → no plus motifs to highlight, rule is identity
        return g
    if name == "partial_pluses":
        # T-shape (4 cells, missing one arm) → not a 5-cell plus, rule fails to detect
        # T-up missing bottom arm
        for (r, c) in [(2, 3), (3, 2), (3, 3), (3, 4)]: g[r][c] = 4
        # L-shape (3 cells)
        for (r, c) in [(6, 6), (7, 6), (7, 7)]: g[r][c] = 6
        return g
    if name == "dense_overlap":
        # two pluses overlapping each other → ambiguous which center belongs to which
        # plus 1 centered at (3,3)
        for (r, c) in [(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)]: g[r][c] = 4
        # plus 2 centered at (3,5) — shares col 4 cell
        for (r, c) in [(3, 5), (2, 5), (4, 5), (3, 6)]: g[r][c] = 6
        return g
    return g

def _plus_centers(grid):
    h, w = len(grid), len(grid[0])
    centers = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            v = grid[r][c]
            if v not in (0, 8) and all(grid[r + dr][c + dc] == v for dr, dc in _CARDINAL):
                centers.append((r, c, v))
    return centers

def self_check(grid, *, difficulty=None, meta=None):
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    lo, hi = (1, 2) if difficulty == "easy" else ((5, 8) if difficulty == "hard" else (2, 4))
    centers = _plus_centers(grid)
    errs = []
    if not (lo <= len(centers) <= hi):
        errs.append(f"expected {lo}..{hi} pluses, got {len(centers)}")
    if any(v == 8 for row in grid for v in row):
        errs.append("input plus color should never be output color 8")
    return errs
