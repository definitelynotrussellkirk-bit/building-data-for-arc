"""Generator for arc_additional_puzzles_21_set6:E36.

Connect 2 same-color cells aligned in row/col.

Combinatorial axes (8): grid_h, grid_w, palette_kind, alignment,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pair, diagonal_only, adjacent_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9c928e7deebc"
VERSION = "2.0.1"  # distinct 72 / under-distributed: only 1 aligned pair + 1 singleton. Rule connects EVERY exactly-2 same-color aligned pair (canonical has 3 pairs). Place 2-4 distinct-color aligned pairs (clear segments) + an optional non-aligned (diagonal) distractor pair the rule leaves alone."
TASK_ID = "9c928e7deebc"
SUMMARY = "2-4 distinct-color pairs, each color appearing exactly twice and aligned in a row or column (>=3 apart, clear segment) so the rule fills the segment; plus an optional diagonal (non-aligned) distractor pair that stays."

INVARIANTS = [
    "≥1 color with 2 cells aligned in row or col",
    "1 distractor singleton of different color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pair", "diagonal_only", "adjacent_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {'grid_h': {'type': 'int', 'default': 'rng 5..7', 'valid': '4..10'},
 'grid_w': {'type': 'int', 'default': 'rng 8..10', 'valid': '6..14'},
 'palette_kind': {'type': 'str', 'default': 'rng helpful', 'valid': 'default|warm|cool|varied'},
 'alignment': {'type': 'str', 'default': 'rng row|col', 'valid': 'row|col'},
 'palette_size': {'type': 'int', 'default': '2', 'valid': '2..2'},
 'position_bias': {'type': 'str',
                   'default': 'aligned_pair_plus_singleton',
                   'valid': 'aligned_pair_plus_singleton'},
 'n_distinct_colors': {'type': 'int', 'default': '2', 'valid': '2..2'},
 'density': {'type': 'str', 'default': 'sparse', 'valid': 'sparse'},
 'texture': {'type': 'str',
             'default': 'alias for palette_kind',
             'valid': 'default|warm|cool|varied|no_pair|diagonal_only|adjacent_pair'}}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6); w = ctx.draw_int("grid_w", 8, 10)
        k_lo, k_hi = 2, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 10); w = ctx.draw_int("grid_w", 10, 14)
        k_lo, k_hi = 3, 4
    else:
        h = ctx.draw_int("grid_h", 5, 8); w = ctx.draw_int("grid_w", 8, 12)
        k_lo, k_hi = 2, 3
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    k = rng.randint(k_lo, k_hi)
    pal = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(k + 1, 9))

    def _seg_clear(cells):
        return all(g[r][c] == 0 for r, c in cells)

    # k aligned pairs (each color appears exactly twice, >=3 apart, clear segment
    # so the rule's fill is visible and unambiguous).
    for color in pal[:k]:
        for _ in range(80):
            if rng.random() < 0.5:                     # horizontal
                r = rng.randrange(h)
                c1 = rng.randint(0, w - 4); c2 = rng.randint(c1 + 3, w - 1)
                cells = [(r, c) for c in range(c1, c2 + 1)]
            else:                                      # vertical
                c = rng.randrange(w)
                r1 = rng.randint(0, h - 4); r2 = rng.randint(r1 + 3, h - 1)
                cells = [(r, c) for r in range(r1, r2 + 1)]
            if _seg_clear(cells):
                g[cells[0][0]][cells[0][1]] = color
                g[cells[-1][0]][cells[-1][1]] = color
                break
    # Optional diagonal (non-aligned) distractor pair: same color twice but NOT
    # sharing a row/col, so the rule leaves it alone (covers the no-connect branch).
    if len(pal) > k and rng.random() < 0.5:
        dcol = pal[k]
        for _ in range(40):
            r1 = rng.randrange(h); c1 = rng.randrange(w)
            r2 = rng.randrange(h); c2 = rng.randrange(w)
            if r1 != r2 and c1 != c2 and g[r1][c1] == 0 and g[r2][c2] == 0:
                g[r1][c1] = dcol; g[r2][c2] = dcol
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "no_pair":
        # only one cell of the would-be pair color
        g[2][4] = 4
        g[4][7] = 6
        return g
    if name == "diagonal_only":
        # pair on a diagonal → no row/col alignment, no segment fill
        g[1][1] = 4; g[3][3] = 4
        g[5][8] = 6
        return g
    if name == "adjacent_pair":
        # pair separated by 1 → segment between them is empty (length-0)
        g[2][3] = 4; g[2][4] = 4
        g[4][7] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: at least one color that has exactly 2 cells aligned in the same row or column."""
    msgs = []
    h, w = len(grid), len(grid[0])
    from collections import defaultdict
    color_rows = defaultdict(list)
    color_cols = defaultdict(list)
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                color_rows[v].append(r)
                color_cols[v].append(c)
    pair_found = False
    for v in color_rows:
        rs = color_rows[v]; cs = color_cols[v]
        if len(rs) == 2:
            if rs[0] == rs[1] or cs[0] == cs[1]:
                pair_found = True
                break
    if not pair_found:
        msgs.append("no color has exactly 2 cells aligned in a row or column")
    return msgs
