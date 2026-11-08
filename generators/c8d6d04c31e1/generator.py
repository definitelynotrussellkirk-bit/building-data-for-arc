"""Generator for arc_puzzle_bank_eighth21:E51.

Rule: in each column with two same-color cells exactly 2 rows apart,
fill the middle cell with the same color.

Combinatorial axes (8): grid_h/w, palette_kind, n_bridges, palette_size,
position_bias, n_distinct_colors, gap_density, texture.
Degenerates: no_pairs, single_endpoint, pairs_too_far.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c8d6d04c31e1"
VERSION = "2.0.1"
TASK_ID = "c8d6d04c31e1"
SUMMARY = (
    "0-bg grid (h~7-9, w~7-9) with 2-4 ACTIVE COLUMNS, "
    "each containing exactly TWO same-color cells "
    "separated by EXACTLY 2 rows (cells at (r, c) and "
    "(r+2, c)), with the middle cell (r+1, c) initially "
    "0. Different active columns use distinct colors. "
    "Rule: for each column with a same-color vertical "
    "pair exactly 2 rows apart, fill the MIDDLE cell "
    "(r+1, c) with the same color. Net: each vertical "
    "pair becomes a solid 3-cell column segment."
)

INVARIANTS = [
    "background is 0",
    "each active column has a same-color pair two rows apart",
    "the midpoint cell is initially zero",
    "bridge colors are distinct to keep pairs unambiguous",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_pairs", "single_endpoint", "pairs_too_far")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "bridges":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "gap_density":    {"type": "str", "default": "fixed_2", "valid": "fixed_2"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
    n = min(ctx.draw_int("bridges", 2, 4), w, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cols = rng.sample(range(w), n)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for c, color in zip(cols, colors):
        r = rng.randint(0, h - 3)
        g[r][c] = color
        g[r + 2][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # singletons only — no midpoint to fill
        g[2][1] = 4
        g[5][6] = 7
        return g
    if name == "single_endpoint":
        # single cell — no second endpoint
        g[3][3] = 5
        return g
    if name == "pairs_too_far":
        # endpoints 4 rows apart — gap >1, rule's "midpoint" undefined
        g[1][2] = 6
        g[5][2] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Each non-bg color appears exactly twice in the same column, exactly 2 rows apart, with a 0 midpoint."""
    msgs = []
    from collections import Counter
    h = len(grid)
    w = len(grid[0]) if h else 0
    cells_by_color: dict = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                cells_by_color.setdefault(v, []).append((r, c))
    if not cells_by_color:
        msgs.append("no non-zero cells found")
        return msgs
    for color, cells in cells_by_color.items():
        if len(cells) != 2:
            msgs.append(f"color {color} has {len(cells)} cells (expected 2)")
            continue
        (r1, c1), (r2, c2) = cells
        if c1 != c2:
            msgs.append(f"color {color} pair not in same column: ({r1},{c1}) vs ({r2},{c2})")
            continue
        if abs(r2 - r1) != 2:
            msgs.append(f"color {color} pair not exactly 2 rows apart: |{r2}-{r1}|={abs(r2-r1)}")
            continue
        mid_r = (r1 + r2) // 2
        if grid[mid_r][c1] != 0:
            msgs.append(f"color {color} midpoint ({mid_r},{c1}) is not 0 (expected empty)")
    return msgs
