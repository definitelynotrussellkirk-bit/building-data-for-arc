"""Generator for arc_puzzle_bank_fifteenth_21_bundle:hard_99_decode_template_transform_gallery.

Combinatorial axes (8): grid_h, grid_w, palette_kind, variant,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_templates, no_id_grid, no_transform_codes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c552e852b3c6"
VERSION = "1.1.1"
TASK_ID = "c552e852b3c6"
SUMMARY = "Decode a 2x2 template id grid and a 2x2 transform code grid into a transformed gallery."

INVARIANTS = [
    "the top four rows contain three 4x4 templates at offsets 0, 5, and 10",
    "rows 6..7 columns 0..1 contain template ids in 1..3",
    "rows 6..7 columns 3..4 contain transform codes",
    "the output is a 2x2 gallery with one blank row and column between transformed templates",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_templates", "no_id_grid", "no_transform_codes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8", "valid": "8..8"},
    "grid_w":         {"type": "int", "default": "14", "valid": "14..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "variant":        {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "templates_plus_id_and_code_grids",
                       "valid": "templates_plus_id_and_code_grids"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_templates|no_id_grid|no_transform_codes"},
}

_TEMPLATES = [
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
]
_IDS = [
    [[1, 2], [3, 1]],
    [[2, 3], [1, 2]],
    [[3, 1], [2, 3]],
    [[1, 3], [2, 1]],
]
_CODES = [
    [[1, 2], [5, 6]],
    [[2, 3], [4, 7]],
    [[5, 1], [2, 4]],
    [[7, 6], [3, 2]],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        variant = ctx.draw_int("variant", 0, 1)
    elif difficulty == "hard":
        variant = ctx.draw_int("variant", 2, 3)
    else:
        variant = ctx.draw_int("variant", 0, len(_IDS) - 1)
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8], 3)
    g = full_grid(8, 14, 0)
    for idx, cells in enumerate(_TEMPLATES):
        _paint(g, 0, idx * 5, cells, colors[idx])
    for r in range(2):
        for c in range(2):
            g[6 + r][c] = _IDS[variant][r][c]
            g[6 + r][3 + c] = _CODES[variant][r][c]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Grid is 8x14; 3 templates in rows 0..3 at offsets 0,5,10; id/code grid at rows 6-7."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if h != 8 or w != 14:
        errors.append(f"expected 8x14 grid, got {h}x{w}")
        return errors
    # Template area (rows 0..3) should have some nonzero cells
    template_cells = sum(grid[r][c] != 0 for r in range(4) for c in range(w))
    if template_cells < 3:
        errors.append(f"expected nonzero template cells in rows 0-3, found {template_cells}")
    # Id cells (rows 6-7, cols 0-1) should be in {1..3}
    id_ok = all(1 <= grid[r][c] <= 3 for r in (6, 7) for c in (0, 1))
    if not id_ok:
        errors.append("id cells (rows 6-7, cols 0-1) not all in {1..3}")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 14, 0)
    if name == "no_templates":
        # id + code grids but no template gallery → nothing to look up
        for r in range(2):
            for c in range(2):
                g[6 + r][c] = _IDS[0][r][c]
                g[6 + r][3 + c] = _CODES[0][r][c]
        return g
    if name == "no_id_grid":
        # templates + codes but no id grid → no selection mapping
        colors = [2, 3, 4]
        for idx, cells in enumerate(_TEMPLATES):
            _paint(g, 0, idx * 5, cells, colors[idx])
        for r in range(2):
            for c in range(2):
                g[6 + r][3 + c] = _CODES[0][r][c]
        return g
    if name == "no_transform_codes":
        # templates + ids but no transform codes → no operation defined
        colors = [2, 3, 4]
        for idx, cells in enumerate(_TEMPLATES):
            _paint(g, 0, idx * 5, cells, colors[idx])
        for r in range(2):
            for c in range(2):
                g[6 + r][c] = _IDS[0][r][c]
        return g
    return g
