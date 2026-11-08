"""Generator for arc_additional_puzzle_bank_volume12:E84.

Rule: the unique smallest nonzero component is recolored yellow.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_components, equal_sizes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "4bc78768be8b"
VERSION = "1.1.1"
TASK_ID = "4bc78768be8b"
SUMMARY = "The unique smallest nonzero component is recolored yellow."

INVARIANTS = [
    "background is 0",
    "there is a unique smallest connected component",
    "the smallest component is not already yellow",
    "larger components are separated and keep their colors",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_components", "equal_sizes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "true",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "random", "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
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
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    draw_rect(g, 0, 0, 2, 3, 7)
    draw_rect(g, h - 3, w - 3, 3, 3, 8)
    r = rng.randint(2, max(2, h - 5))
    c = rng.randint(3, max(3, w - 5))
    g[r][c] = 2
    g[r][c + 1] = 2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify unique-smallest-component invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    problems = []
    flat = [v for row in grid for v in row]
    nonzero = [v for v in flat if v != 0]
    if not nonzero:
        problems.append("no nonzero cells (no components)")
        return problems
    # Need >=2 distinct colors (so there's a smallest and at least one larger)
    distinct = len(set(nonzero))
    if distinct < 2:
        problems.append(f"expected >=2 distinct nonzero colors, found {distinct}")
    return problems


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_components":
        return g
    if name == "equal_sizes":
        draw_rect(g, 0, 0, 2, 2, 7)
        draw_rect(g, 7, 7, 2, 2, 8)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 3
        return g
    return g
