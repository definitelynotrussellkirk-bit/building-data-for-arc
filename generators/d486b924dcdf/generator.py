"""Generator for 7b:m45 — crop union of key-colored blobs.

Rule: row 0 holds 1-2 key-color cells. Find all blobs of those colors,
crop the union (bbox of all key-color cells in the body).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_keys,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_keys, no_distractor, key_color_missing_in_body.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "d486b924dcdf"
VERSION = "1.2.1"
TASK_ID = "d486b924dcdf"
SUMMARY = "Row 0 has key-color markers; rule crops the bbox of all matching-color blobs in the body, discarding distractors and row 0."

# Rivals: 'crop to single largest blob' refuted by ≥2 demos where
# multiple key-color blobs share the cropped bbox. 'include distractor
# in output' refuted by any demo where distractor falls in bbox but
# stays excluded. 'preserve row 0' refuted by any demo (row 0 cropped
# away). 'crop only first key color' refuted by ≥1 demo with both
# colors visibly bounded.
# 4 demos with varied blob positions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "row 0 has exactly 2 key-color cells (distinct colors) at distinct cols",
    "below row 0: ≥1 blob in each key color + ≥1 distractor blob",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_keys", "no_distractor", "key_color_missing_in_body")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_keys":         {"type": "int", "default": "2", "valid": "2..2"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "row0_keys_plus_blobs",
                       "valid": "row0_keys_plus_blobs"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; row 0 has exactly 2 non-zero key-color cells; body has ≥2 non-zero cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    if h < 2:
        errs.append("grid must have ≥2 rows")
        return errs
    row0_nz = [c for c in range(w) if grid[0][c] != 0]
    if len(row0_nz) != 2:
        errs.append(f"row 0 should have exactly 2 key-color cells; found {len(row0_nz)}")
    else:
        # the two key cells must have distinct colors
        k1, k2 = grid[0][row0_nz[0]], grid[0][row0_nz[1]]
        if k1 == k2:
            errs.append(f"row 0 key cells have same color {k1}; expected distinct")
    body_nz = sum(1 for r in range(1, h) for c in range(w) if grid[r][c] != 0)
    if body_nz < 2:
        errs.append(f"body (rows 1+) has only {body_nz} non-zero cells; expected ≥2")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 10)
        blob_size_lo, blob_size_hi = 2, 3
        n_distractor_lo, n_distractor_hi = 1, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 16)
        blob_size_lo, blob_size_hi = 3, 6
        n_distractor_lo, n_distractor_hi = 2, 4
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 13)
        blob_size_lo, blob_size_hi = 2, 4
        n_distractor_lo, n_distractor_hi = 1, 2
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(9, 5))
    keys = palette[:2]
    distractor_pool = palette[2:]
    cols = rng.sample(range(w), 2)
    for c, color in zip(cols, keys):
        g[0][c] = color
    used = {(0, c) for c in cols}
    # Row 1 reserved (gap between keys and body so rule's row-0 detection
    # doesn't collide with body blobs).
    for c in range(w):
        used.add((1, c))
    # Multiple blobs per key color so the union/bbox is non-trivial.
    for color in keys:
        n_blobs = rng.randint(1, 2)
        for _ in range(n_blobs):
            sz = rng.randint(blob_size_lo, blob_size_hi)
            cells = grow_blob(rng, h, w, used, sz, max_attempts=80)
            if cells:
                for r, c in cells: g[r][c] = color
                used |= cells
    n_dist = rng.randint(n_distractor_lo, n_distractor_hi)
    for i in range(n_dist):
        sz = rng.randint(blob_size_lo, blob_size_hi)
        cells = grow_blob(rng, h, w, used, sz, max_attempts=80)
        if cells:
            col = distractor_pool[i % len(distractor_pool)]
            for r, c in cells: g[r][c] = col
            used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_keys":
        # blobs without row-0 key cells → no key colors selected
        for r, c in [(2, 1), (2, 2)]: g[r][c] = 4
        for r, c in [(4, 5), (4, 6)]: g[r][c] = 6
        for r, c in [(6, 8), (7, 8)]: g[r][c] = 7
        return g
    if name == "no_distractor":
        # keys + matching blobs but no distractor → no contrast for "union" rule
        g[0][2] = 4; g[0][6] = 6
        for r, c in [(2, 1), (2, 2)]: g[r][c] = 4
        for r, c in [(4, 5), (4, 6)]: g[r][c] = 6
        return g
    if name == "key_color_missing_in_body":
        # row-0 key colors don't appear below → empty union
        g[0][2] = 4; g[0][6] = 6
        for r, c in [(4, 5), (4, 6)]: g[r][c] = 7  # only distractor color
        return g
    return g
