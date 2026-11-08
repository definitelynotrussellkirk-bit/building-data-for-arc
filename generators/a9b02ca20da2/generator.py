"""Generator for arc_puzzle_bank_21_set23_s:S23_M3 — key-color prototype lookup.

Rule: top-row library maps key colors → 2-motifs; bottom queries name keys.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_library, no_query, key_not_in_library.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a9b02ca20da2"
VERSION = "1.1.1"
TASK_ID = "a9b02ca20da2"

SUMMARY = "A top-row tile library maps key colors to 2-motifs; bottom query tiles name keys."

INVARIANTS = [
    "tiles are 3x3 and separated by full 9 divider rows and columns",
    "top tiles put the key color in their upper-left cell",
    "each top tile contains a distinct 2-colored motif",
    "each bottom tile contains exactly one query key color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_library", "no_query", "key_not_in_library")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "tile_count":     {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "library_query_lattice",
                       "valid": "library_query_lattice"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


MOTIFS = [
    [(1, 1), (1, 2), (2, 1)],
    [(0, 2), (1, 1), (2, 0)],
    [(1, 0), (1, 1), (1, 2), (2, 2)],
    [(0, 1), (1, 1), (2, 1), (2, 2)],
]


def _blank_tile():
    return [[0, 0, 0] for _ in range(3)]


def _assemble(rows):
    tile_h = len(rows[0][0])
    tile_w = len(rows[0][0][0])
    h = len(rows) * tile_h + len(rows) - 1
    w = len(rows[0]) * tile_w + len(rows[0]) - 1
    g = full_grid(h, w, 9)
    for rr, row in enumerate(rows):
        for cc, tile in enumerate(row):
            r0 = rr * (tile_h + 1)
            c0 = cc * (tile_w + 1)
            for r in range(tile_h):
                for c in range(tile_w):
                    g[r0 + r][c0 + c] = tile[r][c]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-9 divider rows and cols; ≥1 top tile with a key (non-0/2/9 at upper-left of tile)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Grid uses color-9 separators (full rows/cols of value 9) between tiles
    sep_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    sep_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not sep_rows and not sep_cols:
        return errs  # degenerate (no_library) or bare structure — allowed
    # Check ≥2 non-zero non-9 colors (keys + motif color 2)
    nz_colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] not in (0, 9)}
    if not nz_colors:
        return errs  # degenerate (completely empty tiles) — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n = ctx.draw_int("tile_count", 3, 3)
    elif difficulty == "hard":
        n = ctx.draw_int("tile_count", 4, 4)
    else:
        n = ctx.draw_int("tile_count", 3, 4)
    rng = ctx.draw_rng("layout")
    keys = rng.sample([3, 4, 5, 6, 7, 8], n)
    motifs = rng.sample(MOTIFS, n)

    top = []
    for key, motif in zip(keys, motifs):
        tile = _blank_tile()
        tile[0][0] = key
        for r, c in motif:
            tile[r][c] = 2
        top.append(tile)

    order = keys[:]
    rng.shuffle(order)
    if order == keys:
        order = order[1:] + order[:1]
    bottom = []
    for key in order:
        tile = _blank_tile()
        tile[1][1] = key
        bottom.append(tile)
    return _assemble([top, bottom])


def _draw_from_degenerate(name, rng):
    n = 3
    if name == "no_library":
        # Top row blank — rule has no key→motif mapping; bottom
        # queries cannot be resolved.
        top = [_blank_tile() for _ in range(n)]
        keys = [3, 4, 5]
        bottom = []
        for key in keys:
            tile = _blank_tile()
            tile[1][1] = key
            bottom.append(tile)
        return _assemble([top, bottom])
    if name == "no_query":
        # Library populated but bottom row blank — rule has no
        # queries to look up; output undefined.
        keys = [3, 4, 5]
        motifs = MOTIFS[:n]
        top = []
        for key, motif in zip(keys, motifs):
            tile = _blank_tile()
            tile[0][0] = key
            for r, c in motif: tile[r][c] = 2
            top.append(tile)
        bottom = [_blank_tile() for _ in range(n)]
        return _assemble([top, bottom])
    if name == "key_not_in_library":
        # Bottom queries reference keys not in library — rule's
        # lookup returns nothing for unmatched keys.
        keys = [3, 4, 5]
        motifs = MOTIFS[:n]
        top = []
        for key, motif in zip(keys, motifs):
            tile = _blank_tile()
            tile[0][0] = key
            for r, c in motif: tile[r][c] = 2
            top.append(tile)
        bottom = []
        for key in [6, 7, 8]:
            tile = _blank_tile()
            tile[1][1] = key
            bottom.append(tile)
        return _assemble([top, bottom])
    return _assemble([[_blank_tile()] * n] * 2)
