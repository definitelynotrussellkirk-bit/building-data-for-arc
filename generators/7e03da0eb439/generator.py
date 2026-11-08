"""Generator for ARC task cce03e0d.

Rule: `(rule! (lambda (g) (self-tile g (lambda (v) (= v 2)))))`. For
every cell that equals 2, paint a copy of the whole input centered at
that cell. Output dims: H² × W² (here 9 × 9 since input is 3 × 3).

Combinatorial axes:
  * grid_size           — input side length (kept at 3 in canonical)
  * n_2_cells           — how many cells get value 2 (the trigger)
  * non_2_pattern       — what fills the non-trigger cells: zero / mixed_low /
                          mixed_full / sparse_high
  * non_2_palette       — set of colors that fills the non-2 cells
  * trigger_layout      — where the 2s sit: random / corners / row /
                          column / cross
  * caller-opt-in degenerates: no_2_cells (rule no-op), all_2_cells
                               (output blows up to 9×9 same shape), monochrome_2
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7e03da0eb439"
VERSION = "2.2.0"  # shape-locked in/out: input fixed 3x3 -> output fixed 9x9. self-tile is size-generic (NxM -> N^2 x W^2). Vary input side 2..5 (output 4x4..25x25, fits the 30 canvas) -> input/output sizes vary.
TASK_ID = "7e03da0eb439"
SUMMARY = (
    "Fixed 3×3 grid (canonical input dim) with: (a) one "
    "or more TRIGGER cells set to color 2; (b) non-2 "
    "cells filled with some pattern (zero / mixed_low / "
    "mixed_full / sparse_high) from a non-2 palette. "
    "Rule: self-tile — output is 9 × 9. For each cell "
    "(R, C) of the output, let (R_tile, C_tile) = (R // 3, "
    "C // 3) and (r, c) = (R % 3, C % 3). The output cell "
    "= input[r][c] IF the tile cell input[R_tile][C_tile] "
    "== 2, else 0. Net: a 3 × 3 mosaic of 3×3 tiles — "
    "each input==2 cell gets stamped with a copy of the "
    "whole input, non-2 cells stay blank."
)

INVARIANTS = [
    "input is a 2×2..5×5 square",
    "color 2 appears at least once (else rule is no-op)",
    "at least one non-trigger cell remains, so not every tile position is active",
]

NON_2_PATTERNS = ("zero", "mixed_low", "mixed_full", "sparse_high")
TRIGGER_LAYOUTS = ("random", "corners", "row", "column", "cross")
DEGENERATE_TEXTURES = ("no_2_cells", "all_2_cells", "monochrome_2")
HELPFUL_TEXTURES = NON_2_PATTERNS

AXES = {'grid_size': {'type': 'int', 'default': 'rng 2..5', 'valid': '2..5'},
 'n_2_cells': {'type': 'int', 'default': 'rng 1..5', 'valid': '1..9'},
 'non_2_pattern': {'type': 'str', 'default': 'rng helpful', 'valid': 'zero|mixed_low|mixed_full|sparse_high'},
 'trigger_layout': {'type': 'str',
                    'default': 'rng random|corners|row|column|cross',
                    'valid': 'random|corners|row|column|cross'},
 'non_2_palette_size': {'type': 'int', 'default': 'rng 1..3', 'valid': '0..6'},
 'texture': {'type': 'str',
             'default': 'alias for non_2_pattern',
             'valid': 'zero|mixed_low|mixed_full|sparse_high|no_2_cells|all_2_cells|monochrome_2'}}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        n_lo, n_hi, p_lo, p_hi = 1, 3, 1, 1
        size = ctx.draw_int("grid_size", 2, 3)
    elif difficulty == "hard":
        n_lo, n_hi, p_lo, p_hi = 4, 8, 2, 3
        size = ctx.draw_int("grid_size", 4, 5)
    else:
        n_lo, n_hi, p_lo, p_hi = 1, 8, 1, 3
        size = ctx.draw_int("grid_size", 2, 5)

    rng = ctx.draw_rng("cells")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    n2 = int(overrides.get("n_2_cells", ctx.draw_int("n_2_cells", n_lo, n_hi)))
    n2 = max(1, min(size * size - 1, n2))
    layout = overrides.get(
        "trigger_layout",
        ctx.draw_choice("trigger_layout", list(TRIGGER_LAYOUTS)))
    pattern = (overrides.get("texture")
               or overrides.get("non_2_pattern")
               or ctx.draw_choice("non_2_pattern", list(NON_2_PATTERNS)))
    n_palette = int(overrides.get("non_2_palette_size",
                                  ctx.draw_int("non_2_palette_size", p_lo, p_hi)))
    non_2_palette = ctx.draw_distinct_colors(
        "non_2_palette", n=max(1, n_palette), exclude={2})

    g = full_grid(size, size, 0)
    trigger_cells = _trigger_layout(layout, n2, rng, size)
    for r, c in trigger_cells:
        g[r][c] = 2

    # Fill non-trigger cells per pattern.
    other_cells = [(r, c) for r in range(size) for c in range(size)
                   if (r, c) not in set(trigger_cells)]
    rng.shuffle(other_cells)
    if pattern == "zero":
        for r, c in other_cells:
            g[r][c] = 0
    elif pattern == "mixed_low":
        for r, c in other_cells:
            g[r][c] = rng.choice(non_2_palette) if rng.random() < 0.4 else 0
    elif pattern == "mixed_full":
        for r, c in other_cells:
            g[r][c] = rng.choice(non_2_palette)
    else:  # sparse_high
        for r, c in other_cells:
            g[r][c] = rng.choice(non_2_palette) if rng.random() < 0.7 else 0
    return g


def _trigger_layout(layout, n, rng, size):
    m = size - 1
    mid = size // 2
    if layout == "corners":
        candidates = [(0, 0), (0, m), (m, 0), (m, m)]
    elif layout == "row":
        r = rng.randint(0, m)
        candidates = [(r, c) for c in range(size)]
    elif layout == "column":
        c = rng.randint(0, m)
        candidates = [(r, c) for r in range(size)]
    elif layout == "cross":
        candidates = [(r, c) for r in range(size) for c in range(size)
                      if r == mid or c == mid]
    else:  # random
        candidates = [(r, c) for r in range(size) for c in range(size)]
    rng.shuffle(candidates)
    n = min(n, len(candidates))
    out = candidates[:n]
    if not out:
        out = [(rng.randint(0, m), rng.randint(0, m))]
    return out


def _draw_from_degenerate(name, rng):
    """Edge-case where the self-tile signature is hidden.

    no_2_cells     — input has no 2s; rule is identity.
    all_2_cells    — every cell is 2; output is 3×3 copies of the all-2
                     grid → just an all-2 9×9.
    monochrome_2   — all cells same value (which is 2); same as all_2_cells
                     but kept for symmetry.
    """
    g = full_grid(3, 3, 0)
    if name == "no_2_cells":
        palette = [c for c in range(10) if c != 2]
        for r in range(3):
            for c in range(3):
                g[r][c] = rng.choice(palette)
        return g
    if name == "all_2_cells" or name == "monochrome_2":
        for r in range(3):
            for c in range(3):
                g[r][c] = 2
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h, w = len(grid), len(grid[0])
    if h != w or not (2 <= h <= 5):
        msgs.append("self-tile input must be a 2x2..5x5 square")
    n2 = sum(v == 2 for row in grid for v in row)
    if n2 < 1:
        msgs.append("expected at least one trigger cell with color 2")
    if n2 >= h * w:
        msgs.append("not every cell should be a trigger")
    vals = {v for row in grid for v in row}
    if any(v < 0 or v > 9 for v in vals):
        msgs.append("grid values must be ARC colors 0..9")
    return msgs
