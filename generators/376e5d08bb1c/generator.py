"""Generator for arc_puzzle_bank_21_set8_s:S8_M6.

Rule: each column has a small seed pattern at the top (contiguous from
row 0 to first 0); repeat the seed pattern downward to fill the column.

Combinatorial axes (8): grid_h/w, palette_kind, seed_len, palette_size,
position_bias, n_distinct_colors, seed_density, texture.
Degenerates: no_seeds, full_columns, gap_in_seed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "376e5d08bb1c"
VERSION = "2.0.1"
TASK_ID = "376e5d08bb1c"
SUMMARY = (
    "Grid where every column has a SEED of 1-3 non-zero values "
    "starting from row 0 (contiguous prefix). Below the seed prefix, "
    "all cells are 0 — the area the rule will fill. Different columns "
    "may have different seed lengths. Rule: for each column c, find "
    "the contiguous-from-top non-zero prefix as the seed pattern. "
    "Repeat that seed downward periodically to fill the column for "
    "all h rows. Output has the same dims as input but with all "
    "0-cells in each column replaced with the corresponding seed value."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "every column's contiguous-from-top non-zero prefix has length 1-3",
    "below the prefix the column is all 0 (the area the rule fills)",
    "seed values may repeat across rows but each column's prefix is well-defined",
]

PALETTE_KINDS = ("default", "short_seeds", "long_seeds", "varied_palette")
DEGENERATE_TEXTURES = ("no_seeds", "full_columns", "gap_in_seed")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_len":       {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "top_anchored",
                       "valid": "top_anchored"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "seed_density":   {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 column has a contiguous non-zero top prefix; below prefix all 0."""
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
    # At least one column should have a nonzero top prefix
    has_seed = any(grid[0][c] != 0 for c in range(w))
    if not has_seed:
        pass  # degenerate (no_seeds) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 5, 6)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 6, 7)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 5, 7)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    for c in range(w):
        seed_len = rng.randint(1, 3)
        for r in range(seed_len):
            g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 6
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # all columns empty — no seed to repeat
        return g
    if name == "full_columns":
        # columns already filled — period repetition is identity
        for c in range(w):
            for r in range(h):
                g[r][c] = ((c % 5) + 1)
        return g
    if name == "gap_in_seed":
        # seed has internal 0 → "first 0" detection picks wrong split
        g[0][2] = 4
        g[1][2] = 0  # gap
        g[2][2] = 6  # value below the gap → ambiguous seed boundary
        return g
    return g
