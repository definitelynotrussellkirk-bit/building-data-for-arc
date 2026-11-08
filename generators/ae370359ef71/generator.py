"""Generator for arc_puzzle_bank_seventh21:E48.

Rule: each row has a 1-marker immediately followed by a color cell;
the color extends as a ray rightward until it hits a 9 stopper or
the edge.

Combinatorial axes (8): grid_h, grid_w, palette_kind, launchers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_launcher, missing_color_cell, launcher_at_right_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ae370359ef71"
VERSION = "2.1.0"
TASK_ID = "ae370359ef71"
SUMMARY = (
    "0-bg grid (h~5-8, w~"
    "9-13) with 2-4 ACTIVE "
    "ROWS, each containing "
    "a LAUNCHER — at "
    "column c, a COLOR-1 "
    "(blue) MARKER "
    "immediately followed "
    "by a COLOR CELL at "
    "(r, c+1) in a non-{0, "
    "1, 9} color drawn "
    "from {2..8}. Some "
    "rows ALSO have a "
    "COLOR-9 (maroon) "
    "STOPPER somewhere to "
    "the right at (r, c+k) "
    "where k ≥ 3. Other "
    "rows have no stopper. "
    "Rule (EACH 1/COLOR "
    "LAUNCHER FIRES A "
    "RIGHTWARD RAY OF ITS "
    "COLOR UNTIL STOPPER "
    "OR EDGE): For EACH "
    "ACTIVE ROW r: locate "
    "the LAUNCHER — a "
    "color-1 cell at "
    "(r, c) immediately "
    "followed by a non-"
    "{0, 1, 9} color C at "
    "(r, c+1). PAINT cells "
    "(r, c+2), (r, c+3), "
    "... with COLOR C, "
    "extending RIGHTWARD, "
    "stopping just before "
    "a COLOR-9 STOPPER or "
    "the grid right edge. "
    "Launcher and color "
    "cells stay. Net: "
    "each row's launcher "
    "paints a rightward "
    "tail in its color "
    "until a 9-stopper or "
    "the right edge."
)

INVARIANTS = [
    "background is 0",
    "each active row has a 1 immediately followed by a nonzero non-9 color",
    "ray path to the right is initially empty until a stopper or edge",
    "optional stopper color is 9",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_launcher", "missing_color_cell", "launcher_at_right_edge")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "3..14"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "launchers":      {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 2..7", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "row_left", "valid": "row_left"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..7", "valid": "1..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 9, 10)
        target = min(ctx.draw_int("launchers", 2, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 12, 13)
        target = min(ctx.draw_int("launchers", 3, 4), h)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 9, 13)
        target = min(ctx.draw_int("launchers", 2, 4), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), target)
    for i, r in enumerate(rows):
        c = rng.randint(0, w - 5)
        color = rng.choice([2, 3, 4, 5, 6, 7, 8])
        g[r][c] = 1
        g[r][c + 1] = color
        has_stopper = i == 0 or (i > 1 and rng.randrange(2) == 0)
        if i == 1:
            has_stopper = False
        if has_stopper:
            g[r][rng.randint(c + 3, w - 1)] = 9
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    launcher_rows = 0
    stopper_rows = 0
    edge_rows = 0
    for r, row in enumerate(grid):
        for c in range(w - 1):
            if row[c] == 1 and row[c + 1] not in (0, 1, 9):
                launcher_rows += 1
                right = row[c + 2:]
                if 9 in right:
                    stopper_rows += 1
                    stop = c + 2 + right.index(9)
                else:
                    edge_rows += 1
                    stop = w
                if any(row[x] != 0 for x in range(c + 2, stop)):
                    errs.append("ray corridor before stopper/edge should be empty")
                break
    if launcher_rows < 2:
        errs.append("expected at least two launcher rows")
    if stopper_rows == 0:
        errs.append("expected at least one stopper branch")
    if edge_rows == 0:
        errs.append("expected at least one edge branch")
    return errs



def _draw_from_degenerate(name, rng):
    h, w = 6, 11
    g = full_grid(h, w, 0)
    if name == "no_launcher":
        # color cell with no preceding 1 → no ray to fire
        g[1][3] = 4
        g[3][2] = 7
        return g
    if name == "missing_color_cell":
        # 1 marker without a color cell after it → ray color undefined
        g[1][2] = 1
        g[3][1] = 1
        return g
    if name == "launcher_at_right_edge":
        # 1 at last column → no room for color cell or ray
        g[1][w - 1] = 1
        g[3][w - 2] = 1; g[3][w - 1] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    if any(v < 0 or v > 9 for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    launchers = []
    for r, row in enumerate(grid):
        for c in range(w - 1):
            if row[c] == 1 and row[c + 1] not in (0, 1, 9):
                launchers.append((r, c, row[c + 1]))
        for c, v in enumerate(row):
            if v == 1 and not (c + 1 < w and row[c + 1] not in (0, 1, 9)):
                errors.append(f"color-1 marker at {(r, c)} is not followed by a ray color")
    lo, hi = ((2, 3) if difficulty == "easy" else (3, 4) if difficulty == "hard" else (2, 4))
    if not (lo <= len(launchers) <= hi):
        errors.append(f"expected {lo}..{hi} launchers, found {len(launchers)}")
    for r, c, color in launchers:
        for cc in range(c + 2, w):
            v = grid[r][cc]
            if v == 9:
                break
            if v != 0:
                errors.append(f"ray path from {(r, c)} is pre-filled at column {cc}")
                break
    return errors

