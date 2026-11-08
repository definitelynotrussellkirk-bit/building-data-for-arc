"""Generator for arc_additional_puzzle_bank_volume23:H155.

Rule: control marker (4 = union, 6 = intersection, 8 = XOR) of the
normalized color-2 and color-3 templates; result painted color 9.

v1.1.0 used 2 hardcoded templates → only 3 unique outputs (one per
control value). v1.2.0 draws templates from a 6-shape bank, varies
positions and grid size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "c30d1ebefb1f"
VERSION = "1.3.1"  # distinct 15: a,b from a FIXED _TEMPLATE_PAIRS bank -> few boolean outputs (rule combines color-2 and color-3 shapes by ctrl colour, union/intersection/xor). Now random shapes sharing a core + extras -> varied boolean output.
TASK_ID = "c30d1ebefb1f"
SUMMARY = "Control marker (4/6/8) selects boolean op (union/intersect/XOR) of color-2 and color-3 normalized templates; output painted color 9."

# Rivals: 'always union' refuted by ≥2 demos with different control colors.
# 'use template colors in output' refuted by any demo (always 9).
# 'output unchanged input' refuted by any demo.
# 4 demos with control_color ∈ {4, 6, 8} + varied templates cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly one control marker (one cell of 4, 6, or 8)",
    "one color-2 template + one color-3 template",
    "templates have overlapping shapes (when normalized) so union/intersect/XOR all differ",
    "output is the boolean-op result painted color 9",
]

PALETTE_KINDS = ("default", "control_4", "control_6", "control_8")
DEGENERATE_TEXTURES = ("no_control", "no_template_2", "no_template_3")
HELPFUL_TEXTURES = PALETTE_KINDS

# Template pairs: (template_a, template_b) where union/intersect/XOR
# under normalization all produce distinct shapes.
_TEMPLATE_PAIRS = [
    # original pair
    ([(0, 0), (1, 0), (2, 0), (2, 1)],
     [(0, 0), (0, 1), (1, 1), (2, 1)]),
    # L-tet vs S-tet
    ([(0, 0), (1, 0), (2, 0), (2, 1)],
     [(0, 1), (1, 0), (1, 1), (2, 0)]),
    # L-tromino vs square (overlap at (0,0))
    ([(0, 0), (0, 1), (1, 0)],
     [(0, 0), (0, 1), (1, 0), (1, 1)]),
    # T-tet vs J-tet
    ([(0, 0), (0, 1), (0, 2), (1, 1)],
     [(0, 2), (1, 0), (1, 1), (1, 2)]),
    # Z-tet vs L-tet
    ([(0, 0), (0, 1), (1, 1), (1, 2)],
     [(0, 0), (1, 0), (1, 1), (1, 2)]),
    # Plus vs cross
    ([(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
     [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)]),
]


AXES = {
    "grid_h":         {"type": "int", "default": "by difficulty", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "by difficulty", "valid": "13..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "control_color":  {"type": "int", "default": "rng 4|6|8", "valid": "4|6|8"},
    "template_pair":  {"type": "int", "default": "rng 0..5", "valid": "0..5"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "overlap_kind":   {"type": "str", "default": "partial", "valid": "partial"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _shape_bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return max(rs) - min(rs) + 1, max(cs) - min(cs) + 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 9, 10, 13, 14
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 14, 16, 18, 20
    else:
        h_lo, h_hi, w_lo, w_hi = 11, 13, 15, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    control_color = rng.choice([4, 6, 8])   # 4->union, 6->intersection, 8(neither)->xor
    # Place control marker somewhere away from templates.
    g[rng.randint(h - 4, h - 1)][rng.randint(0, w - 1)] = control_color

    # random shapes sharing a core (so intersection is non-empty) with per-shape
    # extras (so union/xor differ) -> the boolean output varies (was a FIXED bank).
    def _poly(k, s=4):
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nb = (r + dr, c + dc)
            if nb not in seen and 0 <= r + dr < s and 0 <= c + dc < s:
                cells.append(nb); seen.add(nb)
        return cells
    def _grow(base, extra, s=4):
        cells = set(base)
        for _ in range(extra):
            opts = [(r + dr, c + dc) for (r, c) in cells for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    if 0 <= r + dr < s and 0 <= c + dc < s and (r + dr, c + dc) not in cells]
            if opts:
                cells.add(rng.choice(opts))
        return sorted(cells)
    core = _poly(rng.randint(2, 4))
    template_a = _grow(core, rng.randint(1, 3))
    template_b = _grow(core, rng.randint(1, 3))
    ah, aw = _shape_bbox(template_a)
    bh, bw = _shape_bbox(template_b)

    # Place template_a on right side, template_b on left side.
    a_r = rng.randint(1, max(1, h // 2 - ah))
    a_c = rng.randint(w // 2 + 1, max(w // 2 + 1, w - aw - 1))
    b_r = rng.randint(1, max(1, h // 2 - bh))
    b_c = rng.randint(1, max(1, w // 2 - bw - 1))
    paint_at(g, a_r, a_c, template_a, 2)
    paint_at(g, b_r, b_c, template_b, 3)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one control marker in {4,6,8}, one color-2 region, one color-3 region."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    ctrl = sum(grid[r][c] in (4, 6, 8) for r in range(h) for c in range(w))
    if ctrl != 1:
        errors.append(f"expected exactly 1 control marker (4/6/8), found {ctrl}")
    twos = sum(grid[r][c] == 2 for r in range(h) for c in range(w))
    if twos < 1:
        errors.append("no color-2 template cells found")
    threes = sum(grid[r][c] == 3 for r in range(h) for c in range(w))
    if threes < 1:
        errors.append("no color-3 template cells found")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 11, 15
    g = full_grid(h, w, 0)
    a = _TEMPLATE_PAIRS[0][0]
    b = _TEMPLATE_PAIRS[0][1]
    if name == "no_control":
        paint_at(g, 2, w - 5, a, 2)
        paint_at(g, 1, 1, b, 3)
        return g
    if name == "no_template_2":
        g[h - 3][w - 2] = 6
        paint_at(g, 1, 1, b, 3)
        return g
    if name == "no_template_3":
        g[h - 3][w - 2] = 4
        paint_at(g, 2, w - 5, a, 2)
        return g
    return g
