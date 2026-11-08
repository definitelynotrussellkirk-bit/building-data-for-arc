"""Generator for arc_puzzle_bank_ninth_21_bundle:easy_63_complete_2x2_from_diagonal_pairs.

Combinatorial axes (8): grid_h, grid_w, palette_kind, pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, complete_2x2, single_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0e09cb9954e1"
VERSION = "2.1.1"  # 2.0.0->2.1.0: larger grids + more diagonal pairs -> more output shapes (already clean)
TASK_ID = "0e09cb9954e1"

SUMMARY = (
    "0-bg grid (h~7-10, w~7-10) with 2-4 ISOLATED 2×2 "
    "WINDOWS, each containing a same-color DIAGONAL "
    "PAIR — either main-diagonal ((0,0)+(1,1)) or anti-"
    "diagonal ((0,1)+(1,0)) — with the other two corners "
    "of the 2×2 currently 0. Different pairs use distinct "
    "colors; windows are spaced with ≥1-cell buffer. "
    "Rule: detect each 2×2 window with exactly 2 same-"
    "color cells on a diagonal. COMPLETE the 2×2 to a "
    "SOLID 2×2 BLOCK by filling the missing anti-diagonal "
    "(or main-diagonal) cells with the same color."
)

INVARIANTS = [
    "background is 0",
    "each active 2x2 window has two same-color opposite corners",
    "the other two corners are initially 0",
    "active windows are separated to avoid accidental completions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "complete_2x2", "single_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "pairs":          {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "diagonal_2x2_pairs",
                       "valid": "diagonal_2x2_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        target = ctx.draw_int("pairs", 4, 7)
    else:
        h = ctx.draw_int("grid_h", 7, 14)
        w = ctx.draw_int("grid_w", 7, 14)
        target = ctx.draw_int("pairs", 2, 6)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        r0 = rng.randint(0, h - 2)
        c0 = rng.randint(0, w - 2)
        guard = {
            (r, c)
            for r in range(max(0, r0 - 1), min(h, r0 + 3))
            for c in range(max(0, c0 - 1), min(w, c0 + 3))
        }
        if guard & reserved:
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        if rng.randrange(2) == 0:
            g[r0][c0] = color
            g[r0 + 1][c0 + 1] = color
        else:
            g[r0][c0 + 1] = color
            g[r0 + 1][c0] = color
        reserved.update(guard)
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 qualifying 2x2 diagonal pair (same color at two diagonal corners,
    other two corners empty)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            tl = grid[r][c]; tr = grid[r][c + 1]
            bl = grid[r + 1][c]; br = grid[r + 1][c + 1]
            if tl != 0 and tl == br and tr == 0 and bl == 0:
                return []
            if tr != 0 and tr == bl and tl == 0 and br == 0:
                return []
    return ["no qualifying 2x2 diagonal pair found — rule has nothing to complete"]


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no diagonal pairs to complete
        return g
    if name == "complete_2x2":
        # 2x2 already complete (4 cells of same color) → no missing diagonal
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 4
                g[5 + dr][5 + dc] = 6
        return g
    if name == "single_corner":
        # only 1 corner of each 2x2 set → can't infer the diagonal pair
        g[1][1] = 4
        g[5][6] = 6
        return g
    return g
