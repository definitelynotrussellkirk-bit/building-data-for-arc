"""Generator for arc_puzzle_bank_21_set19_s:S19_E6.

Side-by-side panels vote; cells occupied in at least two panels become an 8-mask.

Combinatorial axes (8): grid_h, grid_w, palette_kind, panel_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_panels, no_overlap, all_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_vertical_panels

GENERATOR_ID = "c88f0bbb3d66"
VERSION = "2.0.0"
TASK_ID = "c88f0bbb3d66"
SUMMARY = (
    "0-bg grid assembled from "
    "N=3-4 SIDE-BY-SIDE PANELS "
    "(each h×w ~ 5-6 × 5-6) "
    "separated by FULL COLOR-9 "
    "(maroon) COLUMNS of width 1. "
    "Each panel is "
    "filled with cells in a "
    "DISTINCT panel color "
    "(2, 3, 4, …): 3-5 SHARED "
    "cells appear in ≥2 panels "
    "(threshold-2 overlap "
    "positions), plus 3 "
    "panel-unique cells. Rule "
    "(MAJORITY-VOTE MASK AT "
    "THRESHOLD 2): identify "
    "the N PANELS (separated "
    "by 9-rows). For EACH "
    "INTERIOR (r, c), COUNT "
    "how many PANELS have a "
    "non-0 cell at (r, c). "
    "EMIT an h×w MASK where "
    "out[r][c] = 8 (cyan) if "
    "COUNT ≥ 2, else 0. Net: "
    "cells lit in ≥2 panels "
    "form an 8-mask."
)

INVARIANTS = [
    "three or four same-size side-by-side panels separated by color-9 columns",
    "some coordinates are occupied in at least two panels",
    "the output is the coordinate-wise majority mask with threshold two",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_panels", "no_overlap", "all_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..6", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "derived", "valid": "13..30"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "panel_count":    {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "9col_separated_panels",
                       "valid": "9col_separated_panels"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_panels|no_overlap|all_overlap"},
}


def _panel(h: int, w: int, cells: set[tuple[int, int]], color: int):
    panel = full_grid(h, w, 0)
    for r, c in cells:
        panel[r][c] = color
    return panel



def _split_by_9_columns(grid):
    """Mirror the canonical rule's split-cols-9 helper for self_check."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    panels = []
    start = 0
    c = 0
    while c < w:
        if all(grid[r][c] == 9 for r in range(h)):
            if start < c:
                panels.append([row[start:c] for row in grid])
            while c < w and all(grid[r][c] == 9 for r in range(h)):
                c += 1
            start = c
        else:
            c += 1
    if start < w:
        panels.append([row[start:w] for row in grid])
    return panels


def _occupied(panel):
    cells = set()
    for r, row in enumerate(panel):
        for c, value in enumerate(row):
            if value not in (0, 9):
                cells.add((r, c))
    return cells


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for the threshold-2 panel-vote mask task."""
    problems = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty 2D list"]
    h = len(grid)
    w = len(grid[0]) if h else 0
    if w == 0 or any(len(row) != w for row in grid):
        problems.append("grid must be rectangular and non-empty")
        return problems
    if h > 30 or w > 30:
        problems.append(f"grid exceeds ARC max dimensions: {h}x{w}")

    panels = _split_by_9_columns(grid)
    if len(panels) not in (3, 4):
        problems.append(f"expected 3 or 4 color-9-separated panels, got {len(panels)}")
        return problems
    dims = {(len(p), len(p[0]) if p else 0) for p in panels}
    if len(dims) != 1:
        problems.append(f"panels must have identical dimensions, got {sorted(dims)}")
    occs = [_occupied(p) for p in panels]
    if any(not cells for cells in occs):
        problems.append("every panel must contain at least one non-background cell")
    all_cells = set().union(*occs) if occs else set()
    vote2 = {cell for cell in all_cells if sum(cell in cells for cells in occs) >= 2}
    if not vote2:
        problems.append("at least one coordinate must be occupied in two or more panels")
    return problems

def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 5, 5)
        w = ctx.draw_int("width", 5, 5)
        n = ctx.draw_int("panel_count", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 6, 6)
        w = ctx.draw_int("width", 6, 6)
        n = ctx.draw_int("panel_count", 4, 4)
    else:
        h = ctx.draw_int("height", 5, 6)
        w = ctx.draw_int("width", 5, 6)
        n = ctx.draw_int("panel_count", 3, 4)
    rng = ctx.draw_rng("cells")
    all_cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(all_cells)
    shared = set(all_cells[:ctx.draw_int("shared_count", 3, 5)])
    cursor = len(shared)
    panels = []
    for idx in range(n):
        cells = set(shared if idx < 2 else rng.sample(tuple(shared), 2))
        cells.update(all_cells[cursor:cursor + 3])
        cursor += 3
        panels.append(_panel(h, w, cells, 2 + idx))
    return assemble_vertical_panels(panels)


def _draw_from_degenerate(name, rng):
    h, w = 5, 5
    if name == "no_panels":
        # blank single panel → no overlap to compute
        return full_grid(h, w, 0)
    if name == "no_overlap":
        # 3 panels with disjoint cells → output mask is empty
        p1 = _panel(h, w, {(0, 0), (0, 1)}, 2)
        p2 = _panel(h, w, {(2, 2), (2, 3)}, 3)
        p3 = _panel(h, w, {(4, 4), (4, 0)}, 4)
        return assemble_vertical_panels([p1, p2, p3])
    if name == "all_overlap":
        # 3 panels with identical cells → output mask is full
        cells = {(1, 1), (2, 2), (3, 3)}
        p1 = _panel(h, w, cells, 2)
        p2 = _panel(h, w, cells, 3)
        p3 = _panel(h, w, cells, 4)
        return assemble_vertical_panels([p1, p2, p3])
    return full_grid(h, w, 0)
