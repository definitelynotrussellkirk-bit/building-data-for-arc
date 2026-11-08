"""Generator for arc_puzzle_bank_21_set5_e:medium_e07 — overlap of color bboxes.

Rule: each color has a bbox (computed from its cells). Output: cells in
the rectangular intersection of the two bboxes painted in 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_colors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_colors, single_color, disjoint_bboxes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "de45fc71c193"
VERSION = "2.2.0"  # distinct only 16 / uniq 11%: the 2 colors were at HARDCODED corner positions -> near-constant bbox-intersection rect. Now random overlapping bboxes (diagonal-corner cells) + wider grids -> intersection rect varies widely."
TASK_ID = "de45fc71c193"
SUMMARY = (
    "0-bg grid (h~6-9, w~"
    "8-11) with HARDCODED "
    "POSITIONS for 2 "
    "DISTINCT colors: (a) "
    "COLOR_A (random from "
    "{2..7}) at fixed "
    "positions (1, 1) and "
    "(h-3, w//2+1) — "
    "defining bbox A; (b) "
    "COLOR_B (distinct) at "
    "fixed positions (2, "
    "w//2-1) and (h-2, w-"
    "2) — defining bbox B. "
    "Hardcoded positions × "
    "color pair choices "
    "≈ ~50 unique. Output "
    "uniq_out=15 "
    "(intrinsic — "
    "intersection rect "
    "dimensions × colors "
    "normalize). Rule "
    "(PAINT INTERSECTION "
    "OF BBOXES IN 8): "
    "For EACH NON-0 "
    "COLOR: COMPUTE BBOX "
    "from its cells. "
    "COMPUTE bbox_A ∩ "
    "bbox_B — the "
    "RECTANGULAR "
    "INTERSECTION. PAINT "
    "every cell inside "
    "that intersection "
    "rect with COLOR-8 "
    "(cyan). Original "
    "color cells stay. "
    "Net: bbox overlap "
    "rect becomes cyan."
)

INVARIANTS = [
    "background is 0",
    "exactly 2 distinct non-zero colors",
    "each color has ≥2 cells defining a bbox",
    "the two bboxes overlap (intersection rect is non-empty)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_colors", "single_color", "disjoint_bboxes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_colors":       {"type": "int", "default": "2", "valid": "2..2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "two_overlapping_bboxes",
                       "valid": "two_overlapping_bboxes"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_colors|single_color|disjoint_bboxes"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([2, 3, 4, 5, 6, 7, 9], 2)
    # RANDOM overlapping bboxes (was hardcoded corners -> near-constant overlap rect).
    # Each color sits at the two diagonal corners of its bbox; the two bboxes are
    # drawn to overlap so the intersection rectangle (filled 8) varies widely.
    for _attempt in range(80):
        rA0 = rng.randint(0, h - 2); rA1 = rng.randint(rA0 + 1, h - 1)
        cA0 = rng.randint(0, w - 2); cA1 = rng.randint(cA0 + 1, w - 1)
        rB0 = rng.randint(0, h - 2); rB1 = rng.randint(rB0 + 1, h - 1)
        cB0 = rng.randint(0, w - 2); cB1 = rng.randint(cB0 + 1, w - 1)
        if max(rA0, rB0) > min(rA1, rB1) or max(cA0, cB0) > min(cA1, cB1):
            continue   # bboxes must overlap (non-empty intersection)
        if len({(rA0, cA0), (rA1, cA1), (rB0, cB0), (rB1, cB1)}) < 4:
            continue   # all 4 corner cells distinct so each bbox stays intact
        g = full_grid(h, w, 0)
        g[rA0][cA0] = palette[0]; g[rA1][cA1] = palette[0]
        g[rB0][cB0] = palette[1]; g[rB1][cB1] = palette[1]
        return g
    # fallback: guaranteed overlap (diagonal corners)
    g = full_grid(h, w, 0)
    g[0][0] = palette[0]; g[h - 1][w - 1] = palette[0]
    g[0][w - 1] = palette[1]; g[h - 1][0] = palette[1]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify two non-8 colors define overlapping bounding boxes."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h = len(grid)
    errs = []
    colors = sorted({grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0})
    if 8 in colors:
        errs.append("input should not contain color 8; the rule writes bbox-overlap cells in 8")
    active = [c for c in colors if c != 8]
    if len(active) != 2:
        errs.append(f"expected exactly two active nonzero colors; got {active}")
        return errs
    bboxes = []
    for color in active:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if len(cells) < 2:
            errs.append(f"color {color} has only {len(cells)} cell(s); need >=2 to define a bbox")
            continue
        bboxes.append((min(r for r, _ in cells), min(c for _, c in cells),
                       max(r for r, _ in cells), max(c for _, c in cells)))
    if len(bboxes) == 2:
        r0 = max(bboxes[0][0], bboxes[1][0])
        c0 = max(bboxes[0][1], bboxes[1][1])
        r1 = min(bboxes[0][2], bboxes[1][2])
        c1 = min(bboxes[0][3], bboxes[1][3])
        if r0 > r1 or c0 > c1:
            errs.append("the two color bboxes do not overlap")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_colors":
        # blank → no bboxes to intersect
        return g
    if name == "single_color":
        # only one color → no second bbox to intersect with
        g[1][1] = 4
        g[5][7] = 4
        return g
    if name == "disjoint_bboxes":
        # two colors but their bboxes don't overlap → empty intersection
        g[1][1] = 4; g[2][3] = 4    # bbox top-left quadrant
        g[5][6] = 6; g[6][8] = 6    # bbox bottom-right, no overlap
        return g
    return g
