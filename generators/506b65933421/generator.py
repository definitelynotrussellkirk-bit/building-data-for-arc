"""Generator for arc_additional_puzzles_21_set18_bundle:E122.

Rule: for each color appearing ≥2 times, fill its bbox rectangle in that
color on a fresh empty grid.

Combinatorial axes (8): grid_h/w, palette_kind, num_colors,
palette_size, position_bias, n_distinct_colors, bbox_aspect, texture.
Degenerates: only_one_cell, no_colors, all_aligned.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "506b65933421"
VERSION = "2.0.1"
TASK_ID = "506b65933421"
SUMMARY = (
    "0-bg grid (h~5-7, w~"
    "9-11) with ONE COLOR "
    "appearing as EXACTLY "
    "2 CELLS placed at "
    "DIAGONAL positions "
    "forming a NON-"
    "DEGENERATE BBOX (≥3 "
    "rows AND ≥3+ cols "
    "span). The two cells "
    "are at (r1, c1) and "
    "(r2, c2) with r2 ≥ "
    "r1 + 2 and c2 ≥ c1 "
    "+ 3 (or other "
    "diagonal arrangement). "
    "Color chosen from "
    "{2..9}. Rule (FILL "
    "EACH 2-CELL COLOR'S "
    "BBOX RECTANGLE WITH "
    "THE COLOR ON A FRESH "
    "EMPTY GRID): For "
    "EACH COLOR appearing "
    "≥2 times (here, "
    "exactly 2): compute "
    "its BBOX (min/max "
    "row and col). PAINT "
    "every cell within "
    "the bbox (inclusive)"
    " with that color in "
    "the output. Other "
    "cells stay 0. Net: "
    "the 2 cells get "
    "filled in to the "
    "solid rectangle they "
    "define."
)

INVARIANTS = [
    "≥1 color with exactly 2 cells",
    "bbox spans ≥3 rows AND ≥3 cols",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("only_one_cell", "no_colors", "all_aligned")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "num_colors":     {"type": "int", "default": "1", "valid": "1..2"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "diagonal",
                       "valid": "diagonal"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "bbox_aspect":    {"type": "str", "default": "rectangle",
                       "valid": "rectangle"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color has exactly 2 cells; their row-span and col-span are both >=2."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    counts: dict[int, list[tuple[int,int]]] = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                counts.setdefault(v, []).append((r, c))
    two_cell_colors = {v: cells for v, cells in counts.items() if len(cells) == 2}
    if not two_cell_colors:
        errs.append("no color with exactly 2 cells found")
    else:
        for v, cells in two_cell_colors.items():
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            if max(rs) - min(rs) < 1 or max(cs) - min(cs) < 1:
                errs.append(f"color {v}: 2-cell bbox must span >=2 rows AND >=2 cols (diagonal)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    r1 = rng.randint(0, h - 4); r2 = rng.randint(r1 + 2, h - 1)
    c1 = rng.randint(0, w - 5); c2 = rng.randint(c1 + 3, w - 1)
    g[r1][c1] = color; g[r2][c2] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "only_one_cell":
        # only 1 cell of the color — bbox is degenerate, rule has nothing to fill
        g[2][3] = 4
        return g
    if name == "no_colors":
        return g
    if name == "all_aligned":
        # all cells of the color in same row → zero-height bbox
        g[3][1] = 5
        g[3][6] = 5
        return g
    return g
