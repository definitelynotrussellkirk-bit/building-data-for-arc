"""Generator for arc_additional_puzzle_bank_volume18:E120 — odd-length blue middle recolor.

Rule: odd-length blue segments have only their middle cell recolored
red.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_segments,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_segments, even_length, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bedf1922195c"
VERSION = "1.2.1"
TASK_ID = "bedf1922195c"
SUMMARY = "Axis-aligned blue (1) segments of various lengths. Rule recolors ONLY the middle cell of each odd-length (≥ 3) horizontal or vertical segment to red (2); even-length segments and singletons unchanged."

# Rivals: 'recolor all blue' refuted by ≥2 demos with even-length or
# singleton segments staying. 'recolor every odd cell' refuted by any
# demo (only segment midpoint becomes 2). 'use a different output
# color' refuted by any demo (mid is 2). 'operate on diagonal too'
# refuted by ≥1 demo with diagonal-only blue cells unchanged.
# 3 demos with mixed segment lengths cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "blue components are straight odd-length segments",
    "segments have length at least three",
    "segments are separated so components do not merge",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_segments", "even_length", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_segments":     {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1 (blue)", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "axis_aligned_odd_length",
                       "valid": "axis_aligned_odd_length"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has blue (1) cells; no color-2 cells in input (rule writes 2)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    blue = [(r, c) for r in range(len(grid)) for c in range(w) if grid[r][c] == 1]
    red = [(r, c) for r in range(len(grid)) for c in range(w) if grid[r][c] == 2]
    if not blue:
        errs.append("no blue (color 1) segments found")
    if red:
        errs.append(f"color 2 already present in input ({len(red)} cells) — rule writes 2")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        n_segments = ctx.draw_int("n_segments", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        n_segments = ctx.draw_int("n_segments", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_segments = ctx.draw_int("n_segments", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    # Place a mix of horizontal/vertical segments with varied lengths
    occupied = [[False] * w for _ in range(h)]
    made = 0
    for _ in range(300):
        if made >= n_segments: break
        horizontal = rng.choice([True, False])
        length = rng.choice([3, 5, 7])
        if horizontal:
            if length > w: continue
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - length)
            # Ensure no overlap and 1-cell margin
            collide = False
            for dr in range(-1, 2):
                for dc in range(-1, length + 1):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and occupied[nr][nc]:
                        collide = True; break
                if collide: break
            if collide: continue
            for dc in range(length):
                g[r][c + dc] = 1
                occupied[r][c + dc] = True
            made += 1
        else:
            if length > h: continue
            r = rng.randint(0, h - length)
            c = rng.randint(0, w - 1)
            collide = False
            for dr in range(-1, length + 1):
                for dc in range(-1, 2):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and occupied[nr][nc]:
                        collide = True; break
                if collide: break
            if collide: continue
            for dr in range(length):
                g[r + dr][c] = 1
                occupied[r + dr][c] = True
            made += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_segments":
        # Empty grid — no blue segment to recolor.
        return g
    if name == "even_length":
        # Blue segments of length 2 and 4 — no integer middle cell,
        # so the rule's middle-recolor never fires.
        for dc in range(2):
            g[1][1 + dc] = 1
        for dc in range(4):
            g[5][2 + dc] = 1
        for dr in range(4):
            g[3 + dr][8] = 1
        return g
    if name == "single_cell":
        # Length-1 segments — too short for the rule's length-3+ filter,
        # no middle cell to recolor.
        g[1][1] = 1; g[3][5] = 1; g[7][2] = 1
        return g
    return g
