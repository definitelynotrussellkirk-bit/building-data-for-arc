"""Generator for arc_puzzle_bank_21_set10_e:easy_j03 — Connect 2-cell same-color pairs in row with alternating fill.

Rule: each row with exactly 2 cells of one color separated by all-0
gets cells between them filled in an alternating (1, 3, 5, ... cells)
pattern with that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, mismatched_endpoints, span_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7de2798953a7"
VERSION = "2.1.0"  # guarantee two/three valid pairs with distinct colors and adequate gaps
TASK_ID = "7de2798953a7"
SUMMARY = (
    "0-bg grid (h~4-6, w~7-9) with "
    "2-3 ACTIVE ROWS, each "
    "containing exactly TWO SAME-"
    "COLOR ENDPOINT CELLS at "
    "columns (c1, c2) with c2 ≥ "
    "c1 + 3 (≥2 cells of 0-gap "
    "between). Each pair uses a "
    "DISTINCT color from {2..9}. "
    "Rows are distinct. Rule "
    "(ALTERNATING-CELL FILL "
    "BETWEEN PAIR): for EACH ROW "
    "with EXACTLY 2 SAME-COLOR "
    "ENDPOINTS and an all-0 GAP, "
    "FILL the cells between them "
    "in an ALTERNATING pattern — "
    "every OTHER cell (1, 3, 5, "
    "...) in the gap gets the "
    "color; cells at even-step "
    "positions stay 0. Net: each "
    "row's same-color pair gets "
    "connected by a dotted "
    "(stripe-1) pattern in their "
    "color."
)

INVARIANTS = [
    "≥2 rows have a color appearing exactly twice, separated by ≥2 0-cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "mismatched_endpoints", "span_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "row_pairs_with_gap",
                       "valid": "row_pairs_with_gap"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..8"},
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
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 7, 9)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = [2, 3, 4, 5, 6, 7, 8, 9]
    n_pairs = ctx.draw_int("n_pairs", 2, min(3, h, len(palette)))
    rows = rng.sample(range(h), n_pairs)
    colors = rng.sample(palette, n_pairs)
    for r, color in zip(rows, colors):
        c1 = rng.randint(0, w - 4)
        c2 = rng.randint(c1 + 3, w - 1)
        g[r][c1] = color; g[r][c2] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 8
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # singletons only — no color appears exactly twice in any row
        g[1][2] = 4
        g[3][5] = 6
        return g
    if name == "mismatched_endpoints":
        # row has 2 cells but in different colors → not a same-color pair
        g[1][1] = 4; g[1][6] = 6
        g[3][2] = 7; g[3][7] = 8
        return g
    if name == "span_already_filled":
        # both endpoints + everything between already painted → rule has nothing
        for c in range(1, 7): g[1][c] = 4
        for c in range(2, 6): g[3][c] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    import collections
    valid = []
    colors = []
    for r, row in enumerate(grid):
        cnt = collections.Counter(v for v in row if v != 0)
        for color, k in cnt.items():
            pos = [i for i, v in enumerate(row) if v == color]
            if k == 2 and pos[1] - pos[0] >= 3 and all(v == 0 for v in row[pos[0] + 1:pos[1]]):
                valid.append(r); colors.append(color)
    msgs = []
    if len(valid) < 2:
        msgs.append("fewer than two valid endpoint-pair rows")
    if len(colors) != len(set(colors)):
        msgs.append("endpoint-pair colors are not distinct")
    return msgs
