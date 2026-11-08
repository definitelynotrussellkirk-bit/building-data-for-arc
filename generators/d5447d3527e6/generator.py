"""Generator for v1_e_m_h_keys:E7.

Combinatorial axes (8): grid_h, grid_w, palette_kind, runs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_runs, all_even, all_short.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d5447d3527e6"
VERSION = "2.0.0"
TASK_ID = "d5447d3527e6"

SUMMARY = (
    "0-bg grid (h~9-13, w~8-12) with 2-4 "
    "VERTICAL RUNS of COLOR 5 (gray), each "
    "of length 3 or 5 (alternating between "
    "lengths). Plus 1-2 DISTRACTOR runs of "
    "length 2 or 4 (even lengths, also "
    "color 5). All runs are placed at "
    "DISTINCT COLUMNS with ≥1 column padding "
    "between them. Rule: identify each "
    "VERTICAL COLOR-5 RUN (vertical line of "
    "consecutive 5-cells). If a run has ODD "
    "LENGTH ≥ 3 (3 or 5), RECOLOR ONLY ITS "
    "CENTER CELL (the middle cell of the "
    "run) to COLOR 2 (red). The other "
    "cells of the run stay 5. EVEN-length "
    "runs (2, 4) are left entirely as 5 (no "
    "well-defined center). Net: odd-length "
    "vertical 5-runs get a single red center "
    "pixel; even-length runs stay solid gray."
)

INVARIANTS = [
    "background is 0",
    "target runs are vertical color-5 runs with odd length at least 3",
    "even and short runs remain as distractors",
    "runs are separated by at least one blank column",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_runs", "all_even", "all_short")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "5..24"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "3..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "runs":           {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "vertical_5_runs",
                       "valid": "vertical_5_runs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the intended vertical-run demo: 0-bg, 5-runs, and ≥1 odd target."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs: list[str] = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    vals = {v for row in grid for v in row}
    bad = vals - {0, 5}
    if bad:
        errs.append(f"unexpected colors in input: {sorted(bad)}")
    target_runs = 0
    for c in range(w):
        r = 0
        while r < h:
            if grid[r][c] != 5:
                r += 1
                continue
            start = r
            while r < h and grid[r][c] == 5:
                r += 1
            length = r - start
            if length >= 3 and length % 2 == 1:
                target_runs += 1
            # runs should be isolated horizontally so the puzzle is about columns.
            for rr in range(start, r):
                for cc in (c - 1, c + 1):
                    if 0 <= cc < w and grid[rr][cc] == 5:
                        errs.append("adjacent 5-runs touch horizontally")
                        break
    if target_runs == 0:
        errs.append("no odd-length vertical 5-run target")
    return errs


def _free(g, r0, c, length):
    h, w = len(g), len(g[0])
    if r0 < 0 or r0 + length > h:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + length + 1)):
        for cc in range(max(0, c - 1), min(w, c + 2)):
            if g[r][cc] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 8, 9)
        target = ctx.draw_int("runs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 11, 12)
        target = ctx.draw_int("runs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 8, 12)
        target = ctx.draw_int("runs", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for length in [3, 5, 3, 5][:target]:
        for _ in range(80):
            c = rng.randrange(w)
            r0 = rng.randint(0, h - length)
            if _free(g, r0, c, length):
                for r in range(r0, r0 + length):
                    g[r][c] = 5
                placed += 1
                break
    for length in (2, 4):
        for _ in range(60):
            c = rng.randrange(w)
            r0 = rng.randint(0, h - length)
            if _free(g, r0, c, length):
                for r in range(r0, r0 + length):
                    g[r][c] = 5
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 9
    g = full_grid(h, w, 0)
    if name == "no_runs":
        # blank → no runs to recolor
        return g
    if name == "all_even":
        # only even-length runs → no odd targets to recolor center
        for r in range(0, 4): g[r][2] = 5
        for r in range(2, 4): g[r][6] = 5
        return g
    if name == "all_short":
        # only length-1 or length-2 runs → no odd run ≥3, no targets
        g[1][2] = 5
        for r in range(4, 6): g[r][6] = 5
        return g
    return g
