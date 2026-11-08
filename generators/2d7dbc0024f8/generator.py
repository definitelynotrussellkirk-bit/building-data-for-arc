"""Generator for arc_puzzle_bank_fourteenth21:M95 — shift by 8-guide vector.

Rule: two 8-cells define src and dst. Shift every non-{0,8} cell by
(dst - src). Output: empty grid + shifted blob.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: one_8_cell, no_blob, src_equals_dst.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "2d7dbc0024f8"
VERSION = "2.1.0"  # FIX all-zero output: the rule shifts by (row-major-second 8 - first), not (dst - src); when src was the later marker the blob shifted the wrong way out of bounds -> empty output. Bounds check now uses the sorted-order vector.
TASK_ID = "2d7dbc0024f8"
SUMMARY = "Two 8-cells (src+dst) + a colored blob; shifted blob in-bounds."

INVARIANTS = [
    "background is 0",
    "exactly two 8-cells defining a non-zero shift vector",
    "≥1 connected non-{0,8} blob whose shift is in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("one_8_cell", "no_blob", "src_equals_dst")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "src_dst_plus_blob",
                       "valid": "src_dst_plus_blob"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
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
        h = ctx.draw_int("grid_h", 7, 8); w = ctx.draw_int("grid_w", 8, 9)
        bmin, bmax = 2, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 11, 14)
        bmin, bmax = 4, 6
    else:
        h = ctx.draw_int("grid_h", 8, 12); w = ctx.draw_int("grid_w", 9, 13)
        bmin, bmax = 3, 5
    rng = ctx.draw_rng("layout")
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])   # any non-{0,8} colour is preserved
    # retry the whole layout until src/dst define a non-zero vector AND the blob's
    # shift stays in-bounds (a failed attempt previously left bare markers -> empty
    # output, a big source of dup-outputs). src/dst span the whole grid for varied
    # final positions.
    for _attempt in range(120):
        g = full_grid(h, w, 0)
        used: set[tuple[int, int]] = set()
        src = (rng.randint(0, h - 1), rng.randint(0, w - 1))
        dst = (rng.randint(0, h - 1), rng.randint(0, w - 1))
        if src == dst:
            continue
        g[src[0]][src[1]] = 8; g[dst[0]][dst[1]] = 8
        used.add(src); used.add(dst)
        blob = grow_blob(rng, h, w, used, rng.randint(bmin, bmax), max_attempts=80)
        if blob is None:
            continue
        # The rule sorts the two 8-markers row-major and shifts by
        # (second - first) -- NOT by (dst - src). If src is the row-major-later
        # marker the rule's actual shift is the negation of (dst - src), so the
        # bounds check must use the SAME sorted-order vector or the blob lands
        # out of bounds and the output is all-zero.
        first, second = sorted((src, dst))
        dr = second[0] - first[0]; dc = second[1] - first[1]
        if not all(0 <= r + dr < h and 0 <= c + dc < w for r, c in blob):
            continue
        for r, c in blob:
            g[r][c] = color
        return g
    return g  # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None):
    """Exactly two 8-markers defining a non-zero shift, plus a non-{0,8} blob
    whose shift (by the row-major (second-first) vector) stays in-bounds, so the
    rule paints a non-empty output. Returns violation list."""
    h, w = len(grid), len(grid[0])
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if len(eights) != 2:
        return [f"need exactly two 8-markers, got {len(eights)}"]
    first, second = sorted(eights)
    dr, dc = second[0] - first[0], second[1] - first[1]
    if dr == 0 and dc == 0:
        return ["zero shift vector"]
    blob = [(r, c) for r in range(h) for c in range(w)
            if grid[r][c] not in (0, 8)]
    if not blob:
        return ["no blob to shift -> empty output"]
    if not all(0 <= r + dr < h and 0 <= c + dc < w for r, c in blob):
        return ["shifted blob leaves the grid -> all-zero output"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "one_8_cell":
        # only one 8-cell → can't define a shift vector
        g[1][1] = 8
        g[3][3] = 4; g[3][4] = 4
        return g
    if name == "no_blob":
        # 8-pair without blob → nothing to shift
        g[1][1] = 8
        g[5][5] = 8
        return g
    if name == "src_equals_dst":
        # both 8-cells coincide → shift vector is (0, 0), rule is identity
        g[3][3] = 8
        g[5][5] = 4; g[5][6] = 4
        return g
    return g
