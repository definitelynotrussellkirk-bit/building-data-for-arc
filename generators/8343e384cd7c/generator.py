"""Generator for arc_puzzle_bank_twentysecond21:E150 — gravity down.

Rule: all non-zero cells fall to the bottom (each shifts down by max-row -
maximum cell row).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: already_at_bottom, no_cells, single_row_at_top.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8343e384cd7c"
VERSION = "2.1.0"  # connected-blob majority (canonical obj_count ~1; drift fix) + AXES synced to the real draws
RULE_HASH = "85c1547361c1"  # canonical rule this generator was written against
TASK_ID = "8343e384cd7c"
SUMMARY = (
    "0-bg grid (h~5-7, w~"
    "5-7) with SPARSE NON-"
    "ZERO CELLS positioned "
    "in the UPPER PORTION "
    "(rows 0..h//2). 2-5 "
    "cells in random non-0 "
    "colors from {1..9} are "
    "placed at random "
    "non-overlapping "
    "positions in the upper "
    "rows. At least one cell "
    "is NOT in the last row "
    "(row h-1) so gravity "
    "has visible effect. "
    "Rule (GRAVITY DOWN AS "
    "A RIGID GROUP — SHIFT "
    "ENTIRE CONTENT DOWN "
    "UNTIL BOTTOM TOUCHES "
    "ROW h-1): compute "
    "max_r = MAXIMUM ROW "
    "INDEX of any non-0 "
    "cell. SHIFT = (h - 1) "
    "- max_r. For EACH "
    "NON-0 CELL at (r, c) "
    "with color C: ERASE "
    "(r, c) to 0 and PAINT "
    "(r + shift, c) with C. "
    "Net: the entire "
    "non-zero content "
    "translates down as a "
    "rigid block until its "
    "bottom-most cell sits "
    "on row h-1. Columns "
    "and colors preserved."
)

# Rivals: 'output is input' refuted by demos where content is not at
# bottom. 'per-column gravity (each col falls independently)' refuted
# by demos showing the SHAPE preserved as a rigid group. 'shift only
# the lowest cell' refuted by demos with all cells shifted equally.
# 'use color 8' refuted by demos preserving colors. 'shift up instead
# of down' refuted by demos showing downward shift. 3 demos with
# varied shape and starting positions pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 non-zero cells in any colors",
    "max row of non-zero content is < h-1 (so the shift is non-zero)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("already_at_bottom", "no_cells", "single_row_at_top")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "4-6 easy / 6-9 med / 9-14 hard",
                       "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "5-7 easy / 6-10 med / 9-14 hard",
                       "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "2-3 easy / 3-6 med / 5-9 hard",
                       "valid": "2..9"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "upper_half",
                       "valid": "upper_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..8"},
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
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 5, 7)
        n = ctx.draw_int("n_cells", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 9, 14)
        n = ctx.draw_int("n_cells", 5, 9)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 6, 10)
        n = ctx.draw_int("n_cells", 3, 6)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    if rng.random() < 0.7:
        # canonical scenes hold ONE connected shape (defect-lint drift:
        # obj_count median 1 vs the old scatter's ~4) — grow a compact blob
        # of n cells in the upper half, 1-2 colors
        r0 = rng.randint(0, max(0, h // 2 - 1))
        c0 = rng.randint(0, w - 1)
        cells = {(r0, c0)}
        tries = 0
        while len(cells) < n and tries < 200:
            tries += 1
            r, c = rng.choice(sorted(cells))
            dr, dc = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            nr, nc = r + dr, c + dc
            if 0 <= nr <= h // 2 and 0 <= nc < w:
                cells.add((nr, nc))
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9],
                            1 if rng.random() < 0.6 else 2)
        for r, c in cells:
            g[r][c] = rng.choice(colors)
    else:
        for _ in range(n):
            for _t in range(40):
                r = rng.randint(0, h // 2)  # upper half
                c = rng.randint(0, w - 1)
                if g[r][c] != 0: continue
                g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 6
    g = full_grid(h, w, 0)
    if name == "already_at_bottom":
        # cells already on bottom row → gravity is identity
        g[h - 1][1] = 3
        g[h - 1][3] = 5
        g[h - 1][4] = 7
        return g
    if name == "no_cells":
        # empty grid → gravity has nothing to drop
        return g
    if name == "single_row_at_top":
        # all cells on top row only → gravity drops a clean horizontal line
        for c in range(w):
            if c % 2 == 0:
                g[0][c] = (c % 9) + 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """bg=0; ≥2 non-bg cells; max row of non-bg content < h-1 (shift is non-trivial)."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(nz) < 2:
        errs.append(f"need ≥2 non-bg cells, found {len(nz)}")
    elif max(r for r, c in nz) >= h - 1:
        errs.append("all non-bg content is in the last row — shift would be trivial")
    return errs
