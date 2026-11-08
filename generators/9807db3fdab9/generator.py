"""Generator for v1_e_m_h_keys:M6 — recolor each object by size-rank ASC: 1, 2, 3.

Rule: sort objects by cell count ascending; recolor the smallest with
1, the next with 2, the next with 3.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects, fewer_than_three, all_same_size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "9807db3fdab9"
VERSION = "1.1.1"
TASK_ID = "9807db3fdab9"
SUMMARY = "3 objects with distinct sizes (1, 2, 3, or 4 cells)."

INVARIANTS = [
    "background is 0",
    "exactly 3 connected non-bg objects",
    "each object has a distinct cell count",
    "each object a distinct color (from {4..9} so output 1/2/3 don't collide)",
    "objects don't touch each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "fewer_than_three", "all_same_size")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "three_distinct_size_objects",
                       "valid": "three_distinct_size_objects"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_objects|fewer_than_three|all_same_size"},
}

_SHAPES_BY_SIZE = {
    1: [[(0, 0)]],
    2: [[(0, 0), (0, 1)], [(0, 0), (1, 0)]],
    3: [[(0, 0), (0, 1), (0, 2)], [(0, 0), (0, 1), (1, 0)], [(0, 0), (1, 0), (2, 0)]],
    4: [[(0, 0), (0, 1), (1, 0), (1, 1)], [(0, 0), (0, 1), (0, 2), (1, 1)]],
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 3 non-bg connected components with distinct sizes."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    seen = set()
    sizes = []
    for r0 in range(h):
        for c0 in range(w):
            if (r0, c0) in seen or grid[r0][c0] == 0:
                continue
            stack = [(r0, c0)]; seen.add((r0, c0)); sz = 0
            while stack:
                r, c = stack.pop(); sz += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 0:
                        seen.add((nr, nc)); stack.append((nr, nc))
            sizes.append(sz)
    errs = []
    if len(sizes) != 3:
        errs.append(f"expected exactly 3 non-bg components; found {len(sizes)}")
    elif len(set(sizes)) != 3:
        errs.append(f"component sizes not all distinct: {sorted(sizes)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    sizes = rng.sample(list(_SHAPES_BY_SIZE.keys()), 3)
    palette = list(random_palette(rng, 3, exclude={1, 2, 3}))
    placed: list[tuple[int, int, int, int]] = []
    for size, color in zip(sizes, palette):
        shape = rng.choice(_SHAPES_BY_SIZE[size])
        sh = max(c[0] for c in shape) + 1
        sw = max(c[1] for c in shape) + 1
        for _ in range(80):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            bb_pad = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
            if any(bbox_overlaps(bb_pad, p) for p in placed): continue
            paint_at(g, r0, c0, shape, color)
            placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_objects":
        # Empty grid — rule has no objects to size-rank.
        return g
    if name == "fewer_than_three":
        # Only two objects — rule's three-rank mapping (1, 2, 3) has
        # one slot unused; sizes can't fully cover the 3-rank palette.
        for r, c in [(2, 2)]: g[r][c] = 4
        for r, c in [(5, 5), (5, 6)]: g[r][c] = 6
        return g
    if name == "all_same_size":
        # Three same-size objects — rule's size-rank ordering is
        # ambiguous; tiebreak path is not defined.
        for r, c in [(2, 2), (2, 3)]: g[r][c] = 4
        for r, c in [(5, 5), (5, 6)]: g[r][c] = 6
        for r, c in [(7, 1), (7, 2)]: g[r][c] = 7
        return g
    return g
