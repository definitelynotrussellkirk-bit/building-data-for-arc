"""Generator for arc_puzzle_bank_twentysecond21:M151.

The left panel is a binary stencil over the right panel. The rule keeps right
panel colors only under nonzero stencil cells and crops the result.

Combinatorial axes (8): panel_h, panel_w, palette_kind, mask_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_mask, no_right_content, mask_misses_content.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7d12467b91a3"
VERSION = "2.0.1"
TASK_ID = "7d12467b91a3"
SUMMARY = (
    "0-bg grid (h~5-7, w = 2*panel_w + 1 with "
    "panel_w~5-7) with TWO EQUAL-SIZE PANELS "
    "separated by ONE FULL-HEIGHT COLOR-8 "
    "(cyan) DIVIDER column. LEFT PANEL (cols "
    "0..panel_w-1) contains a BINARY MASK — "
    "5-10 cells painted in COLOR 1 (blue), the "
    "rest 0 (the mask pattern). RIGHT PANEL "
    "(cols panel_w+1..2*panel_w) contains "
    "COLOR PAYLOAD — some cells painted in "
    "various non-{0, 1, 8} colors; some "
    "payload cells overlap mask positions, "
    "some don't. Rule: use the LEFT PANEL as a "
    "BINARY STENCIL. For each cell at "
    "(r, c) in the right panel, KEEP its color "
    "if the corresponding LEFT-PANEL cell at "
    "(r, c) is NON-ZERO (color 1, in mask); "
    "otherwise CLEAR it to 0. After masking, "
    "CROP the result to its non-zero content "
    "bbox. Output: the cropped masked right "
    "panel. Net: left mask selects which "
    "right-panel colors to keep; output is "
    "cropped, masked payload."
)

INVARIANTS = [
    "two equal-size panels are separated by one full color-8 column",
    "the left panel is a nonzero binary mask",
    "at least one right-panel colored cell is selected by the mask",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_mask", "no_right_content", "mask_misses_content")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 5..7", "valid": "3..10"},
    "panel_w":        {"type": "int", "default": "rng 5..7", "valid": "3..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "mask_count":     {"type": "int", "default": "rng 5..10", "valid": "3..15"},
    "palette_size":   {"type": "int", "default": "rng 5..7", "valid": "3..8"},
    "position_bias":  {"type": "str", "default": "left_mask_right_payload",
                       "valid": "left_mask_right_payload"},
    "n_distinct_colors": {"type": "int", "default": "rng 5..7", "valid": "3..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 full-height color-8 (cyan) divider column; ≥1 color-1 cell in left panel."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    dividers = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if not dividers:
        return ["expected ≥1 full-height color-8 divider column; found none"]
    left_end = min(dividers)
    has_mask = any(grid[r][c] == 1 for r in range(h) for c in range(left_end))
    if not has_mask:
        return ["expected ≥1 color-1 mask cell in left panel; found none"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("panel_h", 5, 5)
        w = ctx.draw_int("panel_w", 5, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("panel_h", 6, 7)
        w = ctx.draw_int("panel_w", 6, 7)
    else:
        h = ctx.draw_int("panel_h", 5, 7)
        w = ctx.draw_int("panel_w", 5, 7)
    g = full_grid(h, w * 2 + 1, 0)
    for r in range(h):
        g[r][w] = 8
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    mask_cells = cells[:rng.randint(5, min(10, len(cells)))]
    selected = mask_cells[:rng.randint(2, min(5, len(mask_cells)))]
    for r, c in mask_cells:
        g[r][c] = 1
    palette = [2, 3, 4, 5, 6, 7, 9]
    for i, (r, c) in enumerate(selected):
        g[r][w + 1 + c] = palette[i % len(palette)]
    for r, c in cells[len(mask_cells):len(mask_cells) + 5]:
        g[r][w + 1 + c] = rng.choice(palette)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 5
    g = full_grid(h, w * 2 + 1, 0)
    for r in range(h):
        g[r][w] = 8
    if name == "no_mask":
        # right-panel colors with no left-panel mask → nothing selected
        g[0][w + 1] = 4; g[1][w + 2] = 6
        g[3][w + 3] = 7
        return g
    if name == "no_right_content":
        # left-panel mask with empty right panel → nothing to keep
        g[0][0] = 1; g[1][1] = 1; g[2][2] = 1
        return g
    if name == "mask_misses_content":
        # mask cells and right-panel cells don't overlap → empty selection
        g[0][0] = 1; g[1][1] = 1
        g[3][w + 3] = 4; g[4][w + 4] = 6
        return g
    return g
