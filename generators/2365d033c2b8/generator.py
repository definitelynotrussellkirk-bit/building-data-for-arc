"""Generator for arc_additional_puzzles_21_set5:M35.

Rule: for each color with exactly 2 aligned cells (same row or column,
even distance), paint the integer midpoint cell with color 9.

Combinatorial axes (8): grid_h/w, palette_kind, num_pairs,
palette_size, position_bias, n_distinct_colors, alignment_mix, texture.
Degenerates: odd_distance, only_one_cell, three_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2365d033c2b8"
VERSION = "2.2.0"  # v2.2.0: prevent pair endpoints from occupying earlier midpoint cells; add self_check.
TASK_ID = "2365d033c2b8"
SUMMARY = (
    "0-bg grid (h~7-9, w~"
    "9-11) with 2 DISTINCT "
    "NON-{0, 9} COLORS, "
    "each appearing as "
    "EXACTLY 2 CELLS at "
    "AXIS-ALIGNED positions "
    "(same ROW or same "
    "COLUMN) at EVEN "
    "DISTANCE ≥ 2 (so the "
    "integer midpoint is "
    "well-defined). Pair "
    "cells and midpoints "
    "don't overlap between "
    "pairs. Other cells "
    "are 0. Rule (PAINT "
    "MIDPOINT OF EACH EVEN-"
    "DISTANCE SAME-COLOR "
    "PAIR WITH MAROON 9): "
    "for EACH COLOR C "
    "with EXACTLY 2 CELLS "
    "at (r1, c1) and (r2, "
    "c2) sharing row OR "
    "column at EVEN "
    "distance: COMPUTE "
    "MIDPOINT ((r1+r2)//2, "
    "(c1+c2)//2). PAINT "
    "the midpoint cell "
    "with COLOR 9 (maroon)"
    ". Endpoints stay at "
    "C. Colors with !=2 "
    "cells or odd-distance "
    "pairs are skipped. "
    "Net: each axis-"
    "aligned same-color "
    "pair gets a maroon "
    "dot between them at "
    "the midpoint."
)

# Rivals: 'paint midpoint with color of pair' refuted by any demo
# (midpoint is always 9). 'paint midpoint regardless of distance
# parity' refuted by ≥1 demo where odd-distance pair leaves no
# midpoint. 'paint at endpoints not midpoint' refuted by ≥1 demo
# where 9 clearly appears between the pair cells. 'paint for
# colors with >2 cells too' refuted by ≥1 demo where 3-cell
# color is left alone.
# 4 demos with varied pair positions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "2 distinct non-{0,9} colors, each with exactly 2 cells",
    "each color's 2 cells are aligned with even distance",
]

PALETTE_KINDS = ("default", "row_only", "col_only", "mixed_axes")
DEGENERATE_TEXTURES = ("odd_distance", "only_one_cell", "three_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..15"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "num_pairs":      {"type": "int", "default": "2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "alignment_mix":  {"type": "str", "default": "row+col", "valid": "row+col"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 11)
        n_pairs = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 13, 17)
        n_pairs = rng.randint(3, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        n_pairs = rng.randint(2, 4)
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], min(8, n_pairs))
    placed = 0
    midpoints = set()
    for color in colors:
        for _ in range(60):
            axis = rng.choice(["row", "col"])
            if axis == "row":
                r = rng.randint(0, h - 1)
                # distance must be even and ≥ 2
                max_dist = w - 1 - (w - 1) % 2
                if max_dist < 2: continue
                dist = rng.randint(1, max_dist // 2) * 2
                c1 = rng.randint(0, w - 1 - dist)
                c2 = c1 + dist
                cells = [(r, c1), (r, c2)]
                mid = (r, (c1 + c2) // 2)
            else:
                c = rng.randint(0, w - 1)
                max_dist = h - 1 - (h - 1) % 2
                if max_dist < 2: continue
                dist = rng.randint(1, max_dist // 2) * 2
                r1 = rng.randint(0, h - 1 - dist)
                r2 = r1 + dist
                cells = [(r1, c), (r2, c)]
                mid = ((r1 + r2) // 2, c)
            # All cells (including midpoint) must be free
            if any(g[r][c] != 0 for r, c in cells):
                continue
            if any(cell in midpoints for cell in cells):
                continue
            if g[mid[0]][mid[1]] != 0:
                continue
            # Midpoint must not collide with another pair's midpoint or cells.
            if mid in midpoints:
                continue
            for r, c in cells:
                g[r][c] = color
            midpoints.add(mid)
            placed += 1
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "odd_distance":
        # distance 5 — no integer midpoint
        g[2][1] = 1
        g[2][6] = 1
        return g
    if name == "only_one_cell":
        # color has only 1 cell — no pair, rule no-op
        g[2][3] = 1
        g[1][6] = 3
        g[5][6] = 3
        return g
    if name == "three_cells":
        # color has 3 cells — pairing ambiguous
        g[2][1] = 1
        g[2][3] = 1
        g[2][7] = 1
        g[1][5] = 3
        g[5][5] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate even-distance same-color midpoint-pair examples."""
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    by_color = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v not in (0, 9):
                by_color.setdefault(v, []).append((r, c))
    min_pairs = 3 if difficulty == "hard" else 2
    if len(by_color) < min_pairs:
        errs.append(f"expected at least {min_pairs} color pairs, got {len(by_color)}")
    midpoints = set()
    for color, cells in by_color.items():
        if len(cells) != 2:
            errs.append(f"color {color} should appear exactly twice")
            continue
        (r1, c1), (r2, c2) = cells
        row_pair = r1 == r2 and abs(c1 - c2) >= 2 and abs(c1 - c2) % 2 == 0
        col_pair = c1 == c2 and abs(r1 - r2) >= 2 and abs(r1 - r2) % 2 == 0
        if not (row_pair or col_pair):
            errs.append(f"color {color} must form an axis-aligned even-distance pair")
        mid = ((r1 + r2) // 2, (c1 + c2) // 2)
        if mid in midpoints:
            errs.append("pair midpoints must be distinct")
        midpoints.add(mid)
        if grid[mid[0]][mid[1]] != 0:
            errs.append("pair midpoint must be empty in the input")
    return errs
