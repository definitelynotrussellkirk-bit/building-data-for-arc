"""Generator for arc_puzzle_bank_21_set24_s:S24_E4.

Combinatorial axes (8): grid_h, grid_w, palette_kind, object_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects, single_layer, all_4x4.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "defe0ec9ccfc"
VERSION = "1.1.0"
TASK_ID = "defe0ec9ccfc"
SUMMARY = "Onion layers are recolored by odd/even depth parity."

INVARIANTS = [
    "background is 0",
    "objects are separated solid rectangles",
    "output colors depend only on onion-depth parity",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "single_layer", "all_4x4")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "8..20"},
    "grid_w":         {"type": "int", "default": "rng 13..17", "valid": "8..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "object_count":   {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "separated_solid_rects",
                       "valid": "separated_solid_rects"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(grid, r0, c0, rh, rw):
    h, w = len(grid), len(grid[0])
    if r0 < 0 or c0 < 0 or r0 + rh > h or c0 + rw > w:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + rh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + rw + 1)):
            if grid[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 14)
        count = ctx.draw_int("object_count", 2, 2)
        min_count = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 15)
        w = ctx.draw_int("grid_w", 16, 17)
        count = ctx.draw_int("object_count", 3, 3)
        min_count = 3
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 13, 17)
        count = ctx.draw_int("object_count", 2, 3)
        min_count = 2
    rng = ctx.draw_rng("layout")
    for target in range(count, min_count - 1, -1):
        for _layout in range(120):
            grid = full_grid(h, w, 0)
            colors = rng.sample([4, 5, 6, 7, 8], target)
            placed = 0
            for color in colors:
                for _ in range(160):
                    rh = rng.randint(4, min(7, h))
                    rw = rng.randint(4, min(7, w))
                    r0 = rng.randint(0, h - rh)
                    c0 = rng.randint(0, w - rw)
                    if not _free(grid, r0, c0, rh, rw):
                        continue
                    for r in range(r0, r0 + rh):
                        for c in range(c0, c0 + rw):
                            grid[r][c] = color
                    placed += 1
                    break
                else:
                    break
            if placed == target:
                return grid
    grid = full_grid(h, w, 0)
    fallback = [(0, 0), (0, max(0, w - 4)), (max(0, h - 4), max(0, w // 2 - 2))]
    for color, (r0, c0) in zip([4, 5, 6], fallback[:min_count]):
        for r in range(r0, min(h, r0 + 4)):
            for c in range(c0, min(w, c0 + 4)):
                grid[r][c] = color
    return grid

def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_objects":
        # blank → no rects to onion-fill
        return g
    if name == "single_layer":
        # 1x1 or 2x2 rect → no nested onion layers (depth ≤ 1)
        for r in range(2):
            for c in range(2): g[2 + r][2 + c] = 4
        return g
    if name == "all_4x4":
        # all rects are 4x4 → only 2 onion depths, parity collapses
        for r in range(4):
            for c in range(4):
                g[1 + r][1 + c] = 4
                g[1 + r][8 + c] = 6
        return g
    return g

def _sc_components(grid):
    h, w = len(grid), len(grid[0]); seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0: continue
            col = grid[r][c]; stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == col:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append(cells)
    return out

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    comps = _sc_components(grid)
    lo = 3 if difficulty == "hard" else 2
    errs: list[str] = []
    if len(comps) < lo: errs.append(f"expected at least {lo} rectangles, got {len(comps)}")
    for cells in comps:
        r1 = min(r for r, _ in cells); c1 = min(c for _, c in cells); r2 = max(r for r, _ in cells); c2 = max(c for _, c in cells)
        if len(cells) != (r2 - r1 + 1) * (c2 - c1 + 1): errs.append("component is not a solid rectangle")
        if r2 - r1 + 1 < 4 or c2 - c1 + 1 < 4: errs.append("rectangle too small for onion layers")
    return errs
