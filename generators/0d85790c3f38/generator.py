"""Generator for arc_puzzle_bank_21_set4_d:easy_d06.

Rule: the right half of the grid is horizontally mirrored onto the left
half (overwriting the left).

Combinatorial axes (8): grid_h, half_w, palette_kind, mark_count,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: already_symmetric, left_half_filled, no_marks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0d85790c3f38"
VERSION = "2.1.1"  # 2.0.0->2.1.0: wider grid/half_w ranges + scale mark count -> more output shapes (already clean)
TASK_ID = "0d85790c3f38"
SUMMARY = (
    "0-bg grid (h ∈ 5-8, w = 2*half_w "
    "with half_w ∈ 4-6 → w ∈ 8-12 "
    "EVEN, by difficulty) with: "
    "MARK_COUNT ∈ 4-7 SOURCE CELLS "
    "placed ONLY in the RIGHT HALF "
    "(cols half_w..2*half_w-1), each "
    "in a random color drawn from "
    "{1..9}. The LEFT HALF (cols "
    "0..half_w-1) starts EMPTY. "
    "Rule (HORIZONTALLY MIRROR THE "
    "RIGHT HALF ONTO THE LEFT HALF, "
    "OVERWRITING ANY LEFT-HALF "
    "CONTENT; THE RIGHT HALF "
    "REMAINS UNCHANGED): For EACH "
    "cell (r, c) with c in 0..half_w"
    "-1: SET g[r][c] = g[r][w-1-c] "
    "(its mirror in the right "
    "half). The right half "
    "preserved. Net: input "
    "becomes left-right symmetric "
    "across the vertical axis at "
    "col half_w; left half is a "
    "mirror copy of right."
)

INVARIANTS = [
    "background is 0",
    "grid width is even",
    "source marks live in the right half",
    "the right half remains unchanged after mirroring",
]

PALETTE_KINDS = ("default", "sparse", "dense", "rainbow")
DEGENERATE_TEXTURES = ("already_symmetric", "left_half_filled", "no_marks")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "3..14"},
    "half_w":         {"type": "int", "default": "rng 4..6", "valid": "2..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "mark_count":     {"type": "int", "default": "rng 4..7", "valid": "1..16"},
    "palette_size":   {"type": "int", "default": "9", "valid": "9"},
    "position_bias":  {"type": "str", "default": "right_half",
                       "valid": "right_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..7",
                          "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        half_w = ctx.draw_int("half_w", 4, 5)
        target_max = 6
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 14)
        half_w = ctx.draw_int("half_w", 6, 10)
        target_max = 16
    else:
        h = ctx.draw_int("grid_h", 5, 12)
        half_w = ctx.draw_int("half_w", 4, 9)
        target_max = 12
    mark_count = ctx.draw_int("mark_count", 4, min(target_max, h * half_w))
    rng = ctx.draw_rng("layout")
    g = full_grid(h, half_w * 2, 0)
    cells = rng.sample([(r, c) for r in range(h) for c in range(half_w, half_w * 2)], mark_count)
    for r, c in cells:
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Width is even AND >=1 non-zero cell in the right half (to mirror)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    if w % 2 != 0:
        errors.append(f"width {w} is odd (halves undefined — rule undefined)")
    else:
        half = w // 2
        right_marks = any(grid[r][c] != 0 for r in range(h) for c in range(half, w))
        if not right_marks:
            errors.append("right half is blank — nothing to mirror to the left")
    return errors


def _draw_from_degenerate(name, rng):
    h, half_w = 6, 5
    w = 2 * half_w
    g = full_grid(h, w, 0)
    if name == "already_symmetric":
        # both halves already mirrored — rule output identical to input
        for r, c, v in [(1, 8, 4), (1, 1, 4), (3, 7, 7), (3, 2, 7)]:
            g[r][c] = v
        return g
    if name == "left_half_filled":
        # left half has its own marks — rule overwrites them silently
        for r, c, v in [(1, 1, 5), (3, 3, 6)]:
            g[r][c] = v
        for r, c, v in [(2, 7, 4), (4, 8, 7)]:
            g[r][c] = v
        return g
    if name == "no_marks":
        return g
    return g
