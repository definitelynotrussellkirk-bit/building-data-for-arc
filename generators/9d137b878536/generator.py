"""Generator for v1_e_m_h_keys:E1.

Rule: each horizontal run of color-2 of length ≥3 has its first and
last cells marked color 8.

Combinatorial axes (8): grid_h/w, palette_kind, n_runs, palette_size,
position_bias, n_distinct_colors, run_density, texture.
Degenerates: no_runs, run_too_short, runs_share_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9d137b878536"
VERSION = "2.0.0"
TASK_ID = "9d137b878536"
SUMMARY = (
    "0-bg grid (h~4-6, w~7-9) with "
    "1-3 LONG HORIZONTAL COLOR-2 RUNS "
    "(length ≥3, up to 5) plus 1-3 "
    "SHORT DISTRACTOR RUNS (length 1 "
    "or 2). Each run is placed at a "
    "random row and random starting "
    "column with 1-cell padding so "
    "they don't merge. No two runs "
    "share a row. Rule (RECOLOR "
    "ENDPOINTS OF LONG RUNS): scan "
    "each ROW LEFT-TO-RIGHT for "
    "HORIZONTAL RUNS of COLOR 2 "
    "(maximal contiguous sequences). "
    "For each run with length ≥3, "
    "RECOLOR its FIRST and LAST "
    "cells to COLOR 8 (cyan); "
    "INTERIOR cells stay 2. Runs of "
    "length 1 or 2 stay color-2 "
    "(no change). Vertical 2-runs "
    "unaffected. Net: long "
    "horizontal runs get cyan-"
    "tagged endpoints; short runs "
    "stay 2."
)

# Rivals: 'output is input' refuted by demos with ≥1 length-≥3 run.
# 'mark endpoints of EVERY run' refuted by demos with a length-2 run
# that stays 2. 'mark every cell of long runs as 8' refuted by demos
# preserving interior 2s. 'mark only the first cell, not the last'
# refuted by demos showing both endpoints. 'use a different color
# than 8' refuted by demos. 'apply to vertical runs too' refuted by
# demos with a column-shaped run staying 2. 4 demos with mixed
# lengths (1, 2, 3, 5) + ≥1 short distractor pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "≥1 horizontal run of color-2 with length ≥3 (so the rule's effect is visible)",
    "≥1 horizontal run with length <3 (singleton or pair) — distractor that stays 2",
    "runs are separated by ≥1 bg cell so they don't merge",
    "no vertical 2-runs (or any vertical sequences) that would be ambiguous: "
    "no two 2-cells stacked vertically in adjacent rows at the same column unless "
    "both lie in length-≥3 horizontal runs (which is fine)",
]

PALETTE_KINDS = ("default", "sparse", "dense", "long_runs")
DEGENERATE_TEXTURES = ("no_runs", "run_too_short", "runs_share_row")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_runs":         {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "run_density":    {"type": "str", "default": "mixed", "valid": "mixed"},
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
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 7, 9)
        n_long_lo, n_long_hi = 1, 2
        n_short_lo, n_short_hi = 1, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 10, 14)
        n_long_lo, n_long_hi = 2, 4
        n_short_lo, n_short_hi = 1, 3
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 8, 11)
        n_long_lo, n_long_hi = 1, 3
        n_short_lo, n_short_hi = 1, 2
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_long = rng.randint(n_long_lo, n_long_hi)
    n_short = rng.randint(n_short_lo, n_short_hi)
    if n_long + n_short > h:
        n_short = max(1, h - n_long)
    rows = list(range(h))
    rng.shuffle(rows)
    placed = 0
    # Place long runs (length ≥3) — these get endpoint-recolored.
    # Rows are consumed exactly once so the short-run distractor never
    # shares a row with a long run and silently merges/overlaps.
    while placed < n_long and rows:
        length = rng.randint(3, min(5, w - 1))
        r = rows.pop()
        c0 = rng.randint(0, w - length)
        for c in range(c0, c0 + length):
            g[r][c] = 2
        placed += 1
    placed_s = 0
    # Place short runs (length 1 or 2) — distractors that stay 2.
    while placed_s < n_short and rows:
        length = rng.randint(1, 2)
        r = rows.pop()
        c0 = rng.randint(0, w - length)
        for c in range(c0, c0 + length):
            g[r][c] = 2
        placed_s += 1
    if placed < n_long or placed_s < n_short:
        raise ValueError("failed to place required long/short run witnesses")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 8
    g = full_grid(h, w, 0)
    if name == "no_runs":
        # singletons / length-1 cells only — no run of length ≥3
        g[1][2] = 2
        g[3][5] = 2
        return g
    if name == "run_too_short":
        # length-2 runs only — fail the ≥3 predicate
        g[1][2] = 2; g[1][3] = 2
        g[3][5] = 2; g[3][6] = 2
        return g
    if name == "runs_share_row":
        # 2 separated runs in the same row → invariant violation
        g[2][0] = 2; g[2][1] = 2; g[2][2] = 2
        g[2][5] = 2; g[2][6] = 2; g[2][7] = 2
        return g
    return g


def _horizontal_runs(g):
    runs = []
    for r, row in enumerate(g):
        c = 0
        while c < len(row):
            if row[c] != 2:
                c += 1
                continue
            c0 = c
            while c < len(row) and row[c] == 2:
                c += 1
            runs.append((r, c0, c - c0))
    return runs


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    runs = _horizontal_runs(grid)
    long_runs = [run for run in runs if run[2] >= 3]
    short_runs = [run for run in runs if run[2] < 3]
    if not long_runs:
        errs.append("missing a color-2 horizontal run of length >=3")
    if not short_runs:
        errs.append("missing a short color-2 distractor run")
    rows = [r for r, _c, _length in runs]
    if len(rows) != len(set(rows)):
        errs.append("multiple runs share a row and can hide the short/long distinction")
    return errs
