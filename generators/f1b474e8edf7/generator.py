"""Generator for 5b526a93.

Rule: ring icons in the key row define stamp columns; matching row
icons receive 8-ring stamps at those columns.

Combinatorial axes (8): grid_h/w, row_icon_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_key_cols.
Degenerates: no_icons, no_key, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import RING_3X3

GENERATOR_ID = "f1b474e8edf7"
VERSION = "2.1.2"  # add self_check + robust key/row icon placement; honor n_key_cols override
TASK_ID = "f1b474e8edf7"
SUMMARY = ("A KEY ROW of 3x3 color-1 rings (at any row) defines stamp columns; the "
           "leftmost key ring's column holds ROW ICONS (above and/or below the key "
           "row). Rule: stamp an 8-ring at each row icon's row x each stamp column. "
           "Key row position, grid size, icon counts vary.")

# Rivals: 'stamp at key icon positions verbatim' refuted by any demo
# where stamps appear at column-aligned positions on different rows.
# 'use input color (1)' refuted by any demo (stamps are color 8).
# 'stamp only one' refuted by ≥1 demo with multiple matches.
# 4 demos with varied grid + key positions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "all icons are 3x3 color-1 rings with a zero center",
    "the row with the most icons is the key row",
    "the leftmost key icon column is the row-icon column",
    "row icons sit above and/or below the key row so the rule has work to do",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_icons", "no_key", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "16 easy / 17-20 med / 20-24 hard", "valid": "12..26"},
    "grid_w":         {"type": "int", "default": "14 easy / 17-20 med / 20-24 hard", "valid": "12..26"},
    "row_icon_count": {"type": "int", "default": "1-2 easy / 2-3 med / 3-4 hard", "valid": "1..6"},
    "n_key_cols":     {"type": "int", "default": "2 easy / 3 med / 3-4 hard", "valid": "2..5"},
    "key_row_pos":    {"type": "str", "default": "rng top/mid/bottom", "valid": "top|mid|bottom"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _ring(g, r0, c0, color):
    for dr, dc in RING_3X3:
        g[r0 + dr][c0 + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h, w = 16, 14
        ric_lo, ric_hi = 1, 2
        n_key_cols = ctx.draw_int("n_key_cols", 2, 2)
    elif difficulty == "hard":
        h, w = rng.randint(20, 24), rng.randint(20, 24)
        ric_lo, ric_hi = 3, 4
        n_key_cols = ctx.draw_int("n_key_cols", 3, 4)
    else:
        h, w = rng.randint(17, 20), rng.randint(17, 20)
        ric_lo, ric_hi = 2, 3
        n_key_cols = ctx.draw_int("n_key_cols", 3, 3)
    row_icon_count = ctx.draw_int("row_icon_count", ric_lo, ric_hi)
    # Keep override-requested key columns feasible before allocating
    # the grid. With leftmost key at column 1 and 4-spaced rings, n
    # key columns need width at least 4*n_key_cols.
    min_w_for_keys = 4 * n_key_cols
    if w < min_w_for_keys:
        w = min_w_for_keys
    # A top key row with four row icons needs at least four 4-spaced
    # non-overlapping rows below it (5,9,13,17).  Hard difficulty can
    # sample h=20, where that is impossible; grow within the declared
    # grid_h axis instead of returning a rare raise.
    if row_icon_count >= 4 and h < 21:
        h = 21
    g = full_grid(h, w, 0)
    # Row-icon column MUST be the LEFTMOST key column so the rule's
    # `row_col = first(sort(key_cols))` matches the row icons' column.
    # Pick it far enough left that the requested number of 4-spaced key
    # columns can fit.  The old rng upper bound could pick row_col too far
    # right, and greedy column sampling could then silently shrink the key row.
    max_row_col_for_keys = max(1, w - 3 - 4 * (n_key_cols - 1))
    row_col_hi = min(max(1, w // 3), max_row_col_for_keys)
    row_col = rng.randint(1, row_col_hi)
    key_cols = [row_col + 4 * i for i in range(n_key_cols)]
    # KEY ROW can be at the top, middle, or bottom (rule finds the row with the
    # most icons, anywhere). Row icons then sit above and/or below it.  Retry the
    # key-row choice so the sampled row_icon_count is actually realized.
    pos = (overrides.get("key_row_pos")
           or ctx.draw_choice("key_row_pos", ["top", "mid", "bottom"]))
    chosen = None
    for _row_attempt in range(80):
        if pos == "top":
            key_row = 1
        elif pos == "bottom":
            key_row = h - 4
        else:
            key_row = rng.randint(1, h - 4)
        available_rows = [r for r in range(0, h - 3) if abs(r - key_row) >= 4]
        rng.shuffle(available_rows)
        placed_rows = []
        for r in available_rows:
            if all(abs(r - p) >= 4 for p in placed_rows):
                placed_rows.append(r)
            if len(placed_rows) >= row_icon_count:
                break
        if len(placed_rows) >= row_icon_count:
            chosen = (key_row, placed_rows)
            break
    if chosen is None:
        raise ValueError(f"could not place {row_icon_count} row icons away from key row")
    key_row, placed_rows = chosen
    for c0 in key_cols:
        _ring(g, key_row, c0, 1)
    for r0 in placed_rows:
        _ring(g, r0, row_col, 1)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the key-row/row-icon ring layout."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    if any(v not in (0, 1) for row in grid for v in row):
        errs.append("input should contain only background 0 and ring color 1")
    anchors: list[tuple[int, int]] = []
    ring_cells = set(RING_3X3)
    for r in range(h - 2):
        for c in range(w - 2):
            if grid[r + 1][c + 1] != 0:
                continue
            cells = {(dr, dc) for dr in range(3) for dc in range(3)
                     if grid[r + dr][c + dc] == 1}
            if cells == ring_cells:
                anchors.append((r, c))
    covered = {(r + dr, c + dc) for r, c in anchors for dr, dc in RING_3X3}
    stray = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1 and (r, c) not in covered]
    if stray:
        errs.append(f"found color-1 cells not covered by a 3x3 ring, e.g. {stray[:3]}")
    if len(anchors) < 3:
        errs.append(f"expected at least 2 key rings plus a row icon, got {len(anchors)} rings")
        return errs
    by_row: dict[int, list[int]] = {}
    for r, c in anchors:
        by_row.setdefault(r, []).append(c)
    max_count = max(len(cols) for cols in by_row.values())
    key_rows = [r for r, cols in by_row.items() if len(cols) == max_count]
    if len(key_rows) != 1 or max_count < 2:
        errs.append(f"expected a unique key row with >=2 rings, got rows {key_rows} count {max_count}")
        return errs
    key_row = key_rows[0]
    key_cols = sorted(by_row[key_row])
    row_col = key_cols[0]
    row_icon_rows = sorted(r for r, c in anchors if r != key_row and c == row_col)
    if not row_icon_rows:
        errs.append("missing row icons in the leftmost key column")
    bad = [(r, c) for r, c in anchors if r != key_row and c != row_col]
    if bad:
        errs.append(f"non-key-row ring(s) are not in the row-icon column: {bad[:3]}")
    if any(abs(r - key_row) < 4 for r in row_icon_rows):
        errs.append("row icons overlap or touch the key-row band")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(19, 17, 0)
    if name == "no_icons":
        return g
    if name == "no_key":
        _ring(g, 6, 1, 1)
        return g
    if name == "full_grid":
        for r in range(19):
            for c in range(17):
                g[r][c] = 1
        return g
    return g
