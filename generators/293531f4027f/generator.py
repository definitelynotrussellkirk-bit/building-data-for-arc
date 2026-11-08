"""Generator for 5b:m34 — component count columns.

Rule: for each non-bg color, count components. Output is a column-bar
chart: column 0 = color A's count, column 2 = color B's count, etc.
(1-cell gaps between columns); cells stacked from the bottom up.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, single_color, all_counts_equal.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "293531f4027f"
VERSION = "1.1.1"
TASK_ID = "293531f4027f"
SUMMARY = "2-3 colors with multiple isolated components each (varying counts)."

INVARIANTS = [
    "background is 0",
    "2-3 distinct non-bg colors are present",
    "each color contributes 1-3 isolated 4-conn components, with counts not all equal to 1",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "single_color", "all_counts_equal")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "scattered_components_by_color",
                       "valid": "scattered_components_by_color"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 distinct non-zero colors present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_components", "single_color", "all_counts_equal"):
        return []
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"only {len(colors)} distinct non-zero color(s); expected ≥2")
    return errs


_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0)],
    [(0, 0), (1, 0)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 14, 17)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 14)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_colors = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_colors)
    counts = rng.sample([1, 2, 3], n_colors)
    for color, count in zip(palette, counts):
        for _ in range(count):
            _place(g, rng, rng.choice(_SHAPES), color)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_components":
        # Empty grid — rule's bar chart is trivially all-zero.
        return g
    if name == "single_color":
        # Only one color — rule's per-color chart has a single
        # bar; rule's "1-cell gap between columns" never applies.
        for r, c in [(2, 2), (2, 3)]: g[r][c] = 4
        for r, c in [(5, 7), (5, 8)]: g[r][c] = 4
        for r, c in [(8, 4), (8, 5)]: g[r][c] = 4
        return g
    if name == "all_counts_equal":
        # Both colors have the same component count — rule's
        # output bar chart has equal bars; effect uniform.
        for r, c in [(2, 2)]: g[r][c] = 4
        for r, c in [(5, 8)]: g[r][c] = 6
        return g
    return g
