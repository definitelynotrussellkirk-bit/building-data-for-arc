"""Generator for arc_additional_puzzles_21_set22_bundle:M152.

Rule: for each non-bg color with 2 aligned cells (same row or col),
paint the span between with that color. Cells in 2+ spans → 9.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: parallel_only, single_pair, no_pairs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "db67c3d76937"
VERSION = "2.0.0"
TASK_ID = "db67c3d76937"
SUMMARY = (
    "0-bg grid (h×w, ~7-9 by ~9-11) with EXACTLY 2 pairs of cells: "
    "one VERTICAL pair of color A (2 cells in same column, "
    "different rows) and one HORIZONTAL pair of color B (2 cells "
    "in same row, different columns), where A ≠ B and A, B ≠ 9. "
    "The two spans (vertical line A, horizontal line B) cross at "
    "exactly one cell. Rule: for each non-bg color with exactly 2 "
    "cells, compute the SPAN (inclusive line of cells from one "
    "endpoint to the other, horizontal if same row, vertical if "
    "same column). Paint each span cell with that color. If any "
    "cell is in 2+ spans (intersection), overwrite with color 9 "
    "(maroon). Output: a cross pattern with 9 at the intersection."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 2 distinct non-zero non-9 colors, each with 2 cells",
    "one pair is vertically aligned (same col), the other horizontally aligned (same row)",
    "the two spans intersect at exactly one cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("parallel_only", "single_pair", "no_pairs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "2", "valid": "2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "crossing_axes",
                       "valid": "crossing_axes"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = [2, 3, 4, 5, 6, 7, 8]; rng.shuffle(palette)
    # Vertical pair (color 0) at column vc, rows vr1, vr2
    vc = rng.randint(2, w - 3)
    vr1 = rng.randint(0, h // 2 - 1)
    vr2 = rng.randint(h // 2 + 1, h - 1)
    # Horizontal pair (color 1) at row hr, cols hc1, hc2 — must cross vc
    hr = rng.randint(vr1 + 1, vr2 - 1)
    hc1 = rng.randint(0, vc - 1)
    hc2 = rng.randint(vc + 1, w - 1)
    g[vr1][vc] = palette[0]
    g[vr2][vc] = palette[0]
    g[hr][hc1] = palette[1]
    g[hr][hc2] = palette[1]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "parallel_only":
        # both pairs horizontal (or both vertical) → spans don't cross, no 9 cell
        g[1][1] = 3; g[1][8] = 3
        g[5][1] = 7; g[5][8] = 7
        return g
    if name == "single_pair":
        # only 1 aligned pair → at most 1 span, no intersections possible
        g[2][2] = 4; g[2][7] = 4
        return g
    if name == "no_pairs":
        # cells exist but none share a row or column → no spans, output equals input
        g[1][2] = 3; g[3][5] = 6; g[5][8] = 7
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    by: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                by.setdefault(v, []).append((r, c))
    if len(by) != 2:
        errs.append(f"expected exactly two nonzero pair colors, got {sorted(by)}")
    spans = []
    for color, pts in by.items():
        if color == 9:
            errs.append("input pair colors must exclude output-overlap color 9")
        if len(pts) != 2:
            errs.append(f"color {color} occurs {len(pts)} times, expected 2")
            continue
        (r1, c1), (r2, c2) = pts
        if r1 != r2 and c1 != c2:
            errs.append(f"color {color} endpoints are not row- or column-aligned")
            continue
        if r1 == r2:
            spans.append({(r1, c) for c in range(min(c1, c2), max(c1, c2) + 1)})
        else:
            spans.append({(r, c1) for r in range(min(r1, r2), max(r1, r2) + 1)})
    if len(spans) == 2 and len(spans[0] & spans[1]) != 1:
        errs.append("the horizontal and vertical spans must cross at exactly one cell")
    return errs
