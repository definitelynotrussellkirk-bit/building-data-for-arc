"""Generator for arc_puzzle_bank_sixth21:M37 — slide every blob to bottom border.

Rule: each blob is shifted vertically so its bbox bottom row lands at
grid bottom row (h-1). Horizontal position unchanged.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: blobs_already_at_bottom, single_blob, blobs_share_cols.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "11fc1931b5ef"
VERSION = "1.1.1"
TASK_ID = "11fc1931b5ef"
SUMMARY = "2-3 distinct-color blobs in upper rows of grid (bottom row stays empty)."

INVARIANTS = [
    "background is 0",
    "all blobs' bbox bottom rows are < h-1 (so the slide moves them)",
    "blobs are 4-disjoint horizontally so no overlap after sliding",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("blobs_already_at_bottom", "single_blob", "blobs_share_cols")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "above_bottom_row",
                       "valid": "above_bottom_row"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid with non-zero blobs; dimensions in valid range."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if h < 8 or h > 14:
        errors.append(f"grid_h={h} out of valid range 8..14")
    if w < 9 or w > 14:
        errors.append(f"grid_w={w} out of valid range 9..14")
    if all(grid[r][c] == 0 for r in range(h) for c in range(w)):
        errors.append("grid is all-zero — no blobs placed")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        n = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        n = 3
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        n = None
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    for r in range(max(0, h - 3), h):
        for c in range(w):
            used.add((r, c))
    if n is None:
        n = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    cols_used: list[range] = []
    for color in palette:
        for _ in range(40):
            cells = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=20)
            if cells is None:
                continue
            cs = [c for _, c in cells]
            cmin, cmax = min(cs), max(cs)
            if any(set(range(cmin, cmax + 1)) & set(cu) for cu in cols_used):
                continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            cols_used.append(range(cmin, cmax + 1))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "blobs_already_at_bottom":
        # blobs already touch the bottom row → sliding is identity, rule effect invisible
        for (r, c) in [(h - 1, 1), (h - 1, 2), (h - 2, 1)]: g[r][c] = 4
        for (r, c) in [(h - 1, 6), (h - 2, 6), (h - 2, 7)]: g[r][c] = 6
        return g
    if name == "single_blob":
        # one blob → sliding works but no comparison across blobs
        for (r, c) in [(2, 5), (2, 6), (3, 5), (3, 6)]: g[r][c] = 4
        return g
    if name == "blobs_share_cols":
        # two blobs share a column → sliding both to bottom would collide; INVARIANT violated
        for (r, c) in [(2, 4), (2, 5), (3, 4)]: g[r][c] = 4
        for (r, c) in [(5, 4), (5, 5), (6, 5)]: g[r][c] = 6   # same col 4-5
        return g
    return g
