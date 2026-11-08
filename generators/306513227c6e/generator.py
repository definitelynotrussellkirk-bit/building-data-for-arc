"""Generator for arc_additional_puzzles_21_set3:H18 — move 4-shape by marker vector.

Rule: markers 2 and 3 define a vector; color-4 cells are kept and
copied by that vector as 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, vector,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, zero_vector, no_motif.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "306513227c6e"
VERSION = "2.1.0"  # choose motif sources greedily so shifted cyan copies never collide with original motif cells or each other
TASK_ID = "306513227c6e"
SUMMARY = (
    "0-bg grid (h, w ~ 8-12) with: (a) "
    "COLOR-2 MARKER at (base_r, base_c) "
    "and COLOR-3 MARKER at (base_r+dr, "
    "base_c+dc) where (dr, dc) is drawn "
    "from {(1, 2), (2, 1), (-1, 2), "
    "(2, -1)} — the marker pair "
    "defines a non-zero VECTOR (dr, "
    "dc); (b) 4 MOTIF CELLS painted in "
    "COLOR 4 at random interior "
    "positions chosen so each motif's "
    "shifted position (r+dr, c+dc) is "
    "in-bounds and not overlapping any "
    "marker. Rule (THE 2/3 MARKER PAIR "
    "DEFINES A VECTOR — COLOR-4 CELLS "
    "ARE KEPT AND COPIED BY THAT "
    "VECTOR AS COLOR 8): identify the "
    "COLOR-2 MARKER and COLOR-3 MARKER; "
    "COMPUTE the VECTOR (dr, dc) = (3-"
    "marker's position) - (2-marker's "
    "position). For EACH COLOR-4 CELL "
    "at (r, c): KEEP it as 4 in the "
    "output; PAINT the cell at "
    "(r+dr, c+dc) with COLOR 8 (cyan). "
    "The original 2 and 3 markers stay. "
    "Net: each color-4 cell duplicates "
    "to its vector-shifted position in "
    "color 8."
)

INVARIANTS = [
    "one color-2 marker and one color-3 marker define a nonzero vector",
    "the color-4 motif has in-bounds shifted copies",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "zero_vector", "no_motif")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "vector":         {"type": "str", "default": "rng vec",
                       "valid": "(1,2)|(2,1)|(-1,2)|(2,-1)"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "markers_with_motif",
                       "valid": "markers_with_motif"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_markers|zero_vector|no_motif"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
    rng = ctx.draw_rng("layout")
    dr, dc = rng.choice([(1, 2), (2, 1), (-1, 2), (2, -1)])
    g = full_grid(h, w, 0)
    base_r = 1 if dr >= 0 else 3
    base_c = 1 if dc >= 0 else w - 3
    g[base_r][base_c] = 2
    g[base_r + dr][base_c + dc] = 3
    occupied = {(base_r, base_c), (base_r + dr, base_c + dc)}
    candidates = [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if (r, c) not in occupied
        and (r + dr, c + dc) not in occupied
        and 0 <= r + dr < h
        and 0 <= c + dc < w
    ]
    rng.shuffle(candidates)
    motif = []
    blocked = set(occupied)
    for r, c in candidates:
        shifted = (r + dr, c + dc)
        # If a shifted copy lands on another source-4 cell, the example no
        # longer teaches "keep the 4 and add an 8" cleanly; likewise duplicate
        # shifted targets hide one of the four copies.  Reserve both source and
        # shifted cells as we pick the motif.
        if (r, c) in blocked or shifted in blocked:
            continue
        motif.append((r, c))
        blocked.add((r, c))
        blocked.add(shifted)
        if len(motif) == 4:
            break
    for r, c in motif:
        g[r][c] = 4
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    twos = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    threes = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    fours = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4]
    if len(twos) != 1:
        errs.append(f"expected one color-2 marker, found {len(twos)}")
    if len(threes) != 1:
        errs.append(f"expected one color-3 marker, found {len(threes)}")
    if len(fours) != 4:
        errs.append(f"expected four color-4 motif cells, found {len(fours)}")
    if len(twos) == 1 and len(threes) == 1:
        dr = threes[0][0] - twos[0][0]
        dc = threes[0][1] - twos[0][1]
        if (dr, dc) == (0, 0):
            errs.append("marker vector is zero")
        marker_cells = set(twos + threes)
        motif_cells = set(fours)
        shifted_cells = []
        for r, c in fours:
            shifted = (r + dr, c + dc)
            if not (0 <= shifted[0] < h and 0 <= shifted[1] < w):
                errs.append("motif shifted copy is out of bounds")
            if shifted in marker_cells:
                errs.append("motif shifted copy overlaps a marker")
            if shifted in motif_cells:
                errs.append("motif shifted copy overlaps an original color-4 source")
            shifted_cells.append(shifted)
        if len(set(shifted_cells)) != len(shifted_cells):
            errs.append("two motif cells share the same shifted target")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # motif-4 cells but no 2/3 markers → no vector defined
        g[3][3] = 4; g[5][5] = 4; g[6][2] = 4
        return g
    if name == "zero_vector":
        # both markers at the same cell (impossible to draw) — emulate by placing them
        # at the same color → degenerate marker vector of length 0; rule has no shift
        g[2][2] = 2; g[2][2] = 3
        g[5][5] = 4; g[6][3] = 4
        return g
    if name == "no_motif":
        # markers define a vector but no color-4 cells → nothing to copy
        g[1][1] = 2
        g[3][3] = 3
        return g
    return g
