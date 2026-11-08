"""Generator for arc_puzzle_bank_fourteenth21:H97.

Combinatorial axes (8): grid_h, grid_w, palette_kind, operation,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_demo, no_target_panels, no_dividers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c6980153fd28"
VERSION = "2.1.1"  # shape-locked (fixed 7x11, 3x3 panels): panels are defined by the color-9 separator row + 2 separator cols -> any equal size. Now vary panel dims (2-5) -> grid + output dims vary.
TASK_ID = "c6980153fd28"
SUMMARY = (
    "Fixed 7×11 0-bg grid laid out as TWO ROWS of "
    "THREE 3×3 PANELS each, separated by COLOR-9 LINES: "
    "(a) 9-DIVIDERS — full vertical column-9 at cols 3 "
    "and 7, full horizontal row-9 at row 3 (so the grid "
    "splits into a 2×3 panel grid with 9 borders); "
    "(b) TOP ROW (DEMO): three 3×3 panels showing _A, "
    "_B, and (_A op _B) where op is one of 5 fixed "
    "binary set ops {union, intersection, xor, A-B, "
    "B-A} chosen for this sample; (c) BOTTOM ROW "
    "(QUERY): bottom-left panel = _D (fixed mask), "
    "bottom-middle panel = _E (fixed mask), bottom-"
    "right panel is BLANK (the target). All masks "
    "painted in a single random non-{0,9} color drawn "
    "from {1..7}. Rule (INFER THE BINARY OCCUPANCY "
    "OP FROM TOP DEMO AND APPLY TO BOTTOM-LEFT × "
    "BOTTOM-MIDDLE INTO BOTTOM-RIGHT): read the TOP "
    "ROW to determine which of the 5 ops produces the "
    "third panel from the first two. APPLY that same op "
    "to the bottom-left and bottom-middle 3×3 occupancy "
    "masks. PAINT the resulting cells (in the same "
    "color) into the bottom-right 3×3 panel. Top row, "
    "dividers, and the two bottom operand panels stay "
    "unchanged. Net: the blank bottom-right panel gets "
    "filled with the inferred op of the two bottom "
    "operands."
)

INVARIANTS = [
    "the grid has two rows of three 3x3 panels separated by color-9 lines",
    "the top row demonstrates union, intersection, xor, A-B, or B-A",
    "the bottom-left and bottom-middle panels are the query operands",
    "the bottom-right panel starts blank and receives the inferred result",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_demo", "no_target_panels", "no_dividers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7", "valid": "7..7"},
    "grid_w":         {"type": "int", "default": "11", "valid": "11..11"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "operation":      {"type": "enum", "default": "rng",
                       "valid": "union|intersection|xor|aminusb|bminusa"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "demo_row_plus_target_row",
                       "valid": "demo_row_plus_target_row"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_OPS = ["union", "intersection", "xor", "aminusb", "bminusa"]
_DEFAULT_A = {(0, 0), (0, 1), (1, 0), (2, 2)}
_DEFAULT_B = {(0, 1), (1, 1), (2, 0), (2, 2)}
_DEFAULT_D = {(0, 0), (0, 2), (1, 2)}
_DEFAULT_E = {(0, 2), (1, 0), (1, 2)}


def _random_mask(rng, ph=3, pw=3, min_cells=2, max_cells=None):
    all_cells = [(r, c) for r in range(ph) for c in range(pw)]
    hi = max_cells if max_cells is not None else max(2, len(all_cells) - 2)
    n = rng.randint(min_cells, min(hi, len(all_cells)))
    return set(rng.sample(all_cells, n))


def _good_pair(rng, op, ph=3, pw=3):
    """Draw a pair (m1, m2) where op(m1, m2) is non-empty and not equal to
    either operand (so all 5 ops give distinguishable demo outputs)."""
    for _ in range(60):
        m1 = _random_mask(rng, ph, pw)
        m2 = _random_mask(rng, ph, pw)
        out = _apply(m1, m2, op)
        if not out:
            continue
        if out == m1 or out == m2:
            continue
        # Avoid m1 == m2 (intersection == xor == both → ambiguous demo)
        if m1 == m2:
            continue
        return m1, m2
    return _DEFAULT_A, _DEFAULT_B


def _apply(a, b, op):
    if op == "union":
        return a | b
    if op == "intersection":
        return a & b
    if op == "xor":
        return (a | b) - (a & b)
    if op == "aminusb":
        return a - b
    return b - a


def _paint_panel(g, row_band, panel, cells, color, ph=3, pw=3):
    top = row_band * (ph + 1)
    left = panel * (pw + 1)
    for r, c in cells:
        g[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        op = ctx.draw_choice("operation", ["union", "intersection"])
    elif difficulty == "hard":
        op = ctx.draw_choice("operation", ["xor", "aminusb", "bminusa"])
    else:
        op = ctx.draw_choice("operation", _OPS)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7])
    # panels are defined by the color-9 separator row + 2 separator columns, so they
    # can be ANY equal size (was hardcoded 3x3 -> fixed 7x11). Vary panel dims.
    if difficulty == "easy":
        ph = pw = 3
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_h", 3, 5); pw = ctx.draw_int("panel_w", 3, 5)
    else:
        ph = ctx.draw_int("panel_h", 2, 4); pw = ctx.draw_int("panel_w", 3, 5)
    h = 2 * ph + 1; w = 3 * pw + 2
    sep_cols = (pw, 2 * pw + 1)
    g = full_grid(h, w, 0)
    for c in sep_cols:
        for r in range(h):
            g[r][c] = 9
    for c in range(w):
        g[ph][c] = 9
    A, B = _good_pair(rng, op, ph, pw)
    D, E = _good_pair(rng, op, ph, pw)
    for idx, cells in enumerate([A, B, _apply(A, B, op)]):
        _paint_panel(g, 0, idx, cells, color, ph, pw)
    _paint_panel(g, 1, 0, D, color, ph, pw)
    _paint_panel(g, 1, 1, E, color, ph, pw)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Color-9 separator lines present; >=1 non-{0,9} demo color."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    nines = sum(grid[r][c] == 9 for r in range(h) for c in range(w))
    if nines < h + w - 1:
        errors.append(f"expected >=1 full row and >=1 full col of 9s, found only {nines} color-9 cells")
    demo_colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] not in (0, 9)}
    if not demo_colors:
        errors.append("no non-{0,9} demo/query cells found")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 11, 0)
    for c in (3, 7):
        for r in range(7): g[r][c] = 9
    for c in range(11): g[3][c] = 9
    if name == "no_demo":
        # only target panels, no demo → operation undefined
        _paint_panel(g, 1, 0, _DEFAULT_D, 4)
        _paint_panel(g, 1, 1, _DEFAULT_E, 4)
        return g
    if name == "no_target_panels":
        # only demo, no target operands → no panels to apply op to
        for idx, cells in enumerate([_DEFAULT_A, _DEFAULT_B,
                                     _apply(_DEFAULT_A, _DEFAULT_B, "union")]):
            _paint_panel(g, 0, idx, cells, 4)
        return g
    if name == "no_dividers":
        # missing color-9 dividers → can't separate panels
        out = full_grid(7, 11, 0)
        for idx, cells in enumerate([_DEFAULT_A, _DEFAULT_B,
                                     _apply(_DEFAULT_A, _DEFAULT_B, "union")]):
            _paint_panel(out, 0, idx, cells, 4)
        _paint_panel(out, 1, 0, _DEFAULT_D, 4)
        _paint_panel(out, 1, 1, _DEFAULT_E, 4)
        return out
    return g
