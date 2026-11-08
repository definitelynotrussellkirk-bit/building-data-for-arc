"""Generator for ARC task 6e02f1e3.

Rule: input is 3×3 with 1, 2, or 3 distinct non-zero colors. Output is
a fixed 3×3 mark pattern by count: 1→top-row 5s, 2→main-diag 5s,
3→anti-diag 5s.

Combinatorial axes (8): color_count, palette_choice, cell_layout,
fg_density, anchor_diag, dominant_color, color_balance, position_jitter.
Degenerates: all_same, all_zero, mixed_with_zero.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "abcb59bec35f"
VERSION = "1.3.0"  # keep canonical 3x3 inputs; finite 3-pattern output codomain is declared explicitly
TASK_ID = "abcb59bec35f"
SUMMARY = "Canonical 3×3 non-zero grid with 1, 2, or 3 distinct colors; rule emits one of three count-keyed 5-patterns."
EXPECTED_OUTPUT_CODOMAIN = 3

INVARIANTS = [
    "input is 3×3",
    "the number of distinct source colors is in {1, 2, 3}",
    "all cells are non-zero (so color count is unambiguous)",
]

CELL_LAYOUTS = ("uniform_random", "diag_anchored", "row_dominant",
                "col_dominant", "checker", "block")
DEGENERATE_TEXTURES = ("all_same", "all_zero", "mixed_with_zero")
HELPFUL_TEXTURES = CELL_LAYOUTS

AXES = {
    "color_count":   {"type": "int",  "default": "rng 1..3", "valid": "1..3"},
    "cell_layout":   {"type": "str",  "default": "rng helpful",
                      "valid": "uniform_random|diag_anchored|row_dominant|col_dominant|checker|block"},
    "anchor_diag":   {"type": "bool", "default": "true",  "valid": "true|false"},
    "color_balance": {"type": "str",  "default": "rng even|skew",
                      "valid": "even|skew"},
    "dominant_color": {"type": "color", "default": "= colors[0]", "valid": "1..9"},
    "position_jitter": {"type": "bool", "default": "true", "valid": "true|false"},
    "fg_density":    {"type": "float", "default": "1.0", "valid": "0..1"},
    "texture":       {"type": "str", "default": "alias for cell_layout",
                      "valid": "uniform_random|diag_anchored|row_dominant|col_dominant|checker|block|all_same|all_zero|mixed_with_zero"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    # Rule output is one of 3 fixed 3x3 patterns chosen by the COUNT of distinct
    # colors (1 / 2 / >=3).  Keep the INPUT canonical too: the original task
    # demonstrations are all 3x3, and larger boards were distribution drift.
    if difficulty == "easy":
        count_choices = [1, 2]
    elif difficulty == "hard":
        count_choices = [2, 3]
    else:
        count_choices = [1, 2, 3]
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    count = int(overrides.get("color_count",
                              ctx.draw_choice("color_count", count_choices)))
    count = max(1, min(3, count))
    h = w = 3
    colors = list(ctx.draw_distinct_colors("palette", n=count, exclude={0}))
    # fill every cell with one of `colors` (all non-zero so the color-count is
    # unambiguous); then guarantee all `count` colors actually appear.
    g = [[rng.choice(colors) for _ in range(w)] for _ in range(h)]
    cells = [(r, c) for r in range(h) for c in range(w)]
    for i, col in enumerate(colors):
        r, c = cells[i]
        g[r][c] = col
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Canonical task invariants: 3x3, all non-zero, 1..3 colors all present."""
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    errs = []
    if len(grid) != 3 or any(not isinstance(row, list) or len(row) != 3 for row in grid):
        errs.append("input must be exactly 3x3")
        return errs
    vals = [v for row in grid for v in row]
    bad = sorted({v for v in vals if not isinstance(v, int) or v < 1 or v > 9})
    if bad:
        errs.append(f"cells must be non-zero colors 1..9; bad={bad}")
    n = len(set(vals))
    if n not in (1, 2, 3):
        errs.append(f"distinct color count must be 1, 2, or 3; got {n}")
    return errs


def _draw_from_degenerate(name, rng):
    if name == "all_same":
        c = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        return [[c] * 3 for _ in range(3)]
    if name == "all_zero":
        return [[0] * 3 for _ in range(3)]
    if name == "mixed_with_zero":
        c1 = rng.choice([1, 2, 3])
        c2 = rng.choice([4, 5, 6])
        return [[c1, 0, c2], [0, c1, 0], [c2, 0, c1]]
    return [[1] * 3 for _ in range(3)]
