"""Generator for arc_additional_puzzle_bank_volume18:E125.

Each color's aligned marker pair is filled into a same-color segment.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_cell, adjacent_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ffb7c0bc9376"
VERSION = "2.2.0"  # QUALITY: + non-aligned decoy pairs (exercise rule's else-branch / alignment precondition)
TASK_ID = "ffb7c0bc9376"
SUMMARY = (
    "0-bg grid (h×w, ~8-13 by ~8-13) with 2-5 COLOR PAIRS. "
    "Each pair: 2 cells of the same non-zero color sharing a ROW "
    "or a COLUMN with ≥1 empty cell between them. Different "
    "pairs use distinct colors. Pairs are placed so they don't "
    "interfere with each other. Plus 1-2 isolated decoration "
    "cells (no partner) to test selectivity. Rule: for each "
    "color, find its cells. If exactly 2 cells share a row, fill "
    "the row segment between them inclusive with that color. If "
    "they share a column, fill the column segment. Isolated cells "
    "with count != 2 are unchanged."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-5 color pairs, each in a distinct color",
    "each pair shares a row OR a column with ≥1 empty cell between",
    "1-2 isolated decoration cells (unpaired colors, count=1)",
    "0-2 non-aligned decoy pairs (count=2 but neither row- nor col-aligned; rule ignores them)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_cell", "adjacent_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_pairs":        {"type": "int", "default": "2 easy / 2-5 med / 5-8 hard", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "row_aligned_pairs",
                       "valid": "row_aligned_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pairs|single_cell|adjacent_pair"},
}


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
        h = ctx.draw_int("grid_h", 15, 20)
        w = ctx.draw_int("grid_w", 15, 20)
        n_pairs = ctx.draw_int("n_pairs", 5, 7)   # +1-2 decor stays within 9 colours
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 10, 14)
        n_pairs = ctx.draw_int("n_pairs", 3, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    colors = list(range(1, 10))
    rng.shuffle(colors)
    placed = 0
    color_idx = 0
    used_pos: set[tuple[int, int]] = set()
    for _ in range(80):
        if placed >= n_pairs or color_idx >= len(colors):
            break
        color = colors[color_idx]
        orient = rng.choice(["row", "col"])
        if orient == "row":
            r = rng.randint(0, h - 1)
            c1 = rng.randint(0, w - 3)
            c2 = rng.randint(c1 + 2, w - 1)
            cells = [(r, c1), (r, c2)]
        else:
            c = rng.randint(0, w - 1)
            r1 = rng.randint(0, h - 3)
            r2 = rng.randint(r1 + 2, h - 1)
            cells = [(r1, c), (r2, c)]
        if any(p in used_pos for p in cells):
            continue
        # Also check the segment between is free
        if orient == "row":
            segment = [(r, c) for c in range(c1, c2 + 1)]
        else:
            segment = [(r, c) for r in range(r1, r2 + 1)]
        if any(g[r][c] != 0 for r, c in segment):
            continue
        for r, c in cells:
            g[r][c] = color
        used_pos.update(segment)
        placed += 1
        color_idx += 1

    # Place 1-2 isolated decoration cells (no pair)
    n_decor = rng.randint(1, 2)
    for _ in range(n_decor):
        if color_idx >= len(colors):
            break
        decor_color = colors[color_idx]
        color_idx += 1
        for _try in range(30):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] == 0 and (r, c) not in used_pos:
                g[r][c] = decor_color
                used_pos.add((r, c))
                break

    # Non-aligned decoy pairs: 2 same-color cells sharing NEITHER a row nor a
    # column. The rule's cond falls to `else -> out`, leaving them untouched, so
    # they enrich the input and force the alignment precondition to be learned
    # (rule-safe: a fresh color the rule never fills, so no real pair gets 3+).
    n_diag = rng.randint(0, 2)
    for _ in range(n_diag):
        if color_idx >= len(colors):
            break
        dc = colors[color_idx]
        pick = None
        for _try in range(40):
            r1 = rng.randint(0, h - 1); c1 = rng.randint(0, w - 1)
            r2 = rng.randint(0, h - 1); c2 = rng.randint(0, w - 1)
            if r1 == r2 or c1 == c2:
                continue  # must be non-aligned so the rule ignores it
            if g[r1][c1] != 0 or g[r2][c2] != 0:
                continue
            pick = [(r1, c1), (r2, c2)]
            break
        if pick:
            for r, c in pick:
                g[r][c] = dc
            used_pos.update(pick)
            color_idx += 1

    if placed == 0:
        g[1][1] = 2
        g[1][4] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no pairs to fill
        return g
    if name == "single_cell":
        # only one cell of each color → "exactly twice" precondition fails
        g[2][3] = 4
        g[5][6] = 6
        return g
    if name == "adjacent_pair":
        # pair adjacent (distance 1) → no empty cells between, segment is degenerate
        g[3][4] = 4; g[3][5] = 4
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    issues = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    by_color = {}
    for r, row in enumerate(grid):
        if len(row) != w:
            issues.append("ragged grid")
            return issues
        for c, v in enumerate(row):
            if v:
                by_color.setdefault(v, []).append((r, c))
    aligned_pairs = 0
    decoy_pairs = 0
    singles = 0
    for color, cells in by_color.items():
        if len(cells) == 1:
            singles += 1
            continue
        if len(cells) != 2:
            issues.append(f"color {color} has {len(cells)} cells, expected 1 or 2")
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2 and abs(c1 - c2) >= 2:
            aligned_pairs += 1
        elif c1 == c2 and abs(r1 - r2) >= 2:
            aligned_pairs += 1
        elif r1 != r2 and c1 != c2:
            decoy_pairs += 1
        else:
            issues.append(f"color {color} adjacent aligned pair has no empty cell between")
    if aligned_pairs < 2:
        issues.append(f"expected at least two fillable aligned pairs, found {aligned_pairs}")
    if singles > 2:
        issues.append(f"expected at most two isolated decoration cells, found {singles}")
    if decoy_pairs > 2:
        issues.append(f"expected at most two non-aligned decoy pairs, found {decoy_pairs}")
    return issues
