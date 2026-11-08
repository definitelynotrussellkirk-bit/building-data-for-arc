"""Generator for arc_puzzle_bank_21_set23_s:S23_E2.

Rule: tiles with nonzero main-diagonal corners receive an 8 center mark.

Combinatorial axes (8): grid_h, grid_w, palette_kind, tile_rows, tile_cols,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_diag_corners, all_diag_corners, single_tile.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.lattice import assemble_tiles, blank_tile

GENERATOR_ID = "bbd8360915fc"
VERSION = "1.4.1"  # keep normal inputs in the canonical {0,2,9} palette; color 8 is output-only
TASK_ID = "bbd8360915fc"
SUMMARY = "3×3 tiles in a 9-divided lattice; rule paints an 8 at center of every tile whose top-left AND bottom-right corner are nonzero (main-diagonal corners set)."

# Rivals: 'mark every tile center' refuted by ≥1 demo where some tile
# has only anti-diag corners (left unmarked). 'mark by anti-diagonal'
# refuted by ≥2 demos with anti-diagonal tiles staying unmarked.
# 'use tile color for mark' refuted by any demo (mark is always 8).
# 'mark only corners' refuted by any demo (mark is at center).
# 4 demos with varied corner patterns cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "divider color is 9",
    "tiles are 3x3",
    "some tiles have both top-left and bottom-right corners nonzero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_diag_corners", "all_diag_corners", "single_tile")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "tile_rows":      {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "tile_cols":      {"type": "int", "default": "rng 3..4", "valid": "1..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "diag_prob":      {"type": "float", "default": "0.55", "valid": "0.0..1.0"},
    "palette_size":   {"type": "int", "default": "rng 4..8", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "tile_grid",
                       "valid": "tile_grid"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..8", "valid": "1..9"},
    "density":        {"type": "str", "default": "tiles", "valid": "tiles"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        rows = ctx.draw_int("tile_rows", 2, 3)
        cols = ctx.draw_int("tile_cols", 2, 3)
    elif difficulty == "hard":
        rows = ctx.draw_int("tile_rows", 4, 5)
        cols = ctx.draw_int("tile_cols", 4, 6)
    else:
        rows = ctx.draw_int("tile_rows", 3, 4)
        cols = ctx.draw_int("tile_cols", 3, 5)
    rng = ctx.draw_rng("layout")
    tiles = []
    palette = [2]  # canonical inputs use color 2 for tile marks; 8 is reserved for output centers
    for r in range(rows):
        row = []
        for c in range(cols):
            tile = blank_tile(3, 3)
            color = palette[rng.randint(0, len(palette) - 1)]
            # Random per-tile decision: main-diagonal corners set?
            main_diag = rng.random() < 0.5
            if main_diag:
                tile[0][0] = color
                tile[2][2] = color
            # Optionally also place anti-diagonal cells (rule ignores them).
            if rng.random() < 0.4:
                anti_color = 2
                tile[0][2] = anti_color
                if rng.random() < 0.5:
                    tile[2][0] = anti_color
            # Optionally add edge cells (rule ignores them).
            if rng.random() < 0.3:
                tile[0][1] = rng.choice(palette)
            if rng.random() < 0.3:
                tile[1][0] = rng.choice(palette)
            if rng.random() < 0.3:
                tile[1][2] = rng.choice(palette)
            if rng.random() < 0.3:
                tile[2][1] = rng.choice(palette)
            row.append(tile)
        tiles.append(row)
    _ensure_mixed_main_diag_tiles(tiles, rng, palette)
    return assemble_tiles(tiles)


def _has_main_diag(tile):
    return tile[0][0] != 0 and tile[2][2] != 0


def _ensure_mixed_main_diag_tiles(tiles, rng, palette):
    """Keep the normal path away from the no/all-positive degenerates."""
    flat = [tile for row in tiles for tile in row]
    if not flat:
        return
    positives = [tile for tile in flat if _has_main_diag(tile)]
    if not positives:
        tile = flat[0]
        color = rng.choice(palette)
        tile[0][0] = color
        tile[2][2] = color
        positives = [tile]
    if len(positives) == len(flat) and len(flat) > 1:
        tile = flat[-1]
        tile[0][0] = 0
        tile[2][2] = 0


def _draw_from_degenerate(name, rng):
    if name == "no_diag_corners":
        # no tile has main-diagonal corners both set → rule marks nothing
        tiles = []
        for r in range(2):
            row = []
            for c in range(3):
                tile = blank_tile(3, 3)
                color = 1 + ((r * 3 + c) % 8)
                tile[0][2] = color  # only anti-diagonal corner
                row.append(tile)
            tiles.append(row)
        return assemble_tiles(tiles)
    if name == "all_diag_corners":
        # every tile has main-diagonal corners → output marks every tile center (saturated)
        tiles = []
        for r in range(2):
            row = []
            for c in range(3):
                tile = blank_tile(3, 3)
                color = 1 + ((r * 3 + c) % 8)
                tile[0][0] = color
                tile[2][2] = color
                row.append(tile)
            tiles.append(row)
        return assemble_tiles(tiles)
    if name == "single_tile":
        # 1×1 tile grid → no per-tile structure to compare
        tile = blank_tile(3, 3)
        tile[0][0] = 4; tile[2][2] = 4
        return assemble_tiles([[tile]])
    return blank_tile(3, 3)

def _lattice_tiles(grid):
    h, w = len(grid), len(grid[0])
    div_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    row_bounds = []
    prev = -1
    for r in div_rows + [h]:
        if r - prev - 1 > 0:
            row_bounds.append((prev + 1, r))
        prev = r
    col_bounds = []
    prev = -1
    for c in div_cols + [w]:
        if c - prev - 1 > 0:
            col_bounds.append((prev + 1, c))
        prev = c
    return [[ [grid[r][c0:c1] for r in range(r0, r1)]
              for c0, c1 in col_bounds]
            for r0, r1 in row_bounds]


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    tiles = _lattice_tiles(grid)
    flat = [tile for row in tiles for tile in row]
    if not flat:
        return ["expected at least one 3x3 tile"]
    bad_shapes = [f"{len(t)}x{len(t[0]) if t else 0}" for t in flat
                  if len(t) != 3 or any(len(row) != 3 for row in t)]
    if bad_shapes:
        errors.append(f"all tiles must be 3x3; saw {bad_shapes[:3]}")
        return errors
    pos = sum(1 for tile in flat if _has_main_diag(tile))
    if pos == 0:
        errors.append("normal path must include at least one tile with both main-diagonal corners set")
    if pos == len(flat) and len(flat) > 1:
        errors.append("normal path must include at least one negative tile without both main-diagonal corners")
    if any(v < 0 or v > 9 for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    if any(v not in (0, 2, 9) for row in grid for v in row):
        errors.append("normal input should use only background 0, tile color 2, and divider 9")
    return errors

