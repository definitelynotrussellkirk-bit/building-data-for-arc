"""Generator for arc_additional_puzzles_21_set9:M59 — Pick k-th object by sort and crop.

Rule: k = at(0,0); set (0,0)=0; sort objs by (size asc, color asc, r1, c1);
take (k-1)-th; output bbox crop from original grid.

Combinatorial axes (8): grid_h, grid_w, palette_kind, k,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_k, k_out_of_range, tied_sort_keys.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "3731418cffe2"
VERSION = "2.0.1"
TASK_ID = "3731418cffe2"
SUMMARY = (
    "0-bg grid (h~9-11, w~10-12) with: (a) an INDEX "
    "MARKER k at (0, 0) drawn as a single non-bg cell in "
    "some color (k ∈ 1..N where N = number of blobs); "
    "(b) N=3-4 disjoint CONNECTED BLOBS at random "
    "interior positions, each in a distinct non-{0, k} "
    "color and each with a distinct size from a small "
    "size-pool. Blobs are 4-adjacency-isolated. Rule: "
    "(1) CLEAR the index marker at (0, 0). (2) SORT the "
    "remaining blobs lexicographically by (size ASC, "
    "color ASC, top-row r1 ASC, left-col c1 ASC). "
    "(3) SELECT the k-th blob (1-indexed) under that "
    "ordering. (4) CROP the original grid to that "
    "blob's axis-aligned BBOX and output the cropped "
    "subgrid. Net: tiny output that's a bounding-box "
    "extract of one rank-selected blob."
)

# Rivals: 'output k-th object by position' refuted by ≥2 demos where
# size-order and position-order disagree. 'output largest object'
# refuted by ≥1 demo where k=1 selects the smallest. 'output k-th by
# color' refuted by ≥2 demos where size-order and color-order differ.
# 'always output the same blob' refuted by ≥2 demos with different k.
# 'output a fixed bbox' refuted by ≥2 demos with different blob sizes.
# 4 demos with varied k + varied blob sizes/shapes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "k at (0,0) ∈ 1..3",
    "exactly 3 non-touching blobs of distinct sizes and distinct colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_k", "k_out_of_range", "tied_sort_keys")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 10..12", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "k":              {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "4", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "k_at_origin_3_distinct_blobs",
                       "valid": "k_at_origin_3_distinct_blobs"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; index marker k at (0,0) in 1..9; ≥2 other nonzero cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    k = grid[0][0]
    if k == 0:
        pass  # degenerate (no_k) — allowed
    elif not (1 <= k <= 9):
        errors.append(f"index marker at (0,0) out of range: {k}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 7, 10, 8, 11
        size_pool = [1, 2, 3, 4]
        n_blobs = 2
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 13, 17, 13, 17
        size_pool = [1, 2, 3, 4, 5, 6, 7, 8]
        n_blobs_rng = ctx.draw_rng("nblobs")
        n_blobs = n_blobs_rng.randint(4, 6)
    else:
        h_lo, h_hi, w_lo, w_hi = 10, 13, 11, 14
        size_pool = [1, 2, 3, 4, 5, 6]
        n_blobs_rng = ctx.draw_rng("nblobs")
        n_blobs = n_blobs_rng.randint(3, 4)
    k = ctx.draw_int("k", 1, n_blobs)
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    g[0][0] = k

    palette = [c for c in range(2, 10) if c != k]
    rng.shuffle(palette)
    # Pick n_blobs distinct sizes (or with replacement if size_pool too small)
    if len(size_pool) >= n_blobs:
        sizes = sorted(rng.sample(size_pool, n_blobs))
    else:
        sizes = sorted([rng.choice(size_pool) for _ in range(n_blobs)])

    # For each size, draw a random connected shape of that size.
    def random_shape(rng, n):
        cells = [(0, 0)]
        seen = {(0, 0)}
        while len(cells) < n:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nc = (r + dr, c + dc)
            if nc not in seen:
                cells.append(nc); seen.add(nc)
        # normalize
        mr = min(rr for rr, _ in cells); mc = min(cc for _, cc in cells)
        return [(rr - mr, cc - mc) for rr, cc in cells]

    shapes = [random_shape(rng, s) for s in sizes]

    # Place each shape with 4-adj clearance and no overlap with marker
    # (0,0) or other shapes. Random positions.
    def try_place(g, shape, color, max_tries=80):
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        for _ in range(max_tries):
            r0 = rng.randint(1, h - sh)
            c0 = rng.randint(1, w - sw)
            ok = True
            for dr, dc in shape:
                r, c = r0 + dr, c0 + dc
                if g[r][c] != 0:
                    ok = False; break
                for ar, ac in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + ar, c + ac
                    if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                        ok = False; break
                if not ok: break
            if ok:
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                return True
        return False

    for shape, color in zip(shapes, palette[:n_blobs]):
        try_place(g, shape, color)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_k":
        # (0,0) is 0 → no k value, rule has no rank index
        paint_at(g, 1, 2, [(0, 0), (0, 1)], 4)
        paint_at(g, 4, 1, [(0, 0), (0, 1), (1, 0)], 6)
        paint_at(g, 6, w - 4, [(0, 0), (0, 1), (1, 0), (1, 1)], 3)
        return g
    if name == "k_out_of_range":
        # k = 5 but only 3 blobs → rank index out of range
        g[0][0] = 5
        paint_at(g, 1, 2, [(0, 0), (0, 1)], 4)
        paint_at(g, 4, 1, [(0, 0), (0, 1), (1, 0)], 6)
        paint_at(g, 6, w - 4, [(0, 0), (0, 1), (1, 0), (1, 1)], 3)
        return g
    if name == "tied_sort_keys":
        # 3 blobs all same (size, color) → sort key fully tied → ambiguous selection
        g[0][0] = 2
        paint_at(g, 1, 2, [(0, 0), (0, 1)], 4)
        paint_at(g, 4, 1, [(0, 0), (0, 1)], 4)   # same size, same color
        paint_at(g, 6, w - 4, [(0, 0), (0, 1)], 4)
        return g
    return g
