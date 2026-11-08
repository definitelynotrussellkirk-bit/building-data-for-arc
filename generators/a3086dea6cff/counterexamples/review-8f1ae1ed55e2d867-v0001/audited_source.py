"""Generator for arc_additional_puzzles_21_set4:M26 — connect aligned same-color pairs.

Rule: for each color appearing exactly twice in the input, if the two
cells share a row, paint the horizontal segment between them; if they
share a column, paint the vertical segment. Else leave them alone.
Colors appearing 0, 1, 3+ times are not connected.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a3086dea6cff"
VERSION = "2.0.1"
TASK_ID = "a3086dea6cff"
SUMMARY = (
    "0-bg grid with N (2-4) pairs of same-colored cells, each pair in "
    "a unique non-bg color. Each pair shares EITHER a row OR a column "
    "(but not both — they're at distinct positions). Rule: for each "
    "color appearing EXACTLY 2 times in the grid: if the two cells "
    "share a row, paint the horizontal segment between them (inclusive); "
    "if they share a column, paint the vertical segment. The segment "
    "uses the pair's color. Colors with count ≠ 2 or non-aligned pairs "
    "stay as-is."
)

# Rivals: 'output is input' refuted by demos (segments drawn).
# 'use a fixed color for segments' refuted by demos with different
# pair colors drawing different segments. 'draw L-shape (not straight)'
# refuted by demos with axis-aligned pairs producing straight segments.
# 'connect all pairs (3 or more cells of same color)' refuted by demos
# where 3+ cells of one color don't all get connected. 'connect
# diagonally-aligned pairs too' refuted by demos with non-aligned
# pairs staying as 2 isolated cells. 3 demos with multiple axis-aligned
# pairs in mixed orientations pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 distinct pair colors, each appearing exactly 2 times",
    "each pair shares EITHER row OR column with separation ≥3 (so segment is visible)",
    "pair colors are distinct (so segments are unambiguously colored)",
    "pairs don't cross each other in any obvious way",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard.
AXES = {
    "grid_h":  {"type": "int", "default": "rng 9..12", "valid": "7..16",
                "doc": "Grid height (easy 7..9, medium 9..12, hard 12..16)."},
    "grid_w":  {"type": "int", "default": "rng 10..13", "valid": "8..16",
                "doc": "Grid width (easy 8..10, medium 10..13, hard 12..16)."},
    "n_pairs": {"type": "int", "default": "rng 2..3", "valid": "1..4",
                "doc": "Same-color pairs to connect (easy 1..2, medium 2..3, hard 3..4)."},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; each non-bg color appears exactly twice;
    each pair shares a row or column."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    positions: dict[int, list[tuple]] = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                positions.setdefault(v, []).append((r, c))
    if not positions:
        errs.append("no non-bg cells")
        return errs
    for color, cells in positions.items():
        if len(cells) != 2:
            errs.append(f"color {color} appears {len(cells)} times (expected 2)")
            break
        (r1, c1), (r2, c2) = cells
        if r1 != r2 and c1 != c2:
            errs.append(f"color {color} pair at {cells} is not row/col aligned")
            break
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        n_pairs = ctx.draw_int("n_pairs", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        n_pairs = ctx.draw_int("n_pairs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
        n_pairs = ctx.draw_int("n_pairs", 2, 3)
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_pairs)
    for color in colors:
        for _ in range(60):
            orient = rng.choice(["h", "v"])
            if orient == "h":
                r = rng.randint(0, h - 1)
                c1 = rng.randint(0, w - 5); c2 = rng.randint(c1 + 3, w - 1)
                if g[r][c1] != 0 or g[r][c2] != 0:
                    continue
                # Check segment is clear (so output is unambiguous)
                if any(g[r][c] != 0 for c in range(c1 + 1, c2)):
                    continue
                g[r][c1] = color
                g[r][c2] = color
                break
            else:
                c = rng.randint(0, w - 1)
                r1 = rng.randint(0, h - 5); r2 = rng.randint(r1 + 3, h - 1)
                if g[r1][c] != 0 or g[r2][c] != 0:
                    continue
                if any(g[r][c] != 0 for r in range(r1 + 1, r2)):
                    continue
                g[r1][c] = color
                g[r2][c] = color
                break
    return g
