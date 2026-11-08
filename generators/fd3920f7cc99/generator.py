"""Generator for arc_puzzle_bank_third_21_bundle:hard_21_cartesian_product_of_row_shapes_and_column_colors.

Color-2 row-shape objects are crossed with top-row color swatches to build a
gallery where each shape is recolored by each column color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_swatches, no_shapes, swatch_color_2.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fd3920f7cc99"
VERSION = "3.0.0"  # variable grid + random positions + random polyomino shapes + more shapes/colors (was fixed 12x11 + 3-shape bank)
TASK_ID = "fd3920f7cc99"
SUMMARY = (
    "0-bg grid (size varies) with: (a) TOP-ROW COLOR "
    "SWATCHES — 2-6 cells in row 0 at distinct columns, "
    "each a distinct color from {1,3,4,5,6,7,8,9} (color 2 "
    "is excluded, it is the shape color); (b) ROW SHAPES — "
    "2-5 connected COLOR-2 random polyominoes placed in "
    "rows 1+, mutually isolated. Rule (CARTESIAN PRODUCT "
    "GALLERY): list the row-0 swatch colors left-to-right "
    "and the color-2 shapes top-to-bottom; output a gallery "
    "grid where cell-block (i, j) is shape i recolored from "
    "2 to swatch color j, blocks separated by 1-cell gaps. "
    "Net: every shape is instantiated in every swatch color "
    "in a 2D grid."
)

INVARIANTS = [
    "background is 0; top-row swatches are non-{0,2}, at distinct columns",
    "row shapes are connected color-2 objects in rows 1+, mutually isolated",
    "at least one shape and at least one swatch exist (gallery is well-defined)",
    "the output recolors every row shape by every swatch color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_swatches", "no_shapes", "swatch_color_2")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-9 easy / 8-12 med / 10-16 hard", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "8-12 easy / 10-16 med / 12-22 hard", "valid": "6..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_shapes":       {"type": "int", "default": "2 easy / 2-3 med / 3-5 hard", "valid": "1..5"},
    "shape_size":     {"type": "int", "default": "rng 3..6 cells per shape", "valid": "2..7"},
    "palette_size":   {"type": "int", "default": "= n swatches", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "row0_swatches_scattered_shapes",
                       "valid": "row0_swatches_scattered_shapes"},
    "n_distinct_colors": {"type": "int", "default": "2-3 easy / 3-4 med / 3-6 hard", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [   # used only by the degenerate fixtures
    [(0, 0), (1, 0), (1, 1)],
    [(0, 1), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 1)],
]


def _paint(g, top, left, cells, color):
    for dr, dc in cells:
        g[top + dr][left + dc] = color


def _rand_poly(rng, size, maxdim=4):
    """Random connected polyomino of `size` cells, bbox <= maxdim x maxdim, normalized."""
    for _ in range(50):
        cells = {(0, 0)}
        frontier = [(0, 0)]
        while len(cells) < size and frontier:
            cr, cc = rng.choice(frontier)
            opts = [(cr + dr, cc + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if (cr + dr, cc + dc) not in cells]
            if not opts:
                frontier.remove((cr, cc))
                continue
            nc = rng.choice(opts)
            cells.add(nc); frontier.append(nc)
        mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
        norm = sorted((r - mr, c - mc) for r, c in cells)
        if (len(norm) == size and max(r for r, _ in norm) + 1 <= maxdim
                and max(c for _, c in norm) + 1 <= maxdim):
            return norm
    return [(0, 0), (1, 0), (1, 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 8, 12)
        n_shapes = ctx.draw_int("n_shapes", 2, 2)
        n_colors = ctx.draw_int("n_colors", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 16)
        w = ctx.draw_int("grid_w", 12, 22)
        n_shapes = ctx.draw_int("n_shapes", 3, 5)
        n_colors = ctx.draw_int("n_colors", 3, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 10, 16)
        n_shapes = ctx.draw_int("n_shapes", 2, 3)
        n_colors = ctx.draw_int("n_colors", 3, 4)
    n_colors = min(n_colors, w, 8)
    colors = rng.sample([1, 3, 4, 5, 6, 7, 8, 9], n_colors)
    g = full_grid(h, w, 0)

    # Swatches: distinct row-0 columns, distinct non-{0,2} colors.
    swatch_cols = rng.sample(range(w), n_colors)
    for col, color in zip(swatch_cols, colors):
        g[0][col] = color

    # Shapes: isolated color-2 polyominoes in rows 1+ (1-cell halo so each is its own
    # 4-connected object, and never touching the row-0 swatches).
    occ = [[False] * w for _ in range(h)]
    for c in range(w):
        occ[0][c] = True
    placed = 0
    for _ in range(n_shapes * 30):
        if placed >= n_shapes:
            break
        shape = _rand_poly(rng, rng.randint(3, 6))
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        if sh > h - 1 or sw > w:
            continue
        r0 = rng.randint(1, h - sh)
        c0 = rng.randint(0, w - sw)
        cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
        halo = [(rr, cc) for r, c in cells
                for rr in range(r - 1, r + 2) for cc in range(c - 1, c + 2)]
        if any(0 <= rr < h and 0 <= cc < w and occ[rr][cc] for rr, cc in halo):
            continue
        for r, c in cells:
            g[r][c] = 2
            occ[r][c] = True
        for rr, cc in halo:
            if 0 <= rr < h and 0 <= cc < w:
                occ[rr][cc] = True
        placed += 1
    if placed == 0:                       # guarantee >=1 shape (rule needs >=1)
        _paint(g, 1, 0, [(0, 0), (1, 0), (1, 1)], 2)
    return g



def _color_components(grid, color):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] != color:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid is not a non-empty 2D list"]
    h = len(grid)
    w = len(grid[0]) if h else 0
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    if h < 3 or w < 3:
        errors.append(f"grid too small for swatches plus row shapes: {h}x{w}")
    vals = {v for row in grid for v in row}
    bad = vals - set(range(10))
    if bad:
        errors.append(f"unexpected color values: {sorted(bad)}")

    top = grid[0]
    swatches = [(c, v) for c, v in enumerate(top) if v != 0]
    if not swatches:
        errors.append("missing top-row color swatches")
    if any(v == 2 for _, v in swatches):
        errors.append("top-row swatch uses color 2, which is reserved for row shapes")
    colors = [v for _, v in swatches]
    if len(colors) != len(set(colors)):
        errors.append("top-row swatch colors are not distinct")

    if any(grid[0][c] == 2 for c in range(w)):
        errors.append("color-2 shape cell appears in row 0")
    comps = _color_components(grid, 2)
    if not comps:
        errors.append("missing color-2 row-shape objects")
    for i, comp in enumerate(comps):
        if any(r == 0 for r, _ in comp):
            errors.append(f"shape component {i} touches swatch row")
        comp_set = set(comp)
        for r, c in comp:
            for rr in range(r - 1, r + 2):
                for cc in range(c - 1, c + 2):
                    if 0 <= rr < h and 0 <= cc < w and (rr, cc) not in comp_set and grid[rr][cc] == 2:
                        errors.append(f"shape component {i} is not separated by a 1-cell halo")
                        return errors
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 11, 0)
    if name == "no_swatches":
        # row shapes but no top-row swatches → no colors to recolor with
        for idx in range(2):
            _paint(g, 2 + idx * 3, 1, _SHAPES[idx], 2)
        return g
    if name == "no_shapes":
        # swatches but no row shapes → nothing to recolor
        for idx, color in enumerate([3, 4, 5]):
            g[0][2 + idx * 3] = color
        return g
    if name == "swatch_color_2":
        # swatch is color 2 → confused with shape color, "exclude 2" violated
        g[0][2] = 2
        for idx in range(2):
            _paint(g, 2 + idx * 3, 1, _SHAPES[idx], 2)
        return g
    return g
