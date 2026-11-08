"""Generator for arc_puzzle_bank_seventeenth21:E115.

Separated 2x2 windows have one missing same-color corner.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_squares,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_squares, full_2x2, two_corners.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b955a6fc94c9"
VERSION = "1.2.0"  # defect-lint round: add executable self_check (L-triomino structure,
# isolation); AXES grid ranges tightened to the real band draws; draw label
# "squares" renamed to match the declared "n_squares" axis.
TASK_ID = "b955a6fc94c9"

SUMMARY = "Separated 2x2 windows have one missing same-color corner."

INVARIANTS = [
    "background is 0",
    "each active 2x2 window has exactly three same-color cells",
    "the fourth corner is initially 0",
    "active windows are separated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_squares", "full_2x2", "two_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "6..9"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "7..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_squares":      {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "isolated_l_triominoes",
                       "valid": "isolated_l_triominoes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("n_squares", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("n_squares", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("n_squares", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(target, 9))
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        r0 = rng.randint(0, h - 2)
        c0 = rng.randint(0, w - 2)
        guard = {
            (r, c)
            for r in range(max(0, r0 - 1), min(h, r0 + 3))
            for c in range(max(0, c0 - 1), min(w, c0 + 3))
        }
        if guard & reserved:
            continue
        missing = rng.choice([(0, 0), (0, 1), (1, 0), (1, 1)])
        color = colors[placed % len(colors)]
        for dr in [0, 1]:
            for dc in [0, 1]:
                if (dr, dc) != missing:
                    g[r0 + dr][c0 + dc] = color
        reserved.update(guard)
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Every non-zero cell belongs to an isolated L-triomino: a 2x2 window with
    exactly three same-color cells, the fourth 0, and a clear 1-cell ring."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    covered: set[tuple[int, int]] = set()
    n_windows = 0
    for r0 in range(h - 1):
        for c0 in range(w - 1):
            cells = [(r0 + dr, c0 + dc) for dr in (0, 1) for dc in (0, 1)]
            vals = [grid[r][c] for r, c in cells]
            nz = [v for v in vals if v != 0]
            if len(nz) == 3 and len(set(nz)) == 1:
                n_windows += 1
                covered.update((r, c) for (r, c), v in zip(cells, vals) if v != 0)
                # isolation: ring around the window is empty
                for r in range(max(0, r0 - 1), min(h, r0 + 3)):
                    for c in range(max(0, c0 - 1), min(w, c0 + 3)):
                        if (r, c) not in cells and grid[r][c] != 0:
                            errs.append(f"window at ({r0},{c0}) not isolated: ({r},{c}) occupied")
    if n_windows < 1:
        errs.append("no L-triomino window (2x2 with exactly three same-color cells)")
    stray = [(r, c) for r in range(h) for c in range(w)
             if grid[r][c] != 0 and (r, c) not in covered]
    if stray:
        errs.append(f"non-zero cells outside any L-triomino window: {stray[:3]}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "no_squares":
        # blank → no L-triominoes to complete
        return g
    if name == "full_2x2":
        # 2x2 already complete → no missing corner
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 4
        return g
    if name == "two_corners":
        # only 2 corners → "exactly three" precondition fails
        g[1][1] = 4; g[2][2] = 4
        return g
    return g
