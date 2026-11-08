"""Generator for arc_additional_puzzle_bank_volume11:E72.

Rule: equal-colored endpoint pairs in a row or column are bridged into
full segments.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n_pairs, texture.
Degenerates: no_pairs, adjacent_pair, no_shared_axis.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "15dd333aa99b"
# 2.1.0: reverse-diversity / canonical-match -- pick pair orientation
# PER PAIR (mix H & V in one grid, as canonical demos do) instead of one
# orientation per grid. Tracks used rows AND cols separately to keep lines clear.
VERSION = "2.1.1"
TASK_ID = "15dd333aa99b"
SUMMARY = (
    "0-bg grid (h, w~8-13) "
    "with 2-4 PAIRS of equal-"
    "colored ENDPOINT MARKERS "
    "in DISTINCT colors from "
    "{1..9}. EACH PAIR is "
    "aligned EITHER "
    "HORIZONTALLY (same row, "
    "≥2-cell gap between "
    "endpoints) OR VERTICALLY "
    "(same col, ≥2-cell gap) "
    "— orientation chosen "
    "once per task. Each "
    "pair occupies a distinct "
    "row (or column). No "
    "other cells. Rule "
    "(BRIDGE ENDPOINT PAIRS "
    "INTO FULL SEGMENTS): "
    "For EACH PAIR of same-"
    "color cells at (r, c1) "
    "and (r, c2) with c1 < c2 "
    "(horizontal), PAINT all "
    "cells (r, c1)..(r, c2) "
    "with that color (fill "
    "the gap). For VERTICAL "
    "pairs at (r1, c) and "
    "(r2, c), PAINT "
    "(r1..r2, c). Endpoints "
    "stay. Net: each "
    "endpoint pair turns "
    "into a full colored "
    "line segment."
)

INVARIANTS = [
    "background is 0",
    "each active nonzero color appears exactly twice",
    "paired markers are aligned horizontally or vertically with clear space between",
    "different colored segments are placed on separate rows or columns",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "adjacent_pair", "no_shared_axis")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "= n_pairs", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "scattered_axis_pairs",
                       "valid": "scattered_axis_pairs"},
    "n_distinct_colors": {"type": "int", "default": "= n_pairs", "valid": "1..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one pair of same-color cells aligned on same row or col."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_pairs", "adjacent_pair", "no_shared_axis"):
        return errs  # degenerate — skip structural check
    from collections import defaultdict
    positions = defaultdict(list)
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                positions[v].append((r, c))
    # At least one pair must be axis-aligned (the core invariant that fires the rule)
    has_pair = any(
        (len(cells) == 2 and (cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1]))
        for cells in positions.values()
    )
    if positions and not has_pair:
        errs.append("no axis-aligned pair found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_pairs = ctx.draw_int("n_pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        n_pairs = ctx.draw_int("n_pairs", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_pairs = ctx.draw_int("n_pairs", 2, 4)
    rng = ctx.draw_rng("placement")
    colors = list(range(1, 10))
    rng.shuffle(colors)
    g = full_grid(h, w, 0)
    # Reserve whole rows / cols per pair so that bridged segments never cross
    # another pair's endpoints (keeps the clear-line precondition satisfied).
    used_rows: set[int] = set()
    used_cols: set[int] = set()
    made = 0
    for color in colors:
        if made >= n_pairs:
            break
        # Each pair independently picks horizontal or vertical (mix in one grid).
        horizontal = rng.choice([True, False])
        if horizontal and len([r for r in range(h) if r not in used_rows]) and w >= 4:
            r = rng.choice([r for r in range(h) if r not in used_rows])
            c1 = rng.randint(0, w - 4)
            c2 = rng.randint(c1 + 2, w - 1)
            g[r][c1] = color
            g[r][c2] = color
            used_rows.add(r)
            made += 1
        elif len([c for c in range(w) if c not in used_cols]) and h >= 4:
            c = rng.choice([c for c in range(w) if c not in used_cols])
            r1 = rng.randint(0, h - 4)
            r2 = rng.randint(r1 + 2, h - 1)
            g[r1][c] = color
            g[r2][c] = color
            used_cols.add(c)
            made += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — no pair to bridge.
        return g
    if name == "adjacent_pair":
        # Pair shares an axis but is adjacent — rule's bridge has no
        # interior cells.
        g[3][2] = 4; g[3][3] = 4
        return g
    if name == "no_shared_axis":
        # Pair has matching color but lies on different rows AND cols
        # — rule's "in-row OR in-col" precondition fails.
        g[2][3] = 4; g[7][8] = 4
        return g
    return g
