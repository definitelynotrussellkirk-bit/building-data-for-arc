"""Generator for arc_puzzle_bank_fifteenth_21_bundle:easy_103_fill_rectangles_from_opposite_corners.

Rule: each unique-color opposite-corner pair has its bounding-box
filled.

Combinatorial axes (8): grid_h, grid_w, palette_kind, rectangles,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_corners, single_corner, collinear_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "89c85768abe1"
VERSION = "1.1.1"
TASK_ID = "89c85768abe1"

SUMMARY = "Place unique-color opposite corner pairs whose bounding boxes get filled."

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "same-color cells are opposite corners of a rectangle",
    "filled rectangle regions are disjoint",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_corners", "single_corner", "collinear_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rectangles":     {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "= rectangles", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "disjoint_corner_pairs",
                       "valid": "disjoint_corner_pairs"},
    "n_distinct_colors": {"type": "int", "default": "= rectangles", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; every non-bg color appears exactly twice."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    counts: dict[int, int] = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                counts[v] = counts.get(v, 0) + 1
    if not counts:
        return []  # no_corners degenerate — allowed
    errs = []
    for color, cnt in counts.items():
        if cnt != 2:
            errs.append(f"color {color} appears {cnt} times (expected 2 for opposite corners)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("rectangles", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 12, 16)
        target = ctx.draw_int("rectangles", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        target = ctx.draw_int("rectangles", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k=target)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        rh = rng.randint(2, min(4, h))
        rw = rng.randint(2, min(5, w))
        r1 = rng.randint(0, h - rh)
        c1 = rng.randint(0, w - rw)
        r2 = r1 + rh - 1
        c2 = c1 + rw - 1
        rect = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        if rect & reserved:
            continue
        color = colors[placed]
        if rng.randrange(2):
            a, b = (r1, c1), (r2, c2)
        else:
            a, b = (r1, c2), (r2, c1)
        g[a[0]][a[1]] = color
        g[b[0]][b[1]] = color
        reserved.update(rect)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_corners":
        # Empty grid — no opposite-corner pair to fill from.
        return g
    if name == "single_corner":
        # Each color appears once — no pair to define a bbox.
        g[2][2] = 4
        g[6][7] = 6
        return g
    if name == "collinear_pair":
        # Same-color cells on the same row — bbox collapses to a line,
        # the rule's fill produces no 2D rectangle.
        g[2][1] = 4; g[2][7] = 4
        g[6][2] = 6; g[6][8] = 6
        return g
    return g
