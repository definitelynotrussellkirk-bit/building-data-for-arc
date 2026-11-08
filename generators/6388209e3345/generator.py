"""Generator for arc_puzzle_bank_twentyfirst21:H143.

Combinatorial axes (8): match_index, transform, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_query, no_protos, ambiguous_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6388209e3345"
VERSION = "3.1.0"  # distinct=16: output is the matched prototype (3x3, in/out shape-lock is rule-intrinsic) but the 2 prototypes were FIXED (_PROTOS), so only proto-index x color varied. Now randomize the two 3x3 prototype shapes (verified DIFFERENT D4 classes and DIFFERENT cell counts so the query matches exactly one) -> output shape varies widely.
TASK_ID = "6388209e3345"
SUMMARY = (
    "Fixed 3×11 grid containing THREE 3×3 "
    "PANELS separated by SOLID color-8 (cyan) "
    "VERTICAL DIVIDERS at columns 3 and 7. "
    "Panel 0 (cols 0-2) and Panel 1 (cols 4-6) "
    "are PROTOTYPE panels each containing a "
    "small shape (3-4 cells) in distinct "
    "non-{0, 8} colors with DIFFERENT shapes "
    "(different cell-supports to avoid ambiguity). "
    "Panel 2 (cols 8-10) is the QUERY panel: "
    "it contains the support of EXACTLY ONE of "
    "the two prototypes under some dihedral "
    "TRANSFORM (id, r1, r2, r3, fh, fv, tr, "
    "atr — one of the 8 D4 symmetries), painted "
    "in its own query color. Rule: identify "
    "which prototype's SHAPE matches the query "
    "panel's shape MODULO any of the 8 "
    "rotations/reflections. Output is a 3×3 "
    "grid containing the MATCHED PROTOTYPE in "
    "its ORIGINAL color and original "
    "orientation (not the query's transform). "
    "Net: pick the matching proto, output it."
)

INVARIANTS = [
    "the input has two 3x3 prototype panels and one query panel",
    "the query support is a symmetry of exactly one prototype",
    "the canonical output is the matched prototype in its original color",
    "prototype supports have different cell counts to avoid ambiguity",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_query", "no_protos", "ambiguous_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "match_index":    {"type": "int", "default": "rng 0..1", "valid": "0..1"},
    "transform":      {"type": "enum", "default": "rng", "valid": "id|r1|r2|r3|fh|fv|tr|atr"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "two_protos_one_query",
                       "valid": "two_protos_one_query"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_PROTOS = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 2)],
]
_CODES = ["id", "r1", "r2", "r3", "fh", "fv", "tr", "atr"]


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _dims(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _xform(cells, code):
    h, w = _dims(cells)
    if code == "id":
        raw = cells
    elif code == "r1":
        raw = [(c, h - 1 - r) for r, c in cells]
    elif code == "r2":
        raw = [(h - 1 - r, w - 1 - c) for r, c in cells]
    elif code == "r3":
        raw = [(w - 1 - c, r) for r, c in cells]
    elif code == "fh":
        raw = [(r, w - 1 - c) for r, c in cells]
    elif code == "fv":
        raw = [(h - 1 - r, c) for r, c in cells]
    elif code == "tr":
        raw = [(c, r) for r, c in cells]
    else:
        raw = [(w - 1 - c, h - 1 - r) for r, c in cells]
    return _normalize(raw)


def _d4_canon(cells):
    """Canonical (min) form over all 8 dihedral transforms of a support."""
    return min(tuple(_xform(cells, code)) for code in _CODES)


def _rand_proto(rng):
    """Random support inside a 3x3 panel (3-6 cells)."""
    pos = [(r, c) for r in range(3) for c in range(3)]
    return _normalize(rng.sample(pos, rng.randint(3, 6)))


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
    match_index = ctx.draw_int("match_index", 0, 1)
    if difficulty == "easy":
        code = ctx.draw_choice("transform", ["id", "fh"])
    elif difficulty == "hard":
        code = ctx.draw_choice("transform", ["r1", "r3", "tr", "atr"])
    else:
        code = ctx.draw_choice("transform", _CODES)
    proto_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 2)
    query_color = rng.choice([4, 6, 7, 9])

    # two random prototypes in DIFFERENT D4 classes so the query (a transform
    # of one) matches exactly one prototype.
    protos = list(_PROTOS)
    for _ in range(100):
        a = _rand_proto(rng); b = _rand_proto(rng)
        if len(a) != len(b) and _d4_canon(a) != _d4_canon(b):
            protos = [a, b]
            break

    g = full_grid(3, 11, 0)
    for sep in (3, 7):
        for r in range(3):
            g[r][sep] = 8
    for idx, cells in enumerate(protos):
        _paint_panel(g, idx, cells, proto_colors[idx])
    _paint_panel(g, 2, _xform(protos[match_index], code), query_color)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(3, 11, 0)
    for sep in (3, 7):
        for r in range(3):
            g[r][sep] = 8
    if name == "no_query":
        # Query panel empty — rule has nothing to match.
        _paint_panel(g, 0, _PROTOS[0], 4)
        _paint_panel(g, 1, _PROTOS[1], 5)
        return g
    if name == "no_protos":
        # Both proto panels empty — rule has no candidate to match against.
        _paint_panel(g, 2, _PROTOS[0], 6)
        return g
    if name == "ambiguous_match":
        # Both protos have same shape — query matches both.
        _paint_panel(g, 0, _PROTOS[0], 4)
        _paint_panel(g, 1, _PROTOS[0], 5)
        _paint_panel(g, 2, _PROTOS[0], 6)
        return g
    return g


def _panel_support(grid, panel):
    left = panel * 4
    return _normalize([(r, c) for r in range(3) for c in range(3)
                       if grid[r][left + c] not in (0, 8)])


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if len(grid) != 3 or any(len(row) != 11 for row in grid):
        return ["expected fixed 3x11 panel grid"]
    if any(grid[r][3] != 8 or grid[r][7] != 8 for r in range(3)):
        errs.append("missing solid color-8 vertical separators")
    protos = [_panel_support(grid, 0), _panel_support(grid, 1)]
    query = _panel_support(grid, 2)
    if not protos[0] or not protos[1] or not query:
        errs.append("one or more prototype/query panels are empty")
        return errs
    if len(protos[0]) == len(protos[1]):
        errs.append("prototype supports have the same cell count")
    if _d4_canon(protos[0]) == _d4_canon(protos[1]):
        errs.append("prototype supports are in the same D4 class")
    matches = [idx for idx, proto in enumerate(protos)
               if tuple(query) in {tuple(_xform(proto, code)) for code in _CODES}]
    if len(matches) != 1:
        errs.append(f"query matches {len(matches)} prototypes instead of exactly one")
    return errs
