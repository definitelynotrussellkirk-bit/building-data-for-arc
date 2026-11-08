"""Generator for arc_puzzle_bank_21_set5_e:hard_e05 — beam intersections.

Rule: color-1 cells in row 0 launch vertical beams downward, color-2 cells
in column 0 launch horizontal beams rightward, and color-5 blockers stop beams.
The output keeps blockers and marks cells reached by both a horizontal and a
vertical beam with color 8.

Combinatorial axes (8): grid_h, grid_w, row_markers, col_markers,
blocker_count, blocker_position, density, texture.
Degenerates: no_top_markers, no_left_markers, blockers_hide_all.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8521aacbc580"
VERSION = "3.0.0"  # rewrite wrong motif-gallery generator to match canonical beam-intersection rule
TASK_ID = "8521aacbc580"

SUMMARY = (
    "0-bg grid with color-1 emitters on the top row, color-2 emitters on the "
    "left column, and color-5 blockers inside the grid. Horizontal beams cast "
    "rightward from each 2; vertical beams cast downward from each 1; blockers "
    "stop beams. Output keeps blockers and paints the cells reached by BOTH "
    "beam families as 8."
)

INVARIANTS = [
    "background is 0",
    "row 0 has 2-4 color-1 vertical beam emitters",
    "column 0 has 2-4 color-2 horizontal beam emitters",
    "at least one color-5 blocker is present and at least one intersection remains visible",
]

PALETTE_KINDS = ("default", "sparse", "blocked", "dense")
DEGENERATE_TEXTURES = ("no_top_markers", "no_left_markers", "blockers_hide_all")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "row_markers":    {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "col_markers":    {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "blocker_count":  {"type": "int", "default": "rng 1..4", "valid": "0..8"},
    "position_bias":  {"type": "str", "default": "beam_paths", "valid": "beam_paths"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _beamcast(grid, start, dr, dc):
    h, w = len(grid), len(grid[0])
    r, c = start[0] + dr, start[1] + dc
    out = []
    while 0 <= r < h and 0 <= c < w:
        if grid[r][c] == 5:
            break
        out.append((r, c))
        r += dr; c += dc
    return out


def _beam_intersections(grid):
    h, w = len(grid), len(grid[0])
    top_cols = [c for c in range(1, w) if grid[0][c] == 1]
    left_rows = [r for r in range(1, h) if grid[r][0] == 2]
    horiz = set()
    for r in left_rows:
        horiz.update(_beamcast(grid, (r, 0), 0, 1))
    vert = set()
    for c in top_cols:
        vert.update(_beamcast(grid, (0, c), 1, 0))
    return horiz & vert, len(top_cols) * len(left_rows)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        nr = ctx.draw_int("col_markers", 2, 2)
        nc = ctx.draw_int("row_markers", 2, 3)
        nb_lo, nb_hi = 1, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 16)
        nr = ctx.draw_int("col_markers", 3, 4)
        nc = ctx.draw_int("row_markers", 3, 4)
        nb_lo, nb_hi = 3, 6
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 14)
        nr = ctx.draw_int("col_markers", 2, 4)
        nc = ctx.draw_int("row_markers", 2, 4)
        nb_lo, nb_hi = 2, 4

    for _attempt in range(120):
        g = full_grid(h, w, 0)
        rows = sorted(rng.sample(range(1, h), min(nr, h - 1)))
        cols = sorted(rng.sample(range(1, w), min(nc, w - 1)))
        for c in cols:
            g[0][c] = 1
        for r in rows:
            g[r][0] = 2

        beam_cells = {(r, c) for r in rows for c in range(1, w)} | \
                     {(r, c) for c in cols for r in range(1, h)}
        # Put blockers on beam paths but never on the launcher cells.  Accept
        # only layouts where some potential intersections are blocked and some
        # remain visible; this exercises both the blocker and intersection rules.
        candidates = list(beam_cells)
        rng.shuffle(candidates)
        blockers = rng.randint(nb_lo, nb_hi)
        placed = 0
        for r, c in candidates:
            if placed >= blockers:
                break
            if g[r][c] != 0:
                continue
            g[r][c] = 5
            placed += 1
        intersections, total = _beam_intersections(g)
        if intersections and len(intersections) < total and placed >= nb_lo:
            return g
    raise ValueError("could not realize beam-intersection layout")


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_top_markers":
        g[3][0] = 2; g[5][0] = 2
        g[2][4] = 5
        return g
    if name == "no_left_markers":
        g[0][2] = 1; g[0][6] = 1
        g[3][4] = 5
        return g
    if name == "blockers_hide_all":
        g[0][2] = 1; g[0][6] = 1
        g[3][0] = 2; g[5][0] = 2
        g[3][1] = 5; g[5][1] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["empty or ragged grid"]
    h, w = len(grid), len(grid[0])
    if any(v not in {0, 1, 2, 5} for row in grid for v in row):
        errs.append("input should use only colors 1,2,5 on background 0")
    top_cols = [c for c in range(1, w) if grid[0][c] == 1]
    left_rows = [r for r in range(1, h) if grid[r][0] == 2]
    if not (2 <= len(top_cols) <= 4):
        errs.append(f"expected 2..4 top-row color-1 emitters, saw {len(top_cols)}")
    if not (2 <= len(left_rows) <= 4):
        errs.append(f"expected 2..4 left-column color-2 emitters, saw {len(left_rows)}")
    blockers = [(r, c) for r in range(1, h) for c in range(1, w) if grid[r][c] == 5]
    if not blockers:
        errs.append("missing blocker color 5")
    intersections, total = _beam_intersections(grid)
    if not intersections:
        errs.append("all beam intersections are hidden")
    if total and len(intersections) == total:
        errs.append("blockers do not hide any potential intersection")
    return errs
