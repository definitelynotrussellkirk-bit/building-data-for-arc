"""Generator for arc_puzzle_bank_twentythird21:E157.

Rule: each non-zero cell in the bottom row paints an up-left diagonal
of that color (until a grid edge).

Combinatorial axes (8): grid_h/w, palette_kind, n_markers, palette_size,
position_bias, n_distinct_colors, marker_density, texture.
Degenerates: no_markers, marker_at_left_edge, body_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eca9d989b5bd"
VERSION = "2.1.1"  # faithful; widen for aggressive standard: more markers (1-5), bigger grids (h<=10,w<=12), varied diagonal lengths/output shapes
TASK_ID = "eca9d989b5bd"
SUMMARY = (
    "0-bg grid (h~5-7, w~6-8) with "
    "1-5 COLORED MARKER CELLS placed "
    "ONLY in the BOTTOM ROW (h-1) at "
    "DISTINCT random columns, each "
    "in a DISTINCT non-zero color "
    "from 1..9. The rest of the grid "
    "(rows 0..h-2) is entirely 0. "
    "Rule (UP-LEFT DIAGONAL RAY): "
    "for EACH BOTTOM-ROW MARKER at "
    "(h-1, c) with color C, EMIT a "
    "DIAGONAL UP-LEFT RAY in color "
    "C — paint cells at "
    "(h-1, c), (h-2, c-1), "
    "(h-3, c-2), ... until the ray "
    "exits the grid (hits row -1 "
    "or col -1). The marker stays "
    "at (h-1, c). Net: each "
    "bottom-row colored marker "
    "draws an upper-left diagonal "
    "line in its color."
)

INVARIANTS = [
    "background is 0",
    "1-5 colored markers on the bottom row at distinct non-left-edge columns",
    "all other cells are 0",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_markers", "marker_at_left_edge", "body_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..10 by diff", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 6..12 by diff", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|sparse|dense|varied_palette"},
    "n_markers":      {"type": "int", "default": "rng 1..5 by diff", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "bottom_row",
                       "valid": "bottom_row"},
    "n_distinct_colors": {"type": "int", "default": "matches n_markers", "valid": "1..9"},
    "marker_density": {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|sparse|dense|varied_palette|no_markers|marker_at_left_edge|body_already_filled"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 6, 8)
        n = ctx.draw_int("n_markers", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        n = ctx.draw_int("n_markers", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 11)
        n = ctx.draw_int("n_markers", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Avoid column 0 in normal training examples: a left-edge marker emits
    # only its own cell, which hides the up-left-ray rule and is already
    # represented by the explicit marker_at_left_edge degenerate texture.
    n = min(n, max(1, w - 1))            # one marker per non-left-edge column
    cols = rng.sample(range(1, w), n)
    # distinct colors (rule allows repeats, but distinct reads cleaner); cap at 9
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(n, 9))
    while len(colors) < n:             # n>9 impossible here, but stay safe
        colors.append(rng.randint(1, 9))
    for c, color in zip(cols, colors):
        g[h - 1][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 7
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # empty grid — no diagonals to paint
        return g
    if name == "marker_at_left_edge":
        # marker at column 0 → diagonal has length 1 (degenerate)
        g[h - 1][0] = 5
        return g
    if name == "body_already_filled":
        # body has cells already → invariant violated
        g[h - 1][3] = 4
        g[2][1] = 6  # body cell, should not exist
        g[3][5] = 7
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    markers = [(c, grid[h - 1][c]) for c in range(w) if grid[h - 1][c] != 0]
    if not (1 <= len(markers) <= 5):
        errs.append(f"expected 1-5 bottom-row markers, got {len(markers)}")
    if any(c == 0 for c, _ in markers):
        errs.append("normal example contains a left-edge marker with degenerate length-1 ray")
    colors = [v for _, v in markers]
    if len(set(colors)) != len(colors):
        errs.append("bottom-row marker colors should be distinct")
    if any(v < 1 or v > 9 for v in colors):
        errs.append("marker color outside 1..9")
    if any(grid[r][c] != 0 for r in range(h - 1) for c in range(w)):
        errs.append("non-bottom-row cells must be background in the input")
    return errs
