"""Generator for arc_puzzle_bank_21_set23_s:S23_E4.

The strongest color-2 source motif is copied as 8 into the color-3 target tile.

Combinatorial axes (8): tile_rows, tile_cols, palette_kind, src_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_source, no_target, no_divider.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.lattice import assemble_tiles, blank_tile

GENERATOR_ID = "4a3ababcaceb"
VERSION = "2.0.1"
TASK_ID = "4a3ababcaceb"
SUMMARY = (
    "Grid laid out as a TILE LATTICE: rows×cols (~2-3 × "
    "3-4) tiles of 3×3 cells separated by color-9 "
    "(maroon) divider lines into a regular grid. "
    "Background of each tile is 0. EXACTLY ONE tile is "
    "the SOURCE — it contains 4-6 color-2 (red) cells "
    "in a random pattern; this is the strongest "
    "color-2 motif by count. EXACTLY ONE other tile is "
    "the TARGET — it contains a single color-3 (green) "
    "cell at its center (1, 1). Remaining tiles may "
    "contain a few stray non-{2, 3, 9} decoy cells at "
    "corners. Rule: find the SOURCE tile (the one with "
    "the most color-2 cells) and the TARGET tile (the "
    "one containing color 3). COPY the source's "
    "color-2 cell pattern into the target tile at the "
    "same intra-tile offsets, painted in COLOR 8 "
    "(cyan). Source tile, dividers, and decoys stay. "
    "Net: the target tile gets a cyan replica of the "
    "source's motif shape."
)

INVARIANTS = [
    "divider color is 9",
    "one tile has the most color-2 cells",
    "exactly one tile contains color 3 as the target marker",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_source", "no_target", "no_divider")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "tile_rows":      {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "tile_cols":      {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "src_size":       {"type": "int", "default": "rng 4..6", "valid": "3..9"},
    "palette_size":   {"type": "int", "default": "rng 5..6", "valid": "4..8"},
    "position_bias":  {"type": "str", "default": "tile_lattice_with_src_target",
                       "valid": "tile_lattice_with_src_target"},
    "n_distinct_colors": {"type": "int", "default": "rng 5..6", "valid": "4..8"},
    "density":        {"type": "str", "default": "dense", "valid": "dense"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        rows = ctx.draw_int("tile_rows", 2, 2)
        cols = ctx.draw_int("tile_cols", 3, 3)
    elif difficulty == "hard":
        rows = ctx.draw_int("tile_rows", 3, 3)
        cols = ctx.draw_int("tile_cols", 4, 4)
    else:
        rows = ctx.draw_int("tile_rows", 2, 3)
        cols = ctx.draw_int("tile_cols", 3, 4)
    rng = ctx.draw_rng("layout")
    total = rows * cols
    src_idx, tgt_idx = rng.sample(range(total), 2)
    src_cells = rng.sample([(r, c) for r in range(3) for c in range(3)], rng.randint(4, 6))
    tiles = []
    for r in range(rows):
        row = []
        for c in range(cols):
            idx = r * cols + c
            tile = blank_tile(3, 3)
            if idx == src_idx:
                for rr, cc in src_cells:
                    tile[rr][cc] = 2
            elif idx == tgt_idx:
                tile[1][1] = 3
            else:
                for rr, cc in rng.sample([(0, 0), (0, 2), (2, 0), (2, 2)], rng.randint(0, 1)):
                    tile[rr][cc] = rng.choice([4, 5, 6, 7, 8])
            row.append(tile)
        tiles.append(row)
    return assemble_tiles(tiles)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify tile-lattice source/target invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    problems = []
    flat = [v for row in grid for v in row]
    if 9 not in flat:
        problems.append("no color-9 dividers found")
    count3 = flat.count(3)
    if count3 != 1:
        problems.append(f"expected exactly 1 color-3 target cell, found {count3}")
    count2 = flat.count(2)
    if count2 < 1:
        problems.append("no color-2 source cells found")
    return problems


def _draw_from_degenerate(name, rng):
    if name == "no_source":
        # tile lattice with target but no color-2 source motif
        tiles = []
        for r in range(2):
            row = []
            for c in range(3):
                tile = blank_tile(3, 3)
                if r == 0 and c == 1:
                    tile[1][1] = 3
                row.append(tile)
            tiles.append(row)
        return assemble_tiles(tiles)
    if name == "no_target":
        # tile lattice with source but no color-3 target marker
        tiles = []
        for r in range(2):
            row = []
            for c in range(3):
                tile = blank_tile(3, 3)
                if r == 0 and c == 0:
                    for rr, cc in [(0, 0), (1, 1), (2, 2)]:
                        tile[rr][cc] = 2
                row.append(tile)
            tiles.append(row)
        return assemble_tiles(tiles)
    if name == "no_divider":
        # source + target but no color-9 divider lattice → no tile structure
        from puzzle_generators.helpers.grid import full_grid
        g = full_grid(7, 11, 0)
        for r, c in [(0, 0), (1, 1), (2, 2)]:
            g[r][c] = 2
        g[5][8] = 3
        return g
    return blank_tile(3, 3)
