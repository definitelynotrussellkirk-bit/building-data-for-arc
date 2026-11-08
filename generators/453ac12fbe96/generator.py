"""Generator for arc_puzzle_bank_21_set12_bundle:hard_l18.

Rule: normalize each object's cells; output union bbox. Cells in 2
shapes → 2; in 3 shapes → 8; else 0.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "453ac12fbe96"
VERSION = "3.1.1"
TASK_ID = "453ac12fbe96"
SUMMARY = (
    "0-bg grid (h~6-8, w~14-16) with EXACTLY 3 distinct-colour shapes "
    "at horizontal slots (1,1),(1,6),(1,11), each a VARIED connected "
    "polyomino (3-4 cells, bbox <=3 wide, always containing its (0,0) "
    "corner so the normalized sets share >=1 cell). Rule: normalize each "
    "shape's cells to (0,0); over the union bbox, colour each cell by "
    "overlap count: 2 shapes share -> 2, 3 shapes share -> 8, else 0. "
    "Varied shapes -> varied overlap-count map."
)

INVARIANTS = [
    "exactly 3 non-touching distinct-color blobs",
    "their normalized cell sets share at least one cell (all contain (0,0))",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("shapes_disjoint", "single_shape", "no_shapes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 14..16", "valid": "11..26"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_shapes":       {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "tri_horizontal",
                       "valid": "tri_horizontal"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|shapes_disjoint|single_shape|no_shapes"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _poly(rng, n):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _corner_poly(rng):
    """A connected 4-7 cell polyomino that contains (0,0) and is <=5 wide/tall,
    so all three shapes share their (0,0) corner (guaranteed overlap). Larger,
    more varied shapes -> larger union bbox (output dims) + richer overlap map."""
    for _ in range(40):
        cells = _poly(rng, rng.randint(4, 7))
        bh = max(r for r, _ in cells) + 1
        bw = max(c for _, c in cells) + 1
        if (0, 0) in cells and bw <= 5 and bh <= 5:
            return cells
    return [(0, 0), (1, 0), (1, 1), (0, 1)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly 3 distinct non-bg colors (one per blob)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = set(grid[r][c] for r in range(h) for c in range(w)) - {0}
    if len(colors) != 3:
        errs.append(f"expected exactly 3 distinct non-bg blob colors, got {len(colors)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 20, 22)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 22, 26)
    else:
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 20, 24)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = list(range(2, 10)); rng.shuffle(palette)
    # slots spaced 7 apart so <=5-wide shapes never touch (separate components)
    for i, c0 in enumerate((1, 8, 15)):
        paint_at(g, 1, c0, _corner_poly(rng), palette[i])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 15
    g = full_grid(h, w, 0)
    if name == "shapes_disjoint":
        # normalized shapes share NO cells → output is all 0 (empty union counts)
        s1 = [(0, 0), (1, 0)]
        s2 = [(0, 1), (1, 1)]
        s3 = [(2, 0), (2, 1)]
        paint_at(g, 1, 1, s1, 4)
        paint_at(g, 1, 6, s2, 6)
        paint_at(g, 1, 11, s3, 7)
        return g
    if name == "single_shape":
        # one shape only → counts collapse to count=1, output is all 0
        paint_at(g, 1, 1, [(0, 0), (1, 0), (1, 1)], 4)
        return g
    if name == "no_shapes":
        # empty grid → no cells to count
        return g
    return g
