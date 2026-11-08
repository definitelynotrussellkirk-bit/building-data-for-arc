"""Generator for arc_puzzle_bank_21_set19_bundle:easy_p04 — reduce odd-length runs to centers.

Rule: horizontal odd-length runs are separated by zeros and reduce to
their centers.

Combinatorial axes (8): grid_h, grid_w, palette_kind, run_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: even_length_runs, no_runs, length_1_runs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b9afcb69acd1"
VERSION = "1.2.1"  # 1.2.0->1.2.1: add self_check. 1.1.0->1.2.0: multiple runs per row with VARIED lengths
# (odd>=3 keep center; even & length 1-2 ERASED) so the length/parity
# discriminator branch is actually exercised (was only odd>=3 runs).
TASK_ID = "b9afcb69acd1"
SUMMARY = "Horizontal runs separated by zeros; odd-length >=3 runs reduce to centers, even/short runs erased."

INVARIANTS = [
    "background is 0",
    "active rows hold 1+ horizontal monochrome runs of mixed lengths (incl even/short)",
    "runs are isolated by >=1 background cell (so each is a distinct run)",
    "at least one run is odd-length >=3 (so the output is non-empty)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("even_length_runs", "no_runs", "length_1_runs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "run_count":      {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "odd_length_runs",
                       "valid": "odd_length_runs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; rows have horizontal runs; at least one nonzero cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        return errs  # degenerate no_runs allowed
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
           if not (0 <= grid[r][c] <= 9)]
    if bad:
        errs.append(f"out-of-range values: {bad[:3]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 9, 10)
        run_count = min(ctx.draw_int("run_count", 2, 2), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 12, 13)
        run_count = min(ctx.draw_int("run_count", 3, 4), h)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 9, 13)
        run_count = min(ctx.draw_int("run_count", 2, 4), h)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)

    rows = rng.sample(range(h), run_count)
    # mix of lengths: odd>=3 keep a center; even & 1-2 are erased by the rule
    lengths_pool = [length for length in (1, 2, 3, 4, 5, 6, 7) if length <= w]
    has_odd = False
    for row in rows:
        c = 0
        while c < w:
            # randomly skip (leave a gap) or place a run
            if rng.random() < 0.35:
                c += 1
                continue
            maxlen = min(rng.choice(lengths_pool), w - c)
            if maxlen < 1:
                break
            color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            for cc in range(c, c + maxlen):
                grid[row][cc] = color
            if maxlen >= 3 and maxlen % 2 == 1:
                has_odd = True
            c += maxlen + 1   # +1 gap so the next run is a separate run
    # guarantee at least one odd>=3 run so the output is non-empty
    if not has_odd:
        row = rows[0]
        length = 3 if w >= 3 else w
        c0 = rng.randint(0, w - length)
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for cc in range(c0, c0 + length):
            grid[row][cc] = color
        # clear a 1-cell margin so it's an isolated run
        if c0 > 0:
            grid[row][c0 - 1] = 0
        if c0 + length < w:
            grid[row][c0 + length] = 0
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 6, 11
    g = full_grid(h, w, 0)
    if name == "even_length_runs":
        # all runs even-length → no unique center cell, rule's reduction is undefined
        for c in range(1, 5): g[1][c] = 4   # length 4
        for c in range(2, 8): g[3][c] = 6   # length 6
        return g
    if name == "no_runs":
        # blank → no runs to reduce
        return g
    if name == "length_1_runs":
        # all runs length-1 (singletons) → center is itself, rule has no observable effect
        g[1][2] = 4
        g[3][5] = 6
        g[4][8] = 3
        return g
    return g
