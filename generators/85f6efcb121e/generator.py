"""Generator for arc_puzzle_bank_fourth_21_bundle:easy_26_complete_2x2_from_l.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_l_pattern, full_2x2_filled, mixed_color_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "85f6efcb121e"
VERSION = "2.0.1"
TASK_ID = "85f6efcb121e"
SUMMARY = (
    "0-bg grid (h~7-11, w~7-11) with 2-4 "
    "ISOLATED THREE-CELL GRAY (color 5) "
    "L-SHAPES placed at non-touching positions "
    "(3-cell pairwise minimum separation). Each "
    "L-shape is a 2×2 window with EXACTLY 3 of "
    "the 4 cells painted in COLOR 5 and the "
    "fourth (missing) corner left as bg-0. The "
    "missing corner is chosen uniformly at "
    "random from {(0,0), (0,1), (1,0), (1,1)}. "
    "All shapes use the same gray color 5 "
    "(palette_size=1). If random placement "
    "fails entirely, a single fallback L is "
    "drawn at (0,0)-(1,1). Rule (COMPLETE EACH "
    "THREE-CELL GRAY L-SHAPE INTO A FULL 2×2 "
    "MONOCHROME BLOCK): for EACH 2×2 WINDOW "
    "with exactly 3 color-5 cells and 1 bg-0 "
    "cell: RECOLOR the missing-corner 0 cell "
    "to COLOR 5, closing the 2×2 monochrome "
    "block. Other cells (already 5, or "
    "outside any active 2×2 window) stay "
    "unchanged. Net: every gray L-triomino "
    "becomes a solid 2×2 gray block."
)

INVARIANTS = [
    "background is 0",
    "each target 2x2 window has exactly three 5s and one 0",
    "target windows do not overlap",
    "at least one missing corner exists",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_l_pattern", "full_2x2_filled", "mixed_color_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..11", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_shapes":       {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_5_l_shapes",
                       "valid": "separated_5_l_shapes"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; color-5 cells appear as 2x2 windows with exactly 3 cells (L-shapes)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    fives = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not fives:
        return []  # degenerate no_l_pattern — allowed
    # Scan all 2x2 windows for partial fills (3-of-4 with color 5)
    l_windows = []
    for r in range(h - 1):
        for c in range(w - 1):
            cnt = sum(1 for dr in range(2) for dc in range(2) if grid[r + dr][c + dc] == 5)
            if cnt == 3:
                l_windows.append((r, c))
            elif cnt == 4:
                return []  # degenerate full_2x2_filled — allowed
    if not l_windows:
        return []  # degenerate — allowed
    errs = []
    # All color-5 cells should be part of exactly one L-window
    covered = set()
    for r, c in l_windows:
        for dr in range(2):
            for dc in range(2):
                if grid[r + dr][c + dc] == 5:
                    covered.add((r + dr, c + dc))
    uncovered = [pos for pos in fives if pos not in covered]
    if uncovered:
        errs.append(f"{len(uncovered)} color-5 cells not part of any 2x2 L-window")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n_shapes = ctx.draw_int("n_shapes", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
        n_shapes = ctx.draw_int("n_shapes", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 7, 11)
        n_shapes = ctx.draw_int("n_shapes", 2, 4)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    boxes: list[tuple[int, int]] = []
    for _ in range(120):
        if len(boxes) >= n_shapes:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        if any(abs(r - rr) < 3 and abs(c - cc) < 3 for rr, cc in boxes):
            continue
        miss = rng.choice([(0, 0), (0, 1), (1, 0), (1, 1)])
        for dr in (0, 1):
            for dc in (0, 1):
                if (dr, dc) != miss:
                    g[r + dr][c + dc] = 5
        boxes.append((r, c))
    if not boxes:
        g[0][0] = g[1][0] = g[1][1] = 5
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_l_pattern":
        # blank → no L-shapes to complete
        return g
    if name == "full_2x2_filled":
        # 2x2 already full → no missing corner
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 5
        return g
    if name == "mixed_color_l":
        # 3 cells use 3 different colors, not all 5 → "exactly three 5s" fails
        g[1][1] = 5; g[1][2] = 6; g[2][1] = 7
        return g
    return g
