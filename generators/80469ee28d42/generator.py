"""Generator for arc_puzzle_bank_next21:E11.

Rule: blank cells with four same-color diagonal neighbors are filled.

Combinatorial axes (8): grid_h, grid_w, palette_kind, motifs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, partial_diagonals, mismatched_diagonals.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "80469ee28d42"
VERSION = "1.1.1"
TASK_ID = "80469ee28d42"

SUMMARY = "Place separated diagonal X corners around empty centers."

INVARIANTS = [
    "background is 0",
    "each active motif has a zero center",
    "the four diagonal neighbors around each center share one nonzero color",
    "motifs are separated to keep centers unambiguous",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "partial_diagonals", "mismatched_diagonals")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 5..8", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "motifs":         {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_x_corners",
                       "valid": "spaced_x_corners"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 cell (r,c) with center=0 and all 4 diagonal neighbors same nonzero color."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            diag_vals = [grid[r - 1][c - 1], grid[r - 1][c + 1],
                         grid[r + 1][c - 1], grid[r + 1][c + 1]]
            if len(set(diag_vals)) == 1 and diag_vals[0] != 0:
                return []
    return ["expected ≥1 interior zero cell with all 4 diagonal neighbors same nonzero color; found none"]


_DIAGS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 5, 6)
        target = ctx.draw_int("motifs", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("motifs", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 5, 8)
        target = ctx.draw_int("motifs", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        cells = {(r + dr, c + dc) for dr, dc in _DIAGS}
        guard = {
            (rr, cc)
            for rr in range(max(0, r - 2), min(h, r + 3))
            for cc in range(max(0, c - 2), min(w, c + 3))
        }
        if guard & reserved:
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for rr, cc in cells:
            g[rr][cc] = color
        reserved.update(guard)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # blank → no diagonal corners, rule has no effect
        return g
    if name == "partial_diagonals":
        # only 3 of 4 diagonals → predicate fails
        g[1][2] = 4; g[1][4] = 4; g[3][2] = 4  # missing BR
        g[4][5] = 6; g[4][7] = 6; g[6][7] = 6  # missing BL
        return g
    if name == "mismatched_diagonals":
        # all 4 diagonals present but in different colors → predicate fails
        g[1][2] = 4; g[1][4] = 6; g[3][2] = 3; g[3][4] = 8
        return g
    return g
