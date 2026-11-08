"""Generator for arc_puzzle_bank_21_set23_s:S23_H4.

Rule: top-row prototype library labels rotated motifs in bottom row;
output strip names matching prototypes.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_library, no_query, all_same_label.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "79df2b4dce92"
VERSION = "2.0.1"  # shape-locked in/out: fixed 2x4 lattice -> output always 1x4. Rule output is a 1xN label strip (N = #column tiles). Vary the number of columns 3..6 (width <=30) -> input AND output width vary, plus more query orderings.
TASK_ID = "79df2b4dce92"
SUMMARY = "2x4 tile lattice. Top row = labeled prototypes (label at tile (0,0), motif elsewhere). Bottom row = rotated copies of those motifs. Output = 1-row strip of the labels in bottom-row order, matched via rotation-canonical shape equivalence."

# Rivals: 'output the labels in top-row order' refuted by ≥2 demos
# where bottom-row order differs from top. 'use the motif color in
# output' refuted by any demo (output is labels). 'output a full grid'
# refuted by any demo (output is 1×4 strip). 'orientation matters'
# refuted by any demo with rotated queries. 4 demos with varied orders
# and rotations cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the grid is a 2x4 lattice of 3x3 tiles separated by color 9",
    "top tiles contain label colors at local (0,0) plus prototype motif cells",
    "bottom tiles are rotated copies of the prototypes",
    "the output strip contains the matching prototype labels in query order",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_library", "no_query", "all_same_label")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "order":          {"type": "int", "default": "rng 0..5", "valid": "0..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "2x4_tile_lattice",
                       "valid": "2x4_tile_lattice"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 1), (1, 1), (1, 2)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 1), (0, 2), (1, 0), (1, 1)],
    [(0, 2), (1, 2), (2, 1), (2, 2)],
    [(0, 1), (0, 2), (1, 1), (2, 1)],
    [(0, 1), (1, 1), (2, 1), (2, 2)],
    [(0, 2), (1, 1), (1, 2), (2, 2)],
]

_ORDERS = [
    [0, 1, 2, 3],
    [1, 3, 0, 2],
    [2, 0, 3, 1],
    [3, 2, 1, 0],
    [0, 2, 1, 3],
    [1, 0, 3, 2],
    [3, 0, 2, 1],
    [2, 1, 0, 3],
]


def _rot90(cells):
    return [(c, 2 - r) for r, c in cells]


def _rot(cells, turns):
    out = list(cells)
    for _ in range(turns % 4):
        out = _rot90(out)
    return out


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _tile_origin(row_idx, col_idx):
    return row_idx * 4, col_idx * 4


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 full-height color-9 separator column, ≥2 distinct non-9 non-zero colors (label + motif)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    sep_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not sep_cols:
        errs.append("no full-height color-9 separator columns found")
    other_colors = {grid[r][c] for r in range(h) for c in range(w)
                    if grid[r][c] not in (0, 9)}
    if len(other_colors) < 2:
        errs.append(f"only {len(other_colors)} non-9 color(s); expected ≥2 (label + motif colors)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        n_cols = ctx.draw_int("n_cols", 3, 4)
    elif difficulty == "hard":
        n_cols = ctx.draw_int("n_cols", 5, 6)
    else:
        n_cols = ctx.draw_int("n_cols", 3, 6)
    labels = rng.sample([1, 3, 4, 5, 6, 7, 8], n_cols)
    shape_ids = rng.sample(range(len(_SHAPES)), n_cols)
    shapes = [_SHAPES[i] for i in shape_ids]
    order = list(range(n_cols)); rng.shuffle(order)

    h = 7
    w = n_cols * 4 - 1
    g = full_grid(h, w, 0)
    for r in range(h):
        for k in range(1, n_cols):          # full-height color-9 divider columns
            g[r][4 * k - 1] = 9
    for c in range(w):                        # full-width color-9 divider row
        g[3][c] = 9

    for col in range(n_cols):                 # top: labeled prototypes
        top, left = _tile_origin(0, col)
        g[top][left] = labels[col]
        _paint(g, top, left, shapes[col], 2)
    for col in range(n_cols):                 # bottom: rotated queries in shuffled order
        top, left = _tile_origin(1, col)
        _paint(g, top, left, _rot(shapes[order[col]], rng.randrange(4)), 2)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 15, 0)
    for r in range(7):
        for c in (3, 7, 11): g[r][c] = 9
    for c in range(15): g[3][c] = 9
    if name == "no_library":
        # Top tiles empty (no prototypes) — rule has no library
        # to look up bottom-row motifs against.
        for col in range(4):
            top, left = _tile_origin(1, col)
            _paint(g, top, left, _SHAPES[col], 2)
        return g
    if name == "no_query":
        # Library present but bottom tiles empty — rule has nothing
        # to classify; output strip undefined.
        labels = [1, 3, 4, 5]
        for col, (label, cells) in enumerate(zip(labels, _SHAPES)):
            top, left = _tile_origin(0, col)
            g[top][left] = label
            _paint(g, top, left, cells, 2)
        return g
    if name == "all_same_label":
        # All 4 prototypes share the same label color — rule's
        # output strip cannot discriminate prototypes.
        for col, cells in enumerate(_SHAPES):
            top, left = _tile_origin(0, col)
            g[top][left] = 4
            _paint(g, top, left, cells, 2)
        for col in range(4):
            top, left = _tile_origin(1, col)
            _paint(g, top, left, _SHAPES[col], 2)
        return g
    return g
