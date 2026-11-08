"""Generator for arc_additional_puzzles_21_set9:M57 — Rotate target around 5-pivot.

Rule: target color is g[0][0]. Rotate target-cells around the 5-pivot
4-fold (0, 90, 180, 270) and paint at each rotation.

Combinatorial axes (8): grid_n, palette_kind, target_color,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pivot, no_target_at_origin, pivot_at_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2829d0f18326"
VERSION = "1.2.0"  # fix identity_demo: guarantee >=1 rotatable target cell off the origin (the 0.7-prob loop could place none on small grids -> only the excluded origin target -> rotation paints nothing -> output==input)
TASK_ID = "2829d0f18326"
SUMMARY = "Square grid with target color at (0,0), 5-pivot in middle, 2-3 target cells, 1 distractor."

INVARIANTS = [
    "g[0][0] is the target color (non-zero, non-5)",
    "exactly one 5-cell at the center",
    "2-3 target cells on a diagonal away from pivot",
    "1 distractor cell of another color (not rotated)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pivot", "no_target_at_origin", "pivot_at_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_n":         {"type": "int", "default": "rng 7..9", "valid": "5..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "target_color":   {"type": "int", "default": "rng 1..9 != 5",
                       "valid": "1..9 != 5"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "pivot_with_diagonal_target",
                       "valid": "pivot_with_diagonal_target"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pivot|no_target_at_origin|pivot_at_corner"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # square odd-n grid (4-fold rotation around a pivot); was {7,9} -> in=2. Widen the
    # odd-n range (rule reads rows/cols).
    if difficulty == "easy":
        n = ctx.draw_int("grid_n", 5, 7)
    elif difficulty == "hard":
        n = ctx.draw_int("grid_n", 11, 15)
    else:
        n = ctx.draw_int("grid_n", 7, 11)
    if n % 2 == 0:
        n += 1
    g = full_grid(n, n, 0)
    rng = ctx.draw_rng("layout")
    target = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    g[0][0] = target
    pivot_r = n // 2; pivot_c = n // 2
    g[pivot_r][pivot_c] = 5
    placed = 0
    for k in range(1, pivot_r):
        if rng.random() < 0.7:
            g[k][k] = target
            placed += 1
    # The rule rotates target cells around the pivot but EXCLUDES the origin
    # (0,0). If the probabilistic loop placed no off-origin target cell, the
    # rotation has nothing to paint and the output equals the input. Force
    # at least one diagonal target cell so a visible rotation always occurs.
    if placed == 0 and pivot_r > 1:
        g[1][1] = target
    distract = rng.choice([v for v in [1, 2, 3, 4, 6, 7, 8, 9] if v != target])
    for _ in range(40):
        r = rng.randint(pivot_r + 1, n - 2); c = rng.randint(0, pivot_c - 1)
        if g[r][c] == 0:
            g[r][c] = distract
            break
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Input must have the target at (0,0), exactly one 5-pivot, and >=1
    further target cell to rotate (else the rule is an identity no-op)."""
    from collections import Counter
    issues = []
    target = grid[0][0]
    if target in (0, 5):
        issues.append(f"origin target is {target} (must be non-zero, non-5)")
    cnt = Counter(v for row in grid for v in row)
    if cnt.get(5, 0) != 1:
        issues.append(f"expected exactly one 5-pivot, got {cnt.get(5, 0)}")
    if cnt.get(target, 0) < 2:
        issues.append("no off-origin target cell -> rotation is a no-op")
    return issues


def _draw_from_degenerate(name, rng):
    n = 7
    g = full_grid(n, n, 0)
    if name == "no_pivot":
        # target cells without 5-pivot → no rotation center
        g[0][0] = 4
        g[1][1] = 4
        g[2][2] = 4
        return g
    if name == "no_target_at_origin":
        # 5-pivot present but g[0][0] is 0 → no target color identified
        g[3][3] = 5  # pivot
        g[1][1] = 4  # cells but g[0][0] = 0
        g[2][2] = 4
        return g
    if name == "pivot_at_corner":
        # pivot at corner → rotated targets fall mostly out of bounds
        g[0][0] = 4
        g[0][n - 1] = 5  # pivot at corner
        g[1][n - 2] = 4
        return g
    return g
