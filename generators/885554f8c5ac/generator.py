"""Generator for arc_puzzle_bank_21_set13_bundle:hard_m04.

Rule: each cell is recolored by the count of other cells it 'sees'
(no obstruction along straight line).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, single_marker, all_collinear.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import positions

GENERATOR_ID = "885554f8c5ac"
VERSION = "2.1.0"  # avoid all-collinear default marker sets
TASK_ID = "885554f8c5ac"
SUMMARY = (
    "0-bg grid (h~7-9, w~9-11) containing 3-5 "
    "SINGLE-CELL MARKERS, each in a DISTINCT "
    "non-zero color from {1..9}, placed at "
    "scattered random positions. Markers are "
    "individual pixels (not connected blobs) "
    "with no enforced separation beyond being "
    "at distinct cells. Rule: for EACH cell "
    "(including bg cells), COUNT the number of "
    "OTHER MARKER CELLS it can 'SEE' — a "
    "marker is visible from cell (r, c) if "
    "there's a STRAIGHT LINE (horizontal, "
    "vertical, or diagonal) connecting them "
    "with NO OTHER MARKER in between "
    "(line-of-sight along 8 cardinal/diagonal "
    "rays). RECOLOR each cell to that "
    "visibility count (e.g., 0 if it sees no "
    "marker, 1 if it sees one, etc.). Output: "
    "grid where every cell shows how many "
    "markers are visible from it. Net: input "
    "is sparse markers; output is a per-cell "
    "visibility-count heatmap."
)

INVARIANTS = [
    "background is 0",
    "3-5 single-cell markers in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "single_marker", "all_collinear")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_markers":      {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _all_collinear(cells):
    if len(cells) < 3:
        return True
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    diag1 = {r - c for r, c in cells}
    diag2 = {r + c for r, c in cells}
    return min(len(rows), len(cols), len(diag1), len(diag2)) == 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        n = ctx.draw_int("n", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        n = ctx.draw_int("n", 3, 5)
    rng = ctx.draw_rng("layout")

    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    spots = [(r, c) for r in range(h) for c in range(w)]
    for _layout in range(100):
        cells = rng.sample(spots, n)
        if _all_collinear(cells):
            continue
        g = full_grid(h, w, 0)
        for (r, c), color in zip(cells, colors):
            g[r][c] = color
        return g
    raise ValueError("could not place a non-collinear marker set")


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # empty grid → all cells see zero markers, output uniform
        return g
    if name == "single_marker":
        # one marker → it sees zero, every other cell sees one — uniform output
        g[3][5] = 4
        return g
    if name == "all_collinear":
        # all markers on the same row → each sees only its row neighbors, no col/diag signal
        for c, v in [(1, 3), (3, 5), (5, 6), (8, 7)]:
            g[2][c] = v
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    cells = positions(grid)
    msgs = []
    if not (3 <= len(cells) <= 5):
        msgs.append("default should contain 3..5 marker cells")
    vals = [grid[r][c] for r, c in cells]
    if len(vals) != len(set(vals)):
        msgs.append("marker colors are not distinct")
    if len(cells) >= 3:
        rows = {r for r, _c in cells}
        cols = {c for _r, c in cells}
        diag1 = {r - c for r, c in cells}
        diag2 = {r + c for r, c in cells}
        if min(len(rows), len(cols), len(diag1), len(diag2)) == 1:
            msgs.append("all markers are collinear (degenerate texture leaked)")
    return msgs
