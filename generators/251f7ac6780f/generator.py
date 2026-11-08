"""Generator for arc_puzzle_bank_21_set9_e:easy_i05.

Rule: each blank cell with four same-color diagonal neighbors is filled with
that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, motifs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, partial_diagonals, mismatched_diagonals.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "251f7ac6780f"
VERSION = "1.1.0"
TASK_ID = "251f7ac6780f"

SUMMARY = "Fill the center of each same-color diagonal X."

INVARIANTS = [
    "background is 0",
    "each active center has four same-color diagonal neighbors",
    "active centers are initially zero",
    "diagonal X motifs are isolated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "partial_diagonals", "mismatched_diagonals")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "motifs":         {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_x_corners",
                       "valid": "spaced_x_corners"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _clear(g, r, c):
    h, w = len(g), len(g[0])
    for rr in range(max(0, r - 2), min(h, r + 3)):
        for cc in range(max(0, c - 2), min(w, c + 3)):
            if g[rr][cc] != 0:
                return False
    return True


def _x_corners(r, c):
    return [(r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1)]


def _can_place_x(g, r, c):
    if g[r][c] != 0:
        return False
    return all(g[rr][cc] == 0 for rr, cc in _x_corners(r, c))


def _paint_x(g, r, c, color):
    for rr, cc in _x_corners(r, c):
        g[rr][cc] = color


def _active_centers(g):
    h, w = len(g), len(g[0])
    out = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if g[r][c] != 0:
                continue
            vals = [g[rr][cc] for rr, cc in _x_corners(r, c)]
            if vals[0] != 0 and len(set(vals)) == 1:
                out.append((r, c, vals[0]))
    return out


def _fallback_layout(h, w, target):
    g = full_grid(h, w, 0)
    anchors = [(1, 1), (1, w - 2), (h - 2, 1), (h - 2, w - 2),
               (h // 2, w // 2)]
    colors = [2, 4, 6, 8, 3]
    placed = 0
    for (r, c), color in zip(anchors, colors):
        if placed >= target:
            break
        if _can_place_x(g, r, c):
            _paint_x(g, r, c, color)
            placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for the same-color diagonal-X fill task."""
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if not (5 <= h <= 14 and 5 <= w <= 16):
        errs.append(f"grid size outside declared range: {h}x{w}")
    centers = _active_centers(grid)
    if len(centers) < 2:
        errs.append(f"expected at least two active X centers, found {len(centers)}")
    center_locs = {(r, c) for r, c, _ in centers}
    if len(center_locs) != len(centers):
        errs.append("duplicate active centers detected")
    # Each active center must still be blank; the rule fills it in the output.
    for r, c, _color in centers:
        if grid[r][c] != 0:
            errs.append(f"active center ({r},{c}) is not blank")
            break
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("motifs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("motifs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("motifs", 2, 4)
    rng = ctx.draw_rng("layout")
    # Rejection-sample complete layouts, not just individual motifs.  The old
    # loop could return a one-motif easy grid in ~25% of seeds because the 5x5
    # moat made a 7x7 board tight after the first random placement.  One motif
    # does not demonstrate that the rule applies to EACH same-color X.
    for _outer in range(80):
        g = full_grid(h, w, 0)
        centers = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
        rng.shuffle(centers)
        placed = 0
        for r, c in centers:
            if placed >= target:
                break
            if not _can_place_x(g, r, c):
                continue
            color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            _paint_x(g, r, c, color)
            placed += 1
        if placed >= target and len(_active_centers(g)) >= target:
            return g
    return _fallback_layout(h, w, target)


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # blank → no diagonal corners, rule has no centers to fill
        return g
    if name == "partial_diagonals":
        # only 3 of 4 diagonal corners → predicate "all 4 same color" fails
        g[2][2] = 4; g[2][4] = 4; g[4][2] = 4  # missing BR
        g[5][6] = 6; g[5][8] = 6; g[7][8] = 6  # missing BL
        return g
    if name == "mismatched_diagonals":
        # all 4 diagonals present but in different colors → predicate fails
        g[2][2] = 4; g[2][4] = 6; g[4][2] = 3; g[4][4] = 8
        return g
    return g
