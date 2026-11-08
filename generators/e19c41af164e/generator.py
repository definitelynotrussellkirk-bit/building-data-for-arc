"""Generator for arc_puzzle_bank_21_set16_s:S16_H4 — fill between the two cells in each row.

Rule (verified against canonical): for every ROW that has EXACTLY two non-zero
cells, fill the cells between them (inclusive) with color 8. Rows with a different
count are left unchanged.

This generator places K rows, each with exactly two markers (distinct columns,
a gap between them), in varied colors; the rule connects each pair with an
8-colored horizontal bar.

Combinatorial axes: grid size, active-row count, marker columns, colors.
Degenerates: no_pairs, three_in_row, adjacent_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e19c41af164e"
VERSION = "2.1.0"  # WRONG-TASK rewrite. Docstring claimed 'gallery pack / vertical pack' but the rule fills between the two cells in each 2-cell row with color 8. Old gen made scattered motifs -> only coincidental 2-cell rows got filled (incoherent). Now each active row has exactly two markers with a gap.
TASK_ID = "e19c41af164e"
SUMMARY = (
    "0-bg grid with K rows each holding EXACTLY two non-zero markers at distinct "
    "columns (>=2 apart, so a gap exists), in varied colors; other rows empty. "
    "Rule: for each row with exactly two non-zero cells, fill the inclusive span "
    "between them with color 8. Net: each marker pair becomes an 8-colored bar."
)

INVARIANTS = [
    "background is 0",
    "each active row has exactly two non-zero cells with >=1 zero between them",
    "non-active rows are entirely zero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "three_in_row", "adjacent_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "6..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": 'default|warm|cool|varied'},
    "n_rows":         {"type": "int", "default": "rng 3..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "two_per_row",
                       "valid": "two_per_row"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": 'default|warm|cool|varied|no_pairs|three_in_row|adjacent_pair'},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check that normal instances are exactly two markers per active row."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    active = []
    for r, row in enumerate(grid):
        cols = [c for c, v in enumerate(row) if v != 0]
        if not cols:
            continue
        active.append(r)
        if len(cols) != 2:
            errors.append(f"row {r} has {len(cols)} nonzero cells, expected exactly 2")
            continue
        if cols[1] - cols[0] < 2:
            errors.append(f"row {r} marker pair has no zero gap: columns {cols}")
        if grid[r][cols[0]] == 8 or grid[r][cols[1]] == 8:
            errors.append(f"row {r} uses output color 8 as an input marker")
    min_rows = 5 if difficulty == "hard" else 2
    if len(active) < min_rows:
        errors.append(f"expected at least {min_rows} active two-marker rows, got {len(active)}")
    if w < 3:
        errors.append("grid width too small to contain a gapped pair")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8); w = ctx.draw_int("grid_w", 9, 10)
        nr = (2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 13, 17)
        nr = (5, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 10, 13)
        nr = (3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_rows = min(rng.randint(*nr), h)
    rows = rng.sample(range(h), n_rows)
    for r in rows:
        # two distinct columns with a gap of >=1 between them
        c1 = rng.randint(0, w - 3)
        c2 = rng.randint(c1 + 2, w - 1)
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])   # non-8 markers
        g[r][c1] = color
        g[r][c2] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # rows with a single marker -> no pair to fill between
        g[2][3] = 4
        g[5][6] = 6
        return g
    if name == "three_in_row":
        # a row with three markers -> not exactly two, rule skips it
        g[2][1] = 4; g[2][4] = 4; g[2][7] = 4
        g[5][2] = 6; g[5][8] = 6   # this row is a valid pair
        return g
    if name == "adjacent_pair":
        # two adjacent markers -> no zero between (fill is just the two cells)
        g[3][4] = 4; g[3][5] = 4
        return g
    return g
