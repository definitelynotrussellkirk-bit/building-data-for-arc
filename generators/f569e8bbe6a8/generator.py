"""Generator for arc_puzzle_bank_eleventh21:M74 — mask one panel with another.

Rule: two equal-width panels separated by a vertical 9-col. Left panel
is a binary mask (1s and 0s). Right panel has colored content. Output:
right panel cells where mask is 1 keep their value, others are 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, panel_w,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, mask_all_zero, mask_all_one.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f569e8bbe6a8"
VERSION = "2.1.0"  # bigger panels + varied mask color (canonical used 2, rule ignores color) + mask-mix guard
TASK_ID = "f569e8bbe6a8"
SUMMARY = (
    "Two EQUAL-WIDTH panels separated by a full vertical color-9 column. The LEFT "
    "panel is a STENCIL (cells of one non-0 color marking which positions to keep; "
    "the rule treats it as binary). The RIGHT panel is fully colored content. "
    "Rule: output the right panel's value at each cell where the stencil is non-0, "
    "else 0. Net: the content is viewed through the stencil's holes. Stencil color "
    "varies (rule ignores it); panels up to ~12 wide. (Was: 4-5 wide, mask color 1.)"
)

INVARIANTS = [
    "background is 0; exactly one full vertical 9-col splitting two equal-width panels",
    "left (stencil) panel uses one non-0 color (rule treats it as binary)",
    "right (content) panel cells are all non-zero (and never 9)",
    "stencil has a mix of marked and empty cells (output is neither blank nor full content)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "mask_all_zero", "mask_all_one")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "4-6 easy / 5-9 med / 8-14 hard", "valid": "3..16"},
    "panel_w":        {"type": "int", "default": "4-5 easy / 5-8 med / 8-12 hard", "valid": "3..13"},
    "mask_color":     {"type": "int", "default": "rng non-0 (rule ignores it)", "valid": "1..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "two_panels_with_9div",
                       "valid": "two_panels_with_9div"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
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
        hr, pr = (4, 6), (4, 5)
    elif difficulty == "hard":
        hr, pr = (8, 14), (8, 12)
    else:
        hr, pr = (5, 9), (5, 8)
    rng = ctx.draw_rng("layout")
    for _attempt in range(40):
        h = rng.randint(*hr); pw = rng.randint(*pr)
        w = pw * 2 + 1
        sep = pw
        mask_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])  # cosmetic; rule reads non-0
        g = full_grid(h, w, 0)
        n_marked = 0
        total = h * pw
        for r in range(h):
            g[r][sep] = 9
            for c in range(pw):
                if rng.random() < 0.45:
                    g[r][c] = mask_color; n_marked += 1
            for c in range(sep + 1, w):
                g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
        # mask must be a MIX (not blank, not full) so the output is non-trivial
        if 1 <= n_marked < total:
            return g

    # deterministic fallback
    g = full_grid(5, 9, 0)
    for r in range(5):
        g[r][4] = 9
        for c in range(5, 9):
            g[r][c] = (r + c) % 7 + 1
    g[0][0] = 2; g[1][1] = 2; g[2][2] = 2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable normal-path invariants for the stencil-mask task."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    sep_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(sep_cols) != 1:
        errors.append(f"expected exactly one full 9 divider column, got {sep_cols}")
        return errors
    sep = sep_cols[0]
    if sep * 2 + 1 != w:
        errors.append(f"divider must split two equal-width panels, got sep={sep} width={w}")
        return errors
    left_vals = [grid[r][c] for r in range(h) for c in range(sep)]
    marks = [v for v in left_vals if v != 0]
    mark_colors = sorted(set(marks))
    if len(mark_colors) != 1:
        errors.append(f"stencil should use exactly one nonzero mark color, got {mark_colors}")
    if not (0 < len(marks) < len(left_vals)):
        errors.append("stencil must mix marked and unmarked cells")
    bad_content = sorted({grid[r][c] for r in range(h) for c in range(sep + 1, w)
                          if grid[r][c] in (0, 9) or not (1 <= grid[r][c] <= 8)})
    if bad_content:
        errors.append(f"right content panel must be fully colored with 1..8, got bad values {bad_content}")
    return errors


def _draw_from_degenerate(name, rng):
    h, pw = 5, 4
    w = pw * 2 + 1
    g = full_grid(h, w, 0)
    sep = pw
    if name == "no_divider":
        # no 9-col → no panel split, mask vs content distinction undefined
        for r in range(h):
            for c in range(pw): g[r][c] = 1 if (r + c) % 2 == 0 else 0
            for c in range(sep + 1, w): g[r][c] = (r + c) % 7 + 2
        return g
    for r in range(h): g[r][sep] = 9
    if name == "mask_all_zero":
        # mask is entirely 0 → output is entirely bg (rule erases everything)
        for r in range(h):
            for c in range(sep + 1, w): g[r][c] = 4
        return g
    if name == "mask_all_one":
        # mask is entirely 1 → output equals right panel (rule keeps everything)
        for r in range(h):
            for c in range(pw): g[r][c] = 1
            for c in range(sep + 1, w): g[r][c] = 4 + (r + c) % 5
        return g
    return g
