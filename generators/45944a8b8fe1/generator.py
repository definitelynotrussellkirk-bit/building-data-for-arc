"""Generator for cf133acc.

Rule: broken horizontal runs and vertical anchors extend colored columns
upward.

Combinatorial axes (8): grid_h/w, line_row, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_runs, no_anchors, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "45944a8b8fe1"
RULE_HASH = "076e1fcd31aa"  # canonical rule this generator was written against
VERSION = "3.0.1"  # shape-locked-in/out (fixed 12x13, 1 run + 2 anchors): rule reads h,w dynamically and output = input size. Now grid varies with 1-3 broken horizontal runs (each a colour with a gap to fill) + 1-2 vertical anchor columns -> input/output shapes vary and the structure is richer (closer to canonical's multi-line layout).
TASK_ID = "45944a8b8fe1"
SUMMARY = (
    "FIXED 12×13 grid with: "
    "(a) LINE ROW at row "
    "∈ {5, 6, 7}: a BROKEN "
    "HORIZONTAL RUN of "
    "LINE-COLOR painted at "
    "cols {2, 3, 8, 9} — "
    "two run segments "
    "(cols 2-3 and cols "
    "8-9) with a GAP of 0s "
    "in cols 4-7 between "
    "them; (b) ANCHOR "
    "COLUMN: an anchor "
    "color is placed at "
    "TWO ROWS — UPPER "
    "ANCHOR at row ∈ "
    "{2, 3}, LOWER ANCHOR "
    "at row ∈ {8, 9}, both "
    "at ANCHOR_COL ∈ "
    "{10, 11}. Rule "
    "(COMPLETE BROKEN RUNS "
    "AND EXTEND COLORED "
    "COLUMNS UPWARD): "
    "(i) IDENTIFY the "
    "broken horizontal "
    "line: FILL the GAP "
    "(cols 4-7 of LINE_ROW) "
    "with the LINE-COLOR "
    "to complete the run; "
    "(ii) for the GAP "
    "COLUMNS just filled "
    "AND the ANCHOR COLUMN: "
    "EXTEND the line-color "
    "UPWARD from the line "
    "row toward each "
    "anchor (paint cells "
    "above the line row up "
    "to the anchor row in "
    "that column). Net: "
    "broken line completes "
    "and vertical bars "
    "project upward to "
    "anchor points."
)

INVARIANTS = [
    "a horizontal same-color run has a blank gap between its observed parts",
    "that gap is first filled to complete the horizontal run",
    "gap columns and isolated anchor columns are extended upward to each anchor",
]

LINE_ROWS = ("R5", "R6", "R7")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_runs", "no_anchors", "full_grid")
HELPFUL_TEXTURES = LINE_ROWS

AXES = {
    "grid_h":         {"type": "int", "default": "12", "valid": "12"},
    "grid_w":         {"type": "int", "default": "13", "valid": "13"},
    "line_row":       {"type": "choice", "default": "rng helpful",
                       "valid": "5|6|7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for line_row",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        H = ctx.draw_int("grid_h", 10, 12); W = ctx.draw_int("grid_w", 11, 13)
        n_runs = 1; n_anchors = 1
    elif difficulty == "hard":
        H = ctx.draw_int("grid_h", 14, 20); W = ctx.draw_int("grid_w", 14, 20)
        n_runs = rng.randint(2, 3); n_anchors = rng.randint(1, 2)
    else:
        H = ctx.draw_int("grid_h", 12, 16); W = ctx.draw_int("grid_w", 12, 16)
        n_runs = rng.randint(1, 2); n_anchors = rng.randint(1, 2)

    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_runs + n_anchors)
    g = full_grid(H, W, 0)
    # broken horizontal runs in the UPPER half: two color segments with a gap
    rows = rng.sample(range(1, max(2, H // 2)), min(n_runs, max(1, H // 2 - 1)))
    for i, r in enumerate(rows):
        color = colors[i]
        seg1 = rng.randint(2, 3)
        a = rng.randint(1, max(1, W - 2 * seg1 - 4))
        gap = rng.randint(2, 4)
        b = a + seg1 + gap
        if b + seg1 > W - 1:
            b = W - 1 - seg1
        if b <= a + seg1:
            continue
        for c in range(a, a + seg1):
            g[r][c] = color
        for c in range(b, min(b + seg1, W - 1)):
            g[r][c] = color
    # vertical anchor columns: an anchor colour at an upper + a lower row
    cols = rng.sample(range(1, W - 1), min(n_anchors, max(1, W - 2)))
    for j, c in enumerate(cols):
        color = colors[n_runs + j]
        ru = rng.randint(1, max(1, H // 2 - 1))
        rl = rng.randint(H // 2 + 1, H - 1)
        if g[ru][c] == 0:
            g[ru][c] = color
        if g[rl][c] == 0:
            g[rl][c] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 13, 0)
    if name == "no_runs":
        g[3][10] = 4
        return g
    if name == "no_anchors":
        for c in [2, 3, 8, 9]:
            g[6][c] = 3
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(13):
                g[r][c] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; at least one non-0 non-zero cell (broken run segment or anchor)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errors.append("grid is entirely background (no run or anchor cells)")
        return errors
    # At least one row in the upper half must contain non-zero cells (run segment)
    upper_nonzero = [r for (r, c) in nonzero if r < h // 2]
    if not upper_nonzero:
        errors.append("no non-zero cells in the upper half (expected at least one run segment)")
    return errors
