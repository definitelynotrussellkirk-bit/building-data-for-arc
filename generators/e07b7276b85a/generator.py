"""Generator for arc_puzzle_bank_fifteenth21:E100 — endpoint pairs fill exact midpoint.

Rule: each unique-color endpoint pair (aligned, even span) has its
midpoint cell filled with the same color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, pairs, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, odd_span, single_endpoint.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e07b7276b85a"
VERSION = "2.2.0"  # clean (endpoint pairs -> midpoint dot) but bounded; widen pair count (axis 1-8) and grids."
TASK_ID = "e07b7276b85a"

SUMMARY = (
    "0-bg grid (h~8-10, w~7-10) with 2-4 ENDPOINT "
    "PAIRS in distinct non-bg colors. Each pair is "
    "AXIALLY ALIGNED (horizontal or vertical) with "
    "an EVEN SPAN between the two endpoints (span ∈ "
    "{2, 4, 6}, so there is a SINGLE integer "
    "MIDPOINT cell between them). Pairs don't "
    "overlap. The cells between the endpoints are 0. "
    "Rule: for each color appearing exactly TWICE at "
    "axially-aligned endpoints with an even span "
    "between them, COMPUTE the MIDPOINT cell "
    "(((r1+r2)/2, (c1+c2)/2)). PAINT that single "
    "midpoint cell with the pair's color. Endpoints "
    "stay; other cells in the span stay 0. Net: each "
    "endpoint pair gets its exact midpoint marked in "
    "the pair's color — no full bridge, just the "
    "center dot."
)

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "endpoint pairs are horizontal or vertical",
    "endpoint span length is even so there is a single midpoint cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "odd_span", "single_endpoint")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "pairs":          {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "= pairs", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "axis_aligned_even_span",
                       "valid": "axis_aligned_even_span"},
    "n_distinct_colors": {"type": "int", "default": "= pairs", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        target = ctx.draw_int("pairs", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        target = ctx.draw_int("pairs", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        target = ctx.draw_int("pairs", 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k=target)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        horizontal = rng.randrange(2) == 0
        if horizontal:
            r = rng.randrange(h)
            span = rng.choice([2, 4, 6][:max(1, (w - 1) // 2)])
            c1 = rng.randint(0, w - span - 1)
            endpoints = [(r, c1), (r, c1 + span)]
            path = [(r, c) for c in range(c1, c1 + span + 1)]
        else:
            c = rng.randrange(w)
            span = rng.choice([2, 4, 6][:max(1, (h - 1) // 2)])
            r1 = rng.randint(0, h - span - 1)
            endpoints = [(r1, c), (r1 + span, c)]
            path = [(r, c) for r in range(r1, r1 + span + 1)]
        # The rule fires only when every intermediate cell between endpoints is
        # zero.  Reserving just endpoints+midpoint let a later endpoint land in
        # the corridor, hiding one color's midpoint branch.
        if any(p in reserved for p in path):
            continue
        color = colors[placed]
        g[endpoints[0][0]][endpoints[0][1]] = color
        g[endpoints[1][0]][endpoints[1][1]] = color
        reserved.update(path)
        placed += 1
    if placed < target:
        return _construct_pairs(h, w, target, colors)
    return g


def _construct_pairs(h, w, target, colors):
    g = full_grid(h, w, 0)
    rows = list(range(0, h, 2))
    made = 0
    for r in rows:
        if made >= target:
            break
        span = 2 if w < 7 else 4
        c1 = 0 if made % 2 == 0 else max(0, w - span - 1)
        if c1 + span >= w:
            continue
        if any(g[r][c] != 0 for c in range(c1, c1 + span + 1)):
            continue
        color = colors[made]
        g[r][c1] = color
        g[r][c1 + span] = color
        made += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    by_color = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v:
                by_color.setdefault(v, []).append((r, c))
    lo = 2 if difficulty == "easy" else (5 if difficulty == "hard" else 3)
    good = 0
    for color, cells in by_color.items():
        if len(cells) != 2:
            msgs.append(f"color {color} appears {len(cells)} times, not exactly two endpoints")
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            a, b = sorted((c1, c2))
            inter = [grid[r1][c] for c in range(a + 1, b)]
        elif c1 == c2:
            a, b = sorted((r1, r2))
            inter = [grid[r][c1] for r in range(a + 1, b)]
        else:
            msgs.append(f"color {color} endpoints are not axis-aligned")
            continue
        if (b - a) % 2 != 0:
            msgs.append(f"color {color} endpoint span is odd")
        elif any(v != 0 for v in inter):
            msgs.append(f"color {color} endpoint corridor is blocked")
        else:
            good += 1
    if good < lo:
        msgs.append(f"expected at least {lo} good endpoint pairs, got {good}")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Singletons only — rule has no aligned pair to bridge.
        g[1][1] = 3; g[3][7] = 4; g[6][2] = 5
        return g
    if name == "odd_span":
        # Endpoints aligned but span is odd (3) — no integer midpoint cell,
        # so the rule has no single cell to fill.
        g[2][1] = 4; g[2][4] = 4
        g[5][2] = 6; g[5][5] = 6
        return g
    if name == "single_endpoint":
        # Each color appears only once — there's no second endpoint to
        # pair with, so no midpoint can be defined.
        g[2][1] = 4
        g[5][6] = 6
        return g
    return g
