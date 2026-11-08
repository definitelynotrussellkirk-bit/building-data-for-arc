"""Generator for arc_puzzle_bank_21_set15_bundle:easy_o07.

Isolated vertical trios are replaced by centered horizontal trios.

Combinatorial axes (8): grid_h, grid_w, palette_kind, run_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_runs, length_2_runs, runs_on_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "857238219e77"
VERSION = "1.3.0"
TASK_ID = "857238219e77"
SUMMARY = "Vertical runs of exactly length 3, away from side edges. Rule replaces each vertical 3-run at column c with a horizontal 3-run at the run's middle row (the center cell + left + right neighbors), in the same color. Length-2 runs and edge-column runs are not converted."

# Rivals: 'output is input' refuted by any demo (verticals become horizontals).
# 'convert all runs' refuted by ≥1 demo with length-2 runs staying.
# 'use bg color for new run' refuted by any demo (color preserved).
# 'leave original run' refuted by any demo (verticals erase). 3 demos
# with varied positions cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "all nonzero objects are vertical runs of length exactly three",
    "run middle columns are not on the left or right edge",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_runs", "length_2_runs", "runs_on_edge")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..15"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "run_count":      {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "vertical_3_runs",
                       "valid": "vertical_3_runs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _clear_zone(g, r, c):
    h, w = len(g), len(g[0])
    for rr in range(max(0, r - 1), min(h, r + 4)):
        for cc in range(max(0, c - 2), min(w, c + 3)):
            if g[rr][cc] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        run_count = ctx.draw_int("run_count", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 13, 17)
        run_count = ctx.draw_int("run_count", 5, 7)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        run_count = ctx.draw_int("run_count", 3, 5)
    colors = ctx.draw_distinct_colors("colors", n=run_count, exclude={0})
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    output_reserved: set[tuple[int, int]] = set()

    def can_place(r, c):
        in_cells = {(r + k, c) for k in range(3)}
        out_cells = {(r + 1, c - 1), (r + 1, c), (r + 1, c + 1)}
        if any(g[rr][cc] != 0 for rr, cc in in_cells):
            return False
        # Keep vertical runs exactly length 3 for the column scanner.
        if r > 0 and g[r - 1][c] != 0:
            return False
        if r + 3 < h and g[r + 3][c] != 0:
            return False
        # Avoid two converted horizontal trios painting the same output cell.
        if out_cells & output_reserved:
            return False
        return True

    def do_place(r, c, color):
        for rr in range(r, r + 3):
            g[rr][c] = color
        output_reserved.update({(r + 1, c - 1), (r + 1, c), (r + 1, c + 1)})

    for color in colors:
        placed = False
        for _ in range(300):
            r = rng.randint(0, h - 3)
            c = rng.randint(1, w - 2)
            if can_place(r, c):
                do_place(r, c, color)
                placed = True
                break
        if not placed:
            spots = [(r, c) for r in range(0, h - 2) for c in range(1, w - 1)]
            rng.shuffle(spots)
            for r, c in spots:
                if can_place(r, c):
                    do_place(r, c, color)
                    placed = True
                    break
        if not placed:
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_runs":
        # blank → no vertical runs to convert
        return g
    if name == "length_2_runs":
        # length-2 runs → "length exactly three" precondition fails
        for r in [1, 2]: g[r][3] = 4
        for r in [4, 5]: g[r][6] = 6
        return g
    if name == "runs_on_edge":
        # run at col 0 → can't center horizontal trio (out of bounds left)
        for r in range(1, 4): g[r][0] = 4
        return g
    return g

def _vertical_runs(grid):
    h, w = len(grid), len(grid[0])
    runs = []
    for c in range(w):
        r = 0
        while r < h:
            v = grid[r][c]
            if v == 0:
                r += 1; continue
            end = r
            while end < h and grid[end][c] == v:
                end += 1
            runs.append((v, r, end - 1, c, end - r))
            r = end
    return runs

def self_check(grid, *, difficulty=None, meta=None):
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    lo, hi = (1, 3) if difficulty == "easy" else ((5, 7) if difficulty == "hard" else (3, 5))
    runs = _vertical_runs(grid)
    errs = []
    if not (lo <= len(runs) <= hi):
        errs.append(f"expected {lo}..{hi} runs, got {len(runs)}")
    for v, r0, r1, c, ln in runs:
        if ln != 3:
            errs.append(f"color {v} run length is {ln}, expected 3")
        if c in (0, w - 1):
            errs.append("run middle column must not be on grid edge")
    return errs
