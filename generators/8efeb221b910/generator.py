"""Generator for arc_puzzle_bank_21_set4_d:medium_d05 — column counts as bars.

Rule: read each input column independently. Count its nonzero cells, remember
that column's first nonzero color, and output one row per column: the row has
that many colored cells, left-justified, padded with 0 to the maximum count.

This replaces a stale motif-gallery generator that belonged to a different task
and drifted far from the canonical examples.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8efeb221b910"
VERSION = "3.0.0"
TASK_ID = "8efeb221b910"

SUMMARY = (
    "Compact 0-bg grid with 4-7 columns. Each nonempty column is a single "
    "color, bottom-justified vertical stack with count 1..h; some columns may "
    "be empty. Rule: column count -> left-justified horizontal bar row in that "
    "column's first nonzero color."
)

INVARIANTS = [
    "background is 0",
    "each nonempty column contains one nonzero color",
    "nonzero cells in a column form a bottom-justified stack",
    "at least two columns have different counts, so the bar chart is nontrivial",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_empty", "uniform_counts", "mixed_color_column")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "grid_w":         {"type": "int", "default": "rng 4..7", "valid": "3..8"},
    "max_count":      {"type": "int", "default": "<= grid_h", "valid": "1..grid_h"},
    "empty_cols":     {"type": "int", "default": "allowed", "valid": "0..grid_w-1"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "density":        {"type": "str", "default": "column_stacks", "valid": "column_stacks"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _column_values(grid, c):
    return [grid[r][c] for r in range(len(grid))]


def _nonzero(vals):
    return [v for v in vals if v != 0]


def _counts(grid):
    return [len(_nonzero(_column_values(grid, c))) for c in range(len(grid[0]))]


def _colors_for_width(rng, w):
    base = [2, 3, 4, 5, 6, 7, 8, 9]
    if w <= len(base):
        return rng.sample(base, w)
    return [base[i % len(base)] for i in range(w)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 5, 7)
    else:
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 4, 6)

    g = full_grid(h, w, 0)
    colors = _colors_for_width(rng, w)

    # Draw varied counts, including occasional empty columns, but reject the
    # all-same histogram because it hides the transformation.
    for _attempt in range(60):
        counts = [rng.randint(0, h) for _ in range(w)]
        if max(counts) == 0:
            counts[rng.randrange(w)] = rng.randint(1, h)
        if len(set(counts)) >= 2:
            break
    else:
        counts = list(range(w))
        counts = [c % (h + 1) for c in counts]

    for c, (count, color) in enumerate(zip(counts, colors)):
        for r in range(h - count, h):
            g[r][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the column-bar-chart teaching invariants."""
    if not grid or not grid[0]:
        return ["grid must be nonempty"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    if not (3 <= h <= 8 and 3 <= w <= 8):
        errors.append(f"expected compact 3..8 x 3..8 input, got {h}x{w}")

    counts = []
    for c in range(w):
        vals = _column_values(grid, c)
        nz = _nonzero(vals)
        counts.append(len(nz))
        if len(set(nz)) > 1:
            errors.append(f"column {c} has multiple nonzero colors: {sorted(set(nz))}")
        # Bottom-justified stack: zeros above, then all nonzeros.
        seen_nonzero = False
        for r, v in enumerate(vals):
            if v != 0:
                seen_nonzero = True
            elif seen_nonzero:
                errors.append(f"column {c} has a gap below a nonzero cell at row {r}")
                break
    if max(counts, default=0) == 0:
        errors.append("all columns are empty")
    if len(set(counts)) < 2:
        errors.append("all columns have the same count; output chart is under-informative")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 5, 5
    g = full_grid(h, w, 0)
    if name == "all_empty":
        return g
    if name == "uniform_counts":
        for c, color in enumerate([2, 3, 4, 5, 6]):
            for r in range(h - 2, h):
                g[r][c] = color
        return g
    if name == "mixed_color_column":
        g[h - 1][0] = 2
        g[h - 2][0] = 3
        for r in range(h - 3, h):
            g[r][2] = 7
        return g
    return g
