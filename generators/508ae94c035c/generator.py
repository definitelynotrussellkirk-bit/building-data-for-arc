"""Generator for additional_bank:H6 — pack horizontal+vertical line objects.

Rule: split objects into horizontal lines (1 row) and vertical lines
(1 column). Sort each group by size desc, then color asc. Output is a
2-row pack: top row = horizontal lines separated by 0; bottom row =
vertical lines (each laid horizontally) separated by 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_horiz (no horizontal lines → top output row is empty),
no_vert (no vertical lines → bottom output row is empty), tied_sizes
(≥2 lines share size → "by-size desc" sort uses color tiebreaker).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "508ae94c035c"
VERSION = "2.0.1"
TASK_ID = "508ae94c035c"
SUMMARY = (
    "0-bg grid (h, w ~8-12) with 1-3 HORIZONTAL line objects "
    "(single-row runs of length 2-w) AND 1-3 VERTICAL line "
    "objects (single-column runs of length 2-h). All in "
    "distinct non-bg colors. Lines isolated by ≥1 bg cell. "
    "Rule: extract objects. Split into horizontal (all cells "
    "share one row) and vertical (share one col). Sort each "
    "group by (size DESC, color ASC). Top output row = "
    "horizontal lines laid out left-to-right, each painted "
    "in its color, separated by 1 zero. Bottom row = vertical "
    "lines (laid horizontally as runs of their color), "
    "separated by 1 zero. Output: 2-row grid sized to max(top, "
    "bottom)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "every non-bg object is either a single row or a single column run",
    "all line objects have distinct colors (so packed output is well-defined)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_horiz", "no_vert", "tied_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..12", "valid": "6..14"},
    "grid_w":            {"type": "int", "default": "rng 8..12", "valid": "6..14"},
    "n_horiz":           {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "n_vert":            {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..6", "valid": "2..6"},
    "position_bias":     {"type": "str", "default": "horiz_plus_vert_lines",
                          "valid": "horiz_plus_vert_lines"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..6", "valid": "2..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _row_free(g, r, c1, c2):
    h, w = len(g), len(g[0])
    if r < 0 or r >= h:
        return False
    for r2 in (r - 1, r, r + 1):
        if 0 <= r2 < h:
            for c in range(max(0, c1 - 1), min(w, c2 + 2)):
                if g[r2][c] != 0:
                    return False
    return True


def _col_free(g, c, r1, r2):
    h, w = len(g), len(g[0])
    if c < 0 or c >= w:
        return False
    for c2 in (c - 1, c, c + 1):
        if 0 <= c2 < w:
            for r in range(max(0, r1 - 1), min(h, r2 + 2)):
                if g[r][c2] != 0:
                    return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 non-zero components; at least one is a horizontal line (all cells in same row)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    visited = [[False] * w for _ in range(h)]
    def flood(r0, c0):
        cells = []
        stack = [(r0, c0)]
        visited[r0][c0] = True
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                rr, cc = r+dr, c+dc
                if 0 <= rr < h and 0 <= cc < w and not visited[rr][cc] and grid[rr][cc] != 0:
                    visited[rr][cc] = True
                    stack.append((rr, cc))
        return cells
    components = []
    for r in range(h):
        for c in range(w):
            if not visited[r][c] and grid[r][c] != 0:
                components.append(flood(r, c))
    if len(components) < 2:
        errs.append(f"expected >=2 line objects, found {len(components)}")
    else:
        has_horiz = any(len({r for r, _ in comp}) == 1 for comp in components)
        has_vert = any(len({c for _, c in comp}) == 1 for comp in components)
        if not has_horiz:
            errs.append("no horizontal line object found (single-row)")
        if not has_vert:
            errs.append("no vertical line object found (single-col)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_h = ctx.draw_int("n_horiz", 1, 1)
        n_v = ctx.draw_int("n_vert", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n_h = ctx.draw_int("n_horiz", 3, 3)
        n_v = ctx.draw_int("n_vert", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        n_h = ctx.draw_int("n_horiz", 1, 3)
        n_v = ctx.draw_int("n_vert", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_h + n_v)
    for i in range(n_h):
        color = palette[i]
        for _ in range(40):
            length = rng.randint(2, max(2, w - 4))
            r = rng.randint(0, h - 1)
            c1 = rng.randint(0, w - length)
            c2 = c1 + length - 1
            if _row_free(g, r, c1, c2):
                for c in range(c1, c2 + 1):
                    g[r][c] = color
                break
    for i in range(n_v):
        color = palette[n_h + i]
        for _ in range(40):
            length = rng.randint(2, max(2, h - 4))
            c = rng.randint(0, w - 1)
            r1 = rng.randint(0, h - length)
            r2 = r1 + length - 1
            if _col_free(g, c, r1, r2):
                for r in range(r1, r2 + 1):
                    g[r][c] = color
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_horiz":
        # No horizontal lines — top output row empty.
        for r in range(2, 6): g[r][2] = 4
        for r in range(2, 5): g[r][6] = 6
        return g
    if name == "no_vert":
        # No vertical lines — bottom output row empty.
        for c in range(2, 6): g[2][c] = 4
        for c in range(2, 5): g[5][c] = 6
        return g
    if name == "tied_sizes":
        # Two horizontal lines share size — color tiebreaker decides.
        for c in range(2, 6): g[1][c] = 4   # length 4
        for c in range(2, 6): g[3][c] = 6   # length 4 (tied)
        for r in range(5, 8): g[r][1] = 7
        return g
    return g
