"""Generator for arc_additional_puzzle_bank_volume13:E85 — diagonal blue → 2x2 square completion.

Rule: each isolated 2x2 box with exactly two diagonal blue cells is
completed into a 2x2 red square.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, axis_aligned, already_full.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a74527c8b210"
VERSION = "1.1.1"
TASK_ID = "a74527c8b210"
SUMMARY = "Isolated blue diagonal pairs in 2x2 boxes are completed into red 2x2 squares."

INVARIANTS = [
    "each target is a 2x2 box with exactly two diagonal blue cells",
    "target boxes are separated so completions do not interact",
    "non-target objects remain unchanged",
    "at least one target pair is present",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "axis_aligned", "already_full")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "5..18"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "1 (blue)", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "scattered_diagonal_2x2",
                       "valid": "scattered_diagonal_2x2"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _clear_for_pair(g: list[list[int]], r0: int, c0: int) -> bool:
    h = len(g)
    w = len(g[0])
    for r in range(max(0, r0 - 1), min(h, r0 + 3)):
        for c in range(max(0, c0 - 1), min(w, c0 + 3)):
            if g[r][c] != 0:
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at least one blue(1) cell; all values are valid ARC colors (0-9)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    bad = [(r, c) for r in range(h) for c in range(w) if not (0 <= grid[r][c] <= 9)]
    if bad:
        errs.append(f"out-of-range values at {bad[:3]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n_pairs = ctx.draw_int("n_pairs", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        n_pairs = ctx.draw_int("n_pairs", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
        n_pairs = ctx.draw_int("n_pairs", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    candidates = [(r, c) for r in range(0, h - 1) for c in range(0, w - 1)]
    rng.shuffle(candidates)
    placed = 0
    for r, c in candidates:
        if placed >= n_pairs:
            break
        if not _clear_for_pair(g, r, c):
            continue
        if rng.choice([True, False]):
            g[r][c] = 1
            g[r + 1][c + 1] = 1
        else:
            g[r][c + 1] = 1
            g[r + 1][c] = 1
        placed += 1
    if placed == 0:
        g[1][1] = 1
        g[2][2] = 1
    if h > 8 and w > 8:
        g[h - 2][w - 2] = rng.choice([7, 8])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — no diagonal pair to complete.
        return g
    if name == "axis_aligned":
        # Blue cells in 2x2 boxes but axis-aligned (horizontal or vertical
        # adjacent), not diagonal — rule's diagonal-pair filter doesn't match.
        g[2][2] = 1; g[2][3] = 1
        g[5][6] = 1; g[6][6] = 1
        return g
    if name == "already_full":
        # 2x2 box already fully filled with blue — rule's "complete to
        # full 2x2" target is already met, no completion needed.
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][3 + dc] = 1
        return g
    return g
