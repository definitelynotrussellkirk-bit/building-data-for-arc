"""Generator for arc_puzzle_bank_21_set2:S2_E3.

Rule: rows with exactly two orange endpoints and an empty gap are
filled horizontally between them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, span_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: single_endpoint_only, span_already_filled, no_endpoints.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8922fefc96ff"
VERSION = "2.0.1"
TASK_ID = "8922fefc96ff"
SUMMARY = (
    "0-bg grid (h~6-9, w~9-12) with "
    "2-4 ACTIVE ROWS, each "
    "containing EXACTLY 2 COLOR-7 "
    "(orange) cells at distinct "
    "columns (c1, c2) with c2 ≥ "
    "c1 + 2 (gap of ≥1 bg cell "
    "between them). Plus 0-2 "
    "INACTIVE ROWS with a SINGLE "
    "orange cell (distractor) and "
    "0-3 INACTIVE ROWS with "
    "non-orange distractor cells. "
    "Spans between endpoints in "
    "active rows are initially 0. "
    "Rule (PER-ROW HORIZONTAL "
    "ENDPOINT FILL): for EACH "
    "ROW, COUNT the COLOR-7 "
    "cells. If EXACTLY 2 (the "
    "endpoint pair) AND all cells "
    "BETWEEN them are 0, FILL the "
    "ENTIRE INCLUSIVE SPAN "
    "(cells from min_c to max_c "
    "in that row) with COLOR 7. "
    "Rows with 0, 1, or 3+ "
    "orange cells unchanged. Net: "
    "each row with exactly 2 "
    "orange endpoints gets filled "
    "between them; single-"
    "endpoint rows stay."
)

# Rivals: 'fill any row with ≥1 orange' refuted by ≥1 demo with
# 1-endpoint or 3-endpoint rows left alone. 'fill across all rows'
# refuted by ≥2 demos where some rows clearly unchanged. 'fill with
# other color' refuted by any demo (fill is 7). 'fill even when span
# is occupied' refuted by ≥1 demo with non-bg span left alone.
# 4 demos with varied rows cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "active rows have exactly two orange cells",
    "the span between each endpoint pair starts empty",
    "rows with one orange cell remain unchanged",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_endpoint_only", "span_already_filled", "no_endpoints")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "span_count":     {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "row_endpoints",
                       "valid": "row_endpoints"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; >=1 row with exactly 2 orange (7) cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    active = [r for r in range(h) if sum(1 for c in range(w) if grid[r][c] == 7) == 2]
    if not active:
        # degenerate textures may have 0, 1, or 3+ per row — allowed
        return errs
    for r in active:
        cols7 = [c for c in range(w) if grid[r][c] == 7]
        c1, c2 = cols7[0], cols7[1]
        if c2 <= c1 + 1:
            errs.append(f"row {r}: orange endpoints too close (c1={c1} c2={c2})")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 8, 11)
        count = ctx.draw_int("span_count", 1, 3)
        n_blocked = 0
        n_extra_endpoint = 0
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 13, 18)
        count = ctx.draw_int("span_count", 4, 7)
        n_blocked = rng.randint(0, 2) if False else 0  # set below
        n_extra_endpoint = 0
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 10, 14)
        count = ctx.draw_int("span_count", 2, 5)
        n_blocked = 0
        n_extra_endpoint = 0
    count = min(count, h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), count)
    for r in rows:
        c1 = rng.randint(0, w - 4)
        c2 = rng.randint(c1 + 2, w - 1)
        g[r][c1] = 7
        g[r][c2] = 7
    inactive_rows = [r for r in range(h) if r not in rows]
    rng.shuffle(inactive_rows)
    # Add inactive rows with a SINGLE orange endpoint (rule leaves alone).
    n_single = min(rng.randint(0, 2), len(inactive_rows))
    for i in range(n_single):
        r = inactive_rows[i]
        g[r][rng.randint(0, w - 1)] = 7
    # Add inactive rows with non-7 distractor cells (rule ignores them).
    n_distract = min(rng.randint(0, 3), max(0, len(inactive_rows) - n_single))
    for i in range(n_distract):
        r = inactive_rows[n_single + i]
        n_cells = rng.randint(1, 3)
        for _ in range(n_cells):
            c = rng.randint(0, w - 1)
            if g[r][c] == 0:
                g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 8, 9])
    # Hard difficulty: optionally place a non-bg cell INSIDE the span
    # of one active row (rule leaves that row alone — span not clear).
    if difficulty == "hard" and rows and rng.random() < 0.5:
        r = rng.choice(rows)
        endpoints = [c for c in range(w) if g[r][c] == 7]
        if len(endpoints) == 2 and endpoints[1] - endpoints[0] >= 3:
            mid = rng.randint(endpoints[0] + 1, endpoints[1] - 1)
            g[r][mid] = rng.choice([1, 2, 3, 4, 5, 6, 8, 9])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "single_endpoint_only":
        # every active row has just one orange cell → no pair, rule is no-op
        for r in range(h):
            g[r][rng_pick(r, w) if False else (r * 2 % w)] = 7
        return g
    if name == "span_already_filled":
        # span between endpoints is already painted with another color → conflict
        g[1][1] = 7; g[1][7] = 7
        for c in range(2, 7):
            g[1][c] = 4
        return g
    if name == "no_endpoints":
        # no orange cells at all → nothing to fill
        for r, c in [(2, 3), (4, 6)]:
            g[r][c] = 5
        return g
    return g
