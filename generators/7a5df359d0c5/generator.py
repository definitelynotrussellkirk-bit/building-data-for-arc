"""Generator for arc_puzzle_bank_eighth_21_bundle:easy_52_markers_to_hollow_squares.

Rule: each interior singleton marker is expanded to a hollow 3x3 square.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, markers_at_edge, multi_cell_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7a5df359d0c5"
VERSION = "1.1.1"
TASK_ID = "7a5df359d0c5"
SUMMARY = "Interior singleton markers are expanded to hollow 3x3 squares."

INVARIANTS = [
    "background is 0",
    "each nonzero cell is an isolated interior marker",
    "markers have enough border margin for a 3x3 ring",
    "marker colors are distinct",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "markers_at_edge", "multi_cell_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_markers":      {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_interior_markers",
                       "valid": "spaced_interior_markers"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, all nonzero cells are isolated singletons not on the grid border."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no nonzero marker cells found")
        return errs
    for r, c in nonzero:
        # Must not be on border
        if r == 0 or r == h-1 or c == 0 or c == w-1:
            errs.append(f"marker at ({r},{c}) is on the grid border (needs ≥1 cell margin)")
            break
    for r, c in nonzero:
        # Must be isolated (no 4-connected nonzero neighbor)
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if 0<=nr<h and 0<=nc<w and grid[nr][nc] != 0:
                errs.append(f"marker at ({r},{c}) has adjacent nonzero at ({nr},{nc}); must be isolated")
                return errs
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
        n_markers = ctx.draw_int("n_markers", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n_markers = ctx.draw_int("n_markers", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        n_markers = ctx.draw_int("n_markers", 2, 4)
    colors = ctx.draw_distinct_colors("colors", n=n_markers, exclude={0})
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    centers: list[tuple[int, int]] = []
    for color in colors:
        for _ in range(100):
            r = rng.randint(1, h - 2)
            c = rng.randint(1, w - 2)
            if all(abs(r - rr) > 2 or abs(c - cc) > 2 for rr, cc in centers):
                centers.append((r, c))
                g[r][c] = color
                break
    if not centers:
        g[2][2] = colors[0]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # blank → no markers, rule has no effect
        return g
    if name == "markers_at_edge":
        # markers on grid border → 3x3 ring would extend off-grid
        g[0][3] = 4
        g[5][0] = 6
        g[h - 1][7] = 3
        return g
    if name == "multi_cell_markers":
        # adjacent cells form 2-cell components, not singletons → predicate fails
        g[2][3] = 4; g[2][4] = 4
        g[5][6] = 6; g[6][6] = 6
        return g
    return g
