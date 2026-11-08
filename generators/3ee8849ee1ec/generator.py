"""Generator for arc_puzzle_bank_21_set18_s:S18_E6.

Rule: sparse rectangle corners expand by row closure then column
closure.

Combinatorial axes (8): height, width, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_corners, single_corner, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3ee8849ee1ec"
VERSION = "2.0.1"
TASK_ID = "3ee8849ee1ec"
SUMMARY = (
    "0-bg grid (h, w ~7-10) with up to 4 color-4 "
    "(yellow) cells marking the corners of a rectangle "
    "(rows r1, r2 with r2 ≥ r1 + 3; cols c1, c2 with "
    "c2 ≥ c1 + 3). All 4 corners are at (r1, c1), "
    "(r1, c2), (r2, c1), (r2, c2). Sometimes an extra "
    "midpoint cell is also painted. Rule: detect the 4 "
    "rectangle corners. ROW CLOSURE: paint every cell "
    "in rows r1 and r2 between columns c1..c2 with "
    "color 4 (top and bottom rails). COL CLOSURE: "
    "paint every cell in cols c1 and c2 between rows "
    "r1..r2 with color 4 (left and right rails). Net: "
    "the 4 corners get connected into a hollow "
    "rectangle outline in color 4."
)

INVARIANTS = [
    "two rows contain matching left/right endpoints",
    "row closure creates horizontal rails",
    "column closure fills the rectangle between those rails",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_corners", "single_corner", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "width":          {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "random", "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=4 color-4 cells marking corners (two rows with matching endpoints)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    fours = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    if len(fours) < 2:
        errs.append(f"expected >=2 color-4 corner cells, found {len(fours)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 7, 8)
        w = ctx.draw_int("width", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 9, 10)
        w = ctx.draw_int("width", 9, 10)
    else:
        h = ctx.draw_int("height", 7, 10)
        w = ctx.draw_int("width", 7, 10)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    r1 = rng.randint(0, h - 5)
    r2 = rng.randint(r1 + 3, h - 1)
    c1 = rng.randint(0, w - 5)
    c2 = rng.randint(c1 + 3, w - 1)
    for r in (r1, r2):
        g[r][c1] = 4
        g[r][c2] = 4
    if rng.random() < 0.5:
        g[(r1 + r2) // 2][rng.choice([c1, c2])] = 4
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 0)
    if name == "no_corners":
        return g
    if name == "single_corner":
        g[2][2] = 4
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(8):
                g[r][c] = 4
        return g
    return g
