"""Generator for arc_additional_puzzles_21_set10_bundle:M66.

Rule: objects are sorted by reading order (top-left position) and encoded as
rows of their color repeated by size. Output = N_objects rows x MAX_size cols,
where row i has size_i copies of color_i (padded with 0). The rule reads only
each object's COLOR and SIZE (not its shape).

The old generator placed EXACTLY 4 objects of FIXED shapes/sizes {1,2,3,4} at
hardcoded corners -> output always 4x4 (shape-locked-out; canonical has 3
objects with varying sizes -> 3x8, 3x5). Now: a VARYING number of objects
(2-5), each a random connected polyomino of VARYING size, distinct colors,
scattered -> output dims (rows = count, cols = max size) vary widely.

Combinatorial axes: object count (-> rows), each object's size (-> max width),
colors, reading-order positions, grid size.
Degenerates: equal_sizes, single_object, no_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "56362868a163"
VERSION = "3.0.1"  # shape-locked-out: rule emits N_objects rows x max-size cols, but old gen placed EXACTLY 4 fixed-size objects {1,2,3,4} -> always 4x4 (canonical has 3 objects, varied sizes). Now vary object count (2-5) + each object's size -> output rows AND width vary. Rule uses only obj color+size, so shapes are random polyominoes.
TASK_ID = "56362868a163"
SUMMARY = (
    "0-bg grid (size varies) with N (2-5) separated OBJECTS, each a random "
    "connected polyomino of varying SIZE (1-9 cells) in a distinct color, at "
    "scattered positions. Rule (SORT BY READING ORDER + ENCODE): sort objects "
    "by top-left position (row then col); emit an output grid of N rows x "
    "MAX_size cols where row i is the i-th object's color repeated by its size "
    "(left-justified, padded with 0). Output dims = (object count) x (max "
    "object size), both varying. Rule reads only each object's color and size."
)

INVARIANTS = [
    "objects are separated (distinct connected components) in reading order",
    "object sizes vary, making row lengths visible",
    "each object has a distinct color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("equal_sizes", "single_object", "no_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "2..5"},
    "size_spread":    {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _poly(rng, n):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for (r, c) in cells]


def _free(g, top, left, cells):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        rr, cc = top + dr, left + dc
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                nr, nc = rr + ddr, cc + ddc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 9, 12)
        n = ctx.draw_int("n_objects", 2, 3); smax = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 14, 20)
        n = ctx.draw_int("n_objects", 4, 5); smax = 9
    else:
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 11, 16)
        n = ctx.draw_int("n_objects", 3, 4); smax = 7

    colors = list(ctx.draw_distinct_colors("colors", n=n, exclude=[0]))
    # distinct sizes where possible so row lengths (and the max) vary
    sizes = [rng.randint(1, smax) for _ in range(n)]
    g = full_grid(h, w, 0)
    placed = 0
    for i in range(n):
        cells = _poly(rng, sizes[i])
        sh = max(r for r, _ in cells) + 1
        sw = max(c for _, c in cells) + 1
        if sh > h or sw > w:
            continue
        for _ in range(120):
            top = rng.randint(0, h - sh)
            left = rng.randint(0, w - sw)
            if _free(g, top, left, cells):
                paint_at(g, top, left, cells, colors[i])
                placed += 1
                break
    if placed < 2:                          # ensure >=2 objects (output >=2 rows)
        g = full_grid(12, 14, 0)
        paint_at(g, 1, 1, _poly(rng, 3), colors[0])
        paint_at(g, 1, 8, _poly(rng, 2), colors[1] if len(colors) > 1 else 3)
        paint_at(g, 7, 3, _poly(rng, 5), colors[2] if len(colors) > 2 else 4)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least 2 distinct-color connected objects present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    # Find 4-connected components (flood fill)
    visited = [[False] * w for _ in range(h)]
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and not visited[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                visited[r][c] = True
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == color:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                components.append((color, len(cells)))
    if len(components) < 2:
        errs.append(f"expected at least 2 objects, found {len(components)}")
    colors = {c for c, _ in components}
    if len(colors) < 2:
        errs.append(f"expected at least 2 distinct colors, found {len(colors)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "equal_sizes":
        paint_at(g, 1, 1, [(0, 0), (0, 1)], 2)
        paint_at(g, 1, w - 4, [(0, 0), (0, 1)], 3)
        paint_at(g, h - 3, 1, [(0, 0), (0, 1)], 4)
        paint_at(g, h - 3, w - 4, [(0, 0), (0, 1)], 5)
        return g
    if name == "single_object":
        paint_at(g, 2, 3, [(0, 0), (0, 1), (0, 2), (1, 1)], 6)
        return g
    if name == "no_objects":
        return g
    return g
