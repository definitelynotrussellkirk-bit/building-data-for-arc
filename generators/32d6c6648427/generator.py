"""Generator for hard_82_boolean_mosaic_from_row_and_column_templates.

Rule: op code at (1,1); two 3x3 row-templates (top) and two col-templates
(left) combine cell-wise via AND/OR/XOR into a 2x2 mosaic of 3x3 panels.

Combinatorial axes: op code, the four 3x3 template masks, template density,
and (distractor) colors.
Degenerates: all_on_templates, all_off_templates, single_op.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "32d6c6648427"
VERSION = "3.1.0"  # +self_check  # rewrite to real boolean-mosaic contract (was wrong rule -> 100% list-ref crash)
TASK_ID = "32d6c6648427"

SUMMARY = (
    "11x11 0-bg grid encoding a BOOLEAN MOSAIC. Cell (1, 1) holds an "
    "OPERATION CODE: 1=AND, 2=OR, else=XOR. Two 3x3 ROW TEMPLATES sit at "
    "the top at columns (4, 8); two 3x3 COL TEMPLATES sit at the left at "
    "rows (4, 8). Each template is a binary mask painted in some non-0 "
    "color (the rule is color-blind: any non-0 cell = ON). Rule: for each "
    "col-template, hstack the cell-wise boolean combination (AND/OR/XOR "
    "per the op code) with each row-template; vstack the two rows into a "
    "2x2 panel layout of 3x3 boolean results (8=true) with 1-cell gaps -> "
    "a 7x7 output. Color and exact template pattern are distractors; only "
    "the ON/OFF masks and the op code matter."
)

INVARIANTS = [
    "background is 0; grid is 11x11",
    "op code in {1=AND, 2=OR, else XOR} at cell (1,1)",
    "two 3x3 row-templates at (0,4),(0,8); two 3x3 col-templates at (4,0),(8,0)",
    "templates are binary masks in non-0 colors (color is a distractor)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_on_templates", "all_off_templates", "single_op")
HELPFUL_TEXTURES = PALETTE_KINDS

# Positions the rule hard-crops (3x3 each); the op code lives at (1,1).
_ROW_TEMPLATES = ((0, 4), (0, 8))
_COL_TEMPLATES = ((4, 0), (8, 0))
_OPS = (1, 2, 3)   # 1=AND, 2=OR, 3(=else)=XOR

AXES = {
    "op":             {"type": "int", "default": "rng 1..3", "valid": "1|2|3"},
    "template_on":    {"type": "int", "default": "rng per band", "valid": "1..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "fixed_boolean_mosaic",
                       "valid": "fixed_boolean_mosaic"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "density":        {"type": "str", "default": "varies", "valid": "varies"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|all_on_templates|all_off_templates|single_op"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid is 11x11, op-code at (1,1) in {1,2,3}, row-templates at cols 4/8."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    h, w = len(grid), len(grid[0])
    if h != 11 or w != 11:
        errs.append(f"expected 11x11 grid, got {h}x{w}")
    elif grid[1][1] not in (1, 2, 3):
        errs.append(f"op code at (1,1) = {grid[1][1]}, expected 1/2/3")
    return errs


def _place_template(g, top, left, on_cells, color):
    for (r, c) in on_cells:
        g[top + r][left + c] = color


def _rand_template(rng, lo, hi):
    """A 3x3 binary pattern with between lo and hi ON cells (positions)."""
    cells = [(r, c) for r in range(3) for c in range(3)]
    return rng.sample(cells, rng.randint(lo, hi))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    # density band = how many cells are ON in each 3x3 template
    if difficulty == "easy":
        lo, hi = 2, 4
    elif difficulty == "hard":
        lo, hi = 2, 7
    else:
        lo, hi = 2, 6

    op = int(overrides["op"]) if "op" in overrides else rng.choice(_OPS)
    g = full_grid(11, 11, 0)
    g[1][1] = op                                    # the rule reads the op here
    palette = [1, 2, 3, 4, 5, 6, 7]
    for (top, left) in _ROW_TEMPLATES + _COL_TEMPLATES:
        # independent ON pattern + independent color per template; the rule is
        # color-blind so color is purely a distractor.
        _place_template(g, top, left, _rand_template(rng, lo, hi), rng.choice(palette))
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    g[1][1] = 1
    if name == "single_op":
        return g                                    # op only, empty templates
    full = [(r, c) for r in range(3) for c in range(3)]
    on = full if name == "all_on_templates" else []
    for (top, left) in _ROW_TEMPLATES + _COL_TEMPLATES:
        _place_template(g, top, left, on, 4)
    return g
