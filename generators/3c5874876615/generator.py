"""Generator for 19b:hard_133 — compose two transforms and center-stamp.

Rule: prototype = top 5 rows cropped to non-bg bbox. Row 5 holds
t1 at (5,0), t2 at (5,1), output_color at (5,2). Apply t1 then t2,
recolor, center-stamp into a 7x7 canvas.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_proto_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_prototype, no_controls, missing_out_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3c5874876615"
VERSION = "2.0.1"  # shape-locked-in (fixed 6x9): the rule reads cols dynamically (subgrid g 0 0 4 (cols-1) + control at row5 cols0..2), so WIDTH is free. Now grid width varies 5..12 (height stays 6: rows0..4 proto + row5 control; output is the rule's hardcoded 7x7 center-stamp -> genuinely intrinsic, out-lock kept).
TASK_ID = "3c5874876615"

SUMMARY = "Top 5 rows: prototype shape; row 5 has 3 control values: t1, t2, out_color."

INVARIANTS = [
    "background is 0",
    "grid is 6 rows tall (rows 0..4 prototype, row 5 control); width varies 5..12",
    "rows 0..4 hold a prototype shape (single color, 4-7 cells, fits in a 5x7 area so it survives the 7x7 center-stamp)",
    "row 5: cells (5,0), (5,1), (5,2) hold t1, t2 (transform codes 1-5), output color",
    "all other cells in row 5 are bg",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_prototype", "no_controls", "missing_out_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6", "valid": "6..6"},
    "grid_w":         {"type": "int", "default": "rng 6..10", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_proto_cells":  {"type": "int", "default": "rng 4..7", "valid": "4..7"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "prototype_with_controls",
                       "valid": "prototype_with_controls"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 6 rows, row 5 has controls at (5,0),(5,1) in 1..5 and (5,2) non-zero."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    if h != 6:
        errs.append(f"expected 6 rows, got {h}")
        return errs
    if w < 3:
        errs.append(f"width too small: {w}")
        return errs
    t1, t2, out_color = grid[5][0], grid[5][1], grid[5][2]
    if not (1 <= t1 <= 5):
        errs.append(f"control t1={t1} not in 1..5")
    if not (1 <= t2 <= 5):
        errs.append(f"control t2={t2} not in 1..5")
    if out_color == 0:
        errs.append("output color at (5,2) is 0")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    h = 6
    # width is the free axis (rule reads cols dynamically); height stays 6.
    if difficulty == "easy":
        w = ctx.draw_int("grid_w", 5, 7); n = rng.randint(4, 5)
    elif difficulty == "hard":
        w = ctx.draw_int("grid_w", 9, 12); n = rng.randint(6, 7)
    else:
        w = ctx.draw_int("grid_w", 6, 10); n = rng.randint(4, 7)
    g = full_grid(h, w, 0)
    proto_color = rng.choice([1, 2, 3, 5, 6, 7, 8, 9])
    out_color = rng.choice([c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c != proto_color])
    # keep the prototype within a 5x7 region (cols 0..min(w,7)-1) so it survives
    # the rule's 7x7 center-stamp under any t1/t2 rotation.
    pw = min(w, 7)
    cells = [(r, c) for r in range(5) for c in range(pw)]
    for r, c in rng.sample(cells, min(n, len(cells))):
        g[r][c] = proto_color
    g[5][0] = rng.randint(1, 5)
    g[5][1] = rng.randint(1, 5)
    g[5][2] = out_color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "no_prototype":
        # control row populated but rows 0..4 are blank → no shape to transform
        g[5][0] = 2; g[5][1] = 4; g[5][2] = 6
        return g
    if name == "no_controls":
        # prototype present but row 5 is empty → no transforms or output color
        g[1][1] = 4; g[1][2] = 4; g[2][1] = 4; g[2][2] = 4
        return g
    if name == "missing_out_color":
        # t1 + t2 set but (5,2) is bg → no recolor color defined
        g[1][1] = 4; g[1][2] = 4; g[2][1] = 4; g[2][2] = 4
        g[5][0] = 2; g[5][1] = 3
        return g
    return g
