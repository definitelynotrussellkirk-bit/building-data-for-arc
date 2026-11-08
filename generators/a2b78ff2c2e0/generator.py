"""Generator for arc_additional_puzzles_21_set4:E28.

Rule: scattered nonzero cells are read into a single row in scan order.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_marks, single_mark, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a2b78ff2c2e0"
VERSION = "2.0.0"  # shape-locked-out: placed 4 cells at FIXED positions -> output always 1x4. Rule reads ALL nonzero values in scan order into a 1xN row (N=count). Scatter k (3..9) non-adjacent cells at varied positions -> output width + value-sequence both vary."
TASK_ID = "a2b78ff2c2e0"
SUMMARY = "Scattered non-adjacent nonzero cells (count varies) read into a single 1xN row in row-major scan order; output width = number of nonzero cells."

INVARIANTS = [
    "nonzero cells are separated by zeros",
    "reading-order values contain at least three cells",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marks", "single_mark", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "5..10"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "6..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6); w = ctx.draw_int("grid_w", 6, 8); k_lo, k_hi = 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 10); w = ctx.draw_int("grid_w", 8, 12); k_lo, k_hi = 6, 9
    else:
        h = ctx.draw_int("grid_h", 5, 8); w = ctx.draw_int("grid_w", 6, 10); k_lo, k_hi = 4, 7
    rng = ctx.draw_rng("layout")
    k = ctx.draw_int("n_marks", k_lo, k_hi)
    g = full_grid(h, w, 0)
    # Output = the 1xN row of nonzero values in row-major scan order. Scatter k
    # non-adjacent cells (Chebyshev >= 2, so they stay "separated by zeros") at
    # varied positions with random colors -> N and the value-sequence both vary.
    spots = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(spots)
    placed = []
    for (r, c) in spots:
        if len(placed) >= k:
            break
        if all(max(abs(r - pr), abs(c - pc)) >= 2 for pr, pc in placed):
            g[r][c] = rng.randint(1, 9)
            placed.append((r, c))
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 8, 0)
    if name == "no_marks":
        return g
    if name == "single_mark":
        g[3][3] = 3
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(8):
                g[r][c] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    marks = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    min_marks = 6 if difficulty == "hard" else (3 if difficulty == "easy" else 4)
    if len(marks) < min_marks:
        msgs.append(f"too few nonzero marks: {len(marks)} < {min_marks}")
    for i, (r, c) in enumerate(marks):
        for er, ec in marks[i + 1:]:
            if max(abs(r - er), abs(c - ec)) < 2:
                msgs.append("nonzero marks are adjacent; expected separated scan-order marks")
    return msgs
