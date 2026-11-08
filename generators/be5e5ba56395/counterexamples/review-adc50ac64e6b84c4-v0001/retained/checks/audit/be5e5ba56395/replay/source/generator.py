"""Generator for arc_puzzle_bank_thirteenth_21_bundle:easy_85_outline_filled_rectangles.

Rule: each filled rectangle component is reduced to its bounding-box
outline (interior cleared).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, rectangles, texture.
Degenerates: no_rectangles, only_2x2_rect, non_rectangular_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "be5e5ba56395"
VERSION = "1.1.1"
TASK_ID = "be5e5ba56395"

SUMMARY = "Solid colored rectangles are reduced to their bounding-box outlines."

INVARIANTS = [
    "background is 0",
    "every colored component is a filled axis-aligned rectangle",
    "rectangles are at least 3x3 so the outline differs from the input",
    "rectangles are separated by background",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rectangles", "only_2x2_rect", "non_rectangular_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rectangles":     {"type": "int", "default": "rng 2..3", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "= rectangles", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered_solid_rectangles",
                       "valid": "scattered_solid_rectangles"},
    "n_distinct_colors": {"type": "int", "default": "= rectangles", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at least one solid filled rectangle of size ≥3×3."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    # Collect non-zero cells grouped by color
    from collections import defaultdict
    by_color: dict = defaultdict(list)
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                by_color[v].append((r, c))
    if not by_color:
        errs.append("no non-zero cells found")
        return errs
    # Each color should form a filled solid rectangle
    found_rect = False
    for color, cells in by_color.items():
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        bh, bw = r1 - r0 + 1, c1 - c0 + 1
        expected = bh * bw
        if len(cells) == expected and bh >= 3 and bw >= 3:
            found_rect = True
    if not found_rect:
        errs.append("no solid filled rectangle ≥3×3 found")
    return errs


def _free(g, r0, c0, r1, c1):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r1 >= h or c1 >= w:
        return False
    for r in range(max(0, r0 - 1), min(h, r1 + 2)):
        for c in range(max(0, c0 - 1), min(w, c1 + 2)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("rectangles", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        target = ctx.draw_int("rectangles", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 9, 14)
        target = ctx.draw_int("rectangles", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(9, target))
    placed = 0
    for _ in range(160):
        if placed >= target:
            break
        rh = rng.randint(3, min(5, h))
        rw = rng.randint(3, min(5, w))
        r0 = rng.randint(0, h - rh)
        c0 = rng.randint(0, w - rw)
        r1, c1 = r0 + rh - 1, c0 + rw - 1
        if _free(g, r0, c0, r1, c1):
            color = colors[placed % len(colors)]
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    g[r][c] = color
            placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_rectangles":
        # Empty grid — rule has no rectangles to outline.
        return g
    if name == "only_2x2_rect":
        # 2×2 rectangle has no strict interior — outline equals the
        # full rectangle, rule's effect is invisible.
        for r in range(2):
            for c in range(2): g[2 + r][3 + c] = 4
        return g
    if name == "non_rectangular_blob":
        # Components are not solid rectangles (e.g., L-shape) — rule's
        # "rectangle outline" preconditions fail; no clean outline
        # to compute.
        for r, c in [(2, 2), (2, 3), (2, 4), (3, 2), (4, 2)]: g[r][c] = 4
        return g
    return g
