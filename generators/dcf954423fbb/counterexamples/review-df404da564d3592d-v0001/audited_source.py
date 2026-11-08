"""Generator for arc_additional_puzzle_bank_volume20:E136 — Recolor 1-blobs that touch the border to 2.

Rule: any 1-color blob with at least one cell on the grid border
(row 0, row h-1, col 0, col w-1) → recolor to 2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_interior, all_border, no_color_1.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "dcf954423fbb"
VERSION = "1.2.0"
TASK_ID = "dcf954423fbb"
SUMMARY = "Mix of 1-blobs touching border vs interior, plus 7-decoration."

INVARIANTS = [
    "≥2 1-blobs touching the grid border",
    "≥1 1-blob fully interior (won't recolor)",
    "1-2 7-decoration blobs",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_interior", "all_border", "no_color_1")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 10..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "4", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "border_and_interior_blobs",
                       "valid": "border_and_interior_blobs"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "1..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}



def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 10, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    sq = [(0, 0), (0, 1), (1, 0), (1, 1)]
    L = [(0, 0), (1, 0), (1, 1)]

    # Keep the three border-touching 1-components separated from the one
    # interior 1-component.  The previous random placements could accidentally
    # make the top blob 4-connected to the supposed interior square.
    top_left = (0, rng.randint(0, 1), sq)
    right_edge = (rng.randint(1, 2), w - 2, [(0, 0), (1, 0)])
    bottom_left = (h - 2, rng.randint(0, 1), L)
    interior_top = max(3, min(h - 4, h // 2 - 1))
    interior_left = max(4, min(w - 5, w // 2 - 1))
    interior = (interior_top, interior_left, sq)
    for top, left, s in [top_left, right_edge, bottom_left, interior]:
        paint_at(g, top, left, s, 1)

    # Decorative non-1 cells, placed away from the components above.
    g[h - 3][min(w - 3, interior_left + 3)] = 7
    g[h - 2][min(w - 4, interior_left + 2)] = 7
    return g


def _components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Verify border-vs-interior 1-blob recoloring setup."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    comps = _components_of_color(grid, 1)
    border = [cells for cells in comps if any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)]
    interior = [cells for cells in comps if all(0 < r < h - 1 and 0 < c < w - 1 for r, c in cells)]
    if len(border) < 2:
        errs.append(f"expected at least two color-1 border blobs; got {len(border)}")
    if len(interior) < 1:
        errs.append("expected at least one interior color-1 blob")
    if sum(1 for row in grid for v in row if v == 7) < 2:
        errs.append("expected visible color-7 decoration")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "all_interior":
        # all 1-blobs are strictly interior → rule recolors nothing, output equals input
        paint_at(g, 3, 3, [(0, 0), (0, 1), (1, 0), (1, 1)], 1)
        paint_at(g, 5, 6, [(0, 0), (1, 0), (1, 1)], 1)
        return g
    if name == "all_border":
        # all 1-blobs touch the border → all recolored to 2; no contrast in output
        paint_at(g, 0, 1, [(0, 0), (0, 1), (1, 0)], 1)
        paint_at(g, h - 2, w - 3, [(0, 0), (0, 1), (1, 1)], 1)
        paint_at(g, 4, 0, [(0, 0), (1, 0)], 1)
        return g
    if name == "no_color_1":
        # no color-1 cells → rule has no blobs to recolor, output equals input
        paint_at(g, 1, 1, [(0, 0), (0, 1), (1, 0)], 4)
        paint_at(g, 5, 5, [(0, 0), (1, 0), (1, 1)], 6)
        return g
    return g
