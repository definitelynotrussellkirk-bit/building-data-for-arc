"""Generator for arc_puzzle_bank_21_set19_bundle:easy_p02.

Rule: one isolated seed broadcasts its color across its full row and column.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors, color.
Degenerates: no_seed, two_seeds, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "29d9bc0725c4"
VERSION = "1.1.1"
TASK_ID = "29d9bc0725c4"
SUMMARY = "Isolated seed broadcasts its color across its full row and column."

INVARIANTS = [
    "background is 0",
    "exactly one nonzero seed is present",
    "the seed is not constrained to a border or center position",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seed", "two_seeds", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "6..10"},
    "grid_w":         {"type": "int", "default": "rng 6..10", "valid": "6..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "color":          {"type": "color", "default": "rng !{0}", "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one non-zero seed cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_seed", "two_seeds", "full_grid"):
        return []
    errs = []
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(nonzero) != 1:
        errs.append(f"expected exactly 1 non-zero seed, found {len(nonzero)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 6, 10)
    grid = full_grid(h, w, 0)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    r = rng.randrange(h)
    c = rng.randrange(w)
    grid[r][c] = color
    return grid


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 0)
    if name == "no_seed":
        return g
    if name == "two_seeds":
        g[2][3] = 3
        g[5][6] = 4
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(8):
                g[r][c] = 3
        return g
    return g
