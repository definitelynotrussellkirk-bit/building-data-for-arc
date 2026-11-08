"""Generator for arc_puzzle_bank_21_set23_s:S23_M7 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a295b0f859cd"
# 3.0.0: the previous body was a MISLABELLED "multi-motif gallery pack" — but the
# canonical rule is a 9-DIVIDER TILE LATTICE that canonically-rotates each tile
# (lex-min of its 4 rotations). Scattered motifs have no 9-dividers, so the whole
# grid is one tile and is often already canonical -> output == input (identity).
# This rewrite builds a real tr x tc lattice of square tiles separated by full
# color-9 rows/cols, and guarantees >=1 tile is NOT already canonical so the rule
# visibly rotates it. Adds self_check.
VERSION = "3.0.0"
TASK_ID = "a295b0f859cd"

SUMMARY = (
    "A tr x tc lattice of s x s tiles separated by single full color-9 divider "
    "rows/cols. Each tile holds a small pattern in {0,2..8}. Rule: split on the "
    "9-dividers, replace each tile by the lex-smallest of its 4 rotations, and "
    "reassemble with the 9-dividers. At least one tile is non-canonical so the "
    "rule visibly rotates it (output != input)."
)

INVARIANTS = [
    "full color-9 rows/cols separate the tiles into a regular lattice",
    "all tiles are square and equal size (rotations preserve dims)",
    "tile cells use only {0, 2..8} (never 9, so dividers are unambiguous)",
    "at least one tile is not its own canonical (lex-min) rotation",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "tile_s":         {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "tr":             {"type": "int", "default": "rng 2..3", "valid": "1..3"},
    "tc":             {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rot_cw(tile):
    s = len(tile)
    return [[tile[s - 1 - c][r] for c in range(s)] for r in range(s)]


def _canon(tile):
    """Lex-smallest of the 4 rotations (matches the rule's canonical-rotation)."""
    variants = [tile]
    t = tile
    for _ in range(3):
        t = _rot_cw(t)
        variants.append(t)
    return min(variants, key=lambda g: [v for row in g for v in row])


def _random_tile(rng, s, colors):
    """Sparse tile over {0} + 1-2 fg colors (matches the canonical {0,2} density)."""
    pool = [0, 0] + list(colors)   # bias toward background for sparsity
    return [[rng.choice(pool) for _ in range(s)] for _ in range(s)]


def _assemble(tiles):
    """tiles: tr x tc matrix of s x s grids -> lattice with single full-9
    divider rows/cols (the exact layout the rule's tile-lattice reads back)."""
    tr = len(tiles); tc = len(tiles[0]); s = len(tiles[0][0])
    H = tr * s + (tr - 1); W = tc * s + (tc - 1)
    g = [[9] * W for _ in range(H)]
    for i in range(tr):
        for j in range(tc):
            top = i * (s + 1); left = j * (s + 1)
            for r in range(s):
                for c in range(s):
                    g[top + r][left + c] = tiles[i][j][r][c]
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        s = ctx.draw_int("tile_s", 3, 3)
        tr, tc = 1, ctx.draw_int("tc", 2, 3)      # wide 1xN lattice (canonical-like)
    elif difficulty == "hard":
        s = ctx.draw_int("tile_s", 3, 3)
        tr = ctx.draw_int("tr", 1, 3); tc = ctx.draw_int("tc", 2, 3)
    else:
        s = ctx.draw_int("tile_s", 2, 3)
        tr = ctx.draw_int("tr", 1, 2); tc = ctx.draw_int("tc", 2, 3)
    if tr * tc < 2:
        tc = 2
    rng = ctx.draw_rng("layout")
    n_colors = ctx.draw_int("n_colors", 1, 2)
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8], n_colors)

    for _outer in range(60):
        tiles = [[_random_tile(rng, s, colors) for _ in range(tc)] for _ in range(tr)]
        # require >=1 tile NOT already canonical so the rule visibly rotates it
        if any(_canon(tiles[i][j]) != tiles[i][j]
               for i in range(tr) for j in range(tc)):
            return _assemble(tiles)
    # deterministic fallback: a tile that is provably non-canonical
    tiles = [[_random_tile(rng, s, colors) for _ in range(tc)] for _ in range(tr)]
    forced = [[0] * s for _ in range(s)]
    forced[0][s - 1] = colors[0]  # a single hot cell at top-right; canonical form
                                  # places it bottom-left -> guaranteed rotation
    tiles[0][0] = forced
    return _assemble(tiles)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """The grid must split on full color-9 rows/cols into equal square tiles, and
    at least one tile must be non-canonical so the rule's rotation changes it."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    div_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not div_rows and not div_cols:
        return ["no full color-9 divider rows/cols — not a tile lattice"]

    def segs(n, divs):
        out = []; prev = -1
        for x in divs + [n]:
            if x - prev - 1 > 0:
                out.append((prev + 1, x))
            prev = x
        return out

    rbs = segs(h, div_rows); cbs = segs(w, div_cols)
    tiles = [[[row[cb[0]:cb[1]] for row in grid[rb[0]:rb[1]]] for cb in cbs]
             for rb in rbs]
    errors = []
    dims = {(len(t), len(t[0])) for trow in tiles for t in trow}
    if len(dims) != 1 or next(iter(dims))[0] != next(iter(dims))[1]:
        errors.append(f"tiles must all be the same square size, got {dims}")
        return errors
    if not any(_canon(t) != t for trow in tiles for t in trow):
        errors.append("every tile is already canonical — the rule's rotation "
                      "leaves the grid unchanged (identity)")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
