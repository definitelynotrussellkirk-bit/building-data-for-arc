"""Generator for arc_additional_puzzles_21_set2:H10.

Rule: sort the 4 distinct-color blobs by color ascending, crop each to
its bounding box, and assemble a 2x2 layout (tl/tr/bl/br in color order)
separated by a 1-cell gap.

Combinatorial axes: grid size, the 4 blob shapes, their colors (which
set the tl/tr/bl/br order), and their positions.
Degenerates: only_three_blobs, all_same_color, five_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "b44242314fb7"
VERSION = "2.0.1"  # diversity: 4 random shapes + colors + positions + grid (was 4 fixed shapes ~9)
TASK_ID = "b44242314fb7"
SUMMARY = (
    "0-bg grid (size varies) with EXACTLY 4 non-touching BLOBS, each a "
    "connected polyomino in a distinct color, placed so their bounding "
    "boxes don't overlap. Rule: sort the blobs by color ascending, crop "
    "each to its bbox, and assemble a 2x2 grid (tl/tr/bl/br in color "
    "order) with a 1-cell gap between quadrants. The grid size, the 4 "
    "shapes, their colors (which set the quadrant order) and positions "
    "all vary freely (was 4 fixed shapes, ~9 distinct)."
)

INVARIANTS = [
    "exactly 4 non-touching blobs in 4 distinct colors",
    "each blob is a single connected component with its own clear bbox",
    "blob bounding boxes do not overlap (each crop is clean)",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("only_three_blobs", "all_same_color", "five_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|rainbow"},
    "num_blobs":      {"type": "int", "default": "4", "valid": "4"},
    "blob_size":      {"type": "str", "default": "varied", "valid": "varied"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|rainbow|"
                                "only_three_blobs|all_same_color|five_blobs"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 4 distinct non-bg colors (the 4 blobs)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) != 4:
        errs.append(f"expected exactly 4 distinct non-bg blob colors; found {sorted(colors)}")
    return errs


def _conn_poly(rng, size, maxd):
    for _ in range(80):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, c in cells); mc = min(c for r, c in cells)
        n = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return n
    return [(0, 0), (0, 1), (1, 0)]


def _reserve_bbox(occ, top, left, bh, bw, h, w):
    for r in range(top - 1, top + bh + 1):
        for c in range(left - 1, left + bw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, szr, md = (11, 13), (12, 15), (3, 4), 3
    elif difficulty == "hard":
        hr, wr, szr, md = (14, 18), (15, 20), (4, 6), 4
    else:
        hr, wr, szr, md = (11, 16), (13, 17), (3, 5), 4

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 4)
        placed = 0
        for col in colors:
            shape = _conn_poly(rng, rng.randint(*szr), md)
            bh = max(r for r, c in shape) + 1; bw = max(c for r, c in shape) + 1
            for _t in range(40):
                top = rng.randint(0, h - bh); left = rng.randint(0, w - bw)
                if _reserve_bbox(occ, top, left, bh, bw, h, w):
                    for r, c in shape:
                        g[top + r][left + c] = col
                    placed += 1
                    break
        if placed == 4:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 12, 15
    g = full_grid(h, w, 0)
    if name == "only_three_blobs":
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0)], 2)
        paint_at(g, 1, 8, [(0, 0), (0, 1), (0, 2)], 3)
        paint_at(g, 6, 1, [(0, 0), (1, 0), (1, 1)], 4)
        return g
    if name == "all_same_color":
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0)], 2)
        paint_at(g, 1, 8, [(0, 0), (0, 1), (0, 2)], 2)
        paint_at(g, 6, 1, [(0, 0), (1, 0), (1, 1)], 2)
        paint_at(g, 7, 10, [(0, 0), (0, 1), (1, 0), (1, 1)], 2)
        return g
    if name == "five_blobs":
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0)], 2)
        paint_at(g, 1, 8, [(0, 0), (0, 1), (0, 2)], 3)
        paint_at(g, 6, 1, [(0, 0), (1, 0), (1, 1)], 4)
        paint_at(g, 7, 10, [(0, 0), (0, 1), (1, 0), (1, 1)], 5)
        paint_at(g, 9, 7, [(0, 0), (0, 1)], 6)
        return g
    return g
