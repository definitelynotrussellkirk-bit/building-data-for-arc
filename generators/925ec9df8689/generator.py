"""Generator for arc_additional_puzzle_bank_volume21:E142.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_windows,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_windows, full_2x2_filled, mixed_color_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "925ec9df8689"
VERSION = "1.2.1"  # add self_check
TASK_ID = "925ec9df8689"
SUMMARY = (
    "0-bg grid with several 2×2 windows where exactly 3 of 4 cells "
    "are color 4 (yellow) and 1 is 0 (missing corner). Optional "
    "decoration cells in other colors elsewhere. Rule: scan all 2×2 "
    "windows. For each window where exactly 3 cells are color 4 and "
    "exactly 1 cell is 0, set the 0-cell to color 2 (red). All other "
    "cells preserved unchanged. Output: each L-shaped yellow pattern "
    "is completed with a red corner."
)

# Rivals: 'output is input' refuted by demos with ≥1 L-pattern.
# 'fill with color 4' refuted by demos showing 2. 'fill any 0 in any
# 2x2 with 2' refuted by demos where windows with <3 yellows stay.
# 'fill 4-yellows (already full) with 2' refuted. 'use color 8'
# refuted. 3 demos with multiple L-patterns at various corner
# orientations pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each active 2×2 window has exactly three color-4 cells and 1 zero",
    "the missing corner starts blank (0)",
    "active windows are separated (centers ≥3 apart) so completions don't overlap",
    "optional 0..2 decoration cells in other colors (preserved by rule)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_windows", "full_2x2_filled", "mixed_color_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_windows":      {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_l_windows",
                       "valid": "separated_l_windows"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 2×2 window with exactly 3 color-4 cells and 1 zero."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    windows = [
        (r, c)
        for r in range(h - 1)
        for c in range(w - 1)
        if [grid[r][c], grid[r][c+1], grid[r+1][c], grid[r+1][c+1]].count(4) == 3
        and [grid[r][c], grid[r][c+1], grid[r+1][c], grid[r+1][c+1]].count(0) == 1
    ]
    if not windows:
        return ["expected ≥1 2×2 window with exactly 3 color-4 cells and 1 zero; found none"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n_windows = ctx.draw_int("n_windows", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        n_windows = ctx.draw_int("n_windows", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
        n_windows = ctx.draw_int("n_windows", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    corners = [(0, 0), (0, 1), (1, 0), (1, 1)]
    anchors: list[tuple[int, int]] = []
    for _ in range(220):
        if len(anchors) >= n_windows:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        if any(abs(r - rr) < 3 and abs(c - cc) < 3 for rr, cc in anchors):
            continue
        missing = rng.choice(corners)
        for dr, dc in corners:
            if (dr, dc) != missing:
                g[r + dr][c + dc] = 4
        anchors.append((r, c))
    if not anchors:
        g[1][1] = 4
        g[1][2] = 4
        g[2][1] = 4
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_windows":
        # blank → no 2x2 windows to complete
        return g
    if name == "full_2x2_filled":
        # 2x2 already full → no missing corner
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 4
        return g
    if name == "mixed_color_l":
        # 3 cells in 2x2 of 3 different colors → no shared yellow color
        g[1][1] = 4; g[1][2] = 6; g[2][1] = 7
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    active = []
    for r in range(h - 1):
        for c in range(w - 1):
            vals = [grid[r + dr][c + dc] for dr in (0, 1) for dc in (0, 1)]
            if vals.count(4) == 3 and vals.count(0) == 1:
                active.append((r, c))
    lo = 2 if difficulty != "hard" else 4
    if len(active) < lo:
        errors.append(f"expected at least {lo} 2x2 yellow L-windows, got {len(active)}")
    for i, (r, c) in enumerate(active):
        for rr, cc in active[i + 1:]:
            if abs(r - rr) < 3 and abs(c - cc) < 3:
                errors.append("active 2x2 windows should be separated")
                return errors
    return errors
