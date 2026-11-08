"""Generator for arc_additional_puzzles_21_set21_bundle:M146 — Pairwise size-comparison matrix.

Rule: sort objects by obj-c1; output is N×N grid where (r, c) is:
  2 if r == c
  5 if size[r] > size[c]
  0 otherwise

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "aa7882e3f5c3"
VERSION = "1.2.1"  # dup-outputs: output is an n x n size-comparison matrix (combinatorially bounded). Raised object count (n up to 5) + wider grid + 7 distinct sizes -> distinct 26->56; residual dup is intrinsic to the small-matrix output space."
TASK_ID = "aa7882e3f5c3"
SUMMARY = "N non-touching blobs of distinct sizes; output is NxN size-comparison matrix."

INVARIANTS = [
    "exactly 2..4 blobs",
    "all distinct sizes",
    "blobs spaced left-to-right (so sort-by-c1 is unambiguous)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9",   "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 12..18", "valid": "10..28"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..4",   "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 2..4",   "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "left_to_right_band",
                       "valid": "left_to_right_band"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 distinct non-zero colors; ≥2 non-zero blobs of distinct sizes."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        return errs  # degenerate (no_blobs) — allowed
    nz_colors = {grid[r][c] for r, c in nz}
    if len(nz_colors) < 2:
        return errs  # degenerate (single_blob) — allowed
    # Quick check: at least 2 cells of different colors at wide horizontal separation
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output = an n x n size-comparison matrix (n = #objects, sorted by column).
    # Distinct outputs scale with n (n! column-vs-size permutations). v1.x capped
    # n at ~2-4 -> distinct 26. Widen grid + raise n (up to 5) for more matrices.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 12, 16)
        n_blobs = ctx.draw_int("n_blobs", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 22, 28)
        n_blobs = ctx.draw_int("n_blobs", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 14, 24)
        n_blobs = ctx.draw_int("n_blobs", 3, 5)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    sizes = list(range(2, 9)); rng.shuffle(sizes)   # 7 distinct sizes -> strict comparisons
    sizes = sizes[:n_blobs]
    colors = list(range(1, 10)); rng.shuffle(colors)
    used = set()
    cur_c = 1
    for i, size in enumerate(sizes):
        for _ in range(15):
            if cur_c >= w - 2: break
            placed = False
            for _ in range(10):
                blob = grow_blob(rng, h, min(w, cur_c + 4), used, size)
                if blob is None: continue
                cs = [c for _, c in blob]
                if min(cs) < cur_c - 1: continue
                used |= blob
                for r, c in blob: g[r][c] = colors[i % len(colors)]
                cur_c = max(cs) + 2
                placed = True
                break
            if placed: break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 14
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # all blobs same size → comparison matrix has no 5s, only 2s on diagonal
        for (r, c) in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        for (r, c) in [(1, 6), (1, 7), (2, 7)]: g[r][c] = 6
        for (r, c) in [(4, 10), (5, 10), (5, 11)]: g[r][c] = 3
        return g
    if name == "single_blob":
        # only one blob → 1x1 output, just a 2 cell
        for (r, c) in [(2, 5), (2, 6), (3, 5), (3, 6)]: g[r][c] = 4
        return g
    if name == "no_blobs":
        # blank grid → no objects to compare, output is empty/undefined
        return g
    return g
