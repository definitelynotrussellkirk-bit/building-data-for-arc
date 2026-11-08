"""Generator for 4290ef0e.

Rule: input L-corner sizes become concentric L-corner rings in the output.
The canonical rule reads each non-background color's bounding-box max-dim
(and corner-arm extent), determines the ring layout from the SET of sizes,
and emits concentric L-rings. So the OUTPUT structure is driven entirely by
the SET OF SHAPE SIZES — that is the discriminator that must vary.

Combinatorial axes: shape_count n (2-6), the L-corner sizes (the ring sizes
{1, 3, ..., 2n-1}, all odd + distinct), grid size, L orientations, colors.
Degenerates: no_shapes, single_shape, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5a01897eb8be"
RULE_HASH = "00935b1c1bf9"  # canonical rule this generator was written against
VERSION = "2.1.0"  # shape-locked-in + frozen sizes {1,3,5,7}: rule is size-generic (reads (rows g)/(cols g)) and builds concentric rings from the SET of shape max-dims. Old gen froze sizes -> identical ring structure, only colors permuted (in=1). Now vary n(2-6) -> ring sizes {1,3,..,2n-1}, vary grid size + L orientations -> output dims + structure vary.
TASK_ID = "5a01897eb8be"
SUMMARY = (
    "0-bg grid (size varies) holding n (2-6) NON-BACKGROUND SHAPES: one "
    "SINGLETON (max-dim 1) plus (n-1) L-CORNERS whose bounding-box sizes are "
    "the ODD DISTINCT values 3, 5, ..., 2n-1 (each a distinct color, L "
    "vertex in a random one of the 4 corners). Rule: read each color's "
    "bbox max-dim, derive the concentric ring layout from the SET of sizes "
    "(has-center -> out-size 2n-1), and emit CONCENTRIC L-RINGS, the largest "
    "shape outermost. Net: the input's nested L sizes become nested rings. "
    "Output size = 2n-1, varying 3..11. (Was fixed 14x14 with frozen sizes "
    "1,3,5,7 -> only 2 output sizes, all structure identical, colors only.)"
)

INVARIANTS = [
    "the upper-left cell is background (0) and defines the background color",
    "each non-background color forms either the singleton or an L-corner",
    "the shape bounding-box sizes are odd and distinct: {1, 3, ..., 2n-1}",
    "the canonical rule maps those sizes to concentric output rings",
]

SHAPE_KINDS = ("S3", "S4")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shapes", "single_shape", "full_grid")
HELPFUL_TEXTURES = SHAPE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..27"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "6..27"},
    "shape_count":    {"type": "int", "default": "rng 2..6", "valid": "2..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 2..6", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "shelf_pack", "valid": "shelf_pack"},
    "n_distinct_colors":{"type": "int", "default": "rng 2..6", "valid": "2..6"},
    "texture":        {"type": "str", "default": "alias for shape_count",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _shape_cells(size, orient):
    """L-corner (or singleton) of bbox size x size; arm length = size.
    orient selects which corner the vertex sits at; max-dim is `size`
    regardless of orientation (the rule reads all 4 diagonal arms)."""
    if size == 1:
        return [(0, 0)]
    cells = []
    for k in range(size):
        if orient == 0:      # vertex top-left
            cells += [(0, k), (k, 0)]
        elif orient == 1:    # vertex top-right
            cells += [(0, k), (k, size - 1)]
        elif orient == 2:    # vertex bottom-left
            cells += [(size - 1, k), (k, 0)]
        else:                # vertex bottom-right
            cells += [(size - 1, k), (k, size - 1)]
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    tx = overrides.get("texture")
    if tx in SHAPE_KINDS:
        n = int(tx[1])
    elif difficulty == "easy":
        n = ctx.draw_int("shape_count", 2, 3)
    elif difficulty == "hard":
        n = ctx.draw_int("shape_count", 5, 6)
    else:
        n = ctx.draw_int("shape_count", 2, 6)

    # sizes are the ring sizes: singleton (1) + L-corners 3,5,...,2n-1.
    # keeping max-dims exactly equal to the ring sizes makes every shape an
    # "exact" ring -> the rule maps each color to its own ring cleanly.
    sizes = [1] + [3 + 2 * i for i in range(n - 1)]
    colors = ctx.draw_distinct_colors("colors", n=n, exclude={0})
    big = sizes[-1]

    # grid width must let the two largest shapes share a shelf (keeps the
    # packed height well under the 30-cell canvas limit).
    W = ctx.draw_int("grid_w", 2 * big, min(27, 2 * big + 8))

    # shelf-pack the shapes (largest first) into width W with 1-cell gaps.
    order = sorted(range(n), key=lambda i: -sizes[i])
    gap = 1
    placements = []  # (r, c, size, color, orient)
    x = gap
    y = gap
    shelf_h = 0
    for i in order:
        s = sizes[i]
        if x + s > W - gap:
            x = gap
            y += shelf_h + gap
            shelf_h = 0
        placements.append((y, x, s, colors[i], rng.randint(0, 3)))
        x += s + gap
        shelf_h = max(shelf_h, s)
    content_h = y + shelf_h + gap

    pad_t = rng.randint(0, 1)
    pad_b = rng.randint(0, 2)
    pad_l = rng.randint(0, 1)
    pad_r = rng.randint(0, 1)
    H = content_h + pad_t + pad_b
    Wg = W + pad_l + pad_r

    g = full_grid(H, Wg, 0)
    for (r, c, s, color, orient) in placements:
        for (dr, dc) in _shape_cells(s, orient):
            g[r + pad_t + dr][c + pad_l + dc] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0 at top-left, >=2 distinct non-bg colors, >=2 non-bg cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 40 or w > 40:
        errs.append(f"grid too large: {h}x{w}")
    if grid[0][0] != 0:
        errs.append("top-left cell is not background (0)")
    nonzero_colors = {grid[r][c] for r in range(h) for c in range(w)
                      if grid[r][c] != 0}
    if len(nonzero_colors) < 2:
        errs.append(f"expected >=2 distinct non-bg colors, found {len(nonzero_colors)}")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 14, 0)
    if name == "no_shapes":
        return g
    if name == "single_shape":
        for k in range(3):
            g[1][1 + k] = 3
            g[1 + k][1] = 3
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(14):
                g[r][c] = 3
        return g
    return g
