"""Generator for arc_additional_puzzle_bank_volume3:M21 — 180-rotate each object within its bbox.

Rule: for each object, paint at the 180-rotated position within its
bbox. (Original cells stay too — fold onto g.) Effect: union of
original and 180-rotation.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: symmetric_blobs, single_cell_blobs, blobs_overlap_bboxes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob, bbox_of, bbox_overlaps

GENERATOR_ID = "1e41c90ec2dc"
# 2.1.0: enforce the stated invariant (>=1 blob NOT 180-symmetric in its bbox)
# at generation — previously all-symmetric draws produced output == input
# (identity demo). Adds self_check.
VERSION = "2.1.0"
TASK_ID = "1e41c90ec2dc"
SUMMARY = (
    "0-bg grid (h, w~8-12) "
    "with 2-4 NON-TOUCHING "
    "BBOX-ISOLATED BLOBS, "
    "each grown to size 3-6 "
    "cells, in DISTINCT colors "
    "shuffled from {1..9}. "
    "Blobs are placed so their "
    "BBOXES DON'T OVERLAP "
    "(strict bbox isolation, "
    "not just 4-non-touching) "
    "and ≥1 blob is NOT 180°-"
    "symmetric so the rule "
    "produces visible change. "
    "Rule (UNION EACH BLOB "
    "WITH ITS 180° ROTATION "
    "WITHIN BBOX): For EACH "
    "BLOB: COMPUTE its BBOX "
    "(r1, c1, r2, c2). For "
    "EACH cell at (r, c) of "
    "the blob, PAINT the "
    "180°-ROTATED position "
    "(r1+r2-r, c1+c2-c) in "
    "the SAME color. Original "
    "cells stay (so the "
    "result is the UNION of "
    "the blob and its 180° "
    "rotation within bbox). "
    "Net: each blob becomes "
    "its own 2-fold "
    "rotationally symmetric "
    "version inside its bbox."
)

INVARIANTS = [
    "between 2 and 4 non-touching blobs",
    "blobs are bbox-isolated",
    "at least one blob is not 180-symmetric",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("symmetric_blobs", "single_cell_blobs", "blobs_overlap_bboxes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread_asymmetric_blobs",
                       "valid": "spread_asymmetric_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least one color-blob must NOT be 180-symmetric within its own bbox,
    otherwise the union-with-180-rotation rule leaves the grid unchanged."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    from collections import defaultdict
    by_color = defaultdict(set)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                by_color[grid[r][c]].add((r, c))
    if not by_color:
        return ["grid has no blobs"]
    any_asym = False
    for color, cells in by_color.items():
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        rot = {(r1 + r2 - r, c1 + c2 - c) for r, c in cells}
        if rot != cells:
            any_asym = True
    if not any_asym:
        errors.append("every blob is already 180-symmetric in its bbox — the rule "
                      "would leave the grid unchanged (identity demo)")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_blobs = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n_blobs = 4
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        n_blobs = ctx.draw_int("n_blobs", 2, 4)
    rng = ctx.draw_rng("layout")

    def _is_180_symmetric(blob, bb):
        r1, c1, r2, c2 = bb
        return {(r1 + r2 - r, c1 + c2 - c) for r, c in blob} == set(blob)

    last = None
    for _attempt in range(30):
        g = full_grid(h, w, 0)
        colors = list(range(1, 10)); rng.shuffle(colors)
        used = set(); bboxes = []; blobs = []
        for i in range(n_blobs):
            size = rng.randint(3, 6)
            for _ in range(10):
                blob = grow_blob(rng, h, w, used, size)
                if blob is None: continue
                bb = bbox_of(blob)
                if any(bbox_overlaps(bb, ob) for ob in bboxes): continue
                used |= blob; bboxes.append(bb); blobs.append((blob, bb))
                for r, c in blob: g[r][c] = colors[i % len(colors)]
                break
        last = g
        # require >=1 asymmetric blob so the 180-union actually changes the grid
        if blobs and any(not _is_180_symmetric(b, bb) for b, bb in blobs):
            return g
    return last


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "symmetric_blobs":
        # all blobs are 180-symmetric → rule's union is identity, no visible change
        for (r, c) in [(1, 1), (1, 2), (2, 1), (2, 2)]: g[r][c] = 4
        for (r, c) in [(5, 6), (4, 6), (6, 6), (5, 5), (5, 7)]: g[r][c] = 6
        return g
    if name == "single_cell_blobs":
        # 1x1 blobs → 180-rotation around the single cell is identity, no expansion
        g[2][3] = 4; g[5][7] = 6; g[7][2] = 3
        return g
    if name == "blobs_overlap_bboxes":
        # blob bboxes overlap → 180-rotation may paint over other blob cells, ambiguous
        for (r, c) in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 4
        for (r, c) in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 6
        return g
    return g
