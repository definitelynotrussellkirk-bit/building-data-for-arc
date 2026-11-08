"""Generator for arc_puzzle_bank_21_set23_s:S23_E5.

Rule: each tile's majority nonzero color becomes one macro-grid cell.

Combinatorial axes (8): grid_h, grid_w, palette_kind, tile_rows, tile_cols,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_majority, single_color_tiles, empty_tiles.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.lattice import assemble_tiles, blank_tile

GENERATOR_ID = "15949bcd466a"
# 1.3.0: tighten the normal path back to the canonical 5x5 / 2x2
# lattice.  The previous version varied tile_rows/tile_cols/tile size so much
# that generated grid area drifted from the canonical task, even though the
# underlying majority-color rule was right.
VERSION = "1.3.0"
TASK_ID = "15949bcd466a"
SUMMARY = "Each tile's majority nonzero color becomes one macro-grid cell."

INVARIANTS = [
    "divider color is 9",
    "tiles are 2x2, uniform size per grid",
    "each tile has a strict nonzero-color majority (random color, varied count)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_majority", "single_color_tiles", "empty_tiles")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "tile_rows":      {"type": "int", "default": "2", "valid": "2"},
    "tile_cols":      {"type": "int", "default": "2", "valid": "2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "majority_count": {"type": "int", "default": "3", "valid": "3..4"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8"},
    "position_bias":  {"type": "str", "default": "tile_grid_majority",
                       "valid": "tile_grid_majority"},
    "n_distinct_colors": {"type": "int", "default": "8", "valid": "8"},
    "density":        {"type": "str", "default": "tiles", "valid": "tiles"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # Canonical train inputs are 5x5: a 2x2 macro lattice of 2x2 tiles
    # separated by one row/col of divider color 9.  Keep the normal generator
    # on that support; diversity should come from tile contents/majorities, not
    # a different lattice size.
    rows = ctx.draw_int("tile_rows", 2, 2)
    cols = ctx.draw_int("tile_cols", 2, 2)
    rng = ctx.draw_rng("layout")
    # Canonical tile size is 2x2, yielding the 5x5 overall input.
    ts = 2
    n_cells = ts * ts
    cells = [(r, c) for r in range(ts) for c in range(ts)]
    # Strict majority: main gets > half the placed nonzero cells.
    maj = max(2, (n_cells // 2) + 1)
    tiles = []
    for r in range(rows):
        row = []
        for c in range(cols):
            tile = blank_tile(ts, ts)
            main = rng.randint(1, 8)
            # how many main cells (>= maj so it strictly dominates)
            n_main = rng.randint(maj, n_cells)
            chosen = cells[:]
            rng.shuffle(chosen)
            for rr, cc in chosen[:n_main]:
                tile[rr][cc] = main
            # fill some remaining cells with distinct minority colors, each
            # strictly fewer than n_main (placed singly so no tie with main)
            rest = chosen[n_main:]
            others = [x for x in range(1, 9) if x != main]
            rng.shuffle(others)
            for i, (rr, cc) in enumerate(rest):
                if rng.random() < 0.6:
                    tile[rr][cc] = others[i % len(others)]
            row.append(tile)
        tiles.append(row)
    return assemble_tiles(tiles)


def _draw_from_degenerate(name, rng):
    rng_ = __import__("random").Random(0)
    if name == "no_majority":
        # each tile has equal counts of two colors → no majority, rule undefined
        cells = [(r, c) for r in range(3) for c in range(3)]
        tiles = []
        for r in range(2):
            row = []
            for c in range(3):
                tile = blank_tile(3, 3)
                chosen = cells[:]
                rng_.shuffle(chosen)
                for i, (rr, cc) in enumerate(chosen[:8]):
                    tile[rr][cc] = (1 + ((r * 3 + c) % 8)) if i < 4 else (1 + ((r * 3 + c + 1) % 8))
                row.append(tile)
            tiles.append(row)
        return assemble_tiles(tiles)
    if name == "single_color_tiles":
        # all tiles uniformly the same color → macro grid is monochrome, no contrast
        tiles = []
        for r in range(2):
            row = []
            for c in range(3):
                tile = blank_tile(3, 3)
                for rr in range(3):
                    for cc in range(3): tile[rr][cc] = 4
                row.append(tile)
            tiles.append(row)
        return assemble_tiles(tiles)
    if name == "empty_tiles":
        # all tiles empty → no nonzero majority anywhere
        tiles = [[blank_tile(3, 3) for _ in range(3)] for _ in range(2)]
        return assemble_tiles(tiles)
    return blank_tile(3, 3)


def self_check(grid, *, difficulty=None, meta=None):
    """Canonical 5x5 lattice: 2x2 tiles separated by divider color 9.

    Each 2x2 tile must have a strict nonzero majority, so the macro-cell
    target is unambiguous.
    """
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    if (h, w) != (5, 5):
        return [f"expected canonical 5x5 lattice, got {h}x{w}"]
    if any(grid[2][c] != 9 for c in range(5)) or any(grid[r][2] != 9 for r in range(5)):
        errs.append("row 2 and column 2 must be divider color 9")
    tile_bounds = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for tr, tc in tile_bounds:
        vals = [grid[r][c] for r in range(tr, tr + 2) for c in range(tc, tc + 2) if grid[r][c] != 0]
        if not vals:
            errs.append(f"tile at {tr},{tc} has no nonzero majority")
            continue
        counts = {v: vals.count(v) for v in set(vals)}
        if max(counts.values()) <= len(vals) / 2:
            errs.append(f"tile at {tr},{tc} has no strict majority: {counts}")
    return errs
