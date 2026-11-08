"""Generator for arc_additional_puzzles_21_set11_bundle:M74 — Pairwise size-equality matrix.

Rule: sort objects by (r1, c1). Output n×n grid: cell (r, c) is 8 if
size(obj_r) == size(obj_c), else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blobs, single_blob, all_distinct_sizes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "8de40926676f"
VERSION = "2.1.0"
TASK_ID = "8de40926676f"
SUMMARY = "n (3-5) non-touching blobs in distinct colors with one repeated-size pair and at least one differently-sized blob; output is the nxn matrix with 8 where two objects share size, else 0. Object count, sizes and positions vary."

INVARIANTS = [
    "between 3 and 5 non-touching blobs",
    "at least one pair of equal-size blobs (so off-diagonal 8s appear)",
    "not all blobs have the same size (so the matrix is not solid 8)",
    "blobs use distinct colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "single_blob", "all_distinct_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..15", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 10..16", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "non_touching_blobs",
                       "valid": "non_touching_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 3-5 isolated, distinct-color blobs with an equal-size pair."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_blobs", "single_blob", "all_distinct_sizes"):
        return errs
    comps = _components_nonzero(grid)
    if not (3 <= len(comps) <= 5):
        errs.append(f"expected 3-5 blobs, found {len(comps)}")
    if len({comp["color"] for comp in comps}) != len(comps):
        errs.append("blob colors should be distinct")
    sizes = [len(comp["cells"]) for comp in comps]
    if len(sizes) == len(set(sizes)):
        errs.append("no equal-size blob pair, so off-diagonal matrix branch is absent")
    if sizes and len(set(sizes)) == 1:
        errs.append("all blobs have the same size, so the output matrix is solid 8")
    owner = {}
    for i, comp in enumerate(comps):
        for cell in comp["cells"]:
            owner[cell] = i
    for (r, c), i in owner.items():
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            j = owner.get((r + dr, c + dc))
            if j is not None and j != i:
                errs.append("blobs should not 4-touch")
                return errs
    return errs


def _components_nonzero(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append({"color": color, "cells": cells})
    return comps


def _sizes_with_equal_pair(rng, n):
    """Return n sizes in 1..5 with a repeated pair and a different size."""
    base = rng.randint(1, 5)
    other = rng.choice([s for s in range(1, 6) if s != base])
    sizes = [base, base, other]
    while len(sizes) < n:
        sizes.append(rng.randint(1, 5))
    rng.shuffle(sizes)
    return sizes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 10, 12)
        n = ctx.draw_int("n_blobs", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n_blobs", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 11, 14)
        n = ctx.draw_int("n_blobs", 3, 5)
    rng = ctx.draw_rng("layout")
    for _attempt in range(30):
        g = full_grid(h, w, 0)
        sizes = _sizes_with_equal_pair(rng, n)
        colors = rng.sample(range(1, 10), n)
        used = set()
        placed = 0
        for i, sz in enumerate(sizes):
            blob = grow_blob(rng, h, w, used, sz, max_attempts=100)
            if blob is None or len(blob) != sz:
                break
            used |= blob
            for r, c in blob:
                g[r][c] = colors[i]
            placed += 1
        if placed == n:
            return g
    # Safe fallback: three isolated objects with two equal areas.
    g = full_grid(h, w, 0)
    for r, c in [(1, 1), (1, 2), (2, 1)]:
        g[r][c] = 4
    for r, c in [(1, w - 3), (1, w - 2), (2, w - 2)]:
        g[r][c] = 6
    for r, c in [(h - 3, w // 2), (h - 2, w // 2)]:
        g[r][c] = 8
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        # blank → 0×0 matrix, no comparisons to make
        return g
    if name == "single_blob":
        # 1 blob → 1×1 matrix is trivially [[8]]
        for r, c in [(2, 2), (3, 2)]: g[r][c] = 4
        return g
    if name == "all_distinct_sizes":
        # all sizes unique → matrix is identity, no off-diagonal 8s
        for r, c in [(1, 1)]: g[r][c] = 4  # size 1
        for r, c in [(4, 1), (4, 2)]: g[r][c] = 6  # size 2
        for r, c in [(7, 1), (7, 2), (7, 3)]: g[r][c] = 7  # size 3
        for r, c in [(1, 6), (1, 7), (2, 6), (2, 7)]: g[r][c] = 8  # size 4
        return g
    return g
