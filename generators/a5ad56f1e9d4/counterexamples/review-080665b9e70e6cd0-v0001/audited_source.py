"""Generator for arc_puzzle_bank_twentysecond21:M154 — recolor 5-shape cells to nearest marker.

Rule: a 5-color solid rectangle (2-3×2-3) sits with two single-cell
markers (distinct colors) outside it. Each 5-cell is recolored to
whichever marker is closer by Manhattan distance (ties use the canonical
color/position precedence).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_rectangle, no_markers, equidistant_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, fill_box
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "a5ad56f1e9d4"
VERSION = "1.1.2"  # keep marker cells 4-disjoint from the 5-rectangle and verify exact geometry
TASK_ID = "a5ad56f1e9d4"
SUMMARY = "5-color solid rectangle (2-3×2-3) + two distinct-color markers outside it."

INVARIANTS = [
    "background is 0",
    "exactly one solid rectangle in color 5 (size 2×3 to 3×3)",
    "exactly two single-cell markers in distinct non-0/non-5 colors outside the rectangle",
    "markers don't touch the rectangle or each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rectangle", "no_markers", "equidistant_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "5..10"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "rect_center_two_markers_outside",
                       "valid": "rect_center_two_markers_outside"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one solid color-5 rectangle and two disjoint single-cell markers
    outside it.  The markers must have a one-cell 4-neighbor gap from the
    rectangle so the intended "outside markers recolor the rectangle" reading is
    not blurred by attached marker cells."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    five_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not five_cells:
        return ["no color-5 rectangle cells found"]
    r1 = min(r for r, _ in five_cells); r2 = max(r for r, _ in five_cells)
    c1 = min(c for _, c in five_cells); c2 = max(c for _, c in five_cells)
    rh, rw = r2 - r1 + 1, c2 - c1 + 1
    if not (2 <= rh <= 3 and 2 <= rw <= 3):
        errs.append(f"color-5 rectangle dims must be 2..3 by 2..3, got {rh}x{rw}")
    rect = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
    if set(five_cells) != rect:
        errs.append("color-5 cells are not one solid filled rectangle")
    markers = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
               if grid[r][c] not in (0, 5)]
    if len(markers) != 2:
        errs.append(f"expected exactly two marker cells, found {len(markers)}")
        return errs
    if len({v for _, _, v in markers}) != 2:
        errs.append("marker colors must be distinct")
    marker_pos = [(r, c) for r, c, _ in markers]
    if any((r, c) in rect for r, c in marker_pos):
        errs.append("marker cell lies inside the color-5 rectangle")
    if abs(marker_pos[0][0] - marker_pos[1][0]) + abs(marker_pos[0][1] - marker_pos[1][1]) <= 1:
        errs.append("markers touch each other")
    if any(abs(r - fr) + abs(c - fc) == 1 for r, c in marker_pos for fr, fc in rect):
        errs.append("marker touches the color-5 rectangle; expected a one-cell gap")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 11)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 6, 8)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rh = rng.randint(2, 3)
    rw = rng.randint(2, 3)
    # Place the rectangle with room for a one-cell gap above the first marker
    # and to the right of the second marker.  The previous bounds sometimes put
    # markers directly 4-adjacent to the rectangle, violating the documented
    # outside-marker invariant.
    r1 = rng.randint(2, h - rh)
    c1 = rng.randint(1, w - rw - 2)
    r2 = r1 + rh - 1
    c2 = c1 + rw - 1
    fill_box(g, r1, c1, r2, c2, 5)
    palette = list(random_palette(rng, 2, exclude={5}))
    m1_r = rng.randint(0, r1 - 2)
    m1_c = rng.randint(c1, c2)
    g[m1_r][m1_c] = palette[0]
    m2_r = rng.randint(r1, r2)
    m2_c = rng.randint(c2 + 2, w - 1)
    g[m2_r][m2_c] = palette[1]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 7
    g = full_grid(h, w, 0)
    if name == "no_rectangle":
        # Two markers but no 5-rectangle — rule has no cells to recolor.
        g[0][3] = 3; g[3][6] = 7
        return g
    if name == "no_markers":
        # 5-rectangle but no markers — rule has nothing to assign each
        # 5-cell to.
        fill_box(g, 2, 2, 3, 4, 5)
        return g
    if name == "equidistant_markers":
        # Both markers exactly equidistant from every 5-cell — ties are
        # everywhere, no strictly-nearest marker exists.
        fill_box(g, 2, 2, 3, 4, 5)
        g[0][3] = 3
        g[5][3] = 7
        return g
    return g
