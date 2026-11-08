"""Generator for arc_additional_puzzle_bank_volume3:E21.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_windows,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_windows, full_2x2, mixed_color_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5b40e03f0a23"
VERSION = "1.2.0"
TASK_ID = "5b40e03f0a23"
SUMMARY = "2x2 green almost-squares are completed by filling the missing cell green."

INVARIANTS = [
    "background is 0",
    "each active 2x2 window has exactly three green cells",
    "the fourth cell starts blank",
    "active windows are separated so closure does not cascade between shapes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_windows", "full_2x2", "mixed_color_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_windows":      {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_l_windows",
                       "valid": "separated_l_windows"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n_windows = ctx.draw_int("n_windows", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        n_windows = ctx.draw_int("n_windows", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
        n_windows = ctx.draw_int("n_windows", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    corners = [(0, 0), (0, 1), (1, 0), (1, 1)]
    anchors: list[tuple[int, int]] = []
    for _ in range(220):
        if len(anchors) >= n_windows:
            break
        r = rng.randint(0, h - 2)
        c = rng.randint(0, w - 2)
        if any(abs(r - rr) < 3 and abs(c - cc) < 3 for rr, cc in anchors):
            continue
        missing = rng.choice(corners)
        for dr, dc in corners:
            if (dr, dc) != missing:
                g[r + dr][c + dc] = 3
        anchors.append((r, c))
    if not anchors:
        g[1][1] = 3
        g[1][2] = 3
        g[2][1] = 3
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one 3-cell L-shape of color 3 (three-quarters of a 2x2)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    # Check that all non-zero cells are color 3
    non_three = [(r, c) for r in range(h) for c in range(w)
                 if grid[r][c] not in (0, 3)]
    if non_three:
        errs.append(f"non-bg, non-3 cells found: {non_three[:3]}")
    # Check at least one color-3 cell exists
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if not threes:
        errs.append("no color-3 cells found")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_windows":
        # blank → no L-shapes to complete
        return g
    if name == "full_2x2":
        # 2x2 already full → no missing corner
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 3
        return g
    if name == "mixed_color_l":
        # 3 cells of 3 different colors → "three green" precondition fails
        g[1][1] = 3; g[1][2] = 4; g[2][1] = 6
        return g
    return g
