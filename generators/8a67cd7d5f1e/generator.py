"""Generator for arc_puzzle_bank_21_set5_s:S5_H6 — color-count bar chart.

REAL rule (the "gallery pack" docstring was WRONG): count the cells of colors
1, 2 and 3. Output a 3-row grid (rows = colors 1,2,3) of width = the max
count, where row r is left-filled with count[r] cells of color r, rest 0 -- a
horizontal bar chart of the three color counts.

The old generator scattered random-colored motifs, so the 1/2/3 counts were
incidental -> few distinct bar charts (distinct=15). This scatters a chosen
number of color-1, color-2 and color-3 cells.

Combinatorial axes: the three counts, scatter positions, grid size.
Degenerates: identical_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a67cd7d5f1e"
VERSION = "2.1.0"  # WRONG-TASK + distinct=15: rule is a 3-row count bar chart of colors 1/2/3 (output 3 x max-count); generator scattered random-colored motifs. Scatter chosen counts of color 1/2/3 cells; vary counts + grid -> bar chart varies.
TASK_ID = "8a67cd7d5f1e"
SUMMARY = "0-bg grid scattered with n1 color-1 cells, n2 color-2, n3 color-3. Rule outputs a 3-row bar chart (rows = colors 1,2,3) of width = max count, each row left-filled with its count. The three counts, positions and grid size vary."

INVARIANTS = [
    "background is 0",
    "colors 1, 2, and 3 each appear at least once",
    "the three counts are not all equal, so the bar-chart lengths differ",
    "no nonzero colors outside {1, 2, 3} appear in default instances",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identical_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..15"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "spread_motifs",
                       "valid": "spread_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 9, 11); cmax = 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 12, 16); cmax = 9
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 11, 14); cmax = 7
    rng = ctx.draw_rng("layout")
    # Counts of colors 1, 2, 3 — keep every row present and make at
    # least one length differ, otherwise the bar-chart rule is under-taught.
    for _ in range(40):
        counts = [rng.randint(1, cmax) for _ in range(3)]
        if len(set(counts)) > 1 and sum(counts) <= h * w:
            break
    else:
        counts = [1, 2, 3]
    g = full_grid(h, w, 0)
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    idx = 0
    for color, cnt in zip((1, 2, 3), counts):
        for _ in range(cnt):
            r, c = cells[idx]; idx += 1
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "identical_motifs":
        # all motifs are the same shape → vertical pack reveals nothing structural
        for (r, c) in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        for (r, c) in [(1, 7), (1, 8), (2, 7)]: g[r][c] = 6
        for (r, c) in [(6, 3), (6, 4), (7, 3)]: g[r][c] = 8
        return g
    if name == "single_motif":
        # only one motif → no gallery to pack, no comparison
        for (r, c) in [(3, 4), (3, 5), (4, 4), (4, 5), (5, 5)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # multiple motifs share one color → predicate "distinct colors" violated
        for (r, c) in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        for (r, c) in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 4
        for (r, c) in [(8, 8), (8, 9), (9, 8)]: g[r][c] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    counts = [sum(v == color for row in grid for v in row) for color in (1, 2, 3)]
    msgs = []
    if any(c == 0 for c in counts):
        msgs.append("colors 1, 2, and 3 must each appear at least once")
    if len(set(counts)) == 1:
        msgs.append("bar-chart counts must not all be equal")
    vals = {v for row in grid for v in row if v != 0}
    if vals - {1, 2, 3}:
        msgs.append("default bar-chart inputs should only use colors 1, 2, and 3")
    return msgs
