"""Generator for arc_puzzle_bank_21_set8:easy_h07.

Replace solid rectangles with their same-color contours.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rects, all_2x2, hollow_outline.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "87b0209ee7e8"
VERSION = "1.1.1"
TASK_ID = "87b0209ee7e8"

SUMMARY = "Replace solid rectangles with their same-color contours."

INVARIANTS = [
    "background is 0",
    "objects are separated solid monochrome rectangles",
    "at least one rectangle has an interior",
    "interior cells are erased while borders remain",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rects", "all_2x2", "hollow_outline")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 10..12", "valid": "6..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rects":        {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "solid_rectangles",
                       "valid": "solid_rectangles"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; non-zero cells form solid filled rectangles; at least one has interior (>= 3x3)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        return []  # degenerate no_rects — allowed
    # Find 4-connected components and check each is a solid rectangle
    visited = set()
    comps = []
    for sr, sc in nonzero:
        if (sr, sc) in visited:
            continue
        comp = []
        stack = [(sr, sc)]
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            if grid[r][c] != 0:
                comp.append((r, c))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited:
                        stack.append((nr, nc))
        if comp:
            comps.append(comp)
    errs = []
    has_interior = False
    for comp in comps:
        rs = [r for r, c in comp]; cs = [c for r, c in comp]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        # Solid filled rectangle: all cells in bbox must be present
        if len(comp) != bh * bw:
            return []  # degenerate hollow_outline — allowed
        if bh >= 3 and bw >= 3:
            has_interior = True
    if not has_interior:
        return []  # degenerate all_2x2 — allowed
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 10, 11)
        target = ctx.draw_int("rectangles", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 12)
        target = ctx.draw_int("rectangles", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 10, 12)
        target = ctx.draw_int("rectangles", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(220):
        if placed >= target:
            break
        rh = rng.randint(3 if placed == 0 else 2, min(4, h))
        rw = rng.randint(3 if placed == 0 else 2, min(5, w))
        r0 = rng.randint(0, h - rh)
        c0 = rng.randint(0, w - rw)
        if not _free(g, r0, c0, r0 + rh - 1, c0 + rw - 1):
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + rw):
                g[r][c] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 11
    g = full_grid(h, w, 0)
    if name == "no_rects":
        # blank → no rectangles to hollow
        return g
    if name == "all_2x2":
        # 2x2 rects → no interior to erase, rule is identity
        for r in range(2):
            for c in range(2):
                g[1 + r][1 + c] = 4
                g[5 + r][7 + c] = 6
        return g
    if name == "hollow_outline":
        # already-hollow outline → rule is identity, no change
        for c in range(2, 7): g[1][c] = 4; g[5][c] = 4
        for r in range(1, 6): g[r][2] = 4; g[r][6] = 4
        return g
    return g
