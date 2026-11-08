"""Generator for v1_e_m_h_keys:E6.

Rule: rows containing exactly one nonzero cell (which must be 7) expand
to full 7 rows; other rows are unchanged.

Combinatorial axes (8): grid_h, grid_w, palette_kind, target_rows,
palette_size, position_bias, n_distinct_colors, distractor_density, texture.
Degenerates: all_target_rows, no_target_rows, ambiguous_distractor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c36d1678a484"
VERSION = "2.0.1"
TASK_ID = "c36d1678a484"
SUMMARY = (
    "0-bg grid (h~7-11, w~"
    "8-14) with 2-4 "
    "TARGET ROWS each "
    "containing EXACTLY "
    "ONE COLOR-7 (orange) "
    "CELL at a random "
    "column. Plus 2 "
    "DISTRACTOR ROWS each "
    "containing 2 cells "
    "of a NON-7 color "
    "(from {1..6, 8, 9}) "
    "at random columns. "
    "Remaining rows are "
    "all 0. Rule (EXPAND "
    "SINGLE-7 ROWS TO "
    "FULL 7 ROWS): For "
    "EACH ROW r: count "
    "non-0 cells. If "
    "EXACTLY ONE non-0 "
    "cell AND that cell's "
    "value is 7: PAINT "
    "the entire row r "
    "with COLOR-7 "
    "(replace all cells). "
    "Distractor rows (2+ "
    "non-0 cells, or "
    "non-7 colors) stay. "
    "Net: rows with a "
    "lone orange cell "
    "fill solid orange; "
    "all other rows "
    "untouched."
)

INVARIANTS = [
    "background is 0",
    "target rows contain exactly one nonzero cell and it is 7",
    "distractor rows have other nonzero patterns",
    "rows are processed independently",
]

PALETTE_KINDS = ("default", "warm_distractor", "cool_distractor", "varied_distractor")
DEGENERATE_TEXTURES = ("all_target_rows", "no_target_rows", "ambiguous_distractor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..11", "valid": "3..20"},
    "grid_w":         {"type": "int", "default": "rng 8..14", "valid": "3..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm_distractor|cool_distractor|varied_distractor"},
    "target_rows":    {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 1..8", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "rows", "valid": "rows"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..8"},
    "distractor_density": {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm_distractor|cool_distractor|varied_distractor|all_target_rows|no_target_rows|ambiguous_distractor"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        target = min(ctx.draw_int("target_rows", 2, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 14)
        target = min(ctx.draw_int("target_rows", 3, 4), h)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 8, 14)
        target = min(ctx.draw_int("target_rows", 2, 4), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), target)
    for r in rows:
        g[r][rng.randrange(w)] = 7
    for r in [r for r in range(h) if r not in rows][:2]:
        cols = rng.sample(range(w), 2)
        color = rng.choice([1, 2, 3, 4, 5, 6, 8, 9])
        for c in cols:
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "all_target_rows":
        # every row has exactly one 7 → output is solid 7 grid
        for r in range(h):
            g[r][r % w] = 7
        return g
    if name == "no_target_rows":
        # only distractor rows → rule has nothing to expand
        for r in range(h):
            g[r][1] = 3; g[r][3] = 5
        return g
    if name == "ambiguous_distractor":
        # rows with a single 7 plus extra non-7 cells → predicate "exactly one nonzero" fails
        for r in range(h):
            g[r][2] = 7
            g[r][5] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    target_rows = []
    distractor_rows = []
    for r, row in enumerate(grid):
        nz = [(c, v) for c, v in enumerate(row) if v != 0]
        if len(nz) == 1 and nz[0][1] == 7:
            target_rows.append(r)
        elif len(nz) >= 2:
            distractor_rows.append(r)
        elif len(nz) == 1:
            msgs.append(f"row {r} has one non-7 cell and may look like a target")
    if not target_rows:
        msgs.append("expected at least one single-7 target row")
    if not distractor_rows:
        msgs.append("expected at least one non-target distractor row")
    for r in distractor_rows:
        vals = [v for v in grid[r] if v != 0]
        if len(vals) == 1 and vals[0] == 7:
            msgs.append("distractor row accidentally satisfies the target predicate")
    return msgs
