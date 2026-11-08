"""Generator for arc_puzzle_bank_21_set24_bundle:easy_p05.

Rule: same-color diagonal corner pairs complete their rectangles.

Combinatorial axes (8): grid_h, grid_w, palette_kind, pair_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, collinear_pairs, mismatched_pair_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f8bf11d8b63a"
VERSION = "2.1.0"  # constructively guarantee diagonal targets plus same-row/col distractors
TASK_ID = "f8bf11d8b63a"
SUMMARY = "Per color: exactly 2 cells form a non-degenerate diagonal pair (different row AND different col). Rule fills the OTHER TWO corners of the implied axis-aligned rectangle with the same color, if those positions are currently 0. Multiple colors are independent. Cells on the same row or same column do not pair."

# Rivals: 'output is input' refuted by any demo (each pair fills 2
# corners). 'fill all cells inside the rectangle' refuted by any
# demo where interior stays 0. 'fill same row/col pairs' refuted
# by any demo with such cells that stay alone. 'overwrite existing
# cells' refuted by demos with pre-existing non-0 at would-be
# corners that stay unchanged. 3 demos with ≥2 distinct colors
# cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "target colors form non-degenerate diagonal corner pairs",
    "optional distractor colors form same-row/same-column pairs that the rule must ignore",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "collinear_pairs", "mismatched_pair_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "4..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "pair_count":     {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_diagonal_pairs",
                       "valid": "spaced_diagonal_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _blocked(cells: list[tuple[int, int]]) -> set[tuple[int, int]]:
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return {(r, c)
            for r in range(min(rs) - 1, max(rs) + 2)
            for c in range(min(cs) - 1, max(cs) + 2)}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10); w = ctx.draw_int("grid_w", 8, 12)
        pair_count = ctx.draw_int("pair_count", 1, 2); ndr = (0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 16, 22)
        pair_count = ctx.draw_int("pair_count", 4, 7); ndr = (2, 3)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 12, 17)
        pair_count = ctx.draw_int("pair_count", 2, 4); ndr = (1, 2)
    rng = ctx.draw_rng("layout")
    n_distractor = rng.randint(*ndr)
    total_colors = min(pair_count + n_distractor, 9)
    if total_colors < pair_count + n_distractor:
        n_distractor = max(0, total_colors - pair_count)

    # Use disjoint 3x3 macro-cells.  Earlier versions sampled arbitrary
    # pairs and sometimes failed silently; the task only needs the two
    # endpoint cells, so a macro-cell construction gives both visibility and
    # guaranteed separation for the requested number of pairs.
    boxes = [(r, c) for r in range(0, h - 2, 3) for c in range(0, w - 2, 3)]
    if len(boxes) < pair_count + n_distractor:
        raise ValueError("not enough disjoint boxes for requested pairs")
    rng.shuffle(boxes)
    allcolors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], total_colors)
    colors = allcolors[:pair_count]
    dcolors = allcolors[pair_count:]
    grid = full_grid(h, w, 0)

    for color, (r, c) in zip(colors, boxes[:pair_count]):
        if rng.choice([True, False]):
            cells = [(r, c), (r + 2, c + 2)]
        else:
            cells = [(r, c + 2), (r + 2, c)]
        for rr, cc in cells:
            grid[rr][cc] = color

    # same-row / same-col DISTRACTOR pairs: the rule never completes these
    # (it requires r1>r0 AND c1!=c0), so they pin the diagonal condition.
    for color, (r, c) in zip(dcolors, boxes[pair_count:pair_count + n_distractor]):
        if rng.choice([True, False]):
            cells = [(r + 1, c), (r + 1, c + 2)]
        else:
            cells = [(r, c + 1), (r + 2, c + 1)]
        for rr, cc in cells:
            grid[rr][cc] = color
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no diagonal corners, rule has no rectangles to complete
        return g
    if name == "collinear_pairs":
        # both cells in same row → degenerate rectangle (zero height), rule undefined
        g[2][1] = 4; g[2][5] = 4  # same row
        g[5][2] = 6; g[5][7] = 6  # same row
        return g
    if name == "mismatched_pair_colors":
        # two cells but in different colors → no actual pair, rule's predicate fails
        g[1][1] = 4; g[3][5] = 6  # different colors at "would-be diagonal"
        g[5][2] = 3; g[7][6] = 8
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    by_color = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                by_color.setdefault(v, []).append((r, c))
    diag = 0
    axis = 0
    for color, cells in by_color.items():
        if len(cells) != 2:
            msgs.append(f"color {color} appears {len(cells)} times, expected exactly two cells")
            continue
        (r1, c1), (r2, c2) = cells
        if r1 != r2 and c1 != c2:
            diag += 1
        else:
            axis += 1
    if diag < (1 if difficulty == "easy" else 2):
        msgs.append("too few non-degenerate diagonal target pairs")
    if difficulty != "easy" and axis < 1:
        msgs.append("expected at least one same-row/col distractor pair")
    return msgs
