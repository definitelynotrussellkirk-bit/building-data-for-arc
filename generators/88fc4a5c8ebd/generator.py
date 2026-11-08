"""Generator for arc_puzzle_bank_21_set5_e:easy_e07 — left-compress non-gray inside gray-blocker segments.

Rule: gray-5 cells split rows into independent segments. Within each
segment, non-gray values are left-compressed (preserving order).

Combinatorial axes (8): grid_h, grid_w, palette_kind, active_rows,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blockers, single_segment, already_packed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "88fc4a5c8ebd"
VERSION = "1.2.0"  # stronger self_check for visible row-segment compression evidence
TASK_ID = "88fc4a5c8ebd"

SUMMARY = "Left-compress non-gray values inside gray-blocker row segments."

INVARIANTS = [
    "background is 0",
    "gray 5 cells split rows into independent segments",
    "non-gray values keep row-local order",
    "at least one segment contains a movable value after a zero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blockers", "single_segment", "already_packed")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "3..12"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "active_rows":    {"type": "int", "default": "rng 3..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_segments_with_5_blockers",
                       "valid": "row_segments_with_5_blockers"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_blockers|single_segment|already_packed"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify visible gray-blocked row-segment compression evidence."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    gray_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not gray_cells:
        return []  # degenerate no_blockers override only
    movable_segments = 0
    for row in grid:
        edges = [-1] + [c for c, v in enumerate(row) if v == 5] + [w]
        for left, right in zip(edges, edges[1:]):
            seen_zero = False
            for c in range(left + 1, right):
                v = row[c]
                if v == 0:
                    seen_zero = True
                elif v != 5 and seen_zero:
                    movable_segments += 1
                    break
    if movable_segments == 0:
        return ["no segment contains a non-gray value to the right of a zero"]
    return []


def _segment_starts(width, rng):
    blockers = sorted(rng.sample(range(1, width - 1), rng.randint(1, 2)))
    edges = [-1] + blockers + [width]
    return blockers, [(edges[i] + 1, edges[i + 1]) for i in range(len(edges) - 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 5)
        w = ctx.draw_int("grid_w", 9, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 11, 14)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 9, 11)
    active_rows = min(ctx.draw_int("active_rows", 3, min(5, h)), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = [1, 2, 3, 4, 6, 7, 8, 9]
    rows = rng.sample(range(h), active_rows)
    forced_move = rng.choice(rows)
    for r in rows:
        blockers, segments = _segment_starts(w, rng)
        for c in blockers:
            g[r][c] = 5
        viable = [(a, b) for a, b in segments if b - a >= 3]
        if not viable:
            continue
        a, b = rng.choice(viable)
        count = rng.randint(1, min(3, b - a))
        if r == forced_move:
            cols = sorted(rng.sample(range(a + 1, b), min(count, b - a - 1)))
        else:
            cols = sorted(rng.sample(range(a, b), count))
        for c in cols:
            g[r][c] = rng.choice(colors)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "no_blockers":
        # No gray-5 blockers — every row is one big segment, removing
        # the per-segment compression evidence.
        g[1][3] = 4; g[2][1] = 6; g[3][5] = 7
        return g
    if name == "single_segment":
        # Blockers exist but only at the edge so segments collapse to
        # one — no per-segment compression evidence.
        g[1][0] = 5; g[1][6] = 4
        g[3][0] = 5; g[3][8] = 6
        return g
    if name == "already_packed":
        # Values already left-compressed against blockers — rule's
        # output equals input, no visible compression.
        g[1][0] = 4; g[1][3] = 5; g[1][4] = 6
        g[3][0] = 7; g[3][1] = 5
        return g
    return g
