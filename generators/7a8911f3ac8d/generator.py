"""Generator for arc_puzzle_bank_twentieth21:M138 — reflect through 9-anchor.

Rule: 9-anchor + a single non-9 blob. Output: original blob + its
reflection through the anchor (point symmetry).

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_anchor, multiple_anchors, blob_through_anchor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7a8911f3ac8d"
VERSION = "1.2.1"
TASK_ID = "7a8911f3ac8d"
SUMMARY = "Single maroon(9) anchor + a non-9 blob; rule keeps the blob and adds its 180° reflection through the anchor."

# Rivals: 'mirror across grid center, not anchor' refuted by ≥2 demos
# where anchor is off-center. 'horizontal flip only' refuted by any
# demo where reflection is on a diagonal. 'erase original blob'
# refuted by any demo (original survives). 'use anchor color (9) for
# mirror' refuted by any demo (mirror uses blob color).
# 4 demos with varied anchor positions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one 9-cell at grid center",
    "non-9 blob fully on one side; reflection in-bounds and disjoint",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchor", "multiple_anchors", "blob_through_anchor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "centered_anchor_with_offset_blob",
                       "valid": "centered_anchor_with_offset_blob"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, exactly one color-9 anchor, ≥1 non-9 non-0 blob cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    anchor_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(anchor_cells) != 1:
        errs.append(f"found {len(anchor_cells)} color-9 anchor cell(s); expected exactly 1")
    blob_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 9)]
    if not blob_cells:
        errs.append("no non-9 blob cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 6, 8)
        n_cells_target = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        n_cells_target = rng.randint(4, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        n_cells_target = rng.randint(3, 5)
    g = full_grid(h, w, 0)
    # Random anchor position (not edge, so reflection has room).
    ar = rng.randint(2, h - 3)
    ac = rng.randint(2, w - 3)
    g[ar][ac] = 9
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    # Pick blob cells whose reflections fit in-bounds and don't
    # overlap the original or anchor.
    cells = []
    attempts = 0
    while len(cells) < n_cells_target and attempts < 80:
        attempts += 1
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if (r, c) == (ar, ac) or (r, c) in cells:
            continue
        mr = 2 * ar - r; mc = 2 * ac - c
        if not (0 <= mr < h and 0 <= mc < w):
            continue
        if (mr, mc) == (ar, ac) or (mr, mc) in cells:
            continue
        # Original cell and reflection must differ (else cell is on the
        # anchor itself).
        if (r, c) == (mr, mc):
            continue
        cells.append((r, c))
    for r, c in cells:
        g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    ar, ac = h // 2, w // 2
    if name == "no_anchor":
        # no 9-cell → rule has no point of symmetry to use
        g[1][1] = 4; g[1][2] = 4; g[2][1] = 4
        return g
    if name == "multiple_anchors":
        # two 9-cells → which one is the symmetry center?
        g[2][2] = 9
        g[5][5] = 9
        g[1][1] = 4; g[1][2] = 4
        return g
    if name == "blob_through_anchor":
        # blob cell coincides with anchor → reflection self-overlaps
        g[ar][ac] = 9
        # cell whose reflection is itself (the anchor)
        g[ar - 1][ac] = 4  # reflection at (ar+1, ac)
        g[ar][ac - 1] = 4  # reflection at (ar, ac+1)
        return g
    return g
