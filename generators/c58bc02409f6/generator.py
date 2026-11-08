"""Generator for arc_puzzle_bank_21_set11_bundle:hard_k18 — hole-count packing.

Rule: each connected component is cropped to its bbox; hole-count is the
number of enclosed-zero regions inside the crop. Sort components by
(hole_count asc, area asc, color asc); pack crops left-to-right with one
blank column between them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: tied_holes, all_solid, single_component.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c58bc02409f6"
VERSION = "1.1.1"
TASK_ID = "c58bc02409f6"

SUMMARY = "3 isolated components with 0, 1, and 2 enclosed holes; output packed left-to-right by ascending hole count."

INVARIANTS = [
    "background is 0",
    "exactly 3 isolated 4-connected components",
    "each component has a distinct enclosed-hole count drawn from {0, 1, 2}",
    "component colors are sampled distinctly from {1..9}",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_holes", "all_solid", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..14", "valid": "10..16"},
    "grid_w":            {"type": "int", "default": "rng 14..18", "valid": "12..20"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "components_with_distinct_holes",
                          "valid": "components_with_distinct_holes"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _solid(rng, color):
    sh, sw = rng.choice([(2, 2), (2, 3), (3, 2)])
    return [(r, c, color) for r in range(sh) for c in range(sw)], sh, sw


def _ring(rng, color):
    sh, sw = rng.choice([(3, 3), (3, 4), (4, 3)])
    cells = []
    for r in range(sh):
        for c in range(sw):
            if r in (0, sh - 1) or c in (0, sw - 1):
                cells.append((r, c, color))
    return cells, sh, sw


def _double_ring(rng, color):
    sh, sw = rng.choice([(3, 5), (3, 6)])
    cells = []
    if sw == 5:
        holes = {(1, 1), (1, 3)}
    else:
        holes = {(1, 1), (1, 4)}
    for r in range(sh):
        for c in range(sw):
            is_perim = (r in (0, sh - 1) or c in (0, sw - 1))
            middle = (r == 1 and 0 < c < sw - 1)
            if is_perim or (middle and (r, c) not in holes):
                cells.append((r, c, color))
    return cells, sh, sw


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 14, 15)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 17, 18)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 14, 18)
    rng = ctx.draw_rng("layout")

    builders = [_solid, _ring, _double_ring]
    rng.shuffle(builders)
    colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)

    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for builder, color in zip(builders, colors):
            cells, sh, sw = builder(rng, color)
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for dr, dc, cc in cells:
                    g[r0 + dr][c0 + dc] = cc
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place 3 isolated components in 40 attempts")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly 3 distinct nonzero colors (components); background is 0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) != 3:
        errors.append(f"expected exactly 3 distinct component colors, found {len(colors)}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 12, 16
    g = full_grid(h, w, 0)
    if name == "tied_holes":
        for c in range(1, 4): g[1][c] = 4; g[3][c] = 4
        g[2][1] = 4; g[2][3] = 4
        for c in range(8, 11): g[1][c] = 6; g[3][c] = 6
        g[2][8] = 6; g[2][10] = 6
        for r, c in [(7, 1), (7, 2), (8, 1), (8, 2)]: g[r][c] = 8
        return g
    if name == "all_solid":
        for r, c in [(2, 1), (2, 2), (3, 1)]: g[r][c] = 4
        for r, c in [(2, 8), (2, 9), (3, 8), (3, 9)]: g[r][c] = 6
        for r, c in [(7, 5), (7, 6), (8, 5)]: g[r][c] = 8
        return g
    if name == "single_component":
        for c in range(2, 5): g[2][c] = 4; g[4][c] = 4
        g[3][2] = 4; g[3][4] = 4
        return g
    return g
