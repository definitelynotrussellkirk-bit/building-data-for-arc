"""Generator for arc_additional_puzzle_bank_volume17:E114.

Rule: three green rectangle corners imply a yellow missing fourth corner.

Combinatorial axes (8): grid_h/w, palette_kind, missing_corner,
palette_size, position_bias, n_distinct_colors, rect_size, texture.
Degenerates: only_2_corners, all_4_corners, no_corners.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1ac6603a9cc3"
VERSION = "1.1.1"
TASK_ID = "1ac6603a9cc3"
SUMMARY = "Three green rectangle corners imply a yellow missing fourth corner."

INVARIANTS = [
    "background is 0",
    "exactly three green cells mark rectangle corners",
    "the missing fourth corner is initially empty",
    "rectangle dimensions vary",
]

PALETTE_KINDS = ("default", "tight_rect", "wide_rect", "tall_rect")
DEGENERATE_TEXTURES = ("only_2_corners", "all_4_corners", "no_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 7..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|tight_rect|wide_rect|tall_rect"},
    "missing_corner": {"type": "str", "default": "rng", "valid": "rng"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "rect_size":      {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|tight_rect|wide_rect|tall_rect|only_2_corners|all_4_corners|no_corners"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 7, 13)
        w = ctx.draw_int("grid_w", 7, 13)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    r0 = rng.randint(0, h - 4)
    r1 = rng.randint(r0 + 2, h - 1)
    c0 = rng.randint(0, w - 4)
    c1 = rng.randint(c0 + 2, w - 1)
    corners = [(r0, c0), (r0, c1), (r1, c0), (r1, c1)]
    missing = rng.choice(corners)
    for r, c in corners:
        if (r, c) != missing:
            g[r][c] = 3
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 3 green (color-3) corner cells present."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    c3 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(c3) != 3:
        errs.append(f"expected exactly 3 green corner cells, found {len(c3)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "only_2_corners":
        # only 2 corners → 4th can't be inferred uniquely
        g[1][1] = 3; g[1][6] = 3
        return g
    if name == "all_4_corners":
        # all 4 corners green — no missing corner
        g[1][1] = 3; g[1][6] = 3
        g[6][1] = 3; g[6][6] = 3
        return g
    if name == "no_corners":
        # empty grid — no rectangle to complete
        return g
    return g
