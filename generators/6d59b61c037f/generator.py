"""Generator for arc_puzzle_bank_twentyfirst21:H145.

Infer union/intersection/xor from an example and apply it to query.

Combinatorial axes (8): grid_h, grid_w, palette_kind, operation,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, no_demo, no_query.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6d59b61c037f"
VERSION = "2.1.0"  # demo/query masks now disambiguate union/intersection/xor and avoid empty query outputs  # distinct=12/dup-inputs33%: example panels (EA,EB) and query panels (QA,QB) were FIXED, so output = op(QA,QB) varied only with the op. Randomize all four 3x3 panels -> op(QA,QB) output varies widely. Output 3x3 is rule-intrinsic.
TASK_ID = "6d59b61c037f"
SUMMARY = "Infer union/intersection/xor from an example and apply it to query."

INVARIANTS = [
    "the input has five 3x3 panels separated by full color-8 columns",
    "panels 1 and 2 plus panel 3 demonstrate one binary support operation",
    "panels 4 and 5 are query supports with a shared query color",
    "the output support is painted with the first nonzero query color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "no_demo", "no_query")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "3", "valid": "3..3"},
    "grid_w":         {"type": "int", "default": "19", "valid": "19..19"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "operation":      {"type": "enum", "default": "rng",
                       "valid": "union|intersection|xor"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "5_panels_8col_separated",
                       "valid": "5_panels_8col_separated"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_OPS = ["union", "intersection", "xor"]
_EA = {(0, 0), (1, 0), (1, 1)}
_EB = {(0, 1), (1, 0), (2, 2)}
_QA = {(0, 0), (0, 2), (1, 1)}
_QB = {(0, 2), (1, 0), (1, 1)}


def _apply_op(a, b, op):
    if op == "union":
        return a | b
    if op == "intersection":
        return a & b
    return (a | b) - (a & b)


def _op_outputs_distinct(a, b):
    outs = [_apply_op(a, b, op) for op in _OPS]
    return all(outs) and len({tuple(sorted(o)) for o in outs}) == len(_OPS)


def _rand_discriminating_pair(rng):
    spots = [(r, c) for r in range(3) for c in range(3)]
    for _ in range(200):
        a = set(rng.sample(spots, rng.randint(3, 6)))
        b = set(rng.sample(spots, rng.randint(3, 6)))
        if _op_outputs_distinct(a, b):
            return a, b
    # Fallback with overlap and private cells in both operands.
    return {(0, 0), (0, 1), (1, 0), (2, 2)}, {(0, 1), (1, 0), (1, 1), (2, 0)}


def _paint_panel(g, panel, cells, color):
    left = panel * 4
    for r, c in cells:
        g[r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        op = ctx.draw_choice("operation", ["union", "intersection"])
    elif difficulty == "hard":
        op = ctx.draw_choice("operation", _OPS)
    else:
        op = ctx.draw_choice("operation", _OPS)
    ex_color = rng.choice([1, 2, 3, 4])
    query_color = rng.choice([5, 6, 7, 9])

    ea, eb = _rand_discriminating_pair(rng)
    qa, qb = _rand_discriminating_pair(rng)
    g = full_grid(3, 19, 0)
    for sep in (3, 7, 11, 15):
        for r in range(3):
            g[r][sep] = 8
    panels = [ea, eb, _apply_op(ea, eb, op), qa, qb]
    colors = [ex_color, ex_color, ex_color, query_color, query_color]
    for idx, (cells, color) in enumerate(zip(panels, colors)):
        _paint_panel(g, idx, cells, color)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(3, 19, 0)
    if name == "no_dividers":
        # missing 8-cols → can't separate 5 panels
        for cells in [_EA, _EB]:
            for r, c in cells: g[r][c] = 4
        return g
    if name == "no_demo":
        # only query panels, no demo of A op B = C → operation undefined
        for sep in (3, 7, 11, 15):
            for r in range(3):
                g[r][sep] = 8
        for r, c in _QA: g[r][12 + c] = 5
        for r, c in _QB: g[r][16 + c] = 5
        return g
    if name == "no_query":
        # demo panels but no query → no operands to apply operation to
        for sep in (3, 7, 11, 15):
            for r in range(3):
                g[r][sep] = 8
        for r, c in _EA: g[r][c] = 4
        for r, c in _EB: g[r][4 + c] = 4
        for r, c in _apply_op(_EA, _EB, "union"): g[r][8 + c] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if len(grid) != 3 or any(len(row) != 19 for row in grid):
        return ["expected fixed 3x19 five-panel grid"]
    for sep in (3, 7, 11, 15):
        if any(grid[r][sep] != 8 for r in range(3)):
            msgs.append("missing full color-8 panel separator")
            break
    def panel(idx):
        left = idx * 4
        return {(r, c) for r in range(3) for c in range(3) if grid[r][left + c] != 0}
    ea, eb, ed, qa, qb = [panel(i) for i in range(5)]
    matches = [op for op in _OPS if _apply_op(ea, eb, op) == ed]
    if len(matches) != 1:
        msgs.append("demo operation is ambiguous")
    if not _op_outputs_distinct(qa, qb):
        msgs.append("query operands do not distinguish all operations")
    if len(matches) == 1 and not _apply_op(qa, qb, matches[0]):
        msgs.append("chosen operation gives an empty query output")
    return msgs
