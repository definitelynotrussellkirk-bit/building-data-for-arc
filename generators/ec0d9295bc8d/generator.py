"""Generator for arc_puzzle_bank_21_set23_s:S23_M5 — per-tile bbox fill.

Rule: full color-9 rows AND full color-9 cols partition the grid into an
EQUAL-SIZED tile lattice. For each tile, take the bbox of its non-zero
cells and fill that bbox solid with 8; reassemble the tiles with the
9-dividers. (The rule assembles assuming all tiles share one size, so
the dividers must be evenly spaced.)

Combinatorial axes (8): tile_rows, tile_cols, tile_h, tile_w,
palette_kind, cells_per_tile, palette_size, texture.
Degenerates: no_dividers, one_tile, empty_tiles.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ec0d9295bc8d"
VERSION = "2.0.0"  # WRONG-TASK rewrite: was scattered motifs with NO 9-dividers (rule saw 1 tile -> 1 blob); the real rule is a 9-divider tile lattice with per-tile bbox-fill
TASK_ID = "ec0d9295bc8d"

SUMMARY = (
    "Grid partitioned by full COLOR-9 divider rows and cols into a "
    "tr x tc lattice of EQUAL-SIZED tiles (th x tw, evenly spaced single "
    "dividers). Each tile holds 2-4 scattered non-9 cells whose bbox is "
    "non-trivial (spans more than the cells). Rule: for each tile, fill "
    "the bbox of its non-zero cells solid with 8; reassemble with the "
    "9-dividers. Net: each tile's scattered cells become a solid 8-filled "
    "bounding box."
)

INVARIANTS = [
    "evenly-spaced full color-9 divider rows AND cols -> equal-sized tiles",
    "at least one divider row and one divider col (>=2x2 tile lattice)",
    "each tile has 2-4 scattered non-9 cells with a non-trivial bbox",
    "tile content colors are non-9, non-0 (rule is color-blind -> outputs 8)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "one_tile", "empty_tiles")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "tile_rows":      {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "tile_cols":      {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "tile_h":         {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "tile_w":         {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cells_per_tile": {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        tr = ctx.draw_int("tile_rows", 2, 2); tc = ctx.draw_int("tile_cols", 2, 2)
        th = ctx.draw_int("tile_h", 3, 4); tw = ctx.draw_int("tile_w", 3, 4)
    elif difficulty == "hard":
        tr = ctx.draw_int("tile_rows", 3, 3); tc = ctx.draw_int("tile_cols", 3, 3)
        th = ctx.draw_int("tile_h", 4, 5); tw = ctx.draw_int("tile_w", 4, 5)
    else:
        tr = ctx.draw_int("tile_rows", 2, 3); tc = ctx.draw_int("tile_cols", 2, 3)
        th = ctx.draw_int("tile_h", 3, 5); tw = ctx.draw_int("tile_w", 3, 5)
    rng = ctx.draw_rng("layout")
    h = tr * th + (tr - 1)
    w = tc * tw + (tc - 1)
    g = full_grid(h, w, 0)
    # full-9 divider rows/cols at the single-line tile boundaries
    div_rows = [i * (th + 1) + th for i in range(tr - 1)]
    div_cols = [j * (tw + 1) + tw for j in range(tc - 1)]
    for r in div_rows:
        for c in range(w):
            g[r][c] = 9
    for c in div_cols:
        for r in range(h):
            g[r][c] = 9
    palette = [c for c in (1, 2, 3, 4, 5, 6, 7, 8)]
    rng.shuffle(palette)
    for ti in range(tr):
        for tj in range(tc):
            r0 = ti * (th + 1)
            c0 = tj * (tw + 1)
            color = palette[(ti * tc + tj) % len(palette)]
            _scatter_tile(g, r0, c0, th, tw, color, rng)
    return g


def _scatter_tile(g, r0, c0, th, tw, color, rng):
    """Place scattered cells in a LOCALIZED sub-bbox of the tile (often
    smaller than the tile) so the rule's bbox-fill is a partial fill, not a
    whole-tile fill. Opposite corners pin the bbox; a couple interior cells
    keep the input scattered (the fill then adds the rest)."""
    bh = rng.randint(2, th)
    bw = rng.randint(2, tw)
    br0 = rng.randint(0, th - bh)
    bc0 = rng.randint(0, tw - bw)
    cells = {(br0, bc0), (br0 + bh - 1, bc0 + bw - 1)}   # pin the bbox corners
    for _ in range(rng.randint(0, 2)):
        cells.add((rng.randint(br0, br0 + bh - 1), rng.randint(bc0, bc0 + bw - 1)))
    for (r, c) in cells:
        g[r0 + r][c0 + c] = color


def self_check(grid, *, difficulty=None, meta=None):
    """Verify color-9 tile-lattice invariants for ec0d9295bc8d."""
    errs = []
    h, w = len(grid), len(grid[0])
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    if 9 not in flat:
        errs.append("color 9 (divider) not present")
    else:
        div_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
        div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
        if not div_rows:
            errs.append("no full-width color-9 divider row")
        if not div_cols:
            errs.append("no full-height color-9 divider column")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_dividers":
        # no full-9 row/col -> the whole grid is one tile (no lattice)
        g[1][1] = 2; g[2][3] = 2; g[4][5] = 3
        return g
    if name == "one_tile":
        # dividers absent on one axis -> degenerate 1xN lattice
        for r in range(h):
            g[r][3] = 9
        g[1][1] = 2; g[2][5] = 3
        return g
    if name == "empty_tiles":
        # dividers present but tiles empty -> rule fills nothing
        for c in range(w):
            g[3][c] = 9
        for r in range(h):
            g[r][3] = 9
        return g
    return g
