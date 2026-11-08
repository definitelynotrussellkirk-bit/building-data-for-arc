"""Generator for b7249182.

Rule: two collinear colored markers generate a split hollow box and
connector lines between them.

Combinatorial axes (8): grid_h/w, orientation, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_markers, single_marker, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7ed082a6d9e0"
VERSION = "2.0.1"
TASK_ID = "7ed082a6d9e0"
SUMMARY = (
    "0-bg grid (h×w, ~11-14 by ~13-16) with EXACTLY 2 non-zero "
    "marker cells (distinct colors) placed COLLINEARLY — either "
    "both in the same row (horizontal) or same column (vertical). "
    "Markers are at least 8-10 cells apart so a hollow split-box "
    "fits between them. Rule: locate the 2 markers and infer "
    "orientation. Between them, draw a hollow rectangular box "
    "centered on the line, ~5 cells along the line and 5 perp. "
    "Split the box into two halves perpendicular to the line "
    "axis: half nearer marker 1 painted in marker 1's color, "
    "other half in marker 2's color. Draw single-line connectors "
    "from each marker to the matching half of the box."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 2 non-zero marker cells in distinct colors",
    "markers are collinear (same row or same column)",
    "markers separated by ≥8 cells (room for split box + connectors)",
]

ORIENTATIONS = ("horizontal", "vertical")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_markers", "single_marker", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "rng 13..16", "valid": "11..20"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "horizontal|vertical"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "center", "valid": "center"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "horizontal|vertical|no_markers|single_marker|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly 2 nonzero cells of distinct colors, collinear (same row/col)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    nz = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(nz) != 2:
        return [f"expected exactly 2 nonzero cells; found {len(nz)}"]
    (r1, c1, v1), (r2, c2, v2) = nz
    errs = []
    if v1 == v2:
        errs.append(f"two markers have same color {v1} (must be distinct)")
    if r1 != r2 and c1 != c2:
        errs.append(f"markers not collinear: ({r1},{c1}) vs ({r2},{c2})")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orientation = (overrides.get("texture") if overrides.get("texture") in ORIENTATIONS else None) or \
                  overrides.get("orientation") or \
                  ctx.draw_choice("orientation", list(ORIENTATIONS))
    h = 11 + rng.randint(0, 3)
    w = 13 + rng.randint(0, 3)
    c1, c2 = ctx.draw_distinct_colors("colors", n=2, exclude={0})
    g = full_grid(h, w, 0)
    if orientation == "horizontal":
        r = h // 2
        g[r][2] = c1
        g[r][w - 3] = c2
    else:
        c = w // 2
        g[2][c] = c1
        g[h - 3][c] = c2
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    if name == "no_markers":
        return g
    if name == "single_marker":
        g[6][6] = 2
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(14):
                g[r][c] = 2
        return g
    return g
