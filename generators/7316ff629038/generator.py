"""Generator for arc_puzzle_bank_21_set24_bundle:hard_p04 — adjacency matrix via dilation overlap.

Rule: connected components sorted top-left. Output N×N: diagonal = component
color, off-diagonal = 8 if their dilated (1-cell halo) cells overlap, else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_components,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, all_isolated, all_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7316ff629038"
VERSION = "1.2.1"
TASK_ID = "7316ff629038"

SUMMARY = "N connected components in distinct colors. Components are sorted by color. Output is N×N binary matrix where cell (i, j) = 1 if center_col(comp_i) < center_col(comp_j), else 0 (diagonal is 0)."

# Rivals: 'output adjacency by row instead of column' refuted by ≥2
# demos where row order doesn't match left-of order. 'output is the
# grid' refuted by any demo (output is small N×N). 'use component
# colors in output' refuted by any demo (output is 0/1 only).
# 'output identity matrix' refuted by ≥1 demo with non-trivial 1s.
# 4 demos with varied component layouts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "3-4 isolated 4-conn components in distinct colors",
    "some components are 1-cell apart (dilation overlap), others are far apart",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "all_isolated", "all_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "10..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_components":   {"type": "int", "default": "rng 3..4", "valid": "2..7"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "mixed_near_far",
                       "valid": "mixed_near_far"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥2 distinct non-zero colors (isolated components)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected ≥2 distinct non-zero colors, got {len(colors)}")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 13)
        n = ctx.draw_int("n_components", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 15, 20)
        n = ctx.draw_int("n_components", 5, 7)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n_components", 3, 5)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n)

    shape_bank = [
        [(0, 0)],
        [(0, 0), (0, 1)],
        [(0, 0), (1, 0)],
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (0, 2)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 1)],
    ]
    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for color in palette:
            shape = rng.choice(shape_bank)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError(f"could not place {n} components")


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_components":
        return g
    if name == "all_isolated":
        g[1][1] = 4; g[1][6] = 5; g[6][1] = 6; g[6][9] = 7
        return g
    if name == "all_overlap":
        g[2][2] = 4; g[2][4] = 5; g[2][6] = 6; g[4][2] = 7
        return g
    return g
