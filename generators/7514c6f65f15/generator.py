"""Generator for arc_puzzle_bank_fourth21:M23 — recolor tallest blob.

Rule: pick the blob with greatest bbox height; recolor to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, tied_height, single_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "7514c6f65f15"
VERSION = "2.0.1"
TASK_ID = "7514c6f65f15"
SUMMARY = (
    "0-bg grid (h×w, ~8-11 by ~9-12) containing exactly 3 connected "
    "blobs in 3 distinct non-zero colors (≠ 8). Blobs have 3, 4, "
    "and 5 cells. Their BBOX HEIGHTS are strictly distinct (so the "
    "tallest is unambiguous). Blobs don't 4-touch (≥1-cell buffer). "
    "Rule: sort all components by bbox-height descending (then by "
    "size desc, then top-left row asc, then col asc). Pick the "
    "top one. Recolor all its cells from its original color to 8. "
    "Other blobs preserved. Output: same grid with the tallest "
    "blob's cells now color 8."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 3 connected blobs in distinct non-zero colors (≠ 8)",
    "blobs have strictly distinct bbox heights (unambiguous winner)",
    "blobs separated by ≥1-cell buffer (4-conn isolated)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "tied_height", "single_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3", "valid": "3..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "distinct_height_blobs",
                       "valid": "distinct_height_blobs"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥2 distinct non-{0,8} colors (blobs), no color 8 in input."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    non8_colors = colors - {8}
    if len(non8_colors) < 2:
        errs.append(f"expected ≥2 distinct non-{{0,8}} blob colors, got {len(non8_colors)}")
    if 8 in colors:
        errs.append("color-8 appears in input (should only be in output)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)
    sizes = [3, 4, 5]
    used: set[tuple[int, int]] = set()
    seen_heights: set[int] = set()
    for size, color in zip(sizes, palette):
        for _ in range(60):
            cells = grow_blob(rng, h, w, used, size, max_attempts=20)
            if cells is None:
                continue
            rs = [r for r, _ in cells]
            bb_h = max(rs) - min(rs) + 1
            if bb_h in seen_heights:
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            seen_heights.add(bb_h)
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # blank → no blobs to find tallest
        return g
    if name == "tied_height":
        # 2 blobs share max bbox height → ambiguous winner
        g[1][1] = 4; g[2][1] = 4; g[3][1] = 4  # height 3
        g[1][7] = 6; g[2][7] = 6; g[3][7] = 6  # height 3 (same)
        return g
    if name == "single_blob":
        # only one blob → trivially tallest, no contrast
        g[1][3] = 4; g[2][3] = 4; g[3][3] = 4
        return g
    return g
