"""Generator for arc_puzzle_bank_21_set23_s:S23_M2 — OR-overlay of divider tiles.

Rule: color-9 forms FULL-ROW / FULL-COL dividers that split the grid into a
lattice of equal-size TILES. Each tile is a small color-2 pattern. The output
(tile-sized) is the OR-overlay of all tiles: cell (r,c) is 8 if ANY tile has a
nonzero at (r,c), else 0.

The old docstring ("multi-motif gallery pack ... vertical pack") was WRONG and
the generator scattered random colors {2..9} with no 9-dividers, so the rule
found no lattice (one tile = the whole grid) and just recolored everything to 8
(nc=9 vs canonical {0,2,9}). This rewrite builds the real structure: a lattice
of equal tiles separated by color-9 dividers, each tile a random color-2
pattern.

Combinatorial axes: tile dims, lattice shape (tile rows x cols), per-tile
color-2 patterns.
Degenerates: no_dividers, single_tile, empty_tiles.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "467d87cb509c"
VERSION = "2.0.1"  # WRONG-TASK ('gallery pack' docstring, nc=9): real rule splits the grid by color-9 full-row/col dividers into equal tiles and OR-overlays them to 8. Old gen scattered random colours with no dividers. Now a real 9-divider lattice of equal tiles, each a random color-2 pattern; colours {0,2,9}(+8 out).
TASK_ID = "467d87cb509c"
SUMMARY = (
    "0-bg grid: a lattice of equal-size TILES separated by color-9 full "
    "dividers (rows/cols). Each tile is a random color-2 pattern. Rule: "
    "OR-overlay all tiles -> a tile-sized output that is 8 where any tile has "
    "a nonzero cell, else 0. Colors are {0,2,9} (output adds 8)."
)

INVARIANTS = [
    "background is 0",
    "color-9 forms full-row and/or full-col dividers splitting equal tiles",
    "each tile is the same size",
    "input colors are a subset of {0,2,9}",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("no_dividers", "single_tile", "empty_tiles")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "tile_h":         {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "tile_w":         {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "tile_rows":      {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "tile_cols":      {"type": "int", "default": "rng 2..4", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "default",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_tile(rng, th, tw):
    # SPARSE pattern (<= ~half the cells) so the OR-overlay of several tiles
    # does not saturate to all-8 -> more distinct outputs.
    cells = [(r, c) for r in range(th) for c in range(tw)]
    k = rng.randint(1, max(1, (len(cells) + 1) // 2))
    return set(rng.sample(cells, k))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # Keep the tile COUNT low (2-4) so the OR-overlay stays non-saturated; use
    # LARGER tiles (more output cells) for more distinct OR-patterns.
    if difficulty == "easy":
        th = ctx.draw_int("tile_h", 2, 3); tw = ctx.draw_int("tile_w", 2, 3)
        nrt = ctx.draw_int("tile_rows", 1, 1); nct = ctx.draw_int("tile_cols", 2, 2)
    elif difficulty == "hard":
        th = ctx.draw_int("tile_h", 3, 4); tw = ctx.draw_int("tile_w", 3, 4)
        nrt = ctx.draw_int("tile_rows", 1, 2); nct = ctx.draw_int("tile_cols", 2, 2)
    else:
        th = ctx.draw_int("tile_h", 3, 4); tw = ctx.draw_int("tile_w", 3, 4)
        nrt = ctx.draw_int("tile_rows", 1, 1); nct = ctx.draw_int("tile_cols", 2, 3)
    if nrt * nct < 2:
        nct = 2

    H = nrt * th + (nrt - 1)
    W = nct * tw + (nct - 1)
    g = full_grid(H, W, 0)
    # divider rows/cols = full lines of 9
    for i in range(1, nrt):
        rr = i * (th + 1) - 1
        for c in range(W):
            g[rr][c] = 9
    for j in range(1, nct):
        cc = j * (tw + 1) - 1
        for r in range(H):
            g[r][cc] = 9
    # fill each tile with a random color-2 pattern.  Resample if the
    # cellwise OR saturates to all 8s; saturated outputs hide the aggregation
    # evidence and were a small but real degeneration in smoke samples.
    for _attempt in range(80):
        tile_sets = []
        union = set()
        for _i in range(nrt * nct):
            cells = _rand_tile(rng, th, tw)
            tile_sets.append(cells); union |= cells
        if len(union) < th * tw:
            break
    else:
        tile_sets[-1] = set(tile_sets[-1])
        tile_sets[-1].discard(next(iter(union)))
    ti = 0
    for i in range(nrt):
        for j in range(nct):
            top = i * (th + 1); left = j * (tw + 1)
            for (r, c) in tile_sets[ti]:
                g[top + r][left + c] = 2
            ti += 1
    return g



def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    h, w = len(grid), len(grid[0])
    div_rows = [r for r in range(h) if all(v == 9 for v in grid[r])]
    div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    def segments(n, divs):
        out = []; prev = -1
        for x in divs + [n]:
            if x - prev - 1 > 0:
                out.append((prev + 1, x))
            prev = x
        return out
    rows = segments(h, div_rows); cols = segments(w, div_cols)
    if len(rows) * len(cols) < 2:
        errors.append("expected at least two tiles separated by full 9-divider lines")
        return errors
    th = rows[0][1] - rows[0][0]; tw = cols[0][1] - cols[0][0]
    union = set()
    for r0, r1 in rows:
        for c0, c1 in cols:
            if r1 - r0 != th or c1 - c0 != tw:
                errors.append("tile lattice has unequal tile sizes")
            tile_cells = {(r - r0, c - c0) for r in range(r0, r1) for c in range(c0, c1) if grid[r][c] != 0}
            if not tile_cells:
                errors.append("empty tile would contribute no aggregation evidence")
            union |= tile_cells
    if len(union) >= th * tw:
        errors.append("tile OR union saturates the whole output tile")
    return errors

def _draw_from_degenerate(name, rng):
    rng = rng or __import__("random").Random(0)
    if name == "no_dividers":
        g = full_grid(3, 3, 0)
        g[0][0] = 2; g[1][1] = 2
        return g
    if name == "single_tile":
        g = full_grid(3, 3, 0)
        g[0][1] = 2; g[2][2] = 2
        return g
    if name == "empty_tiles":
        # dividers but no tile cells -> output all 0
        g = full_grid(3, 7, 0)
        for r in range(3):
            g[r][2] = 9; g[r][4] = 9
        return g
    return full_grid(3, 3, 0)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """input colors are subset of {0,2,9}; at least one 9 divider; at least one 2 tile cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    allowed = {0, 2, 9}
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in allowed:
                errors.append(f"unexpected color {grid[r][c]} at ({r},{c}); expected {{0,2,9}}")
                return errors
    has_nine = any(grid[r][c] == 9 for r in range(h) for c in range(w))
    if not has_nine:
        errors.append("no color-9 divider cells found")
    has_two = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_two:
        errors.append("no color-2 tile cells found")
    return errors
