"""Generator for arc_puzzle_bank_21_set19_s:S19_M7 — 4-panel sort by occupancy.

Rule: input has exactly 4 equal-size panels separated by 3 full-height
color-9 columns. Each panel contains some non-zero colored cells.
Rule: sort the panels by (cell count ASC, original index ASC), then
arrange them in 4 quadrants of a 2*panel_h × 2*panel_w output, all
painted with color 8 (preserving each panel's binary shape).
Quadrant order: TL, TR, BL, BR.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "32287e53c19c"
VERSION = "2.2.0"  # also force panel-count order to refute preserve-input-order
TASK_ID = "32287e53c19c"

SUMMARY = (
    "0-bg grid (panel_h~3-7 rows, w = "
    "4*panel_w+3 cols) with EXACTLY 4 "
    "EQUAL-SIZE PANELS separated by 3 "
    "full-height COLOR-9 DIVIDER COLUMNS. "
    "Each panel contains a DIFFERENT count "
    "of non-zero cells in some non-{0, 9} "
    "color, ensuring panel cell counts are "
    "STRICTLY DISTINCT. Rule: SPLIT into 4 "
    "panels. SORT by (CELL COUNT ASC, "
    "ORIGINAL INDEX ASC). Build a "
    "2*panel_h × 2*panel_w OUTPUT divided "
    "into 4 QUADRANTS (TL, TR, BL, BR). "
    "STAMP sorted panels: sorted[0] → TL, "
    "sorted[1] → TR, sorted[2] → BL, "
    "sorted[3] → BR. All stamped cells "
    "painted COLOR 8 (cyan), preserving "
    "each panel's binary shape. Net: "
    "panels rearranged by ascending count "
    "into a 2×2 quadrant layout in cyan."
)

# Rivals: 'output is input' refuted by demos (smaller, 8-colored).
# 'preserve panel order' refuted by demos with sort-order changes.
# 'sort by max color' refuted by demos with different color cells.
# 'output single color from largest panel' refuted by demos showing
# 4 quadrants of distinct patterns. 3 demos with ≥3 distinct cell
# counts cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 3 full-height color-9 columns evenly spaced",
    "4 equal-width panels separated by those columns",
    "each panel has 1..H*W-1 non-zero cells in non-{0,9} colors",
]

AXES = {
    "panel_h":   {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "panel_w":   {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "min_cells": {"type": "int", "default": "1", "valid": "0..N"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        panel_h = rng.randint(3, 4); panel_w = rng.randint(3, 4)
    elif difficulty == "hard":
        panel_h = rng.randint(5, 7); panel_w = rng.randint(5, 7)
    else:
        panel_h = rng.randint(4, 5); panel_w = rng.randint(4, 5)

    panel_w = min(panel_w, (30 - 3) // 4)  # 4 panels + 3 dividers must fit 30 (hard pw=7 -> w=31 -> clipped/corrupt)
    h = panel_h
    w = 4 * panel_w + 3  # 4 panels + 3 dividers
    g = full_grid(h, w, 0)
    # Dividers at cols panel_w, 2*panel_w+1, 3*panel_w+2
    div_cols = [panel_w, 2 * panel_w + 1, 3 * panel_w + 2]
    for dc in div_cols:
        for r in range(h):
            g[r][dc] = 9

    # 4 panels with distinct cell counts.
    panel_starts = [0, panel_w + 1, 2 * panel_w + 2, 3 * panel_w + 3]
    cells_per_panel = panel_h * panel_w
    # Make counts strictly distinct so sort order is unambiguous.
    available_counts = list(range(1, cells_per_panel))
    rng.shuffle(available_counts)
    counts = sorted(available_counts[:4])  # ascending
    rng.shuffle(counts)  # then shuffle for input randomness
    if counts == sorted(counts):
        # A sorted input order makes the sorted-output rule indistinguishable from
        # "preserve panel order" for this episode.  Swap two counts so every
        # generated instance contains a visible order-change witness.
        counts[0], counts[1] = counts[1], counts[0]
    for pi, c0 in enumerate(panel_starts):
        positions = [(r, c) for r in range(panel_h) for c in range(c0, c0 + panel_w)]
        rng.shuffle(positions)
        cell_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])  # not 9
        for (r, c) in positions[:counts[pi]]:
            g[r][c] = cell_color
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not isinstance(grid, list) or not all(isinstance(row, list) for row in grid):
        return ["grid is not a non-empty 2D list"]
    h = len(grid)
    w = len(grid[0]) if h else 0
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(div_cols) != 3:
        errors.append(f"expected exactly 3 full-height color-9 dividers, got {div_cols}")
        return errors
    panel_w = div_cols[0]
    expected_divs = [panel_w, 2 * panel_w + 1, 3 * panel_w + 2]
    if div_cols != expected_divs:
        errors.append(f"divider columns are not evenly spaced: got {div_cols}, expected {expected_divs}")
    starts = [0, div_cols[0] + 1, div_cols[1] + 1, div_cols[2] + 1]
    counts = []
    for c0 in starts:
        if c0 + panel_w > w:
            errors.append("panel extends past grid width")
            continue
        vals = [grid[r][c] for r in range(h) for c in range(c0, c0 + panel_w)]
        bad = [v for v in vals if v == 9]
        if bad:
            errors.append("panel contains divider color 9")
        n = sum(v not in (0, 9) for v in vals)
        counts.append(n)
        if not (0 < n < h * panel_w):
            errors.append(f"panel cell count {n} is empty or full")
    if len(counts) == 4:
        if len(set(counts)) != 4:
            errors.append(f"panel counts are not strictly distinct: {counts}")
        if counts == sorted(counts):
            errors.append(f"panel counts already sorted, preserving order would pass: {counts}")
    return errors
