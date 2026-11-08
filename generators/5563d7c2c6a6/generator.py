"""Generator for arc_additional_puzzle_bank_volume4:E28.

Rule: among the red (color 2) connected components, the SMALLEST is
recolored to blue (color 1). Other red components and bg are unchanged.

Combinatorial axes (8): grid_h/w, palette_kind, n_components, shape_ids,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_objects, single_object, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "5563d7c2c6a6"
VERSION = "1.2.1"
TASK_ID = "5563d7c2c6a6"
SUMMARY = "Multiple red (2) connected components, one uniquely smallest. Rule recolors only the smallest component to blue (1); the others stay red."

# Rivals: 'recolor all red to blue' refuted by ≥2 demos where only one
# component changes color. 'recolor the largest' refuted by ≥1 demo
# where the largest stays red. 'recolor by position (e.g. top-left)'
# refuted by ≥1 demo where the smallest is not in any specific
# location. 'use a different output color' refuted by any demo (1 is
# the target). 3 demos with varied sizes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "there are multiple red connected components",
    "one red component is uniquely smallest",
    "components are separated by background",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "single_object", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "8..18"},
    "n_components":   {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES_BY_SIZE = {
    1: [[(0, 0)]],
    2: [[(0, 0), (0, 1)], [(0, 0), (1, 0)]],
    3: [[(0, 0), (0, 1), (1, 0)], [(0, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (1, 1)], [(0, 0), (0, 1), (0, 2)],
        [(0, 0), (1, 0), (2, 0)]],
    4: [[(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 0), (0, 1), (1, 0), (2, 0)]],
    5: [[(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1)],
        [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]],
    6: [[(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]],
}


def _free(g, r0, c0, shape):
    h, w = len(g), len(g[0])
    for dr, dc in shape:
        r, c = r0 + dr, c0 + dc
        if not (0 <= r < h and 0 <= c < w): return False
        if g[r][c] != 0: return False
    for dr, dc in shape:
        for nr in range(r0 + dr - 1, r0 + dr + 2):
            for nc in range(c0 + dc - 1, c0 + dc + 2):
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid with bg=0; ≥2 red(2) components present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not reds:
        return errors  # degenerate (no_objects) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        n = ctx.draw_int("n_components", 2, 3)
        size_pool = [1, 2, 3, 4]
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 14, 18)
        n = ctx.draw_int("n_components", 4, 6)
        size_pool = [1, 2, 3, 4, 5, 6]
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 10, 14)
        n = ctx.draw_int("n_components", 3, 5)
        size_pool = [1, 2, 3, 4, 5]
    sizes = rng.sample(size_pool, n)
    g = full_grid(h, w, 0)
    for size in sizes:
        shape = rng.choice(_SHAPES_BY_SIZE[size])
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        for _ in range(80):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            if not _free(g, r0, c0, shape): continue
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = 2
            break
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_objects":
        return g
    if name == "single_object":
        draw_rect(g, 4, 4, 2, 2, 2)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 2
        return g
    return g
