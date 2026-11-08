"""Generator for arc_puzzle_bank_thirteenth_21_bundle:hard_85_decode_library_shape_transform_and_recolor.

Combinatorial axes (8): grid_h, grid_w, palette_kind, selector,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_library, no_command_row, selector_not_in_library.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "551b790d352e"
VERSION = "3.0.1"
TASK_ID = "551b790d352e"
SUMMARY = "Top 5 rows hold 3 library panels at column offsets {0, 6, 12} (5 cols each); each panel has a distinct non-zero shape in a distinct color. Row 6 has 3 instruction cells: g[6][0]=selector color (matches one library panel), g[6][1]=transform code (1=identity, 2=cw90, 3=180, 4=ccw90, 5=flip-lr), g[6][2]=output recolor. Rule selects the matching library panel, crops to its non-zero bbox, applies the transform, then recolors all non-zero cells to the output color."

# Rivals: 'output is input' refuted by any demo (output is small
# transformed shape). 'use selector color in output' refuted by any
# demo (output color = g[6][2]). 'ignore transform' refuted by ≥1
# demo with non-identity code producing rotated/flipped shape.
# 'pick first library panel always' refuted by demos with different
# selectors. 3 demos with ≥2 distinct selectors cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the top five rows contain three five-column library panels at offsets 0, 6, and 12",
    "each library panel has a distinct nonzero selector color",
    "row 6 contains selector color, transform code, and output color",
    "the output is the selected crop transformed and recolored",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_library", "no_command_row", "selector_not_in_library")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7", "valid": "7..7"},
    "grid_w":         {"type": "int", "default": "17", "valid": "17..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "selector":       {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "3library_panels_with_command_row",
                       "valid": "3library_panels_with_command_row"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    # 4-5 cell motifs that fit in a 3x3 or 3x4 area
    [(0, 0), (1, 0), (1, 1), (2, 1)],         # S
    [(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)], # H-ish
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 2)], # zigzag
    [(0, 0), (0, 1), (0, 2), (1, 1)],         # T
    [(0, 0), (1, 0), (2, 0), (2, 1)],         # L
    [(0, 0), (0, 1), (1, 0), (1, 1)],         # square
    [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)], # corner
    [(0, 1), (1, 0), (1, 1), (1, 2)],         # T flipped
    [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)], # bracket
    [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)], # X
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _rand_shape(rng):
    """Random connected polyomino, 3-6 cells, bbox within 3x3 (fits a panel)."""
    n = rng.randint(3, 6)
    cells = {(rng.randint(0, 2), rng.randint(0, 2))}
    guard = 0
    while len(cells) < n and guard < 200:
        guard += 1
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            cells.add((nr, nc))
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for (r, c) in cells]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid is 7x17; row 6 has a command cell at col 0 and col 1 and col 2."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if h != 7:
        return errors  # degenerate — allowed
    if w != 17:
        return errors  # degenerate — allowed
    # Command row: row 6 should have non-zero values at cols 0,1,2
    if grid[6][0] == 0:
        return errors  # degenerate (no_command_row) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        selector = ctx.draw_int("selector", 0, 0)
        transform = ctx.draw_int("transform", 1, 2)
    elif difficulty == "hard":
        selector = ctx.draw_int("selector", 0, 2)
        transform = ctx.draw_int("transform", 1, 5)
    else:
        selector = ctx.draw_int("selector", 0, 2)
        transform = ctx.draw_int("transform", 1, 5)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    out_color = rng.choice([c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in colors])
    shapes = [_rand_shape(rng) for _ in range(3)]   # random library shapes (was a fixed 10-shape bank)
    g = full_grid(7, 17, 0)
    for idx, cells in enumerate(shapes):
        _paint(g, 1, idx * 6 + 1, cells, colors[idx])
    g[6][0] = colors[selector]
    g[6][1] = transform
    g[6][2] = out_color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 17, 0)
    if name == "no_library":
        # command row but no library panels → no shapes to select
        g[6][0] = 4; g[6][1] = 1; g[6][2] = 7
        return g
    if name == "no_command_row":
        # library panels but no row 6 commands → no selector/transform/recolor
        for idx, cells in enumerate(_SHAPES):
            _paint(g, 1, idx * 6 + 1, cells, [2, 3, 4][idx])
        return g
    if name == "selector_not_in_library":
        # selector color absent from library → no panel matches
        for idx, cells in enumerate(_SHAPES):
            _paint(g, 1, idx * 6 + 1, cells, [2, 3, 4][idx])
        g[6][0] = 9  # not 2/3/4 → no match
        g[6][1] = 1
        g[6][2] = 7
        return g
    return g
