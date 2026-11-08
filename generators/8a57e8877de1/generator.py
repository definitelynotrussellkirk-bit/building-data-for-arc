"""Generator for v3_rich_schema:easy_01_exact_horizontal_triples — recolor exact-3 horizontal runs.

Rule: each horizontal run of color-2 of EXACTLY length 3 is recolored to 7.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_triples,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_triples, all_distractors, vertical_triples.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a57e8877de1"
VERSION = "1.2.0"
TASK_ID = "8a57e8877de1"

SUMMARY = "Horizontal color-2 runs of EXACT length 3 + distractor runs of other lengths (2, 4, 5, …). Rule recolors exactly-length-3 horizontal runs from 2 → 7; other runs stay 2."

# Rivals: 'recolor all 2s' refuted by ≥2 demos where distractor runs stay 2.
# 'recolor exact-length-4 runs' refuted by any demo where length-4 stays 2.
# 'use a different output color' refuted by any demo (output is 7).
# 'operate per column (vertical runs)' refuted by ≥1 demo with vertical
# runs unchanged. 3 demos with mixed lengths cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "1-3 horizontal color-2 runs of EXACT length 3 in distinct rows",
    "0-1 distractor horizontal color-2 runs of length 2 or 4 (won't match the rule)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_triples", "all_distractors", "vertical_triples")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..15 by diff", "valid": "4..15"},
    "grid_w":         {"type": "int", "default": "rng 7..18 by diff", "valid": "6..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_triples":      {"type": "int", "default": "rng 1..6 by diff", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "horizontal_triples_with_distractors",
                       "valid": "horizontal_triples_with_distractors"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_triples|all_distractors|vertical_triples"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 10)
        n_triples = ctx.draw_int("n_triples", 1, 2)
        n_distract = rng.randint(0, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 15)
        w = ctx.draw_int("grid_w", 12, 18)
        n_triples = ctx.draw_int("n_triples", 3, 6)
        n_distract = rng.randint(2, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 9, 14)
        n_triples = ctx.draw_int("n_triples", 2, 4)
        n_distract = rng.randint(1, 3)
    g = full_grid(h, w, 0)
    total = min(n_triples + n_distract, h)
    rows = rng.sample(range(h), total)
    triple_rows = rows[:n_triples]
    distract_rows = rows[n_triples:total]
    for r in triple_rows:
        if w < 3: continue
        c0 = rng.randint(0, w - 3)
        for c in range(c0, c0 + 3):
            g[r][c] = 2
    for r in distract_rows:
        length = rng.choice([2, 4, 5, 6])
        if w - length < 0: continue
        c0 = rng.randint(0, w - length)
        for c in range(c0, c0 + length):
            g[r][c] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "no_triples":
        # blank → no exact-3 runs to recolor
        return g
    if name == "all_distractors":
        # only length-2 and length-4 runs → "exact length 3" precondition fails
        for c in range(2, 4): g[1][c] = 2
        for c in range(2, 6): g[3][c] = 2
        return g
    if name == "vertical_triples":
        # vertical runs only → "horizontal" precondition fails
        for r in range(1, 4): g[r][3] = 2
        return g
    return g

def _runs(grid):
    out = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] != 2:
                c += 1; continue
            c0 = c
            while c < len(row) and row[c] == 2: c += 1
            out.append((r, c0, c - c0))
    return out

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    runs = _runs(grid)
    exact = [x for x in runs if x[2] == 3]
    distractors = [x for x in runs if x[2] != 3]
    errs: list[str] = []
    lo = 3 if difficulty == "hard" else (2 if difficulty is None else 1)
    if len(exact) < lo:
        errs.append(f"expected at least {lo} exact-3 horizontal runs, got {len(exact)}")
    if difficulty in (None, "hard") and not distractors:
        errs.append("normal/default and hard examples should include a non-length-3 stay-blue distractor run")
    if any(v not in (0, 2) for row in grid for v in row):
        errs.append("input should use only 0 and 2")
    return errs
