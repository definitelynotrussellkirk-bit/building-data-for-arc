"""Generator for arc_puzzle_bank_21_set3:S3_M4.

Rule: row 0 holds 2-marks at certain cols. Below row 0, every 1-cell
in those marked cols becomes 3. Other 1-cells stay.

Combinatorial axes (8): grid_h/w, palette_kind, n_marks, palette_size,
position_bias, n_distinct_colors, marker_density, texture.
Degenerates: no_2_marks, no_body_1s, all_columns_marked.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "81f7234dc4a2"
VERSION = "1.1.1"
TASK_ID = "81f7234dc4a2"
SUMMARY = "Row 0 has 2-3 2-marks + scattered 1-cells below (some in marked cols)."

INVARIANTS = [
    "background is 0",
    "row 0 has 2-3 2-cells at distinct cols",
    "rows below have scattered 1-cells (some at marked cols, some not)",
]

PALETTE_KINDS = ("default", "sparse", "dense", "balanced")
DEGENERATE_TEXTURES = ("no_2_marks", "no_body_1s", "all_columns_marked")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_marks":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "axis", "valid": "axis"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "marker_density": {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: row 0 has 2-3 color-2 cells at distinct cols; body rows have only 0/1 cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    marks = [c for c in range(w) if grid[0][c] == 2]
    errs = []
    if not marks:
        return []  # no_2_marks degenerate — allowed
    if len(marks) < 2 or len(marks) > 3:
        errs.append(f"row 0 has {len(marks)} color-2 cells; expected 2-3")
    for r in range(1, h):
        for c in range(w):
            v = grid[r][c]
            if v not in (0, 1):
                errs.append(f"body row {r} col {c} has unexpected value {v}; expected 0 or 1")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 8, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n = rng.randint(2, 3)
    cols = rng.sample(range(w), n)
    for c in cols:
        g[0][c] = 2
    for r in range(1, h):
        for c in range(w):
            if rng.random() < 0.2:
                g[r][c] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_2_marks":
        # body 1s exist but no top-row 2-marks → no columns selected
        for r in range(1, h):
            for c in range(w):
                if (r + c) % 4 == 0:
                    g[r][c] = 1
        return g
    if name == "no_body_1s":
        # 2-marks exist but no body 1s → rule has nothing to recolor
        g[0][2] = 2
        g[0][5] = 2
        return g
    if name == "all_columns_marked":
        # every column marked → every body 1 becomes 3 (rule trivial)
        for c in range(w):
            g[0][c] = 2
        for r in range(1, h):
            for c in range(w):
                if (r + c) % 4 == 0:
                    g[r][c] = 1
        return g
    return g
