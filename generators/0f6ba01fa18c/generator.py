"""Generator for arc_puzzle_bank_third_21_bundle:hard_20_boolean_combine_two_templates_by_key.

Two binary templates in colors 1 and 2 are combined by a singleton control
color: 3 for union, 4 for intersection, and 6 for xor.

Combinatorial axes (8): grid_h, grid_w, palette_kind, op_key,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key, no_template_a, no_template_b.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0f6ba01fa18c"
VERSION = "2.2.0"  # guarantee templates fit their half-grid and that the selected boolean op has nonempty support (no crash / no [[0]] default cases)
TASK_ID = "0f6ba01fa18c"
SUMMARY = (
    "8×10 0-bg grid with: (a) one connected color-1 (blue) "
    "TEMPLATE A; (b) one connected color-2 (red) TEMPLATE B; "
    "(c) exactly one SINGLETON KEY cell with color ∈ {3, 4, "
    "6} placed somewhere apart. Rule: extract A's cells and "
    "normalize → s1; same for B's cells → s2. Detect control "
    "color (the one with count == 1 in {3, 4, 6}). Apply "
    "boolean op on the two normalized cell-sets: 3 → UNION, "
    "4 → INTERSECTION, 6 → XOR (symmetric difference). If "
    "result empty → output [[0]]. Else: normalize result to "
    "(0, 0), paint cells color 8 (cyan). Output: small grid "
    "sized to result's bbox."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "8×10 grid",
    "one connected color-1 template object",
    "one connected color-2 template object",
    "exactly one of colors 3, 4, or 6 appears as a singleton control",
    "the selected boolean operation has a nonempty support",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_template_a", "no_template_b")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..12"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "op_key":         {"type": "int", "default": "rng 3|4|6", "valid": "3|4|6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "two_templates_with_key",
                       "valid": "two_templates_with_key"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (1, 0), (1, 1), (2, 1)],          # S
    [(0, 1), (1, 0), (1, 1), (2, 0)],          # Z
    [(0, 0), (0, 1), (1, 0), (1, 1)],          # 2x2 square
    [(0, 0), (0, 1), (0, 2), (1, 1)],          # T
    [(0, 0), (1, 0), (2, 0), (2, 1)],          # L
    [(0, 1), (1, 0), (1, 1), (1, 2)],          # ⊥
    [(0, 0), (0, 1), (1, 1), (2, 1)],          # ⌐
]


def _paint(g, top, left, cells, color):
    for dr, dc in cells:
        g[top + dr][left + dc] = color


def _shape_dims(cells):
    return (max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1)


def _fits(cells, max_h, max_w):
    sh, sw = _shape_dims(cells)
    return sh <= max_h and sw <= max_w


def _norm_cells(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
    if not cells:
        return set()
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return {(r - mr, c - mc) for r, c in cells}


def _op_result(a, b, key):
    if key == 3:
        return a | b
    if key == 4:
        return a & b
    if key == 6:
        return a ^ b
    return set()


def _draw_fitting_shape(rng, size_range, max_h, max_w):
    """Sample a connected normalized polyomino that fits the reserved panel."""
    for _ in range(200):
        cells = _grow(rng, rng.randint(*size_range))
        if _fits(cells, max_h, max_w):
            return cells
    for cells in _SHAPES:
        if _fits(cells, max_h, max_w):
            return list(cells)
    # Last-resort tiny connected triomino; all current grid bands have room for it.
    return [(0, 0), (1, 0), (1, 1)]


def _grow(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 9, 11)
        key = ctx.draw_choice("op_key", [3]); sz = (3, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 11, 14)
        key = ctx.draw_choice("op_key", [4, 6]); sz = (4, 7)
    else:
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 10, 13)
        key = ctx.draw_choice("op_key", [3, 4, 6]); sz = (3, 6)
    g = full_grid(h, w, 0)
    # Two varied polyomino templates, color 1 (left half) and 2 (right half),
    # separated so they're distinct components.  The two halves can be narrow;
    # draw shapes against the common fit budget so `_paint` cannot overflow.
    # Also reject op/result degeneracy: intersection must intersect, xor must
    # not receive identical normalized templates.
    half = w // 2
    max_shape_h = h - 1                       # top is >=1, bottom may touch edge
    max_shape_w = min(max(1, half - 1), max(1, w - half - 1))
    shape_a = _draw_fitting_shape(rng, sz, max_shape_h, max_shape_w)
    a_set = set(shape_a)
    for _ in range(200):
        shape_b = _draw_fitting_shape(rng, sz, max_shape_h, max_shape_w)
        if _op_result(a_set, set(shape_b), key):
            break
    else:
        if key == 4:
            shape_b = list(shape_a)
        else:
            shape_b = next(
                (list(s) for s in _SHAPES if _fits(s, max_shape_h, max_shape_w) and set(s) != a_set),
                [(0, 0), (1, 0), (1, 1)],
            )
    sha = max(r for r, _ in shape_a) + 1; swa = max(c for _, c in shape_a) + 1
    shb = max(r for r, _ in shape_b) + 1; swb = max(c for _, c in shape_b) + 1
    ra = rng.randint(1, h - sha); ca = rng.randint(1, half - swa)
    rb = rng.randint(1, h - shb); cb = rng.randint(half + 1, w - swb)
    _paint(g, ra, ca, shape_a, 1)
    _paint(g, rb, cb, shape_b, 2)
    # singleton control marker on an empty cell in the bottom area
    for _ in range(60):
        kr = rng.randint(0, h - 1); kc = rng.randint(0, w - 1)
        if g[kr][kc] == 0:
            g[kr][kc] = key
            break
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    key_cells = [(r, c, v) for r, row in enumerate(grid)
                 for c, v in enumerate(row) if v in (3, 4, 6)]
    if len(key_cells) != 1:
        errs.append(f"expected exactly one control key in {{3,4,6}}, found {len(key_cells)}")
        key = None
    else:
        key = key_cells[0][2]
    a = _norm_cells(grid, 1)
    b = _norm_cells(grid, 2)
    if not a:
        errs.append("missing color-1 template")
    if not b:
        errs.append("missing color-2 template")
    if key is not None and a and b and not _op_result(a, b, key):
        errs.append(f"selected boolean op {key} has empty support")
    return errs


_A = _SHAPES[0]
_B = _SHAPES[2]


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 10, 0)
    if name == "no_key":
        # both templates exist but no 3/4/6 control → no operation defined
        _paint(g, 1, 1, _A, 1)
        _paint(g, 1, 5, _B, 2)
        return g
    if name == "no_template_a":
        # color-2 template + key but no color-1 template → operation has no LHS
        _paint(g, 1, 5, _B, 2)
        g[6][3] = 4
        return g
    if name == "no_template_b":
        # color-1 template + key but no color-2 template → operation has no RHS
        _paint(g, 1, 1, _A, 1)
        g[6][6] = 4
        return g
    return g
