"""Generator for arc_additional_puzzle_bank_volume12:E78.

Blue L-triominoes are completed into solid red 2x2 squares.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_l_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_l, full_squares, length_4_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "65782055e5a5"
VERSION = "2.0.1"
TASK_ID = "65782055e5a5"
SUMMARY = (
    "0-bg grid (h, w~7-12) "
    "with 2-5 BLUE (color-1) "
    "L-TRIOMINOES — each is a "
    "3-cell L-shape fitting "
    "inside a 2×2 bbox with "
    "one of 4 MISSING-CORNER "
    "ORIENTATIONS (top-left/"
    "top-right/bottom-left/"
    "bottom-right corner "
    "missing). L-triominoes "
    "placed with ≥3-cell "
    "separation (no 4-touch "
    "or near-touch). Rule "
    "(COMPLETE L-TRIOMINO TO "
    "SOLID 2×2 SQUARE, "
    "RECOLOR RED): For EACH "
    "BLUE L-TRIOMINO: "
    "identify its 2×2 BBOX "
    "and the MISSING CORNER. "
    "PAINT the MISSING "
    "CORNER cell. Then "
    "RECOLOR the entire 2×2 "
    "(now solid) from blue "
    "(color 1) to RED "
    "(color 2). Net: each "
    "L-triomino's missing "
    "corner fills in and the "
    "whole 2×2 turns red."
)

INVARIANTS = [
    "background is 0",
    "target blue components are exact 3-cell Ls in a 2x2 box",
    "target components are separated so they remain independent",
    "the missing corner orientation varies",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_l", "full_squares", "length_4_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_l_shapes":     {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_l_triominoes",
                       "valid": "separated_l_triominoes"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_l|full_squares|length_4_l"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 blue (color-1) L-triomino cell present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture == "no_l":
        return errs
    has_1 = any(grid[r][c] == 1 for r in range(h) for c in range(w))
    if not has_1:
        errs.append("no blue (color-1) L-triomino cells found")
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
        n_l_shapes = ctx.draw_int("n_l_shapes", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        n_l_shapes = ctx.draw_int("n_l_shapes", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
        n_l_shapes = ctx.draw_int("n_l_shapes", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    corners = [(0, 0), (0, 1), (1, 0), (1, 1)]
    anchors: list[tuple[int, int]] = []
    for _ in range(220):
        if len(anchors) >= n_l_shapes:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        if any(abs(r - rr) < 3 and abs(c - cc) < 3 for rr, cc in anchors):
            continue
        missing = rng.choice(corners)
        for dr, dc in corners:
            if (dr, dc) != missing:
                g[r + dr][c + dc] = 1
        anchors.append((r, c))
    if not anchors:
        g[1][1] = 1
        g[1][2] = 1
        g[2][1] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_l":
        # blank → no L-triominoes
        return g
    if name == "full_squares":
        # 2x2 already full → no missing corner
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 1
        return g
    if name == "length_4_l":
        # 4-cell L → not a 3-cell L-triomino, rule won't fire
        for r, c in [(1, 1), (1, 2), (2, 1), (3, 1)]:
            g[r][c] = 1
        return g
    return g
