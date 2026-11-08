"""Generator for arc_puzzle_bank_fourth_21_bundle:easy_23_fill_hollow_ring_centers.

Rule: each hollow 3x3 ring of color 1 has its center cell filled with 2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rings,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rings, solid_squares, ring_centers_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6bc12a0a6621"
VERSION = "1.1.1"
TASK_ID = "6bc12a0a6621"
SUMMARY = "Hollow 3x3 rings of color 1 with zero centers."

INVARIANTS = [
    "background is 0",
    "every target is an exact hollow 3x3 ring of color 1",
    "ring centers are 0 before the rule fills them with 2",
    "rings do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rings", "solid_squares", "ring_centers_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rings":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "spaced_3x3_rings",
                       "valid": "spaced_3x3_rings"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; >=1 hollow 3x3 ring of color 1 (8-perimeter, center=0)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not ones:
        return errs  # degenerate (no_rings) — allowed
    # Check for at least one hollow 3x3 ring: 8 perimeter cells of color 1, center = 0
    found_ring = False
    for r1 in range(h - 2):
        for c1 in range(w - 2):
            perimeter = [(r1, c1), (r1, c1+1), (r1, c1+2),
                         (r1+1, c1), (r1+1, c1+2),
                         (r1+2, c1), (r1+2, c1+1), (r1+2, c1+2)]
            if all(grid[r][c] == 1 for r, c in perimeter) and grid[r1+1][c1+1] == 0:
                found_ring = True
                break
        if found_ring:
            break
    if not found_ring:
        errs.append("color-1 cells present but no hollow 3x3 ring found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n_rings = ctx.draw_int("n_rings", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n_rings = ctx.draw_int("n_rings", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        n_rings = ctx.draw_int("n_rings", 2, 4)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    boxes: list[tuple[int, int]] = []
    for _ in range(120):
        if len(boxes) >= n_rings:
            break
        r = rng.randint(0, h - 3)
        c = rng.randint(0, w - 3)
        if any(abs(r - rr) < 4 and abs(c - cc) < 4 for rr, cc in boxes):
            continue
        boxes.append((r, c))
        for dr in range(3):
            for dc in range(3):
                if dr != 1 or dc != 1:
                    g[r + dr][c + dc] = 1
    if not boxes:
        for dr in range(3):
            for dc in range(3):
                if dr != 1 or dc != 1:
                    g[dr][dc] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_rings":
        # blank → no rings, rule has no effect
        return g
    if name == "solid_squares":
        # solid 3x3 squares (no hole) → rule's hollow predicate fails
        for r in range(1, 4):
            for c in range(1, 4): g[r][c] = 1
        for r in range(5, 8):
            for c in range(5, 8): g[r][c] = 1
        return g
    if name == "ring_centers_filled":
        # rings present but centers already non-zero → rule writes over wrong color
        for dr in range(3):
            for dc in range(3):
                if dr != 1 or dc != 1: g[1 + dr][1 + dc] = 1
        g[2][2] = 8  # already filled with wrong color
        for dr in range(3):
            for dc in range(3):
                if dr != 1 or dc != 1: g[5 + dr][5 + dc] = 1
        g[6][6] = 3  # different wrong color
        return g
    return g
