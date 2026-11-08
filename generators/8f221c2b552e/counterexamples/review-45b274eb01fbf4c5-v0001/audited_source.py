"""Generator for arc_puzzle_bank_seventh_21_bundle:easy_43_bridge_row_pairs.

Rule: rows contain same-color marker pairs whose interior segment is
filled.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, mismatched_endpoints, span_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8f221c2b552e"
VERSION = "1.2.2"
TASK_ID = "8f221c2b552e"

SUMMARY = "Rows contain same-color marker pairs; rule fills the interior segment between them with the pair's color."

# Rivals: 'bridge with a fixed color' refuted by ≥2 demos with different
# pair colors. 'bridge only first pair' refuted by ≥1 demo with ≥2
# active rows. 'bridge across columns regardless of row' refuted by
# any demo where each pair stays in its own row. 'erase endpoints'
# refuted by any demo (endpoints survive in output).
# 3 demos with varied pair counts + colors cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each active row has one same-color pair",
    "the cells between the paired endpoints are initially empty",
    "at least one row has a gap to bridge",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "mismatched_endpoints", "span_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "3..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_pairs":        {"type": "int", "default": "2-3 easy / 3-5 med / 4-7 hard", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_pairs",
                       "valid": "row_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|mismatched_endpoints|span_already_filled"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 row has a same-color pair at two different columns."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_pairs", "mismatched_endpoints", "span_already_filled"):
        return errs
    found_pair = False
    for r in range(h):
        seen: dict[int, int] = {}
        for c in range(w):
            v = grid[r][c]
            if v == 0:
                continue
            if v in seen and seen[v] != c:
                found_pair = True
                break
            seen[v] = c
        if found_pair:
            break
    if not found_pair:
        errs.append("no row has a same-color pair at two different columns")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 10)
        target = min(ctx.draw_int("n_pairs", 2, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 13, 16)
        target = min(ctx.draw_int("n_pairs", 4, 7), h)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 10, 13)
        target = min(ctx.draw_int("n_pairs", 3, 5), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), target)
    palette = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(palette)
    for i, r in enumerate(rows):
        color = palette[i % len(palette)]
        c0 = rng.randint(0, w - 4)
        c1 = rng.randint(c0 + 2, w - 1)
        g[r][c0] = color
        g[r][c1] = color
        if rng.randrange(3) == 0 and c0 > 1:
            g[r][rng.randrange(0, c0)] = rng.choice([c for c in palette if c != color])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # singletons only — no row has a same-color pair
        g[1][2] = 4
        g[3][5] = 6
        return g
    if name == "mismatched_endpoints":
        # rows have 2 cells but in different colors → not a same-color pair
        g[1][1] = 4; g[1][6] = 6
        g[3][2] = 7; g[3][7] = 8
        return g
    if name == "span_already_filled":
        # both endpoints + everything between already painted → rule has nothing
        for c in range(1, 7): g[1][c] = 4
        for c in range(2, 6): g[3][c] = 6
        return g
    return g
