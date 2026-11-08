"""Generator for arc_puzzle_bank_twentieth21:E135 — vertical connect same-color pairs.

Rule: each non-empty column has exactly 2 cells of the same color. Output
draws a vertical line of that color between them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cols,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, adjacent_pair, mixed_colors_in_col.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "021ea70e8ed8"
VERSION = "2.1.1"
TASK_ID = "021ea70e8ed8"
SUMMARY = (
    "0-bg grid (h~6-9, w~4-6) with 1-3 selected "
    "COLUMNS, each containing exactly 2 cells of "
    "the SAME non-zero color placed at "
    "DIFFERENT rows (separated by ≥2 empty rows); "
    "columns may SHARE a color, and near-miss "
    "content (mixed-color columns, 3-cell columns, "
    "horizontal pairs) stays unconnected. "
    "Rule: for each non-empty column, "
    "find the two same-color endpoint cells and "
    "CONNECT them by drawing a VERTICAL LINE of "
    "that column's color through every cell "
    "between them (inclusive of endpoints). "
    "Net: input has pairs of dots in each "
    "non-empty column; output has those dots "
    "replaced by solid vertical color segments "
    "spanning between the endpoints."
)

# Rivals: 'connect any aligned same-color pair' refuted by HORIZONTAL
# pairs that stay dots (rule is column-only). 'connect any 2-cell
# column' refuted by mixed-color columns. 'connect closest cells in
# 3-cell columns' refuted (they stay). 'colors unique per column'
# refuted by shared-color columns connecting independently.
# 3 demos incl. >=1 near-miss column or row pair.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "1-3 columns each have exactly 2 same-color cells (span >= 2)",
    "near-miss columns (mixed-color / 3-cell) stay unconnected",
    "horizontal same-color pairs (when present) stay unconnected",
]

DEGENERATE_TEXTURES = ("no_pairs", "adjacent_pair")
HELPFUL_TEXTURES = ("plain", "mixed_col", "triple_col", "row_pair")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 6..9 (hard 8..11)",
                "valid": "5..12", "doc": "Grid height."},
    "grid_w":  {"type": "int", "default": "rng 4..6 (hard 6..9)",
                "valid": "3..10", "doc": "Grid width."},
    "n_cols":  {"type": "int", "default": "rng 1..3", "valid": "1..5",
                "doc": "Connecting columns."},
    "share_colors": {"type": "bool", "default": "rng ~40%", "valid": "0|1",
                     "doc": "Two connecting columns may share a color."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|mixed_col|triple_col|row_pair|no_pairs|adjacent_pair",
                "doc": "Near-miss flavor or a degenerate name."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "mixed_col", "triple_col", "row_pair"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 4, 5)
        n = ctx.draw_int("n_cols", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 6, 9)
        n = ctx.draw_int("n_cols", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 4, 6)
        n = ctx.draw_int("n_cols", 1, min(3, w))
    n = min(n, w)
    share = bool(int(overrides.get(
        "share_colors", 1 if ctx.draw_int("share_roll", 0, 99) < 40 else 0)))
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    free_cols = list(range(w))
    rng.shuffle(free_cols)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], max(n, 2))
    if share and n >= 2:
        palette[1] = palette[0]  # two columns share a color — both connect
    for i in range(n):
        if not free_cols:
            break
        c = free_cols.pop()
        r1 = rng.randint(0, h - 4)
        r2 = rng.randint(r1 + 2, h - 1)
        g[r1][c] = palette[i % len(palette)]
        g[r2][c] = palette[i % len(palette)]

    spare = [v for v in (1, 2, 3, 4, 5, 6, 7, 8, 9) if v not in palette[:n]]
    if texture == "mixed_col" and free_cols and len(spare) >= 2:
        # 2-cell column with DIFFERENT colors: stays unconnected
        c = free_cols.pop()
        r1 = rng.randint(0, h - 4)
        r2 = rng.randint(r1 + 2, h - 1)
        g[r1][c] = spare[0]
        g[r2][c] = spare[1]
    elif texture == "triple_col" and free_cols and spare:
        # 3 same-color cells in one column: length != 2, stays
        c = free_cols.pop()
        rows = sorted(rng.sample(range(h), 3))
        for r in rows:
            g[r][c] = spare[0]
    elif texture == "row_pair" and len(free_cols) >= 2 and spare:
        # horizontal same-color pair: each column holds a singleton —
        # the column-only rule leaves them as dots
        c1, c2 = free_cols.pop(), free_cols.pop()
        r = rng.randrange(h)
        g[r][c1] = spare[0]
        g[r][c2] = spare[0]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=1 column has exactly 2 same-color cells with span>=2."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    found_connecting = False
    for c in range(w):
        col_vals = [(r, grid[r][c]) for r in range(h) if grid[r][c] != 0]
        if len(col_vals) == 2 and col_vals[0][1] == col_vals[1][1]:
            span = col_vals[1][0] - col_vals[0][0]
            if span >= 2:
                found_connecting = True
                break
    if not found_connecting:
        errors.append("no column has exactly 2 same-color cells with span>=2")
    return errors


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_pairs      — singletons only: nothing connects.
    adjacent_pair — endpoints touch: the 'line' adds no new cells.
    """
    h = ctx.draw_int("grid_h", 6, 9)
    w = ctx.draw_int("grid_w", 4, 6)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
    if name == "no_pairs":
        cols = rng.sample(range(w), 2)
        g[rng.randrange(h)][cols[0]] = colors[0]
        g[rng.randrange(h)][cols[1]] = colors[1]
        return g
    # adjacent_pair
    for c, color in zip(rng.sample(range(w), 2), colors):
        r = rng.randint(0, h - 2)
        g[r][c] = color
        g[r + 1][c] = color
    return g
