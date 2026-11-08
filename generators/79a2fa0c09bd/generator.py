"""Generator for ff72ca3e.

Rule: for each 4-cell, halo radius = (min Chebyshev distance to any
5-cell) - 1; fill square neighborhood with 2 where currently 0.

Combinatorial axes (8): grid_h/w, n_fives, n_fours, five_position_bias,
four_position_bias, four_distance_kind, edge_avoidance, anchor_corner.
Degenerates: no_fives, no_fours, all_5s.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "79a2fa0c09bd"
VERSION = "1.2.0"  # add task-specific self_check coverage
TASK_ID = "79a2fa0c09bd"
SUMMARY = "5-anchors + 4-cells; rule paints 2-halos by Chebyshev distance."

INVARIANTS = [
    "background is 0",
    ">=1 cell of color 5 (anchor)",
    ">=1 cell of color 4 with Chebyshev distance >=2 to nearest 5",
    "no color 2 in input (rule writes 2 for output)",
]

POSITION_BIAS = ("center", "spread", "edge", "corners")
DEGENERATE_TEXTURES = ("no_fives", "no_fours", "all_5s")
HELPFUL_TEXTURES = POSITION_BIAS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 6..12", "valid": "5..16"},
    "grid_w":            {"type": "int", "default": "rng 6..12", "valid": "5..16"},
    "n_fives":           {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_fours":           {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "five_position_bias": {"type": "str", "default": "rng helpful",
                           "valid": "|".join(POSITION_BIAS)},
    "four_position_bias": {"type": "str", "default": "rng spread|center",
                           "valid": "spread|center"},
    "four_distance_kind": {"type": "str", "default": "rng near|medium|far",
                           "valid": "near|medium|far"},
    "edge_avoidance":    {"type": "bool", "default": "false",
                          "valid": "true|false"},
    "texture":           {"type": "str", "default": "alias for five_position_bias",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 5, 7
    elif difficulty == "hard":
        h_lo, h_hi = 11, 16
    else:
        h_lo, h_hi = 6, 12
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_fives = int(overrides.get("n_fives",
                                ctx.draw_int("n_fives", 1, 3)))
    n_fives = max(1, min(5, n_fives))
    n_fours = int(overrides.get("n_fours",
                                ctx.draw_int("n_fours", 1, 3)))
    n_fours = max(1, min(5, n_fours))
    five_bias = (overrides.get("texture") or
                 overrides.get("five_position_bias")
                 or ctx.draw_choice("five_position_bias",
                                    list(POSITION_BIAS)))
    four_bias = overrides.get("four_position_bias",
                              ctx.draw_choice("four_position_bias",
                                              ["spread", "center"]))
    dist_kind = overrides.get("four_distance_kind",
                              ctx.draw_choice("four_distance_kind",
                                              ["near", "medium", "far"]))
    g = full_grid(h, w, 0)
    five_positions = _pick_positions(five_bias, h, w, n_fives, rng)
    for r, c in five_positions:
        g[r][c] = 5
    min_dist = {"near": 2, "medium": 3, "far": 4}.get(dist_kind, 2)
    placed_fours = 0
    for _ in range(n_fours * 5):
        if placed_fours >= n_fours:
            break
        for _try in range(20):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0:
                continue
            min_cheb = min(max(abs(r - fr), abs(c - fc))
                           for fr, fc in five_positions)
            if min_cheb < min_dist:
                continue
            g[r][c] = 4
            placed_fours += 1
            break
    if placed_fours < 1:
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0:
                    min_cheb = min(max(abs(r - fr), abs(c - fc))
                                   for fr, fc in five_positions)
                    if min_cheb >= 2:
                        g[r][c] = 4
                        return g
    return g


def _pick_positions(bias, h, w, n, rng):
    positions = []
    cells = [(r, c) for r in range(h) for c in range(w)]
    if bias == "center":
        cr, cc = h // 2, w // 2
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return cells[:n]
    if bias == "edge":
        cells.sort(key=lambda rc: -min(rc[0], h - 1 - rc[0],
                                       rc[1], w - 1 - rc[1]))
        return cells[:n]
    if bias == "corners":
        corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
        return corners[:n]
    rng.shuffle(cells)
    return cells[:n]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_fives":
        g[h // 2][w // 2] = 4
        return g
    if name == "no_fours":
        g[h // 2][w // 2] = 5
        return g
    if name == "all_5s":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    fives = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    fours = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4]
    if not fives:
        errors.append("expected at least one color-5 anchor")
    if not fours:
        errors.append("expected at least one color-4 halo source")
    if any(v == 2 for row in grid for v in row):
        errors.append("input should not contain output-only color 2")
    if fives and fours:
        far_enough = [max(abs(r - fr), abs(c - fc)) for r, c in fours for fr, fc in fives]
        if not any(d >= 2 for d in far_enough):
            errors.append("at least one 4-cell should be distance >=2 from a 5-cell")
    return errors
