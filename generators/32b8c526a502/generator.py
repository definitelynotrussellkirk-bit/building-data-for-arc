"""Generator for arc_additional_puzzles_21_set12_bundle:E82.

Rule: count cells of color 1, 2, 3; emit 3-row bar chart of those
counts. Row 0 = 1s, row 1 = 2s, row 2 = 3s. Width = max count.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_colors,
palette_size, position_bias, n_distinct_colors, count_spread, texture.
Degenerates: equal_counts, missing_color, no_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "32b8c526a502"
VERSION = "3.1.0"  # +self_check  # distinct=54 (38% dup): output = 3 x max(counts) bar-chart of counts of colors 1/2/3, determined by the (c1,c2,c3) triple. Was sample(range(1,6),3) -> ~60 triples. Now independent counts 1..cmax (may repeat) + bigger grids.
TASK_ID = "32b8c526a502"
SUMMARY = (
    "0-bg grid with SCATTERED cells of colors 1, 2, 3 at random "
    "non-overlapping positions; each color appears 1..cmax times (counts are "
    "independent and may repeat). Rule: count cells of each color (1,2,3) and "
    "emit a 3-row bar chart: row 0 = n1 cells of color 1 (left-aligned), row 1 "
    "= n2 of color 2, row 2 = n3 of color 3. Output dims = 3 × max(n1,n2,n3)."
)

INVARIANTS = [
    "1..cmax occurrences of each of {1, 2, 3}",
    "output is a 3-row bar chart of the three counts",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("equal_counts", "missing_color", "no_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_colors":       {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "count_spread":   {"type": "str", "default": "distinct", "valid": "distinct"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: each of colors 1, 2, 3 appears at least once; no unexpected colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    flat = [v for row in grid for v in row]
    for color in (1, 2, 3):
        if flat.count(color) == 0:
            errs.append(f"color {color} missing (expected ≥1 cell of each of 1, 2, 3)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output = 3 x max(counts) bar-chart of the counts of colors 1/2/3, so it is
    # fully determined by the (c1,c2,c3) triple. Was sample(range(1,6),3) -> only
    # ~60 distinct (distinct counts <=5). Now independent counts 1..cmax (may repeat).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 7, 9); cmax = 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 10, 12); cmax = 9
    else:
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 8, 11); cmax = 7
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    counts = [rng.randint(1, cmax) for _ in range(3)]
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    idx = 0
    for color, cnt in zip([1, 2, 3], counts):
        for _ in range(cnt):
            r, c = cells[idx]; idx += 1
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "equal_counts":
        # counts of 1, 2, 3 all equal → bar chart rows are identical, no signal
        for r, c, v in [(1, 1, 1), (1, 2, 1), (1, 3, 1),
                        (3, 1, 2), (3, 2, 2), (3, 3, 2),
                        (5, 1, 3), (5, 2, 3), (5, 3, 3)]:
            g[r][c] = v
        return g
    if name == "missing_color":
        # one of {1,2,3} has count 0 → bar chart row collapses
        for r, c in [(1, 1), (1, 2)]:
            g[r][c] = 1
        for r, c in [(3, 1), (3, 2), (3, 3), (3, 4)]:
            g[r][c] = 3
        return g
    if name == "no_cells":
        # empty grid → bar chart is trivially empty / undefined width
        return g
    return g
