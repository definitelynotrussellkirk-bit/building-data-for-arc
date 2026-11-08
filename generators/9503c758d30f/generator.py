"""Generator for arc_additional_puzzles_21_set3:M18.

Rule: for each SOLID color-6 rectangle, paint color 2 at the 4 cells
diagonally just outside its bbox (one step past each corner), where
that cell is in-bounds and currently empty.

Combinatorial axes: grid size, number of solid 6-rects (1-4), their
sizes and positions.
Degenerates: no_rects, rect_at_edge, corners_already_marked.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9503c758d30f"
VERSION = "2.0.1"  # add self_check  # diversity: N random solid 6-rects (size/pos) + grid (was 2 fixed rects)
TASK_ID = "9503c758d30f"
SUMMARY = (
    "0-bg grid (size varies). 1-4 SOLID color-6 (magenta) RECTANGLES of "
    "random sizes/positions, each kept >=1 cell from every grid edge and "
    "placed apart (a 1-cell gap all around, so the diagonal-corner cells "
    "are in-bounds, empty, and never shared). Rule: for each solid 6-rect, "
    "paint COLOR 2 (red) at the four cells diagonally one step outside its "
    "bbox corners. The grid size, the number of rects and their "
    "sizes/positions all vary freely (was 2 fixed rects)."
)

INVARIANTS = [
    "1-4 non-touching solid color-6 rectangles",
    "each rect is >=1 cell from every edge (its 4 diagonal corners are in-bounds)",
    "each rect's 4 diagonal-corner cells start empty (rule paints them red)",
]

PALETTE_KINDS = ("default", "small_rects", "tall_rects", "wide_rects")
DEGENERATE_TEXTURES = ("no_rects", "rect_at_edge", "corners_already_marked")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|small_rects|tall_rects|wide_rects"},
    "num_rects":      {"type": "int", "default": "varies", "valid": "1..4"},
    "rect_size":      {"type": "str", "default": "varies", "valid": "varies"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|small_rects|tall_rects|wide_rects|"
                                "no_rects|rect_at_edge|corners_already_marked"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥4 color-6 cells (at least 1 solid rect); no color-2 in input."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    n6 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 6)
    has_2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if n6 < 4:
        errs.append(f"expected ≥4 color-6 cells (≥1 solid rect); got {n6}")
    if has_2:
        errs.append("color 2 (red) found in input — rule writes 2 for corners; input should not have it")
    return errs


def _solid(g, r1, c1, r2, c2, color):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            g[r][c] = color


def _reserve_expanded(occ, top, left, bh, bw, h, w):
    """Reserve the bbox plus a 1-cell ring (the diagonal corners + edges)."""
    for r in range(top - 1, top + bh + 1):
        for c in range(left - 1, left + bw + 1):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top - 1, top + bh + 1):
        for c in range(left - 1, left + bw + 1):
            if 0 <= r < h and 0 <= c < w:
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
        hr, wr, nr, szr = (9, 11), (9, 11), (1, 2), (2, 3)
    elif difficulty == "hard":
        hr, wr, nr, szr = (13, 16), (13, 16), (3, 4), (2, 4)
    else:
        hr, wr, nr, szr = (10, 13), (10, 13), (2, 3), (2, 4)

    for _attempt in range(50):
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)
        want = rng.randint(*nr)
        placed = 0
        for _ in range(want):
            for _t in range(40):
                bh = rng.randint(*szr); bw = rng.randint(*szr)
                if bh > h - 2 or bw > w - 2:
                    continue
                # keep >=1 cell from every edge so all 4 diagonal corners are in-bounds
                top = rng.randint(1, h - 1 - bh)
                left = rng.randint(1, w - 1 - bw)
                if _reserve_expanded(occ, top, left, bh, bw, h, w):
                    _solid(g, top, left, top + bh - 1, left + bw - 1, 6)
                    placed += 1
                    break
        if placed >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_rects":
        return g
    if name == "rect_at_edge":
        # rect at top-left corner — its outer diagonal cells are out of bounds
        _solid(g, 0, 0, 1, 2, 6)
        _solid(g, h - 4, w - 4, h - 2, w - 2, 6)
        return g
    if name == "corners_already_marked":
        # diagonal corners pre-painted with 2 — rule finds no fresh cells
        _solid(g, 1, 1, 2, 3, 6)
        for r, c in [(0, 0), (0, 4), (3, 0), (3, 4)]:
            g[r][c] = 2
        return g
    return g
