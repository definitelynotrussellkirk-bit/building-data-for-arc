"""Generator for arc_puzzle_bank_eighth21:H55 — labeled-shape match-and-recolor.

Rule: input is 3 panels separated by full-height color-9 columns.
Each of panels 0 and 1 has a label color at (0, 0) plus a shape
(other non-zero cells). Panel 2 is the query shape. Rule: check if
the query shape matches panel 0's shape (under translation or some
transform); if yes, output the query shape painted in panel 0's
label color; else, paint in panel 1's label color. Output is a
fresh panel-sized grid (same h × panel_w).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "395201c95f9d"
VERSION = "2.0.1"
TASK_ID = "395201c95f9d"

SUMMARY = (
    "0-bg grid (h ≈ panel_h, "
    "w = 3*panel_w + 2) with "
    "3 EQUAL-WIDTH PANELS "
    "separated by 2 FULL-"
    "HEIGHT COLOR-9 DIVIDER "
    "COLUMNS (at cols "
    "panel_w and 2*panel_w + "
    "1). Panel 0 carries a "
    "LABEL color at cell (0, "
    "0) and SHAPE 0 (other "
    "non-zero cells in "
    "panel 0). Panel 1 "
    "carries a LABEL color "
    "at panel 1's (0, 0) "
    "and SHAPE 1 (distinct "
    "from shape 0). Panel 2 "
    "holds the QUERY SHAPE, "
    "drawn in a query color "
    "— this query shape "
    "matches EXACTLY ONE of "
    "shape 0 or shape 1 (the "
    "match panel chosen at "
    "random). Rule (MATCH "
    "QUERY → REPAINT IN "
    "WINNING LABEL COLOR): "
    "compare the query "
    "shape (panel 2's "
    "shape cells) to shape "
    "0 and shape 1. Find "
    "the MATCH PANEL "
    "(whichever shape "
    "equals the query). "
    "Output is a fresh "
    "panel-sized blank "
    "(panel_h × panel_w) "
    "grid with the QUERY "
    "SHAPE painted in the "
    "LABEL COLOR of the "
    "matching panel. Net: "
    "isolate the panel "
    "whose shape matches; "
    "redraw the query in "
    "that panel's label "
    "color."
)

# Rivals: 'output is input' refuted by demos (output is small).
# 'use query color' refuted by demos (output uses label0 or label1).
# 'always pick panel 0' refuted by demos where the query matches
# panel 1. 'output entire grid' refuted by demos (panel-sized output).
# 3 demos covering match-to-panel-0 and match-to-panel-1 cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "3 panels separated by 2 full-height color-9 columns",
    "panels 0 and 1 each have a label at (0, 0) and a distinct shape",
    "panel 2's shape matches exactly one of the two panel shapes",
]

AXES = {
    "panel_h":  {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "panel_w":  {"type": "int", "default": "rng 4..6", "valid": "3..7"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 2 full-height color-9 divider columns; ≥1 label cell."""
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
    # Find full-height color-9 divider columns
    div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not div_cols:
        pass  # allow edge cases
    elif len(div_cols) != 2:
        errors.append(f"expected 2 full-height color-9 divider cols, found {len(div_cols)}")
    return errors


_SHAPES = [
    [(1, 1), (2, 1), (3, 1), (3, 2)],
    [(1, 2), (2, 1), (2, 2), (2, 3)],
    [(1, 1), (1, 2), (1, 3), (2, 2)],
    [(1, 1), (2, 1), (2, 2), (3, 2)],
    [(1, 1), (1, 2), (2, 2), (3, 2)],
    [(1, 1), (1, 2), (2, 1)],
    [(1, 2), (2, 1), (2, 2)],
    [(1, 1), (2, 1), (3, 1)],
    [(1, 1), (1, 2), (1, 3)],
    [(1, 1), (2, 1), (2, 2)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        panel_h = rng.randint(4, 5); panel_w = rng.randint(4, 5)
    elif difficulty == "hard":
        panel_h = rng.randint(6, 8); panel_w = rng.randint(5, 7)
    else:
        panel_h = rng.randint(5, 6); panel_w = rng.randint(4, 6)

    h = panel_h
    w = 3 * panel_w + 2  # 2 dividers
    g = full_grid(h, w, 0)
    # Dividers
    sep1 = panel_w
    sep2 = 2 * panel_w + 1
    for r in range(h):
        g[r][sep1] = 9
        g[r][sep2] = 9

    # Pick 2 distinct shapes — one is the match
    shape_pool = [s for s in _SHAPES
                  if all(r < panel_h and c < panel_w for r, c in s)]
    if len(shape_pool) < 2:
        shape_pool = _SHAPES[:2]
    shape0, shape1 = rng.sample(shape_pool, 2)
    match_panel = rng.choice([0, 1])
    matching_shape = shape0 if match_panel == 0 else shape1

    # Label colors and shape colors
    label0, label1 = rng.sample([2, 3, 4, 5, 6, 7, 8], 2)
    shape_color_0 = rng.choice([c for c in range(1, 10) if c not in (0, 9, label0)])
    shape_color_1 = rng.choice([c for c in range(1, 10) if c not in (0, 9, label1)])
    query_color = rng.choice([c for c in range(1, 10) if c not in (0, 9)])

    # Panel 0
    g[0][0] = label0
    for dr, dc in shape0:
        if dr < panel_h and dc < panel_w:
            g[dr][dc] = shape_color_0
    # Panel 1
    g[0][sep1 + 1] = label1
    for dr, dc in shape1:
        if dr < panel_h and dc < panel_w:
            g[dr][sep1 + 1 + dc] = shape_color_1
    # Panel 2 (query)
    for dr, dc in matching_shape:
        if dr < panel_h and dc < panel_w:
            g[dr][sep2 + 1 + dc] = query_color
    return g
