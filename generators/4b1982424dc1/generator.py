"""Generator for additional_bank:E5 — extend horizontal length-3 8-bars.

Rule: each exact horizontal length-3 bar of color 8 is extended one cell
at each open end.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_bars,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_bars, all_distractors, bars_at_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4b1982424dc1"
VERSION = "2.0.0"
TASK_ID = "4b1982424dc1"
SUMMARY = (
    "0-bg grid (h×w, ~6-10 by ~8-12) with 2-4 EXACT horizontal "
    "length-3 BARS of color 8 (cyan) in distinct rows, each "
    "with at least 1 cell of bg on both sides (so extension "
    "has room). Plus 1-2 DISTRACTOR color-8 shapes (vertical "
    "bars, singletons, or longer bars) that are NOT exact "
    "horizontal length-3 bars. Rule: for each connected color-8 "
    "component, check if it's an exact horizontal length-3 bar "
    "(3 cells, all same row, cols form contiguous span of 3). "
    "If yes, extend by painting cell to the left of leftmost "
    "and cell to the right of rightmost (if in-bounds and bg). "
    "If no, leave unchanged."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-4 exact horizontal length-3 bars of color 8 in distinct rows",
    "bar endpoints have open background cells (extension has room)",
    "1-2 distractor color-8 shapes that are NOT 3-length horizontal bars",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_bars", "all_distractors", "bars_at_edge")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_bars":         {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "horiz_3bars_with_room_at_ends",
                       "valid": "horiz_3bars_with_room_at_ends"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
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
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
        n_bars = ctx.draw_int("n_bars", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n_bars = ctx.draw_int("n_bars", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        n_bars = ctx.draw_int("n_bars", 2, 4)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    # Bars must land in PAIRWISE NON-ADJACENT rows: two length-3 bars in
    # adjacent rows over shared columns 4-connect into a 2x3 block, which is NOT
    # an exact horizontal length-3 bar -> the rule wouldn't extend it (identity).
    used_rows: list[int] = []
    for _ in range(n_bars):
        rows = [r for r in range(h)
                if all(abs(r - ur) >= 2 for ur in used_rows)]
        if not rows:
            break
        r = rows[rng.randint(0, len(rows) - 1)]
        # start at col >=2 so col 0/1 stay clear: the left extension lands on
        # col c-1 (bg) and the col-0 vertical distractor can't merge with a bar.
        c = rng.randint(2, w - 4)
        for dc in range(3):
            g[r][c + dc] = 8
        used_rows.append(r)
    if h >= 3:
        g[0][0] = g[1][0] = 8
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """At least one color-8 component must be an EXACT isolated horizontal
    length-3 bar with bg on both ends, so the extend rule fires. Returns
    violation list."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    for sr in range(h):
        for sc in range(w):
            if seen[sr][sc] or grid[sr][sc] != 8:
                continue
            stack = [(sr, sc)]; seen[sr][sc] = True; cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == 8):
                        seen[nr][nc] = True; stack.append((nr, nc))
            rs = {r for r, _ in cells}; cs = sorted(c for _, c in cells)
            if (len(cells) == 3 and len(rs) == 1
                    and cs == list(range(cs[0], cs[0] + 3))):
                r = next(iter(rs))
                lc, rc = cs[0] - 1, cs[-1] + 1
                if lc >= 0 and rc < w and grid[r][lc] == 0 and grid[r][rc] == 0:
                    return []
    return ["no extendable horizontal length-3 8-bar -> extend rule is identity"]


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_bars":
        # no length-3 bars → rule has nothing to extend
        g[2][1] = 8; g[2][2] = 8   # length-2
        g[4][5] = 8                  # singleton
        return g
    if name == "all_distractors":
        # only distractors (vertical bars, 4-bars, scattered 8s) → no length-3 horiz bars
        g[1][1] = 8; g[2][1] = 8; g[3][1] = 8   # vertical
        g[5][3] = 8; g[5][4] = 8; g[5][5] = 8; g[5][6] = 8   # length-4
        g[2][8] = 8                              # singleton
        return g
    if name == "bars_at_edge":
        # length-3 bars touching grid edge → extension would clip out of bounds
        g[1][0] = 8; g[1][1] = 8; g[1][2] = 8   # left edge
        g[4][w - 3] = 8; g[4][w - 2] = 8; g[4][w - 1] = 8   # right edge
        return g
    return g
