"""Generator for arc_puzzle_bank_tenth21:E69.

Two-cell diagonal color chains extend one more step.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_cell_chains, three_cell_chains.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c14c7af8df05"
VERSION = "2.0.2"  # fail closed if target diagonal-pair count cannot be placed; verify continuation cells
TASK_ID = "c14c7af8df05"

SUMMARY = (
    "0-bg grid (h~7-10, w~7-10) with 2-4 TWO-CELL "
    "DIAGONAL COLOR CHAINS: for each chain, pick a "
    "distinct color from {1..9}, choose diagonal "
    "direction (down-right or down-left), pick a "
    "starting cell (r, c) so that the chain plus its "
    "one-step continuation fit in bounds. PAINT both "
    "chain cells (r, c) and (r+1, c±1) with the chain "
    "color. The THIRD cell at (r+2, c±2) is reserved "
    "(invariant: in-bounds and bg-0). Chains use "
    "disjoint cells; no two chains share any cell or "
    "extension cell. Rule (EXTEND EACH DIAGONAL CHAIN "
    "ONE MORE STEP): for EACH color C with exactly TWO "
    "cells forming a one-step diagonal (offset (+1, "
    "+1) or (+1, -1)): COMPUTE the continuation cell "
    "by extending one more step in the same diagonal "
    "direction. PAINT that continuation cell with COLOR "
    "C. Original two chain cells stay unchanged. Net: "
    "each two-cell diagonal becomes a three-cell "
    "diagonal of the same color, extending downward in "
    "the natural direction."
)

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "the two cells form a one-step diagonal",
    "the continuation cell is in bounds and initially empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_cell_chains", "three_cell_chains")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "diagonal_pairs",
                       "valid": "diagonal_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Each non-zero color appears exactly twice as a one-step diagonal pair,
    and its one-step continuation is in bounds and blank."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    from collections import defaultdict
    by_color: dict = defaultdict(list)
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                by_color[v].append((r, c))
    min_pairs = 3 if difficulty == "hard" else 2
    if len(by_color) < min_pairs:
        errs.append(f"expected at least {min_pairs} diagonal pairs, found {len(by_color)}")
    for color, cells in by_color.items():
        if len(cells) != 2:
            errs.append(f"color {color} appears {len(cells)} times (expected 2)")
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        dr, dc = r2 - r1, c2 - c1
        if dr != 1 or abs(dc) != 1:
            errs.append(f"color {color} pair not a downward 1-step diagonal: ({r1},{c1})-({r2},{c2})")
            continue
        rr, cc = r2 + dr, c2 + dc
        if not (0 <= rr < h and 0 <= cc < w):
            errs.append(f"color {color} continuation {(rr, cc)} is out of bounds")
        elif grid[rr][cc] != 0:
            errs.append(f"color {color} continuation {(rr, cc)} is blocked by {grid[rr][cc]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("n_pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("n_pairs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("n_pairs", 2, 4)
    rng = ctx.draw_rng("layout")
    colors0 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for _layout_attempt in range(60):
        g = full_grid(h, w, 0)
        colors = list(colors0)
        rng.shuffle(colors)
        used: set[tuple[int, int]] = set()
        placed = 0
        for color in colors:
            if placed >= target:
                break
            for _ in range(100):
                dr = 1
                dc = rng.choice([-1, 1])
                r = rng.randint(0, h - 3)
                c = rng.randint(2 if dc < 0 else 0, w - 3 if dc > 0 else w - 1)
                cells = [(r, c), (r + dr, c + dc), (r + 2 * dr, c + 2 * dc)]
                if any(p in used for p in cells):
                    continue
                g[cells[0][0]][cells[0][1]] = color
                g[cells[1][0]][cells[1][1]] = color
                # Reserve the continuation cell too, so no later chain can block
                # this color's one-step extension.
                used.update(cells)
                placed += 1
                break
        if placed == target:
            return g
    raise ValueError("could not place requested diagonal pairs")


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no diagonal chains to extend
        return g
    if name == "single_cell_chains":
        # only one cell of color → "appears exactly twice" precondition fails
        g[2][2] = 4
        g[5][5] = 6
        return g
    if name == "three_cell_chains":
        # 3 cells of same color → "exactly twice" precondition fails (continuation already exists)
        g[1][1] = 4; g[2][2] = 4; g[3][3] = 4
        return g
    return g
