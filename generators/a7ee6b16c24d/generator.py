"""Generator for arc_additional_puzzle_bank_volume12:E79 — Yellow rings get cyan centers.

Rule: exact hollow 3×3 yellow-ring components receive cyan centers.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rings,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rings, solid_squares, centers_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "a7ee6b16c24d"
VERSION = "1.1.1"
TASK_ID = "a7ee6b16c24d"
SUMMARY = "Exact hollow 3x3 yellow-ring components receive cyan centers."

INVARIANTS = [
    "background is 0",
    "target yellow components are exact hollow 3x3 rings",
    "rings are separated by at least one background row or column",
    "center cells start empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rings", "solid_squares", "centers_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rings":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "spaced_3x3_rings",
                       "valid": "spaced_3x3_rings"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; any 3×3 yellow(4) ring has an empty center; no non-{0,4} cells."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Only colors 0 and 4 are used (palette_size=1, n_distinct_colors=1)
    bad = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 4)]
    if bad:
        errs.append(f"expected only colors 0 and 4; found others at {bad[:3]}")
        return errs
    # Any 3×3 subgrid with 8 yellow borders must have empty center
    for r in range(h - 2):
        for c in range(w - 2):
            border = [
                grid[r][c], grid[r][c+1], grid[r][c+2],
                grid[r+1][c], grid[r+1][c+2],
                grid[r+2][c], grid[r+2][c+1], grid[r+2][c+2],
            ]
            if all(v == 4 for v in border) and grid[r+1][c+1] != 0:
                errs.append(f"3×3 ring at ({r},{c}) has non-empty center {grid[r+1][c+1]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_rings = ctx.draw_int("n_rings", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 12, 13)
        n_rings = ctx.draw_int("n_rings", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_rings = ctx.draw_int("n_rings", 2, 4)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    anchors: list[tuple[int, int]] = []
    for _ in range(200):
        if len(anchors) >= n_rings:
            break
        r = rng.randint(0, h - 3)
        c = rng.randint(0, w - 3)
        if any(abs(r - rr) < 4 and abs(c - cc) < 4 for rr, cc in anchors):
            continue
        draw_rect_outline(g, r, c, 3, 3, 4)
        anchors.append((r, c))
    if not anchors:
        draw_rect_outline(g, 1, 1, 3, 3, 4)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_rings":
        # blank → no rings to fill
        return g
    if name == "solid_squares":
        # solid 3x3 yellow squares (no hollow center) → no center to fill
        for r in range(3):
            for c in range(3): g[1 + r][1 + c] = 4
        for r in range(3):
            for c in range(3): g[5 + r][5 + c] = 4
        return g
    if name == "centers_already_filled":
        # 3x3 ring with center already non-bg → no 0-cell to fill
        draw_rect_outline(g, 1, 1, 3, 3, 4)
        g[2][2] = 6
        draw_rect_outline(g, 5, 5, 3, 3, 4)
        g[6][6] = 7
        return g
    return g
