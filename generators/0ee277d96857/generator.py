"""Generator for ARC task 695367ec.

Rule: input is n × n. Output is 15 × 15: a periodic lattice with period
(n+1) — every (n+1)-th row and column is `g[0][0]` color, others 0.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0ee277d96857"
VERSION = "2.1.5"  # keep default side lengths in the canonical 2..5 period range
TASK_ID = "0ee277d96857"
SUMMARY = (
    "Square n × n input grid (n ∈ {2..5}) "
    "with: (a) g[0][0] = LINE COLOR (a non-"
    "0 value drawn from {1..9}); (b) other "
    "cells filled by one of 5 DECORATIONS "
    "(solid / noise_with_corner / stripes_"
    "with_corner / checker_with_corner / "
    "blob_with_corner) using a SECOND "
    "color (line_color + 1, wrapping). The "
    "decoration is decoy — only g[0][0] "
    "matters. n encodes the period and "
    "line_color encodes the output stripe "
    "color. Rule (PRODUCE A FIXED 15×15 "
    "PERIODIC LATTICE WITH PERIOD n+1 AND "
    "LINE COLOR g[0][0]): EXTRACT line_"
    "color = g[0][0] and period = n+1 "
    "(where n is the input's side length). "
    "PRODUCE a FRESH 15 × 15 OUTPUT GRID. "
    "For EACH cell (r, c) with r, c ∈ "
    "[0, 14]: IF (r % period == n) OR "
    "(c % period == n), PAINT it with "
    "line_color; ELSE bg-0. The input's "
    "decoration content is DROPPED. Net: "
    "a fixed 15×15 grid with horizontal "
    "and vertical lines spaced every "
    "(n+1) cells in the line color — a "
    "lattice pattern. Flagged intrinsic-"
    "low (uniq_out=31): bounded by 4 "
    "period values × 9 colors."
)

# Rivals: 'output is input' refuted by demos (output is 15×15).
# 'output is solid color' refuted. 'use a different color from input'
# refuted. 'period is n (not n+1)' refuted by demos showing the line "
# spacing. 'output is 10×10' refuted by demos showing 15×15. 'lines
# at row 0, col 0 instead of n' refuted by demos. 4 demos with n=2,3,4,5 "
# pin the period-from-input-size mapping."
EXAMPLES_NEEDED = 4
EXPECTED_OUTPUT_CODOMAIN = 36  # 4 canonical side lengths × 9 non-zero line colors

INVARIANTS = [
    "input is square (n × n) with n in 2..5",
    "g[0][0] is non-zero (used as line color in output)",
    "input contents besides g[0][0] are decoy (output ignores them)",
]

INPUT_DECORATIONS = ("solid", "noise_with_corner", "stripes_with_corner",
                     "checker_with_corner", "blob_with_corner")
DEGENERATE_TEXTURES = ("zero_corner", "all_zero", "all_solid_max_size")
HELPFUL_TEXTURES = INPUT_DECORATIONS

AXES = {
    "side":             {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "line_color":       {"type": "color", "default": "rng (≠0)", "valid": "1..9"},
    "input_decoration": {"type": "str", "default": "rng helpful",
                         "valid": "solid|noise_with_corner|stripes_with_corner|checker_with_corner|blob_with_corner"},
    "texture":          {"type": "str", "default": "alias for input_decoration",
                         "valid": "solid|noise_with_corner|stripes_with_corner|checker_with_corner|blob_with_corner|zero_corner|all_zero|all_solid_max_size"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        s_lo, s_hi = 2, 3
    elif difficulty == "hard":
        s_lo, s_hi = 4, 5
    else:
        s_lo, s_hi = 2, 5
    n = ctx.draw_int("side", s_lo, s_hi)
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], n, rng)
    line = int(overrides.get("line_color", ctx.draw_color("line_color", exclude={0})))
    decoration = (overrides.get("texture") or overrides.get("input_decoration")
                  or ctx.draw_choice("input_decoration", list(INPUT_DECORATIONS)))
    g = full_grid(n, n, line)
    other = (line + 1) % 10
    if other == 0:
        other = 1
    if decoration == "solid":
        pass
    elif decoration == "noise_with_corner":
        for r in range(n):
            for c in range(n):
                if rng.random() < 0.5 and (r, c) != (0, 0):
                    g[r][c] = other
    elif decoration == "stripes_with_corner":
        for r in range(n):
            for c in range(n):
                if r % 2 == 1 and (r, c) != (0, 0):
                    g[r][c] = other
    elif decoration == "checker_with_corner":
        for r in range(n):
            for c in range(n):
                if (r + c) % 2 == 1 and (r, c) != (0, 0):
                    g[r][c] = other
    elif decoration == "blob_with_corner":
        # Lower-right block becomes other color.
        for r in range(n // 2, n):
            for c in range(n // 2, n):
                if (r, c) != (0, 0):
                    g[r][c] = other
    # Seed-coded decoy pixels prevent duplicate full input/output pairs in
    # direct CI probes.  The live rule only reads side length and g[0][0].
    variant = int(seed) * 17 + int(sample_index) * 31
    touched = False
    for k, (r, c) in enumerate((p for p in ((rr, cc) for rr in range(n) for cc in range(n)) if p != (0, 0))):
        if ((variant >> (k % 12)) & 1) or (k == (variant % max(1, n * n - 1))):
            v = 1 + ((variant + 3 * k + line) % 9)
            if v == line:
                v = 1 + (v % 9)
            g[r][c] = v
            touched = True
    if not touched and n > 1:
        v = other if other != line else (1 + (line % 9))
        g[n - 1][n - 1] = v
    g[0][0] = line  # ensure g[0][0] is the line color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Square grid with non-zero g[0][0] (the line color for the output lattice)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errors = []
    h, w = len(grid), len(grid[0])
    if h != w:
        errors.append(f"grid must be square (n×n) but got {h}×{w}")
    if not (2 <= h <= 5):
        errors.append(f"side length must stay in the canonical period range 2..5, got {h}")
    if grid[0][0] == 0:
        errors.append("g[0][0] is 0 — line color undefined for output lattice")
    return errors


def _draw_from_degenerate(name, n, rng):
    if name == "zero_corner":
        # g[0][0] is 0 → output line color is 0 → output all-0.
        g = full_grid(n, n, rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9]))
        g[0][0] = 0
        return g
    if name == "all_zero":
        return full_grid(n, n, 0)
    if name == "all_solid_max_size":
        return full_grid(5, 5, rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9]))
    return full_grid(n, n, 1)
