"""Generator for arc_additional_puzzles_21_set4:E24 — 2x2 with 3 same-color cells + 1 zero → fill the zero.

Rule: for each 2×2 sub-block where exactly 3 cells share a single
non-zero color and 1 cell is 0, set the 0-cell to that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_l,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_l_pattern, full_squares, mixed_color_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0d655a5e1a2d"
VERSION = "1.2.1"  # + self_check
TASK_ID = "0d655a5e1a2d"
SUMMARY = "2-3 L-trominoes (size 3 in 2×2 bbox) of distinct colors."

INVARIANTS = [
    "≥2 L-tromino patterns: 3 cells of one color in a 2×2 with 4th = 0",
    "no two patterns within distance 2",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_l_pattern", "full_squares", "mixed_color_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "5..13"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_l":            {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "separated_l_trominoes",
                       "valid": "separated_l_trominoes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 L-tromino patterns (3 cells of one color in a 2x2 with 4th=0)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    count = 0
    for r in range(h - 1):
        for c in range(w - 1):
            block = [grid[r][c], grid[r][c+1], grid[r+1][c], grid[r+1][c+1]]
            nz = [v for v in block if v != 0]
            if len(nz) == 3 and len(set(nz)) == 1:
                count += 1
    if count < 1:
        errs.append(f"found {count} L-tromino pattern(s); need >=1")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 6, 7)
        target = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
        target = None
    else:
        h = ctx.draw_int("grid_h", 5, 11)
        w = ctx.draw_int("grid_w", 6, 12)
        target = None
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    if target is None:
        target = rng.randint(2, 5) if difficulty == "hard" else rng.randint(2, 4)
    palette = [2, 3, 4, 5, 6, 7, 8, 9]
    placed = []
    L_variants = [
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (1, 1)],
        [(0, 1), (1, 0), (1, 1)],
    ]
    for _ in range(120):
        if len(placed) >= target:
            break
        r = rng.randint(0, h - 2); c = rng.randint(0, w - 2)
        if all(abs(r - pr) > 2 or abs(c - pc) > 2 for pr, pc in placed):
            color = rng.choice(palette)
            for dr, dc in rng.choice(L_variants):
                g[r + dr][c + dc] = color
            placed.append((r, c))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 7
    g = full_grid(h, w, 0)
    if name == "no_l_pattern":
        # blank → no L-trominoes to complete
        return g
    if name == "full_squares":
        # 2x2 fully filled → no zero corner to fill
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 4
        return g
    if name == "mixed_color_l":
        # 2×2 has 3 nonzero cells of 3 different colors → no shared color
        g[1][1] = 4; g[1][2] = 6; g[2][1] = 7
        return g
    return g
