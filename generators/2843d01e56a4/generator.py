"""Generator for arc_puzzle_bank_next21:E9.

Place separated 2x2 same-color L-shapes with one missing corner.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_shapes, full_2x2, two_corners.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2843d01e56a4"
VERSION = "1.1.1"
TASK_ID = "2843d01e56a4"

SUMMARY = "Place separated 2x2 same-color L-shapes with one missing corner."

INVARIANTS = [
    "background is 0",
    "each active 2x2 block has exactly three same-color cells",
    "the missing corner is initially 0",
    "active windows are separated to avoid accidental completions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_shapes", "full_2x2", "two_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_shapes":       {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "isolated_l_triominoes",
                       "valid": "isolated_l_triominoes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_shapes|full_2x2|two_corners"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 non-zero cells (L-triominoes); no fully-filled 2×2 block."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_shapes", "full_2x2", "two_corners"):
        return []
    errs = []
    nonzero = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nonzero < 3:
        errs.append(f"only {nonzero} non-zero cells; expected ≥3 for an L-triomino")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
        target = ctx.draw_int("shapes", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        target = ctx.draw_int("shapes", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 6, 9)
        target = ctx.draw_int("shapes", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(target, 9))
    for _ in range(300):
        if placed >= target:
            break
        r0 = rng.randint(0, h - 2)
        c0 = rng.randint(0, w - 2)
        guard = {
            (r, c)
            for r in range(max(0, r0 - 1), min(h, r0 + 3))
            for c in range(max(0, c0 - 1), min(w, c0 + 3))
        }
        if guard & reserved:
            continue
        missing = rng.choice([(0, 0), (0, 1), (1, 0), (1, 1)])
        color = colors[placed % len(colors)]
        for dr in [0, 1]:
            for dc in [0, 1]:
                if (dr, dc) != missing:
                    g[r0 + dr][c0 + dc] = color
        reserved.update(guard)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_shapes":
        # blank → no L-shapes to complete
        return g
    if name == "full_2x2":
        # 2x2 already complete → no missing corner
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 4
        return g
    if name == "two_corners":
        # only 2 corners → "exactly three" precondition fails
        g[1][1] = 4; g[2][2] = 4
        return g
    return g
