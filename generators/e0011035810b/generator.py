"""Generator for arc_additional_puzzle_bank_volume2:E12 — cyan singletons get magenta to right.

Rule: isolated cyan singleton cells gain a magenta cell immediately
to the right.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_singletons,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_singletons, multi_cell_blobs, singletons_at_right_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e0011035810b"
VERSION = "1.1.0"
TASK_ID = "e0011035810b"
SUMMARY = "Isolated cyan singleton cells gain a magenta cell immediately to the right."

INVARIANTS = [
    "background is 0",
    "target cyan cells are cardinally isolated singletons",
    "each target has an empty in-bounds cell immediately to its right",
    "targets are separated so shadows do not collide",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_singletons", "multi_cell_blobs", "singletons_at_right_edge")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "3..18"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_singletons":   {"type": "int", "default": "rng 3..6", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "spaced_cyan_singletons",
                       "valid": "spaced_cyan_singletons"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_singletons|multi_cell_blobs|singletons_at_right_edge"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        n_singletons = ctx.draw_int("n_singletons", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
        n_singletons = ctx.draw_int("n_singletons", 5, 6)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 8, 13)
        n_singletons = ctx.draw_int("n_singletons", 3, 6)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    cells: list[tuple[int, int]] = []
    for _ in range(220):
        if len(cells) >= n_singletons:
            break
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 2)
        if any(abs(r - rr) <= 1 and abs(c - cc) <= 2 for rr, cc in cells):
            continue
        g[r][c] = 8
        cells.append((r, c))
    if not cells:
        g[1][1] = 8
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    cyan = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 8:
                cyan.append((r, c))
            elif v != 0:
                errs.append(f"unexpected nonzero color {v} at ({r},{c}); expected only cyan 8")
    if not cyan:
        errs.append("no cyan singleton targets")
    for r, c in cyan:
        if c + 1 >= w:
            errs.append(f"cyan target ({r},{c}) is on the right edge")
        elif grid[r][c + 1] != 0:
            errs.append(f"cyan target ({r},{c}) has nonzero right shadow cell")
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 8:
                errs.append(f"cyan target ({r},{c}) is not cardinally isolated")
        for rr, cc in cyan:
            if (rr, cc) != (r, c) and rr == r and cc == c + 1:
                errs.append(f"cyan target ({r},{c}) would shadow onto another target")
    return errs



def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_singletons":
        # blank → no cyan to shadow
        return g
    if name == "multi_cell_blobs":
        # cyan multi-cell blobs (not singletons) → "isolated" precondition fails
        g[2][2] = 8; g[2][3] = 8
        g[5][5] = 8; g[6][5] = 8
        return g
    if name == "singletons_at_right_edge":
        # cyan at the rightmost column → no in-bounds cell to right of it
        g[2][w - 1] = 8
        g[5][w - 1] = 8
        return g
    return g
