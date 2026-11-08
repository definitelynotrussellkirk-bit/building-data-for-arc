"""Generator for f8be4b64.

Rule: green-armed pluses cast row and column rays of their center colors,
with column priority.

Combinatorial axes (8): grid_h/w, plus_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_pluses, no_arms, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3dbd1a94c4d7"
VERSION = "3.0.1"  # shape-locked-in/out (fixed 13x13, 3 fixed plus centers): rule reads h,w dynamically (output = input size) and canonical spans 10x10..30x30. Now grid size varies + pluses scattered at random separated positions, count 1..6.
TASK_ID = "3dbd1a94c4d7"
SUMMARY = (
    "13×13 0-bg grid with 1-3 PLUSES, each at fixed centers "
    "{(3,3), (9,5), (5,10)}. Each plus has a non-{0,3} CENTER "
    "cell and 4 cardinal ARMS in color 3 (green). Pluses use "
    "distinct center colors. Rule: detect pluses by their "
    "4-green-arm pattern. For each empty bg cell (r, c), look "
    "for a plus whose center is on the same COLUMN c and "
    "whose column-extent (cells in col c reachable from "
    "center without hitting another plus's arm) includes r. "
    "If yes → paint with that plus's center color. Else check "
    "row-extent on the same row. Net: each plus's center "
    "color shoots row and column rays that stop at other "
    "pluses' arms; column projections take priority where "
    "both row and column rays cover a cell."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "each plus has four color-3 arms",
    "the plus center color supplies the ray color",
    "rays stop at other plus arms",
    "column projections take priority over row projections where both apply",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_pluses", "no_arms", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "13", "valid": "13"},
    "grid_w":         {"type": "int", "default": "13", "valid": "13"},
    "plus_count":     {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 color-3 arm cell and >=1 non-{0,3} center color (plus structure)."""
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
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    centers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 3)]
    if not threes:
        errs.append("no color-3 arm cells found")
    if not centers:
        errs.append("no non-{0,3} plus center cells found")
    return errs


def _plus(g, r, c, color):
    g[r][c] = color
    g[r - 1][c] = 3
    g[r + 1][c] = 3
    g[r][c - 1] = 3
    g[r][c + 1] = 3


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # canonical inputs span 10x10..30x30 and the rule reads h,w dynamically;
    # vary the grid and scatter the pluses (was fixed 13x13 + 3 fixed centers).
    if difficulty == "easy":
        plus_count = ctx.draw_int("plus_count", 1, 2); h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 10, 13)
    elif difficulty == "hard":
        plus_count = ctx.draw_int("plus_count", 3, 6); h = ctx.draw_int("grid_h", 18, 30); w = ctx.draw_int("grid_w", 18, 30)
    else:
        plus_count = ctx.draw_int("plus_count", 2, 4); h = ctx.draw_int("grid_h", 12, 20); w = ctx.draw_int("grid_w", 12, 20)
    colors = list(ctx.draw_distinct_colors("center_colors",
                                           n=min(plus_count, 7), exclude={0, 3}))
    g = full_grid(h, w, 0)
    placed = []
    for i in range(plus_count):
        color = colors[i % len(colors)]
        for _ in range(120):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            # plus bbox is the 3x3 around (r,c); require it + a 1-cell halo free
            if all(0 <= rr < h and 0 <= cc < w and g[rr][cc] == 0
                   for rr in range(r - 2, r + 3) for cc in range(c - 2, c + 3)):
                _plus(g, r, c, color)
                placed.append((r, c))
                break
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_pluses":
        return g
    if name == "no_arms":
        g[3][3] = 4
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 3
        return g
    return g
