"""Generator for arc_additional_puzzles_21_set8:E50.

Rule: find the full-height 5-column (or full-width 5-row); mirror each
non-{0, 5} cell across that divider.

Combinatorial axes (8): grid_h, grid_w, palette_kind, num_marks,
divider_col, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_divider, divider_partial, no_marks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "58cd4c4a5bd4"
VERSION = "2.1.0"
TASK_ID = "58cd4c4a5bd4"
SUMMARY = (
    "Grid h×9 (h~4-6, w=9 fixed) with "
    "0-bg and: (a) ONE FULL-HEIGHT "
    "COLOR-5 (gray) DIVIDER COLUMN "
    "at col 4 (middle); (b) 2-3 "
    "ISOLATED non-{0, 5} CELLS in "
    "the LEFT SIDE (cols 0..3) at "
    "random rows in random colors "
    "from {1, 2, 3, 4, 6, 7, 8, 9}. "
    "Right side (cols 5..8) is "
    "all 0. Rule (MIRROR LEFT "
    "ACROSS DIVIDER): for EACH "
    "non-{0, 5} CELL at (r, c) on "
    "the LEFT side (c < 4), "
    "COMPUTE its MIRROR position "
    "(r, 8 - c) (or equivalently "
    "(r, w - 1 - c)) on the RIGHT "
    "side. PAINT the mirror cell "
    "with the SAME COLOR. The "
    "divider stays. Left cells "
    "stay. Net: left-side cells "
    "are mirrored across the gray "
    "divider to the right side."
)

INVARIANTS = [
    "exactly 1 full-height col of 5s",
    "left side has 2-3 isolated non-{0,5} cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("no_divider", "divider_partial", "no_marks")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "9", "valid": "9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "num_marks":      {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "divider_col":    {"type": "int", "default": "4", "valid": "4"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8"},
    "position_bias":  {"type": "str", "default": "left_half",
                       "valid": "left_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3",
                          "valid": "1..8"},
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
        h = ctx.draw_int("grid_h", 4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 5, 6)
    else:
        h = ctx.draw_int("grid_h", 4, 6)
    w = 9
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    gc = 4
    for r in range(h):
        g[r][gc] = 5
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], rng.randint(2, 3))
    for color in palette:
        for _ in range(20):
            r = rng.randint(0, h - 1); c = rng.randint(0, gc - 1)
            if g[r][c] == 0:
                g[r][c] = color
                break
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    h, w = len(grid), len(grid[0])
    if w != 9:
        errors.append(f"expected fixed width 9, got {w}")
    div_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if div_cols != [4]:
        errors.append(f"expected exactly one full divider column at col 4, got {div_cols}")
    marks = [(r, c, grid[r][c]) for r in range(h) for c in range(4) if grid[r][c] not in (0, 5)]
    if not (2 <= len(marks) <= 3):
        errors.append(f"expected 2-3 left-side marks, got {len(marks)}")
    colors = [v for _, _, v in marks]
    if len(colors) != len(set(colors)):
        errors.append("left-side marks should use distinct colors")
    if any(grid[r][c] != 0 for r in range(h) for c in range(5, w)):
        errors.append("right side must start empty so the mirror action is visible")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 5, 9
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # marks but no 5-line — rule has no axis to mirror over
        g[1][2] = 4
        g[2][1] = 7
        g[3][3] = 6
        return g
    if name == "divider_partial":
        # 5-column has gaps — not a full-height divider
        for r in [0, 2, 4]:
            g[r][4] = 5
        g[1][2] = 4
        g[3][1] = 7
        return g
    if name == "no_marks":
        # divider but no marks to mirror — rule has nothing to do
        for r in range(h):
            g[r][4] = 5
        return g
    return g
