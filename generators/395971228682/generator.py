"""Generator for v1_e_m_h_keys:E4.

Rule: each non-zero cell at (r, c) mirrors to (r, w-1-c) with the same color.

Combinatorial axes (8): grid_h/w, palette_kind, num_marks,
palette_size, position_bias, n_distinct_colors, half_offset, texture.
Degenerates: already_symmetric, on_center_column, no_marks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "395971228682"
VERSION = "1.2.0"  # wire num_marks axis and make self_check enforce non-identity mirror setup
TASK_ID = "395971228682"
SUMMARY = "Sparse non-zero cells in the left half; right half is empty."

INVARIANTS = [
    "background is 0",
    "2-4 non-zero cells in the left half (cols 0..w/2-1)",
    "right half is all 0",
]

PALETTE_KINDS = ("default", "sparse", "dense", "rainbow")
DEGENERATE_TEXTURES = ("already_symmetric", "on_center_column", "no_marks")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "4..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|sparse|dense|rainbow"},
    "num_marks":      {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "9", "valid": "9"},
    "position_bias":  {"type": "str", "default": "left_half",
                       "valid": "left_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..4",
                          "valid": "1..9"},
    "half_offset":    {"type": "int", "default": "0", "valid": "0"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|sparse|dense|rainbow|already_symmetric|on_center_column|no_marks"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the default mirror-left-to-right teaching setup."""
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
    half = w // 2
    left = [(r, c) for r in range(h) for c in range(half) if grid[r][c] != 0]
    right = [(r, c) for r in range(h) for c in range(half, w) if grid[r][c] != 0]
    if not (2 <= len(left) <= 4):
        errors.append(f"expected 2..4 source marks in left half, found {len(left)}")
    if right:
        errors.append(f"right half/center column should be blank before mirroring; found {right[:4]}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 7, 8)
    else:
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 6, 8)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    half = w // 2
    n = ctx.draw_int("num_marks", 2, 4)
    for _ in range(n):
        for _t in range(40):
            r = rng.randint(0, h - 1); c = rng.randint(0, half - 1)
            if g[r][c] != 0:
                continue
            g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 7
    g = full_grid(h, w, 0)
    if name == "already_symmetric":
        # both halves filled with mirror image — rule output identical to input
        for r, c, v in [(1, 1, 4), (1, 5, 4), (3, 2, 7), (3, 4, 7)]:
            g[r][c] = v
        return g
    if name == "on_center_column":
        # cells on center column (odd width) mirror to themselves
        cc = w // 2
        g[1][cc] = 5
        g[3][cc] = 6
        return g
    if name == "no_marks":
        return g
    return g
