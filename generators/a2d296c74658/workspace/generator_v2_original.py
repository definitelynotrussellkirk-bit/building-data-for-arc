"""Generator for arc_additional_puzzles_21_set3:E18.

Rule: cells (r, c) = 0 with g[r-1][c] = 7 AND g[r+1][c] = 7 become 4.

Combinatorial axes (8): grid_h/w, palette_kind, num_triplets, vertical_offset,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: only_one_seven, sevens_adjacent, gap_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a2d296c74658"
VERSION = "2.0.0"
TASK_ID = "a2d296c74658"
SUMMARY = (
    "0-bg grid (h~7-9, w~6-8) with: (a) 2-3 "
    "VERTICAL (7, 0, 7) TRIPLETS — pairs of "
    "COLOR-7 (orange) cells at (r, c) and "
    "(r+2, c) in the same column, with the 0 "
    "between them at (r+1, c) being bg. Each "
    "triplet occupies a distinct column; (b) "
    "1-2 SINGLETON color-7 distractor cells "
    "placed without forming any new triplet. "
    "Rule: for EVERY 0-CELL at (r, c) where "
    "1 ≤ r ≤ h-2, check if BOTH g[r-1][c] == 7 "
    "AND g[r+1][c] == 7. If yes, RECOLOR that "
    "0-cell to COLOR 4 (yellow). The orange "
    "cells STAY. Net: each sandwich bg cell "
    "between two vertical oranges becomes "
    "yellow; singletons stay."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 columns have a vertical (7, 0, 7) triplet",
    "≥1 singleton 7-cell without a triplet partner (to test selectivity)",
]

PALETTE_KINDS = ("default", "scattered", "tight", "wide_grid")
DEGENERATE_TEXTURES = ("only_one_seven", "sevens_adjacent", "gap_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "num_triplets":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "vertical_offset": {"type": "int", "default": "2", "valid": "2"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "uniform", "valid": "uniform"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
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
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 7, 8)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 6, 8)
    rng = ctx.draw_rng("layout")
    n_triplets = rng.randint(2, 4) if difficulty == "hard" else rng.randint(2, 3)
    n_singletons = rng.randint(1, 2)

    for _layout_attempt in range(80):
        g = full_grid(h, w, 0)
        used_cols = set()
        for _ in range(n_triplets):
            for _ in range(80):
                c = rng.randint(0, w - 1); r = rng.randint(0, h - 3)
                if c not in used_cols and g[r][c] == 0 and g[r + 1][c] == 0 and g[r + 2][c] == 0:
                    g[r][c] = 7; g[r + 2][c] = 7
                    used_cols.add(c)
                    break
        target_triggers = _sandwiches(g)
        if len(target_triggers) < n_triplets:
            continue
        placed_singletons = 0
        for _ in range(n_singletons * 40):
            if placed_singletons >= n_singletons:
                break
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0 or c in used_cols:
                continue
            g[r][c] = 7
            # The old decoy guard missed the bottom endpoint case: two singleton
            # decoys in the same column, separated by one zero, accidentally formed
            # extra 7-0-7 triggers and sometimes left no harmless singleton at all.
            if _sandwiches(g) != target_triggers or _cell_participates_in_sandwich(g, r, c):
                g[r][c] = 0
                continue
            placed_singletons += 1
        if placed_singletons >= 1:
            return g
    raise ValueError("could not realize vertical-sandwich layout with safe singleton decoys")


def _sandwiches(g):
    h, w = len(g), len(g[0])
    return [(r, c) for r in range(1, h - 1) for c in range(w)
            if g[r][c] == 0 and g[r - 1][c] == 7 and g[r + 1][c] == 7]


def _cell_participates_in_sandwich(g, r, c):
    return any(c == cc and (r == rr - 1 or r == rr + 1) for rr, cc in _sandwiches(g))


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    triggers = _sandwiches(grid)
    if len(triggers) < 2:
        msgs.append(f"expected at least two visible 7-0-7 triggers; got {len(triggers)}")
    harmless = 0
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 7 and not _cell_participates_in_sandwich(grid, r, c):
                harmless += 1
    if harmless < 1:
        msgs.append("expected at least one harmless singleton 7 decoy")
    return msgs

def _draw_from_degenerate(name, rng):
    h, w = 8, 7
    g = full_grid(h, w, 0)
    if name == "only_one_seven":
        # single 7 with no partner — no triplet exists
        g[2][2] = 7
        g[4][5] = 7
        return g
    if name == "sevens_adjacent":
        # 7s with no zero between them — no fill happens
        g[2][2] = 7
        g[3][2] = 7
        g[4][5] = 7
        g[5][5] = 7
        return g
    if name == "gap_already_filled":
        # the would-be-4 cell is already nonzero — rule has nothing to fill
        g[2][2] = 7
        g[3][2] = 4
        g[4][2] = 7
        return g
    return g
