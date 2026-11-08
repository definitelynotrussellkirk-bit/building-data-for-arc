"""Generator for arc_puzzle_bank_21_set14_bundle:easy_n07.

Several nonzero colors appear, with one strict majority. The solver keeps only
that majority color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, majority_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_majority, single_color, all_minority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e4e80c9fad18"
VERSION = "2.1.0"  # clean but n_distinct_colors hardcoded 3 (1 majority + 2 minorities); rule picks max-count among ANY number of colors. Vary color count 2-5 (1 majority + 1-4 minorities) and grids so the 'pick max among more candidates' is exercised.
TASK_ID = "e4e80c9fad18"
SUMMARY = (
    "0-bg grid (h~6-9, w~"
    "8-12) with 3 DISTINCT "
    "NON-0 COLORS scattered "
    "at distinct positions: "
    "(a) MAJORITY color "
    "appears 6-10 times "
    "(strictly highest "
    "count); (b) TWO "
    "MINORITY colors each "
    "appear 1-3 times. "
    "Cells placed at random "
    "positions without "
    "overlap. Rule (KEEP "
    "ONLY THE NONZERO "
    "MAJORITY COLOR): "
    "identify the NON-0 "
    "COLOR with STRICTLY "
    "HIGHEST FREQUENCY in "
    "the grid (the "
    "majority). KEEP all "
    "cells of the majority "
    "color. ERASE all "
    "other non-0 cells "
    "(set to 0). Net: "
    "minority colors "
    "vanish; only the "
    "dominant color "
    "survives."
)

INVARIANTS = [
    "background is 0",
    "at least two nonzero colors appear",
    "one nonzero color has strictly highest frequency",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_majority", "single_color", "all_minority")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "majority_count": {"type": "int", "default": "rng 6..10", "valid": "2..30"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_majority",
                       "valid": "scattered_majority"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..5"},
    "density":        {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}




def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants: bg=0 plus a unique non-zero majority color.

    This catches the normal-path degenerates declared above: no majority,
    single-color identity, and all-minority/noise-only grids.
    """
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    counts = {}
    bg_cells = 0
    for row in grid:
        for v in row:
            if v == 0:
                bg_cells += 1
            else:
                counts[v] = counts.get(v, 0) + 1
    if bg_cells == 0:
        errs.append("expected 0 background cells")
    if len(counts) < 2:
        errs.append(f"expected at least two non-zero colors, found {len(counts)}")
        return errs
    max_count = max(counts.values())
    winners = [c for c, n in counts.items() if n == max_count]
    if len(winners) != 1:
        errs.append(f"expected a unique majority color, tied winners={sorted(winners)} count={max_count}")
    if max_count <= 1:
        errs.append("majority color appears only once")
    return errs

def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
        majority_count = ctx.draw_int("majority_count", 5, 7)
        n_col = ctx.draw_int("n_col", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
        majority_count = ctx.draw_int("majority_count", 10, 16)
        n_col = ctx.draw_int("n_col", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 8, 12)
        majority_count = ctx.draw_int("majority_count", 6, 10)
        n_col = ctx.draw_int("n_col", 3, 4)
    colors = ctx.draw_distinct_colors("colors", n=n_col, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    positions = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(positions)
    # 1 strict majority + (n_col-1) minorities (each 1-3, strictly below majority)
    counts = [majority_count] + [rng.randint(1, 3) for _ in range(n_col - 1)]
    idx = 0
    for color, count in zip(colors, counts):
        for r, c in positions[idx:idx + count]:
            g[r][c] = color
        idx += count
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_majority":
        # all colors tied → ambiguous which color to keep
        for (r, c) in [(1, 1), (2, 3), (3, 5)]: g[r][c] = 4
        for (r, c) in [(4, 1), (5, 3), (6, 5)]: g[r][c] = 6
        for (r, c) in [(1, 7), (2, 8), (3, 9)]: g[r][c] = 3
        return g
    if name == "single_color":
        # only one nonzero color → "majority" is trivial, rule is identity
        for (r, c) in [(1, 1), (2, 3), (3, 5), (4, 7), (5, 2)]: g[r][c] = 4
        return g
    if name == "all_minority":
        # all colors appear exactly once → no majority defined
        for (r, c, v) in [(1, 1, 4), (2, 3, 6), (3, 5, 3), (4, 7, 8)]: g[r][c] = v
        return g
    return g
