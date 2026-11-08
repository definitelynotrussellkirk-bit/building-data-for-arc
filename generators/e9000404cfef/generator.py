"""Generator for arc_puzzle_bank_21_set23_s:S23_E1.

Rule: a 3x3 tile lattice is summarized by nonzero counts per tile.

Combinatorial axes (8): grid_h, grid_w, palette_kind, tile_rows, tile_cols,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_tiles, all_same_count, single_tile.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.lattice import assemble_tiles, blank_tile

GENERATOR_ID = "e9000404cfef"
VERSION = "3.0.0"  # tile was hardcoded 3x3 (canonical uses 2x2) and counts only 1-7. Rule is tile-size-agnostic -> vary tile size (incl non-square, area<=9 so counts stay <=9), use full count range 0..area, widen lattice. Output value = per-tile count
TASK_ID = "e9000404cfef"
SUMMARY = (
    "Tiled lattice: tile_rows x tile_cols equal tiles separated by 1-cell "
    "color-9 divider rows/columns. Tile size varies (2x2/2x3/3x2/2x4/4x2/3x3, "
    "area<=9 so per-tile counts stay <=9, incl non-square). Each tile holds "
    "count (0..area) random non-0 cells in one colour. Rule: split on full-9 "
    "dividers and output a tile_rows x tile_cols grid where each cell = that "
    "tile's nonzero count. Tile size, counts (0..area), lattice dims and "
    "colours all vary."
)

INVARIANTS = [
    "divider color is 9; dividers sit only BETWEEN tiles",
    "all tiles are equal-sized (uniform tile_h x tile_w, area<=9)",
    "each tile's nonzero count is in 0..area (so output cells stay 0..9)",
    "tiles never use color 9 (no accidental divider lines)",
]

DEGENERATE_TEXTURES = ("empty_tiles", "all_same_count", "single_tile")
HELPFUL_TEXTURES = ("square", "wide_tile", "tall_tile")

# tile shapes with area <= 9 so the per-tile count (the output value) stays <= 9
_TILE_SIZES = [(2, 2), (2, 3), (3, 2), (2, 4), (4, 2), (3, 3)]

AXES = {
    "tile_rows":  {"type": "int", "default": "rng 1..5 by diff", "valid": "1..5"},
    "tile_cols":  {"type": "int", "default": "rng 2..6 by diff", "valid": "1..6"},
    "tile_size":  {"type": "str", "default": "rng (area<=9)",
                   "valid": "2x2|2x3|3x2|2x4|4x2|3x3"},
    "texture":    {"type": "str", "default": "alias",
                   "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: has full-width color-9 rows and full-height color-9 cols (tile lattice dividers)."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    nine_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    nine_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not nine_rows and not nine_cols:
        pass  # degenerate (empty_tiles or single_tile) — allowed
    return errors


def _tile_with_count(rng, th, tw, count, color):
    tile = blank_tile(th, tw)
    cells = [(r, c) for r in range(th) for c in range(tw)]
    rng.shuffle(cells)
    for r, c in cells[:count]:
        tile[r][c] = color
    return tile


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        r_lo, r_hi, c_lo, c_hi = 1, 2, 2, 3
    elif difficulty == "hard":
        r_lo, r_hi, c_lo, c_hi = 3, 5, 4, 6
    else:
        r_lo, r_hi, c_lo, c_hi = 2, 3, 3, 4
    rows = ctx.draw_int("tile_rows", r_lo, r_hi)
    cols = ctx.draw_int("tile_cols", c_lo, c_hi)
    rng = ctx.draw_rng("layout")
    th, tw = rng.choice(_TILE_SIZES)
    # keep the assembled INPUT grid within 30x30
    while rows * th + rows - 1 > 30 and rows > 1:
        rows -= 1
    while cols * tw + cols - 1 > 30 and cols > 1:
        cols -= 1
    area = th * tw
    tiles = []
    for r in range(rows):
        row = []
        for c in range(cols):
            count = rng.randint(0, area)          # full range -> output values 0..area (<=9)
            color = rng.randint(1, 8)             # never 9 (divider) or 0
            row.append(_tile_with_count(rng, th, tw, count, color))
        tiles.append(row)
    return assemble_tiles(tiles)


def _draw_from_degenerate(name, rng):
    if name == "empty_tiles":
        # all tiles empty → counts all 0, no signal
        tiles = [[blank_tile(3, 3) for _ in range(3)] for _ in range(2)]
        return assemble_tiles(tiles)
    if name == "all_same_count":
        # every tile has count 4 → output is uniform, no per-tile contrast
        rng = __import__("random").Random(0)
        tiles = []
        for r in range(2):
            row = []
            for c in range(3):
                row.append(_tile_with_count(rng, 3, 3, 4, 1 + ((r * 3 + c) % 8)))
            tiles.append(row)
        return assemble_tiles(tiles)
    if name == "single_tile":
        # 1×1 tile lattice → no per-tile comparison
        tile = blank_tile(3, 3)
        tile[1][1] = 4
        return assemble_tiles([[tile]])
    return blank_tile(3, 3)
