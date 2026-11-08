"""Generator for f35919cb93b9 — 4-fold rotation around color-9 pivot.

Rule: find pivot = first color-9 cell. For each non-{0, 9} cell at
(r, c), compute offset (dr, dc) = (r - pivot_r, c - pivot_c). Generate
4 rotations: (dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr). Paint each
rotated position (pivot + offset) with the cell's color, if in bounds.
Output: 4-fold rotational symmetry around pivot.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f35919cb93b9"
VERSION = "2.2.0"  # +self_check (pivot/source/visible-rotation mirror) + AXES synced to real draws
RULE_HASH = "dde410311dc3"  # canonical rule this generator was written against
TASK_ID = "f35919cb93b9"

SUMMARY = (
    "0-bg grid (h×w, ~9-12 by ~9-12) with: (a) EXACTLY ONE "
    "color-9 PIVOT cell placed roughly in the center; (b) a "
    "SOURCE shape of 1-3 non-{0, 9} cells in some single color, "
    "placed off-center so its 4 rotations land at distinct "
    "positions and stay in bounds. Rule: find pivot. For each "
    "non-zero non-9 cell at (r, c), compute offset from pivot. "
    "Generate 4 rotational offsets (90° turns: (dr, dc), "
    "(dc, -dr), (-dr, -dc), (-dc, dr)). Paint each rotated "
    "position with the cell's color (if in bounds). Output: "
    "input + 3 rotated copies of each source cell."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one color-9 pivot cell, placed near center",
    "1-3 non-{0, 9} source cells in a single color",
    "all 4 rotations of every source cell land in-bounds",
    "source cells are not at the pivot (offset is non-zero)",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("no_pivot", "no_source", "source_at_pivot")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "9-10 easy / 9-13 med / 12-16 hard",
                       "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "9-10 easy / 9-13 med / 12-16 hard",
                       "valid": "9..16"},
    "n_source_cells": {"type": "int", "default": "1-2 easy / 2-3 med / 3-5 hard",
                       "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "default", "valid": "default"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "pivot_center_source_off",
                       "valid": "pivot_center_source_off"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Mirror the rule: exactly one maroon-9 pivot (its absence CRASHES the
    rule's `first`), >=1 colored source cell, and >=1 rotation image landing
    on a cell that changes (else identity)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    pivots = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(pivots) != 1:
        return [f"expected exactly one 9-pivot, found {len(pivots)}"]
    pr, pc = pivots[0]
    sources = [(r, c) for r in range(h) for c in range(w)
               if grid[r][c] not in (0, 9)]
    if not sources:
        return ["no colored source cells — nothing to rotate"]
    changes = False
    for (r, c) in sources:
        dr, dc = r - pr, c - pc
        for rr, cc in ((pr + dc, pc - dr), (pr - dr, pc - dc), (pr - dc, pc + dr)):
            if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != grid[r][c]:
                changes = True
    if not changes:
        return ["every rotation image is clipped or already painted — identity output"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n_source = ctx.draw_int("n_source_cells", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        n_source = ctx.draw_int("n_source_cells", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 9, 13)
        n_source = ctx.draw_int("n_source_cells", 2, 3)

    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    maxoff = max(2, min(h, w) // 2)   # offsets scale with grid (rotations checked below)

    for _outer in range(60):
        g = full_grid(h, w, 0)
        # Pivot near center (allow slight variation)
        pr = rng.randint(h // 2 - 1, h // 2 + 1)
        pc = rng.randint(w // 2 - 1, w // 2 + 1)
        g[pr][pc] = 9

        # Place source cells such that all 4 rotations land in bounds
        placed = 0
        attempts = 0
        cells_used = set([(pr, pc)])
        while placed < n_source and attempts < 80:
            attempts += 1
            # Pick offset
            dr = rng.randint(-maxoff, maxoff)
            dc = rng.randint(-maxoff, maxoff)
            if dr == 0 and dc == 0:
                continue
            # Check all 4 rotations are in-bounds
            rotations = [(dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr)]
            in_bounds = True
            for rd, rc in rotations:
                rr = pr + rd
                cc = pc + rc
                if not (0 <= rr < h and 0 <= cc < w):
                    in_bounds = False
                    break
            if not in_bounds:
                continue
            src_r = pr + dr
            src_c = pc + dc
            if (src_r, src_c) in cells_used:
                continue
            g[src_r][src_c] = color
            cells_used.add((src_r, src_c))
            placed += 1

        if placed >= n_source:
            return g
    raise ValueError("could not place pivot + source cells with in-bounds rotations")


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_pivot":
        g[2][3] = 4
        return g
    if name == "no_source":
        g[4][4] = 9
        return g
    if name == "source_at_pivot":
        g[4][4] = 9  # pivot and source coincide
        return g
    return g
