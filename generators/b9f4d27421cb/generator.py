"""Generator for arc_puzzle_bank_twelfth21:H82.

Rule: top pair shows a geometric transform, mid pair shows a recolor
map, apply BOTH to the bottom-left query and paint into the blank
bottom-right panel.

Combinatorial axes: panel_size (rule detects separators), transform,
source/target colors, shape + recolor layouts.
Degenerates: no_separators, no_query, no_recolor_map.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b9f4d27421cb"
VERSION = "3.1.1"  # 3.1.0->3.1.1: add self_check. 3.0.0->3.1.0: widen panel size n to 3..7 (rule re-detects
# the 9-separators so output shape 3n+2 x 2n+1 follows) -> out_shapes 2 -> more
TASK_ID = "b9f4d27421cb"
SUMMARY = (
    "A 3-row x 2-col grid of n x n panels separated by full color-9 "
    "dividers (rows n and 2n+1, col n; n varies by difficulty). "
    "TOP pair (left=template, right=transformed) demonstrates ONE of "
    "5 geometric transforms (rot-cw / rot-180 / rot-ccw / flip-lr / "
    "flip-ud) on a RANDOM ASYMMETRIC color shape (all 8 dihedral "
    "images distinct, so the transform is uniquely inferable). MID "
    "pair demonstrates a RANDOM color RECOLOR MAP (k source colors -> "
    "k distinct targets). BOTTOM-LEFT holds a RANDOM query in the "
    "source colors; BOTTOM-RIGHT is blank. Rule: read the transform "
    "from the top pair, the recolor from the mid pair, apply both to "
    "the query, paint the result into the blank. Panel size, shape, "
    "transform, color sets and all three layouts now vary freely "
    "(were 5 hardcoded inputs)."
)

INVARIANTS = [
    "two full color-9 rows and one full color-9 column split a 3x2 example/query layout",
    "the top pair demonstrates one geometric transform",
    "the middle pair demonstrates a nonzero color substitution map",
    "the bottom-left query is transformed and recolored into the blank bottom-right panel",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separators", "no_query", "no_recolor_map")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_size":     {"type": "int", "default": "rng 4..7 (easy 3..4, hard 6..7)", "valid": "3..7"},
    "transform":      {"type": "int", "default": "rng 1..5", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 2..3 sources", "valid": "4..7"},
    "position_bias":  {"type": "str", "default": "3x2_example_query",
                       "valid": "3x2_example_query"},
    "n_distinct_colors": {"type": "int", "default": "rng", "valid": "4..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_separators|no_query|no_recolor_map"},
}


def _dihedral_images(cells, n):
    """All 8 dihedral images of a cell set within an n x n frame."""
    return [
        frozenset(cells),
        frozenset((r, n - 1 - c) for r, c in cells),
        frozenset((n - 1 - r, c) for r, c in cells),
        frozenset((c, n - 1 - r) for r, c in cells),
        frozenset((n - 1 - r, n - 1 - c) for r, c in cells),
        frozenset((n - 1 - c, r) for r, c in cells),
        frozenset((c, r) for r, c in cells),
        frozenset((n - 1 - c, n - 1 - r) for r, c in cells),
    ]


def _random_asym(rng, n, lo, hi):
    """Random shape whose 8 dihedral images are all DISTINCT, so the
    top-pair transform is uniquely inferable by the rule."""
    allcells = [(r, c) for r in range(n) for c in range(n)]
    cells = rng.sample(allcells, rng.randint(lo, hi))
    for _ in range(400):
        if len(set(_dihedral_images(cells, n))) == 8:
            return cells
        cells = rng.sample(allcells, rng.randint(lo, hi))
    return cells


# Cell-space transforms keyed to match the rule's cond order exactly.
def _xform(cells, n, code):
    if code == 1:   # rotate-cw
        return [(c, n - 1 - r) for r, c in cells]
    if code == 2:   # rotate-180
        return [(n - 1 - r, n - 1 - c) for r, c in cells]
    if code == 3:   # rotate-ccw
        return [(n - 1 - c, r) for r, c in cells]
    if code == 4:   # flip-lr
        return [(r, n - 1 - c) for r, c in cells]
    if code == 5:   # flip-ud
        return [(n - 1 - r, c) for r, c in cells]
    return list(cells)


def _paint_cells(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _scatter(rng, n, colors, lo, hi):
    """Random {(r,c): color} placement, each color in `colors` used >=1."""
    allcells = [(r, c) for r in range(n) for c in range(n)]
    count = max(len(colors), rng.randint(lo, hi))
    count = min(count, len(allcells))
    pos = rng.sample(allcells, count)
    pal = list(colors)
    rng.shuffle(pal)
    out = {}
    for i, p in enumerate(pos):
        out[p] = pal[i] if i < len(pal) else rng.choice(colors)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid has color-9 full divider rows and a full divider column."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    # check grid has color-9 dividers (full rows or full cols of 9)
    full_9_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    full_9_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    has_9 = any(grid[r][c] == 9 for r in range(h) for c in range(w))
    if not has_9:
        return errs  # degenerate no_separators
    if not full_9_rows:
        errs.append("no full color-9 divider rows found")
    if not full_9_cols:
        errs.append("no full color-9 divider column found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        n = rng.randint(3, 4)
        k = 2
        q_lo, q_hi = 3, 5
    elif difficulty == "hard":
        n = rng.randint(6, 7)
        k = 3
        q_lo, q_hi = 6, 12
    else:
        n = rng.randint(4, 7)
        k = rng.randint(2, 3)
        q_lo, q_hi = 4, 9

    code = rng.randint(1, 5)

    # Color budget: bg=0, divider=9 reserved. Pick a top-shape color, k
    # distinct source colors, and k distinct target colors all different
    # from sources (so every recolor is visible).
    pool = [1, 2, 3, 4, 5, 6, 7, 8]
    rng.shuffle(pool)
    shape_color = pool[0]
    sources = pool[1:1 + k]
    rest = [c for c in pool if c not in sources]
    targets = rng.sample(rest, k)
    cmap = dict(zip(sources, targets))

    # The full grid: 3 rows x 2 cols of n x n panels + 2 divider rows + 1
    # divider col. The rule re-detects the separators, so n is free.
    H, W = 3 * n + 2, 2 * n + 1
    g = full_grid(H, W, 0)
    r1, r2, csep = n, 2 * n + 1, n
    for c in range(W):
        g[r1][c] = 9
        g[r2][c] = 9
    for r in range(H):
        g[r][csep] = 9

    # TOP pair: asymmetric template (left) + its transform (right).
    top_cells = _random_asym(rng, n, n, 2 * n)
    _paint_cells(g, 0, 0, top_cells, shape_color)
    _paint_cells(g, 0, csep + 1, _xform(top_cells, n, code), shape_color)

    # MID pair: a scattered source layout recolored by the map.
    mid = _scatter(rng, n, sources, k, 2 * k + 1)
    for (r, c), v in mid.items():
        g[r1 + 1 + r][c] = v
        g[r1 + 1 + r][csep + 1 + c] = cmap[v]

    # BOTTOM-LEFT query: random cells in the source colors.
    query = _scatter(rng, n, sources, q_lo, q_hi)
    for (r, c), v in query.items():
        g[r2 + 1 + r][c] = v

    return g


def _draw_from_degenerate(name, rng):
    n = 4
    H, W = 3 * n + 2, 2 * n + 1
    g = full_grid(H, W, 0)
    top = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]
    midL = {(0, 0): 2, (1, 1): 3, (2, 0): 4}
    midR = {(0, 0): 6, (1, 1): 7, (2, 0): 8}
    query = {(0, 0): 2, (1, 1): 3, (2, 2): 4}
    if name == "no_separators":
        # No 9-dividers — the rule's 6-panel split fails.
        _paint_cells(g, 0, 0, top, 2)
        for (r, c), v in midL.items():
            g[5 + r][c] = v
        for (r, c), v in query.items():
            g[10 + r][c] = v
        return g
    for c in range(W):
        g[n][c] = 9
        g[2 * n + 1][c] = 9
    for r in range(H):
        g[r][n] = 9
    if name == "no_query":
        # Examples shown but bottom-left empty — nothing to apply to.
        _paint_cells(g, 0, 0, top, 2)
        _paint_cells(g, 0, n + 1, _xform(top, n, 4), 2)
        for (r, c), v in midL.items():
            g[n + 1 + r][c] = v
        for (r, c), v in midR.items():
            g[n + 1 + r][n + 1 + c] = v
        return g
    if name == "no_recolor_map":
        # Mid example identical L=R — the recolor map is identity.
        _paint_cells(g, 0, 0, top, 2)
        _paint_cells(g, 0, n + 1, _xform(top, n, 4), 2)
        for (r, c), v in midL.items():
            g[n + 1 + r][c] = v
            g[n + 1 + r][n + 1 + c] = v
        for (r, c), v in query.items():
            g[2 * n + 2 + r][c] = v
        return g
    return g
