"""Generator for arc_additional_puzzles_21_set19_bundle:H131 — pack crops by hole count.

Rule: each connected component is cropped to its bbox; hole-count =
enclosed-zero-region count inside the crop. Sort components by
(hole_count desc, area desc, color asc); pack crops left-to-right with
one blank column between them. Output dim = max(rows) × sum(cols)+gaps.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_components (no shapes → output empty); single_component
(only 1 → trivial pack, no contrast); all_solid (every component has
0 holes → primary key collapses, only secondary keys remain).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b20d975c39c8"
VERSION = "2.0.1"
TASK_ID = "b20d975c39c8"

SUMMARY = (
    "0-bg grid (h~11-13, w~"
    "13-16) with 3 ISOLATED "
    "4-CONNECTED COMPONENTS"
    " in distinct colors "
    "from {1..9}, each with "
    "a DISTINCT ENCLOSED-"
    "HOLE COUNT: (a) "
    "SOLID BLOCK — 2×2 / "
    "2×3 / 3×2 with 0 "
    "holes; (b) HOLLOW "
    "RING — 3×3 / 3×4 / "
    "4×3 outline with 1 "
    "enclosed hole; (c) "
    "DOUBLE-HOLED RING — "
    "3×5 / 3×6 / 5×3 with "
    "an extra divider line "
    "creating 2 enclosed "
    "holes. Components are "
    "placed at non-touching "
    "positions. Rule "
    "(SORT COMPONENTS BY "
    "(HOLE-COUNT DESC, "
    "AREA DESC, COLOR "
    "ASC), PACK BBOX CROPS "
    "HORIZONTALLY): for "
    "each 4-CONNECTED "
    "COMPONENT: crop to "
    "BBOX, compute "
    "HOLE-COUNT (# enclosed "
    "zero regions inside "
    "the crop). SORT by "
    "(hole_count DESC, "
    "area DESC, color ASC)"
    ". PACK the crops "
    "LEFT-TO-RIGHT with "
    "1-column BLANK GAP "
    "between adjacent "
    "crops. Output "
    "dimensions = max(crop "
    "rows) × (sum(crop "
    "cols) + gaps). Net: "
    "components stacked "
    "left-to-right by "
    "complexity (holes "
    "first, then area)."
)

INVARIANTS = [
    "background is 0",
    "exactly 3 isolated 4-connected components",
    "each component has a distinct enclosed-hole count (drawn from 0, 1, 2)",
    "components are colored from {1..9} \\ {0} with distinct colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "single_component", "all_solid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "grid_w":            {"type": "int", "default": "rng 13..16", "valid": "12..20"},
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 3 distinct non-bg colors (the 3 components)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) != 3:
        errs.append(f"expected exactly 3 distinct non-bg component colors; found {sorted(colors)}")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _solid_block(rng, color):
    shape = rng.choice([(2, 2), (2, 3), (3, 2)])
    sh, sw = shape
    cells = [(r, c, color) for r in range(sh) for c in range(sw)]
    return cells, sh, sw


def _ring(rng, color):
    shape = rng.choice([(3, 3), (3, 4), (4, 3)])
    sh, sw = shape
    cells = []
    for r in range(sh):
        for c in range(sw):
            if r == 0 or r == sh - 1 or c == 0 or c == sw - 1:
                cells.append((r, c, color))
    return cells, sh, sw


def _double_ring(rng, color):
    shape = rng.choice([(3, 5), (3, 6), (5, 3)])
    sh, sw = shape
    cells = []
    if sh == 3:
        if sw == 5:
            holes = [(1, 1), (1, 3)]
        else:
            holes = [(1, 1), (1, 4)]
        for r in range(sh):
            for c in range(sw):
                is_perimeter = (r == 0 or r == sh - 1 or c == 0 or c == sw - 1)
                middle = (r == 1 and 0 < c < sw - 1)
                if is_perimeter:
                    cells.append((r, c, color))
                elif middle and (r, c) not in holes:
                    cells.append((r, c, color))
    else:
        if sh == 5:
            holes = [(1, 1), (3, 1)]
        for r in range(sh):
            for c in range(sw):
                is_perimeter = (r == 0 or r == sh - 1 or c == 0 or c == sw - 1)
                middle = (c == 1 and 0 < r < sh - 1)
                if is_perimeter:
                    cells.append((r, c, color))
                elif middle and (r, c) not in holes:
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
        w = ctx.draw_int("grid_w", 13, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 15, 16)
    else:
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 16)
    rng = ctx.draw_rng("layout")

    builders = [_solid_block, _ring, _double_ring]
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


def _draw_from_degenerate(name, rng):
    h, w = 12, 15
    g = full_grid(h, w, 0)
    if name == "no_components":
        return g
    if name == "single_component":
        for r in range(3):
            for c in range(3):
                if r in (0, 2) or c in (0, 2):
                    g[3 + r][5 + c] = 4
        return g
    if name == "all_solid":
        for r in range(2):
            for c in range(2):
                g[1 + r][1 + c] = 1
        for r in range(2):
            for c in range(3):
                g[1 + r][6 + c] = 2
        for r in range(3):
            for c in range(2):
                g[5 + r][2 + c] = 3
        return g
    return g
