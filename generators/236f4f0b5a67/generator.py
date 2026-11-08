"""Generator for arc_puzzle_bank_21_set12_bundle:hard_l15 — connect 5 colored markers around 5-walls.

Rule: find positions of colors 1, 2, 3, 4, 6; BFS shortest path between
consecutive pairs (avoiding color-5 walls); paint background cells along the
combined path with color 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_walls (degenerate-easy: BFS is unobstructed Manhattan
path, walls don't matter), markers_in_line (all 5 markers collinear →
the path collapses to a 1D segment, no branching), missing_marker
(only 4 colors present → "consecutive pair" loop has nothing to
connect for the 5th).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "236f4f0b5a67"
VERSION = "1.1.1"
TASK_ID = "236f4f0b5a67"

SUMMARY = "5 colored markers + sparse 5-walls; consecutive markers connected by BFS shortest path."

INVARIANTS = [
    "background is 0",
    "exactly 5 single-cell markers in colors 1, 2, 3, 4, 6",
    "0-3 sparse color-5 wall cells",
    "all markers reachable from each other through non-wall cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "markers_in_line", "missing_marker")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "n_walls":        {"type": "int", "default": "rng 0..3", "valid": "0..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "five_markers_with_walls",
                       "valid": "five_markers_with_walls"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one cell each for colors 1,2,3,4,6 (the markers); optional color-5 walls."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    marker_colors = (1, 2, 3, 4, 6)
    for mc in marker_colors:
        count = sum(1 for r in range(h) for c in range(w) if grid[r][c] == mc)
        if count == 0:
            return errors  # degenerate missing_marker — allowed
        if count != 1:
            errors.append(f"color {mc} appears {count} times (expected exactly 1 marker)")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        n_walls = ctx.draw_int("n_walls", 0, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 16)
        n_walls = ctx.draw_int("n_walls", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n_walls = ctx.draw_int("n_walls", 0, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        markers = []
        ok = True
        for color in [1, 2, 3, 4, 6]:
            placed = False
            for _ in range(120):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0: continue
                if any(abs(r - mr) + abs(c - mc) < 2 for mr, mc in markers): continue
                g[r][c] = color
                markers.append((r, c))
                placed = True; break
            if not placed:
                ok = False; break
        if not ok:
            continue
        for _ in range(n_walls):
            for _t in range(40):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0: continue
                if any(abs(r - mr) + abs(c - mc) <= 1 for mr, mc in markers): continue
                g[r][c] = 5
                break
        return g
    raise ValueError("could not realize hard_l15 layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_walls":
        # No walls — BFS is unobstructed; rule reduces to a Manhattan
        # path between consecutive markers (no decision points).
        markers = [(1, 1), (1, 9), (5, 5), (8, 2), (8, 10)]
        for (r, c), color in zip(markers, [1, 2, 3, 4, 6]):
            g[r][c] = color
        return g
    if name == "markers_in_line":
        # All 5 markers on the same row — combined path collapses to
        # a 1D segment; no rule branching (corners) emerges.
        for c, color in zip([1, 3, 5, 7, 10], [1, 2, 3, 4, 6]):
            g[5][c] = color
        return g
    if name == "missing_marker":
        # Only 4 colors present — rule's "consecutive pair" loop
        # cannot connect the 5th; output is partially defined.
        markers = [(1, 1), (1, 9), (5, 5), (8, 2)]
        for (r, c), color in zip(markers, [1, 2, 3, 4]):
            g[r][c] = color
        return g
    return g
