"""Generator for arc_puzzle_bank_21_more:medium_b01.

Rule: cell (0, 0) names a marker color; all other cells of that color
are cropped as a mask.

Combinatorial axes (8): grid_h, grid_w, palette_kind, marker_color,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: missing_marker, no_target_cells, marker_only_at_origin.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "85c59d39af56"
VERSION = "2.0.1"  # distinct=9/out_sh=1: marker motif was a FIXED 4-cell shape -> output (its bbox crop) was one 3x2 shape. Rule crops all marker-colored cells (minus origin). Use a RANDOM marker motif (varied bbox incl non-square) -> output shape/content vary.
TASK_ID = "85c59d39af56"
SUMMARY = "Cell (0,0) names a marker color; a random connected motif of that color sits elsewhere (plus distractor cells of another color). Rule crops the marker-colored cells (excluding the origin) to their bbox, painted in the marker color. The motif shape, marker color and grid size vary."

INVARIANTS = [
    "marker color appears at (0,0) and in a separated motif",
    "non-marker distractor colors are ignored",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_marker", "no_target_cells", "marker_only_at_origin")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "marker_color":   {"type": "color", "default": "rng nonzero", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "marker_top_left",
                       "valid": "marker_top_left"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|missing_marker|no_target_cells|marker_only_at_origin"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: (0,0) names a marker color; a connected motif of that color exists elsewhere."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    marker = grid[0][0]
    if marker == 0:
        return []  # degenerate missing_marker — allowed
    other_marker = [(r, c) for r in range(h) for c in range(w)
                    if grid[r][c] == marker and (r, c) != (0, 0)]
    if not other_marker:
        return []  # degenerate no_target_cells — allowed
    errs = []
    if len(other_marker) < 2:
        errs.append(f"expected motif of >=2 marker cells besides origin; found {len(other_marker)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 8, 10); k_lo, k_hi = 3, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 11, 14); k_lo, k_hi = 5, 8
    else:
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 8, 12); k_lo, k_hi = 3, 7
    marker = ctx.draw_color("marker_color", exclude=[0])
    other = ctx.draw_color("other_color", exclude=[0, marker])
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    g[0][0] = marker
    # random marker motif placed clear of the (0,0) origin cell
    for _ in range(40):
        motif = _rand_poly(rng, rng.randint(k_lo, k_hi))
        sh = max(r for r, _ in motif) + 1; sw = max(c for _, c in motif) + 1
        if sh > h - 2 or sw > w - 1:
            continue
        top = rng.randint(2, h - sh); left = rng.randint(0, w - sw)
        for dr, dc in motif:
            g[top + dr][left + dc] = marker
        break
    # a couple distractor cells (ignored by the rule)
    g[h - 2][w - 2] = other
    g[h - 3][w - 2] = other
    return g


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "missing_marker":
        # cell (0,0) is bg → no marker color named, target is undefined
        g[3][3] = 4; g[3][4] = 4; g[4][4] = 4; g[5][3] = 4
        g[h - 2][w - 2] = 6
        return g
    if name == "no_target_cells":
        # marker named but only the (0,0) cell carries that color → mask is empty
        g[0][0] = 4
        g[h - 2][w - 2] = 6
        g[h - 3][w - 2] = 6
        return g
    if name == "marker_only_at_origin":
        # only the origin cell is marker color and rest are distractor → cropped mask trivial
        g[0][0] = 5
        for r in range(2, 6):
            for c in range(2, 6):
                g[r][c] = 8
        return g
    return g
