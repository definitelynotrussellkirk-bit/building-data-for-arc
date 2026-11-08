"""Generator for arc_puzzle_bank_21_set23_s:S23_M4 — find the odd tile under rotation.

Rule (verified from canonical Racket): full rows/cols of colour 9 split the grid
into a LATTICE of tiles. Each tile's occupancy is reduced to its canonical
rotation (lexmin over the 4 rotations). All but one tile share a canonical shape;
the ODD tile's shape is unique. Output is a 1xN one-hot row (N = tile count, row
major) with colour 8 at the odd tile's index.

The previous body was the generic scatter template; with no colour-9 dividers the
whole grid was a single tile, so the output was always the 1x1 one-hot [[8]]
(distinct_out=1). This rewrite CONSTRUCTS a row of tiles separated by colour-9
columns: N-1 are rotations of a base shape and exactly one is a different shape.

Axes: tile size, tile count, base/odd shapes, odd position, rotations.
Degenerates: single_tile, all_same, two_odd.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7c105b75673c"
VERSION = "2.3.0"
TASK_ID = "7c105b75673c"

SUMMARY = ("Tiles separated by colour-9 columns: all but one are rotations of a common shape, "
           "one is different. The rule outputs a 1xN one-hot (colour 8) at the odd tile's index. "
           "Tile size/count, the shapes and the odd position vary.")

INVARIANTS = [
    "tiles are separated by full-height colour-9 divider columns",
    "N-1 tiles are rotations of one base occupancy; exactly one (the odd) differs",
    "the odd tile has a different cell count, so its canonical rotation is unique",
]

DEGENERATE_TEXTURES = ("single_tile", "all_same", "two_odd")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "tile_s":     {"type": "int", "default": "rng 3..4 (square tile)", "valid": "2..5"},
    "n_tiles":    {"type": "int", "default": "4-6 easy / 7-10 hard", "valid": "3..10"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|single_tile|all_same|two_odd"},
}


def _canon_occ(cells, s):
    """Canonical rotation signature for an s x s tile occupancy."""
    variants = []
    cur = set(cells)
    for _ in range(4):
        variants.append(tuple(sorted(cur)))
        cur = _rot90(cur, s)
    return min(variants)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the full teaching invariant: one odd tile under rotation."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors: list[str] = []
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not dividers:
        return ["expected ≥1 full-height color-9 divider column; found none"]

    bounds = []
    prev = -1
    for c in dividers + [w]:
        if c - prev - 1 > 0:
            bounds.append((prev + 1, c))
        prev = c
    if len(bounds) < 3:
        errors.append(f"expected at least 3 tiles, found {len(bounds)}")
    if any((c1 - c0) != h for c0, c1 in bounds):
        errors.append("tiles must be square and match grid height")

    signatures = []
    for c0, c1 in bounds:
        cells = {(r, c - c0) for r in range(h) for c in range(c0, c1)
                 if grid[r][c] not in (0, 9)}
        if not cells:
            errors.append(f"blank tile at columns {c0}..{c1 - 1}")
        signatures.append(_canon_occ(cells, h))
    counts = {sig: signatures.count(sig) for sig in set(signatures)}
    if len(counts) != 2 or sorted(counts.values()) != [1, len(signatures) - 1]:
        errors.append("expected exactly one rotation-class singleton and one majority class")
    return errors


def _rot90(cells, s):
    return {(c, s - 1 - r) for (r, c) in cells}


def _rand_occ(rng, s, k):
    """A random occupancy of k cells in an s x s tile (k>=1)."""
    spots = [(r, c) for r in range(s) for c in range(s)]
    return set(rng.sample(spots, max(1, min(k, len(spots)))))


def _paint_tile(g, cells, r0, c0, color):
    for (r, c) in cells:
        g[r0 + r][c0 + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        s = ctx.draw_int("tile_s", 3, 3); n = ctx.draw_int("n_tiles", 4, 6)
    elif difficulty == "hard":
        s = ctx.draw_int("tile_s", 2, 3); n = ctx.draw_int("n_tiles", 7, 10)
    else:
        s = ctx.draw_int("tile_s", 2, 4); n = ctx.draw_int("n_tiles", 4, 8)
    while n * s + (n - 1) > 30:                 # keep total width <= 30
        s -= 1
    rng = ctx.draw_rng("layout")

    # base shape (kb cells) and an odd shape with a DIFFERENT cell count
    kb = rng.randint(2, s * s - 1)
    base = _rand_occ(rng, s, kb)
    ko = kb
    while ko == kb:
        ko = rng.randint(1, s * s)
    odd = _rand_occ(rng, s, ko)

    odd_idx = rng.randint(0, n - 1)
    h = s
    w = n * s + (n - 1)                       # tiles + 1-wide colour-9 dividers
    g = full_grid(h, w, 0)
    for i in range(n):
        c0 = i * (s + 1)
        if i == odd_idx:
            cells = odd
        else:
            cells = base
            for _ in range(rng.randint(0, 3)):  # a random rotation of the base
                cells = _rot90(cells, s)
        _paint_tile(g, cells, 0, c0, rng.choice([1, 2, 3, 4, 5, 6, 7]))
        if i < n - 1:                          # full-height colour-9 divider column
            for r in range(h):
                g[r][c0 + s] = 9
    return g


def _draw_from_degenerate(name, rng):
    s = 3
    if name == "single_tile":
        # one tile -> trivially unique -> 1x1 one-hot
        g = full_grid(s, s, 0)
        g[0][0] = 4; g[1][1] = 4
        return g
    n = 3
    h = s; w = n * s + (n - 1)
    g = full_grid(h, w, 0)
    base = {(0, 0), (1, 1), (2, 2)}
    odd = {(0, 0), (0, 1), (0, 2), (1, 1)}
    for i in range(n):
        c0 = i * (s + 1)
        if name == "two_odd" and i in (1, 2):
            cells = odd if i == 1 else {(0, 0), (0, 1)}   # two distinct odd tiles
        elif name == "all_same":
            cells = base                                  # every tile identical -> first wins
        else:
            cells = odd if i == 1 else base
        _paint_tile(g, cells, 0, c0, 3 + i)
        if i < n - 1:
            for r in range(h):
                g[r][c0 + s] = 9
    return g
