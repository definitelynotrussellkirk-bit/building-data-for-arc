"""Generator for arc_additional_puzzle_bank_volume7:H47.

Rule: the number of red cells gives the Manhattan distance from green
markers to paint as 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, red_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_green, no_red, distance_zero.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3511f98c7b84"
VERSION = "1.2.0"
TASK_ID = "3511f98c7b84"
SUMMARY = "Count of red(2) cells = Manhattan distance ring radius around green(3) markers; bg cells at that radius become 8."

# Rivals: 'paint distance = fixed N' refuted by ≥2 demos with different
# red counts. 'paint all bg' refuted by any demo with bg cells off-ring.
# 'use red color for the ring' refuted by any demo (always 8). 'distance
# from any color' refuted by ≥1 demo with non-3 distractor cells — the
# rule's distance ring centers only on color-3.
# 4 demos with varied red counts + multiple green markers cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "there is at least one green marker",
    "red cell count is small enough to leave visible blank cells at that distance",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_green", "no_red", "distance_zero")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "red_count":      {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
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
        h_lo, h_hi, w_lo, w_hi = 8, 10, 8, 10
        k_lo, k_hi = 1, 2
        n_green_lo, n_green_hi = 1, 1
        n_distract_lo, n_distract_hi = 0, 2
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 13, 16, 13, 16
        k_lo, k_hi = 3, 5
        n_green_lo, n_green_hi = 2, 3
        n_distract_lo, n_distract_hi = 3, 6
    else:
        h_lo, h_hi, w_lo, w_hi = 10, 13, 10, 13
        k_lo, k_hi = 2, 4
        n_green_lo, n_green_hi = 1, 2
        n_distract_lo, n_distract_hi = 1, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    k = ctx.draw_int("red_count", k_lo, k_hi)
    n_green = ctx.draw_int("n_green", n_green_lo, n_green_hi)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Random green positions (was fixed at center + maybe one fixed
    # corner).
    placed_green = 0
    for _ in range(40):
        if placed_green >= n_green: break
        r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
        if g[r][c] == 0:
            g[r][c] = 3
            placed_green += 1
    # k red cells, anywhere on bg.
    placed_red = 0
    for _ in range(60):
        if placed_red >= k: break
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] == 0:
            g[r][c] = 2
            placed_red += 1
    # Distractor cells of non-{0, 2, 3, 8} colors. Rule ignores these.
    n_distractors = rng.randint(n_distract_lo, n_distract_hi)
    distractor_pool = [1, 4, 5, 6, 7, 9]
    placed_distract = 0
    for _ in range(60):
        if placed_distract >= n_distractors: break
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] == 0:
            g[r][c] = rng.choice(distractor_pool)
            placed_distract += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_green":
        # no green markers → distance has no source point
        g[2][3] = 2; g[5][7] = 2
        return g
    if name == "no_red":
        # no red cells → count is 0, distance 0, ring collapses to the marker
        g[h // 2][w // 2] = 3
        return g
    if name == "distance_zero":
        # red_count = 0 and only green present → ring is the marker itself, no 8s painted
        g[h // 2][w // 2] = 3
        g[2][w - 3] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """≥1 green(3) marker; ≥1 red(2) cell to set ring radius."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    if not any(grid[r][c] == 3 for r in range(h) for c in range(w)):
        errs.append("no green(3) marker found")
    if not any(grid[r][c] == 2 for r in range(h) for c in range(w)):
        errs.append("no red(2) cell found (ring radius undefined)")
    return errs
