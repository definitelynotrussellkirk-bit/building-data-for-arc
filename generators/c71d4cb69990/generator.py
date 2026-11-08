"""Generator for 2546ccf6.

Rule: in separator lattices, every adjacent 2x2 tile block with exactly one
empty tile and three same-color patterned tiles is completed by flipping the
matching neighbor into the empty tile.

Combinatorial axes (9): tile_rows, tile_cols, cell_size, empty_corner,
num_missing_blocks, palette_kind, anchor_corner, asymmetry_force, texture.
Degenerates: no_separators, no_patches, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c71d4cb69990"
RULE_HASH = "1409b8ddf462"  # canonical rule this generator was written against
VERSION = "2.1.0"
TASK_ID = "c71d4cb69990"
SUMMARY = (
    "A 3x3 or 4x4 separator lattice contains one or more adjacent 2x2 tile "
    "blocks with exactly one missing patterned tile; the rule fills each missing "
    "tile by the appropriate horizontal/vertical flip."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "full nonzero separator rows and columns divide the grid into equal tiles",
    "at least one 2x2 block of tiles has exactly one empty tile and three same-color patterned tiles",
    "the missing tile is reconstructed by horizontal or vertical flip from its neighbor",
    "all separator cells remain unchanged",
]

CORNERS = ("tl", "tr", "bl", "br")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_separators", "no_patches", "full_grid")
HELPFUL_TEXTURES = CORNERS

AXES = {
    "tile_rows": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "tile_cols": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "cell_size": {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "empty_corner": {"type": "str", "default": "rng helpful", "valid": "tl|tr|bl|br"},
    "num_missing_blocks": {"type": "int", "default": "difficulty-scaled", "valid": "1..4"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "warm|cool|broad|primary"},
    "anchor_corner": {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force": {"type": "bool", "default": "true", "valid": "true|false"},
    "palette_size": {"type": "int", "default": "2..5", "valid": "2..5"},
    "n_distinct_colors": {"type": "int", "default": "2..5", "valid": "2..5"},
    "texture": {"type": "str", "default": "alias for empty_corner", "valid": "tl|tr|bl|br|no_separators|no_patches|full_grid"},
}


def _base_patch(k, color, rng):
    # Asymmetric L+notch shape: flips are visibly different for every corner.
    patch = [[0 for _ in range(k)] for _ in range(k)]
    for r in range(k):
        patch[r][0] = color
    for c in range(k):
        patch[k - 1][c] = color
    patch[0][rng.randint(1, k - 1)] = color
    if k >= 4:
        patch[1][k - 1] = color
    return patch


def _put(g, r0, c0, patch):
    for r, row in enumerate(patch):
        for c, v in enumerate(row):
            g[r0 + r][c0 + c] = v


def _mirror_columns(patch):
    return [list(reversed(row)) for row in patch]


def _mirror_rows(patch):
    return [list(row) for row in reversed(patch)]


def _tile_origin(k, tr, tc):
    return tr * (k + 1), tc * (k + 1)


def _draw_lattice(tile_rows, tile_cols, k, sep_color):
    h = tile_rows * k + (tile_rows - 1)
    w = tile_cols * k + (tile_cols - 1)
    g = full_grid(h, w, 0)
    for tr in range(1, tile_rows):
        r = tr * k + (tr - 1)
        for c in range(w):
            g[r][c] = sep_color
    for tc in range(1, tile_cols):
        c = tc * k + (tc - 1)
        for r in range(h):
            g[r][c] = sep_color
    return g


def _install_missing_block(g, k, br, bc, empty, shape_color, rng):
    base = _base_patch(k, shape_color, rng)
    patches = {
        "tl": base,
        "tr": _mirror_columns(base),
        "bl": _mirror_rows(base),
        "br": _mirror_rows(_mirror_columns(base)),
    }
    tile_names = {"tl": (br, bc), "tr": (br, bc + 1), "bl": (br + 1, bc), "br": (br + 1, bc + 1)}
    for name, (tr, tc) in tile_names.items():
        if name == empty:
            continue
        r0, c0 = _tile_origin(k, tr, tc)
        _put(g, r0, c0, patches[name])


def _separator_rows_cols(grid):
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if grid[r][0] != 0 and all(grid[r][c] == grid[r][0] for c in range(w))]
    cols = [c for c in range(w) if grid[0][c] != 0 and all(grid[r][c] == grid[0][c] for r in range(h))]
    return rows, cols


def self_check(grid, *, difficulty=None, meta=None):
    """Require a true separator lattice plus at least one one-missing 2x2 tile block."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if (meta or {}).get("texture") in DEGENERATE_TEXTURES:
        return []
    errs = []
    h, w = len(grid), len(grid[0])
    sep_rows, sep_cols = _separator_rows_cols(grid)
    if not sep_rows:
        errs.append("no full-width uniform nonzero separator row found")
    if not sep_cols:
        errs.append("no full-height uniform nonzero separator column found")
    rb = [-1] + sep_rows + [h]
    cb = [-1] + sep_cols + [w]
    tile_nonempty = []
    for ri in range(len(rb) - 1):
        row = []
        for ci in range(len(cb) - 1):
            vals = [grid[r][c]
                    for r in range(rb[ri] + 1, rb[ri + 1])
                    for c in range(cb[ci] + 1, cb[ci + 1])]
            row.append(any(v != 0 for v in vals))
        tile_nonempty.append(row)
    found_one_missing = False
    for ri in range(len(tile_nonempty) - 1):
        for ci in range(len(tile_nonempty[0]) - 1):
            flags = [tile_nonempty[ri][ci], tile_nonempty[ri][ci + 1],
                     tile_nonempty[ri + 1][ci], tile_nonempty[ri + 1][ci + 1]]
            if sum(flags) == 3:
                found_one_missing = True
    if not found_one_missing:
        errs.append("no adjacent 2x2 tile block with exactly one missing patterned tile")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        k = ctx.draw_int("cell_size", 3, 4)
        tile_rows = tile_cols = 3
        block_count = 1
    elif difficulty == "hard":
        k = ctx.draw_int("cell_size", 4, 5)
        tile_rows = tile_cols = 4
        block_count = ctx.draw_int("num_missing_blocks", 3, 4)
    else:
        k = ctx.draw_int("cell_size", 3, 5)
        tile_rows = tile_cols = 4
        block_count = ctx.draw_int("num_missing_blocks", 2, 3)

    sep_color, *shape_colors = ctx.draw_distinct_colors("colors", n=1 + block_count, exclude={0})
    g = _draw_lattice(tile_rows, tile_cols, k, sep_color)
    empty0 = (overrides.get("texture") if overrides.get("texture") in CORNERS else None) or \
             ctx.draw_choice("empty_corner", list(CORNERS))
    block_origins = [(0, 0), (0, 2), (2, 0), (2, 2)] if tile_rows >= 4 and tile_cols >= 4 else [(0, 0)]
    for i, (br, bc) in enumerate(block_origins[:block_count]):
        empty = empty0 if i == 0 else rng.choice(CORNERS)
        _install_missing_block(g, k, br, bc, empty, shape_colors[i], rng)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_separators":
        g[1][1] = 3
        return g
    if name == "no_patches":
        for i in range(7):
            g[3][i] = 5
            g[i][3] = 5
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 3
        return g
    return g
