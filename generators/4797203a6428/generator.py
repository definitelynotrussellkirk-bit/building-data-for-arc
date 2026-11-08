"""Generator for arc_additional_puzzles_21_set6:M37.

Rule: top-left cell's color identifies which color to keep; rule keeps
only that color (excluding the top-left cell itself) and crops.

Combinatorial axes (8): grid_h, grid_w, palette_kind, selector,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_selector_in_body, only_selector_in_body, selector_at_corner_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4797203a6428"
VERSION = "1.1.1"
TASK_ID = "4797203a6428"
SUMMARY = "Selector at (0,0); rule keeps only that color (excluding (0,0)) and crops."

INVARIANTS = [
    "top-left cell (0,0) is non-zero (the selector)",
    "selector color appears at >=2 cells other than (0,0)",
    ">=1 distractor color appears in >=3 cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_selector_in_body", "only_selector_in_body", "selector_at_corner_only")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "selector":       {"type": "color", "default": "rng", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "selector_corner_with_distractors",
                       "valid": "selector_corner_with_distractors"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..5"},
    "density":        {"type": "str", "default": "scattered", "valid": "scattered"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 8, 14)
        w = ctx.draw_int("grid_w", 8, 14)
    selector = ctx.draw_color("selector", exclude={0})
    distractors = ctx.draw_distinct_colors("distractors", n=2, exclude={0, selector})
    rng = ctx.draw_rng("placement")

    g = full_grid(h, w, 0)
    g[0][0] = selector

    placed_sel = 0
    for _ in range(15):
        if placed_sel >= 4: break
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if (r, c) == (0, 0) or g[r][c] != 0: continue
        g[r][c] = selector
        placed_sel += 1
    placed_d = 0
    for _ in range(20):
        if placed_d >= 6: break
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0: continue
        g[r][c] = rng.choice(distractors)
        placed_d += 1
    if placed_sel < 2:
        return [[0]]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_selector_in_body":
        # selector at (0,0) but no matching cells in body → bbox is empty after exclusion
        g[0][0] = 4
        g[2][3] = 6; g[5][7] = 8; g[7][2] = 3
        return g
    if name == "only_selector_in_body":
        # body is filled exclusively with the selector color → bbox spans the entire body
        g[0][0] = 4
        for (r, c) in [(2, 3), (3, 5), (5, 1), (5, 7), (7, 4), (8, 8)]:
            g[r][c] = 4
        return g
    if name == "selector_at_corner_only":
        # selector ONLY at (0,0) → after exclusion, no cells of selector exist; bbox undefined
        g[0][0] = 4
        # everything else is distractor
        g[2][3] = 6; g[4][5] = 8; g[6][7] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """(0,0) is non-zero (selector); selector color appears in >=1 other cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    selector = grid[0][0]
    if selector == 0:
        errors.append("top-left cell (0,0) is 0; expected non-zero selector color")
        return errors
    # selector must appear in at least one other cell in the body
    body_matches = [(r, c) for r in range(h) for c in range(w)
                    if (r, c) != (0, 0) and grid[r][c] == selector]
    if not body_matches:
        errors.append(f"selector color {selector} does not appear outside (0,0)")
    return errors
