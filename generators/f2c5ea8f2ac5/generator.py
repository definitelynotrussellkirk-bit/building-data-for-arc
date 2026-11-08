"""Generator for arc_puzzle_bank_third21:M19 — crop to active area.

Rule: crop the grid to the bbox of all non-zero cells (smaller output).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, full_grid_active, blob_at_border.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "f2c5ea8f2ac5"
VERSION = "2.1.0"  # more blobs/colors at harder bands (rule crops bbox of all non-zero; was fixed 2 blobs)
TASK_ID = "f2c5ea8f2ac5"
SUMMARY = (
    "0-bg grid (h~7-10, w~"
    "8-11) with 2 NON-ZERO "
    "BLOBS in 2 distinct "
    "colors from {1..9}, "
    "located in the "
    "INTERIOR — at LEAST 1 "
    "all-zero row above and "
    "below the content, "
    "and at LEAST 1 all-"
    "zero col left and "
    "right of the content. "
    "Blobs are 2-4 cells "
    "each, placed at non-"
    "touching interior "
    "positions. Rule (CROP "
    "TO THE BBOX OF ALL "
    "NON-ZERO CELLS): "
    "COMPUTE min_r = "
    "minimum row of any "
    "non-zero cell, max_r "
    "= maximum row, min_c "
    "= minimum col, max_c "
    "= maximum col. OUTPUT "
    "is the SUBGRID from "
    "(min_r, min_c) to "
    "(max_r, max_c) "
    "INCLUSIVE — i.e., the "
    "rectangle tightly "
    "wrapping all non-zero "
    "content (cell colors "
    "preserved). Output "
    "dimensions = (max_r - "
    "min_r + 1) × (max_c - "
    "min_c + 1). Net: "
    "input is trimmed to "
    "its active bbox, "
    "dropping zero-padding."
)

# Rivals: 'output is input' refuted by demos (output is smaller).
# 'output is just the largest blob' refuted by demos with multiple
# blobs all in the output. 'output is fixed N×N (e.g. 3×3)' refuted
# by demos with varying output dims. 'crop to grid of fixed border
# (1-cell)' refuted by demos showing exact non-zero bbox. 'recolor
# the cropped output' refuted by demos preserving colors. 3 demos
# with varied blob distributions pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥1 all-zero row at top, bottom, ≥1 all-zero col at left, right (so output is strictly smaller than input)",
    "≥1 non-zero blob inside the active area",
    "non-zero cells span a non-degenerate bbox (≥2 cells across in at least one dimension preferred)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "full_grid_active", "blob_at_border")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "2", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "interior_padded",
                       "valid": "interior_padded"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "1..9"},
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
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 10)
        nb = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 18)
        w = ctx.draw_int("grid_w", 14, 20)
        nb = ctx.draw_int("n_blobs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        nb = ctx.draw_int("n_blobs", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    for r in range(h):
        used.add((r, 0)); used.add((r, w - 1))
    for c in range(w):
        used.add((0, c)); used.add((h - 1, c))
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(nb, 9))
    for color in palette:
        cells = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=80)
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify this instance demonstrates a strict non-zero-bbox crop."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        errs.append("no non-zero cells; crop rule would be undefined/degenerate")
        return errs
    min_r = min(r for r, _ in nz); max_r = max(r for r, _ in nz)
    min_c = min(c for _, c in nz); max_c = max(c for _, c in nz)
    if min_r <= 0 or max_r >= h - 1:
        errs.append("active bbox must leave at least one all-zero row above and below")
    if min_c <= 0 or max_c >= w - 1:
        errs.append("active bbox must leave at least one all-zero column left and right")
    if any(grid[0][c] != 0 or grid[h - 1][c] != 0 for c in range(w)):
        errs.append("top/bottom border rows must stay zero in default generation")
    if any(grid[r][0] != 0 or grid[r][w - 1] != 0 for r in range(h)):
        errs.append("left/right border columns must stay zero in default generation")
    if len({grid[r][c] for r, c in nz}) < 1:
        errs.append("no active colors found")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # blank → no active area, rule undefined
        return g
    if name == "full_grid_active":
        # active cells span whole grid → crop is identity
        for r in range(h):
            for c in range(w):
                if (r + c) % 2 == 0: g[r][c] = 4
                else: g[r][c] = 6
        return g
    if name == "blob_at_border":
        # blob touches the outer border → no padding margin, crop is full grid
        for c in range(w): g[0][c] = 4
        g[3][3] = 6; g[4][4] = 6
        return g
    return g
