"""Generator for 16b:m112 — pack blob crops by ascending width.

Rule: sort blobs by bbox width ascending, gallery-pack horizontally.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, single_blob, tied_widths.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "abf3863c9aa5"
VERSION = "2.0.1"
TASK_ID = "abf3863c9aa5"
SUMMARY = (
    "0-bg grid (h~7-10, w~10-12) with 4 "
    "BLOBS each a 2-4 cell 4-connected blob "
    "grown via grow_blob, painted in a "
    "DISTINCT non-0 color drawn from a "
    "shuffled palette {1..9}. Each blob's "
    "BBOX WIDTH is STRICTLY DISTINCT from "
    "the other 3 (seen_widths set ensures no "
    "two blobs share width). Blobs are "
    "placed at non-touching non-overlapping "
    "positions via used-cell tracking. Rule "
    "(SORT BLOBS BY BBOX WIDTH ASCENDING, "
    "GALLERY-PACK HORIZONTALLY): extract "
    "every 4-CONNECTED non-bg COMPONENT. "
    "CROP each to its tight bbox. SORT crops "
    "by BBOX WIDTH ASCENDING (since widths "
    "are strictly distinct, sort is "
    "unambiguous). PACK the cropped blobs "
    "LEFT-TO-RIGHT in sorted order with a "
    "1-column bg gap between consecutive "
    "crops, into a horizontal output grid. "
    "OUTPUT HEIGHT = max bbox_h across "
    "blobs; shorter crops are bottom-aligned "
    "(or top-aligned per demos). Net: 4 "
    "scattered blobs collapse into a "
    "horizontal gallery ordered by "
    "increasing width."
)

INVARIANTS = [
    "background is 0",
    "4 distinct-color blobs with strictly distinct bbox widths",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "single_blob", "tied_widths")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 10..12", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "4", "valid": "4..4"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "distinct_width_blobs",
                       "valid": "distinct_width_blobs"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least 2 distinct nonzero colors (blobs)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_blobs",):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct blob colors; found {len(colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 10, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)
    used: set[tuple[int, int]] = set()
    seen_widths: set[int] = set()
    for color in palette:
        for _ in range(60):
            cells = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=20)
            if cells is None:
                continue
            cs = [c for _, c in cells]
            bb_w = max(cs) - min(cs) + 1
            if bb_w in seen_widths:
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            seen_widths.add(bb_w)
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # blank → no blobs to sort
        return g
    if name == "single_blob":
        # one blob → trivially sorted, no contrast
        for r, c in [(2, 3), (2, 4), (3, 4)]: g[r][c] = 4
        return g
    if name == "tied_widths":
        # 2 blobs share width → "strictly distinct widths" precondition fails
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 4  # width 2
        for r, c in [(4, 6), (4, 7)]: g[r][c] = 6  # width 2 (tie)
        for r, c in [(7, 1), (7, 2), (7, 3)]: g[r][c] = 7  # width 3
        return g
    return g
