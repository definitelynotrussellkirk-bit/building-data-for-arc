"""Generator for arc_puzzle_bank_21_set9_e:hard_i20.

A color-1 template is shown with several colored candidates. Exactly one
candidate has the same binary shape under a dihedral transform; the rule crops
that candidate and recolors its nonzero cells to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_template (no color-1 → rule has nothing to match);
no_match (template + distractors but no candidate matches dihedral
class → selector returns nothing); tied_match (two candidates both
match → selector's "exactly one" precondition fails).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c83b187a9e1c"
VERSION = "2.0.1"
TASK_ID = "c83b187a9e1c"
SUMMARY = (
    "FIXED 10×w grid (w ∈ "
    "[13, 15]) with: (a) "
    "COLOR-1 (blue) "
    "TEMPLATE — a fixed "
    "5-cell shape "
    "{(0, 0), (1, 0), (1, "
    "1), (2, 1), (2, 2)} "
    "painted at (1, 1); "
    "(b) MATCHING "
    "CANDIDATE — same "
    "shape transformed by "
    "one of 8 DIHEDRAL "
    "TRANSFORMS (rotations "
    "+ reflections), in a "
    "CANDIDATE color from "
    "{2..9} (excluding 1)"
    ", placed at (1, "
    "match_left) where "
    "match_left is chosen "
    "to fit; (c) TWO "
    "DISTRACTOR shapes "
    "with DIFFERENT "
    "normalized shapes "
    "(different dihedral "
    "class), each in a "
    "DISTINCT color, "
    "placed at bottom-"
    "left and bottom-"
    "right. Rule (FIND "
    "THE CANDIDATE "
    "MATCHING THE "
    "TEMPLATE UP TO "
    "DIHEDRAL SYMMETRY, "
    "CROP, RECOLOR TO 8)"
    ": identify the "
    "COLOR-1 TEMPLATE. "
    "For EACH non-1 "
    "candidate: check if "
    "its normalized "
    "shape matches any of "
    "the 8 dihedral "
    "variants of the "
    "template's "
    "normalized shape. "
    "Find the UNIQUE "
    "match. CROP it to "
    "its BBOX. RECOLOR "
    "ALL its cells to "
    "COLOR 8 (cyan). "
    "Output is the cropped "
    "matching candidate "
    "in cyan. Flag: "
    "INTRINSIC-LOW — "
    "fixed template × 8 "
    "variants → 4 "
    "distinct cropped "
    "shapes."
)

INVARIANTS = [
    "there is exactly one color-1 template object",
    "candidate objects are single-color non-1 objects",
    "exactly one candidate is a dihedral transform of the template shape",
    "the output is the matching candidate crop recolored to 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_match", "tied_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "variant":           {"type": "int", "default": "rng 0..7", "valid": "0..7"},
    "grid_w":            {"type": "int", "default": "rng 13..15", "valid": "10..20"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "position_bias":     {"type": "str", "default": "template_plus_dihedral_match",
                          "valid": "template_plus_dihedral_match"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_BASE = [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]
_DISTRACTORS = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
    [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],
]


def _norm(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _xform(cells, code):
    raw = []
    for r, c in cells:
        if code == 0:
            raw.append((r, c))
        elif code == 1:
            raw.append((c, -r))
        elif code == 2:
            raw.append((-r, -c))
        elif code == 3:
            raw.append((-c, r))
        elif code == 4:
            raw.append((r, -c))
        elif code == 5:
            raw.append((-r, c))
        elif code == 6:
            raw.append((c, r))
        else:
            raw.append((-c, -r))
    return _norm(raw)


def _paint(g, top, left, cells, color):
    for dr, dc in cells:
        g[top + dr][left + dc] = color


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
        w = ctx.draw_int("grid_w", 13, 15); h = 10; k_lo, k_hi = 4, 5
    elif difficulty == "hard":
        w = ctx.draw_int("grid_w", 16, 20); h = 13; k_lo, k_hi = 5, 7
    else:
        w = ctx.draw_int("grid_w", 14, 18); h = 11; k_lo, k_hi = 4, 6
    variant = ctx.draw_int("variant", 0, 7)
    candidate_color, d1_color, d2_color = rng.sample([2, 3, 4, 5, 6, 7, 9], 3)
    # RANDOM template (was the FIXED _BASE -> only 4 distinct cropped outputs). The
    # output is the matching candidate (= template under a dihedral transform) in 8,
    # so a random template makes the output vary widely.
    template = _rand_poly(rng, rng.randint(k_lo, k_hi))
    variants = {tuple(_xform(template, v)) for v in range(8)}
    match = _xform(template, variant)

    def _distractor():
        for _ in range(80):
            d = _rand_poly(rng, rng.randint(k_lo, k_hi))
            if tuple(_norm(d)) not in variants:   # different dihedral class -> cannot match
                return _norm(d)
        return _norm(_DISTRACTORS[0])

    d1 = _distractor(); d2 = _distractor()
    th = max(r for r, _ in template) + 1; tw = max(c for _, c in template) + 1
    mh = max(r for r, _ in match) + 1; mw = max(c for _, c in match) + 1
    g = full_grid(h, w, 0)
    _paint(g, 1, 1, template, 1)
    _paint(g, 1, max(1 + tw + 1, w - mw - 1), match, candidate_color)
    d1h = max(r for r, _ in d1) + 1; d1w = max(c for _, c in d1) + 1
    d2h = max(r for r, _ in d2) + 1; d2w = max(c for _, c in d2) + 1
    _paint(g, h - d1h - 1, 1, d1, d1_color)
    _paint(g, h - d2h - 1, max(1 + d1w + 1, w - d2w - 1), d2, d2_color)
    return g


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    return _norm(cells)


def _draw_from_degenerate(name, rng):
    h, w = 10, 14
    g = full_grid(h, w, 0)
    if name == "no_template":
        # No color-1 template — rule has nothing to match.
        _paint(g, 1, 1, _BASE, 4)
        _paint(g, 6, 8, _DISTRACTORS[0], 6)
        return g
    if name == "no_match":
        # Template (L-pentomino) but distractors all 2x2 squares (different class).
        _paint(g, 1, 1, _BASE, 1)
        _paint(g, 1, 8, _DISTRACTORS[0], 4)
        _paint(g, 6, 1, _DISTRACTORS[0], 6)
        _paint(g, 6, 8, _DISTRACTORS[0], 7)
        return g
    if name == "tied_match":
        # Two candidates both match the template's dihedral class.
        _paint(g, 1, 1, _BASE, 1)
        _paint(g, 1, 8, _xform(_BASE, 0), 4)   # match 1: identity
        _paint(g, 6, 8, _xform(_BASE, 2), 6)   # match 2: 180
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Grid must have color-1 template cells and at least one non-1 candidate object."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not ones:
        msgs.append("no color-1 template cells found")
    candidates = set(grid[r][c] for r in range(h) for c in range(w)
                     if grid[r][c] not in (0, 1))
    if not candidates:
        msgs.append("no candidate objects (non-0, non-1) found")
    return msgs
