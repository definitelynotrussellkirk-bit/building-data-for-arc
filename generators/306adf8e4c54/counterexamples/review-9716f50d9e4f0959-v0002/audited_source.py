"""Generator for additional_scaffolded:E3 — fill 1-cell black gaps between aligned 4s.

Rule: black one-cell gaps between aligned color-4 endpoints get filled
with color 4.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_gaps,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, no_gap, gap_blocked.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "306adf8e4c54"
VERSION = "1.1.1"
TASK_ID = "306adf8e4c54"
SUMMARY = "Black one-cell gaps between aligned color-4 endpoints are filled."

INVARIANTS = [
    "background is 0",
    "each target gap is exactly one black cell between two 4 cells",
    "horizontal and vertical gap orientations can both appear",
    "placed gap patterns are separated to avoid accidental longer runs",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "no_gap", "gap_blocked")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "3..18"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "3..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_gaps":         {"type": "int", "default": "rng 3..6", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "1 (color 4)", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "axis_aligned_1cell_gaps",
                       "valid": "axis_aligned_1cell_gaps"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _too_close(r: int, c: int, used: list[tuple[int, int]]) -> bool:
    return any(abs(r - rr) < 2 and abs(c - cc) < 4 for rr, cc in used)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """≥1 gap pattern: two color-4 cells separated by exactly one zero cell (horizontally or vertically)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    has_gap = False
    # Check horizontal gaps: 4, 0, 4
    for r in range(h):
        for c in range(w - 2):
            if grid[r][c] == 4 and grid[r][c+1] == 0 and grid[r][c+2] == 4:
                has_gap = True
                break
    # Check vertical gaps: 4, 0, 4
    if not has_gap:
        for r in range(h - 2):
            for c in range(w):
                if grid[r][c] == 4 and grid[r+1][c] == 0 and grid[r+2][c] == 4:
                    has_gap = True
                    break
    if not has_gap:
        errs.append("no (4, 0, 4) gap pattern found horizontally or vertically")
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
        n_gaps = ctx.draw_int("n_gaps", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        n_gaps = ctx.draw_int("n_gaps", 6, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
        n_gaps = ctx.draw_int("n_gaps", 3, 6)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    used: list[tuple[int, int]] = []
    for _ in range(240):
        if len(used) >= n_gaps:
            break
        vertical = rng.choice([False, True])
        if vertical:
            r = rng.randint(1, h - 2)
            c = rng.randint(0, w - 1)
            cells = [(r - 1, c), (r + 1, c)]
        else:
            r = rng.randint(0, h - 1)
            c = rng.randint(1, w - 2)
            cells = [(r, c - 1), (r, c + 1)]
        if any(_too_close(rr, cc, used) for rr, cc in cells):
            continue
        if any(g[rr][cc] != 0 for rr, cc in cells):
            continue
        for rr, cc in cells:
            g[rr][cc] = 4
            used.append((rr, cc))
    if not used:
        g[2][1] = 4
        g[2][3] = 4
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Singletons only — no aligned 4-pair to bridge.
        g[2][2] = 4; g[5][7] = 4; g[7][3] = 4
        return g
    if name == "no_gap":
        # Adjacent 4 cells (no zero between) — rule's 1-cell-gap filter
        # never matches; the cells are already touching.
        g[2][2] = 4; g[2][3] = 4
        g[5][6] = 4; g[5][7] = 4
        return g
    if name == "gap_blocked":
        # Aligned 4s at distance 2, but the midpoint cell is already
        # non-zero (different color) — rule's gap-fill cannot proceed.
        g[2][1] = 4; g[2][3] = 4; g[2][2] = 7
        g[5][2] = 4; g[5][4] = 4; g[5][3] = 8
        return g
    return g
