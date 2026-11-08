"""Generator for arc_additional_puzzle_bank_volume16:M112 — blanks touching both 1 and 2 → 8.

Rule: for each 0-cell, check its 4 cardinal neighbors. If at least
one is color 1 AND at least one is color 2, replace the 0 with 8.
Other cells preserved unchanged.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "40f6e5fa30e1"
VERSION = "1.2.2"
TASK_ID = "40f6e5fa30e1"
SUMMARY = (
    "0-bg grid with scattered color-1 and color-2 cells (and possibly "
    "other colors). Rule: for each 0-cell, check its 4 cardinal "
    "neighbors. If ≥1 neighbor is color 1 AND ≥1 neighbor is color 2, "
    "replace the 0 with color 8. Other cells (non-0, or 0 without "
    "the dual-touch condition) are preserved unchanged."
)

# Rivals: 'output is input' refuted by demos with ≥1 dual-touch cell.
# 'recolor every 0 to 8' refuted by demos where 0s without dual-touch
# stay 0. 'recolor every 0 adjacent to 1 OR 2 (not both)' refuted by
# demos. 'use color 4 instead of 8' refuted. 'apply to 8-conn
# neighbors' refuted by demos where diagonally-adjacent 1+2 don't
# trigger. 'recolor the 1 or 2 cells (not the 0s)' refuted by demos
# showing 1s and 2s preserved. 3 demos with mixed dual-touch and
# single-touch cases pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥1 color-1 cell AND ≥1 color-2 cell",
    "≥1 dual-touch 0-cell exists (so the rule's recolor is visible)",
    "≥1 0-cell adjacent to ONLY color-1 or ONLY color-2 (so the rule's "
    "selectivity is observable — those stay 0)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_color_1", "no_color_2", "no_adjacency")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..11", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "5..14"},
    "n_dual_touch":   {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_single_1":     {"type": "int", "default": "rng 1..2", "valid": "0..4"},
    "n_single_2":     {"type": "int", "default": "rng 1..2", "valid": "0..4"},
    "n_decor":        {"type": "int", "default": "rng 0..2", "valid": "0..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _neighbor_colors(grid, r, c):
    h, w = len(grid), len(grid[0])
    out = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            out.append(grid[nr][nc])
    return out


def _dual_touch_zero_count(grid):
    return sum(
        1
        for r, row in enumerate(grid)
        for c, v in enumerate(row)
        if v == 0 and 1 in _neighbor_colors(grid, r, c) and 2 in _neighbor_colors(grid, r, c)
    )


def _single_touch_zero_count(grid):
    return sum(
        1
        for r, row in enumerate(grid)
        for c, v in enumerate(row)
        if v == 0
        and ((1 in _neighbor_colors(grid, r, c)) ^ (2 in _neighbor_colors(grid, r, c)))
    )


def _force_teaching_pattern(grid):
    """Inject one positive 1+2 touch and one negative single-touch example."""
    h, w = len(grid), len(grid[0])
    # Positive: center 0 touches both 1 and 2 cardinally.
    pr, pc = 1, 1
    for rr in range(max(0, pr - 1), min(h, pr + 2)):
        for cc in range(max(0, pc - 1), min(w, pc + 2)):
            grid[rr][cc] = 0
    grid[pr][pc - 1] = 1
    grid[pr][pc + 1] = 2
    # Negative: center 0 touches only color 1, proving selectivity.
    nr, nc = h - 2, w - 2
    for rr in range(max(0, nr - 1), min(h, nr + 2)):
        for cc in range(max(0, nc - 1), min(w, nc + 2)):
            grid[rr][cc] = 0
    grid[nr][nc - 1] = 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify default examples visibly exercise both the positive and negative cases."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has1 = any(grid[r][c] == 1 for r in range(h) for c in range(w))
    has2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has1:
        errs.append("no color-1 cells found")
    if not has2:
        errs.append("no color-2 cells found")
    if _dual_touch_zero_count(grid) < 1:
        errs.append("no dual-touch 0-cell; rule would be identity on this example")
    if _single_touch_zero_count(grid) < 1:
        errs.append("no single-touch negative 0-cell; OR-vs-AND selectivity is hidden")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n_dual_lo, n_dual_hi = 1, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        n_dual_lo, n_dual_hi = 3, 5
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        n_dual_lo, n_dual_hi = 2, 4
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Place dual-touch anchors: each contributes a 0-cell with both
    # a 1 and 2 cardinal neighbor.
    n_dual = rng.randint(n_dual_lo, n_dual_hi)
    placed_dual = 0
    for _ in range(n_dual * 8):
        if placed_dual >= n_dual:
            break
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        if g[r][c] != 0:
            continue
        # Pick which 2 cardinal directions hold 1 and 2
        # (other 2 directions can be 0)
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        rng.shuffle(dirs)
        # Place 1 at first, 2 at second
        d1 = dirs[0]; d2 = dirs[1]
        n1r, n1c = r + d1[0], c + d1[1]
        n2r, n2c = r + d2[0], c + d2[1]
        if g[n1r][n1c] != 0 or g[n2r][n2c] != 0:
            continue
        g[n1r][n1c] = 1
        g[n2r][n2c] = 2
        placed_dual += 1
    # Place isolated 1s and 2s (not touching each other in cardinals)
    # so the rule's "needs both" is visible
    for color in [1, 2]:
        for _ in range(rng.randint(1, 2) * 8):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0:
                continue
            other = 2 if color == 1 else 1
            # No cardinal neighbor of "other"
            has_other = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == other:
                    has_other = True
                    break
            if has_other:
                continue
            g[r][c] = color
            break
    # Add 0..2 decoration cells in other colors
    n_decor = rng.randint(0, 2)
    for _ in range(n_decor * 4):
        if n_decor <= 0:
            break
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        g[r][c] = rng.choice([3, 4, 5, 6, 7, 9])
        n_decor -= 1
    if _dual_touch_zero_count(g) < 1 or _single_touch_zero_count(g) < 1:
        _force_teaching_pattern(g)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_color_1":
        g[2][1] = 2; g[2][3] = 2
        g[5][4] = 2
        return g
    if name == "no_color_2":
        g[2][1] = 1; g[2][3] = 1
        g[5][4] = 1
        return g
    if name == "no_adjacency":
        g[1][1] = 1
        g[6][6] = 2
        return g
    return g
