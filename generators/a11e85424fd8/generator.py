"""Generator for arc_puzzle_bank_twentysecond21:H151.

Rule: find the candidate object whose support matches the query under a
dihedral transform; output cropped + recolored to the query color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_query, no_candidates, identical_candidates.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a11e85424fd8"
VERSION = "3.0.1"  # distinct 6 / all shape-locked: FIXED 3x11 grid + fixed L query + fixed distractor -> output always the same L in q_color. Rule splits panels by full-8 cols, matches query to a candidate under D4, outputs it cropped+recolored (canonical varies height 3/5 + output shape). Random query polyomino + dihedrally-distinct distractor + varied height -> output shape/size/color all vary."
TASK_ID = "a11e85424fd8"
SUMMARY = (
    "Fixed 3×11 grid with: (a) cols 0-2 = QUERY panel "
    "containing a 3-cell L-shape (after some dihedral "
    "transform) in q_color; (b) col 3 = full color-8 "
    "separator; (c) cols 4-6 = first CANDIDATE (the "
    "L-shape in hit_color, normalized orientation); "
    "(d) cols 7 = blank gap; (e) cols 8-10 = second "
    "CANDIDATE (a 4-cell distractor in other_color). "
    "Rule: extract the query shape and each candidate "
    "shape's binary support; for each candidate test all "
    "8 dihedral transforms — the candidate whose support "
    "matches the query under some D4 transform is the "
    "WINNER. Output: the winner cropped to its bbox, "
    "recolored to the query's color."
)

INVARIANTS = [
    "the input has a 3x3 query panel and a wider candidate-object panel",
    "candidate objects are 4-connected and separated by background",
    "exactly one candidate support matches the query under a dihedral transform",
    "the output is that candidate cropped and recolored to the query color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_query", "no_candidates", "identical_candidates")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "transform":      {"type": "enum", "default": "rng",
                       "valid": "id|r1|r2|r3|fh|fv|tr|atr"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "query_with_two_candidates",
                       "valid": "query_with_two_candidates"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 full-col color-8 separator; >=2 non-{0,8} color regions (query + >=1 candidate)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    sep_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if not sep_cols:
        errs.append("no full-column color-8 separator found")
    # Count distinct non-{0,8} colors (proxy for 2+ panels)
    colors = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] not in (0, 8))
    if len(colors) < 2:
        errs.append(f"expected >=2 distinct non-{{0,8}} colors, found {len(colors)}")
    return errs


_QUERY = [(0, 0), (1, 0), (1, 1)]
_DISTRACTOR = [(0, 0), (0, 1), (1, 1), (2, 1)]
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


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    return _normalize(cells)


def _dihedral_set(cells):
    return frozenset(tuple(_xform(cells, c)) for c in _CODES)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        k_lo, k_hi = 3, 4
    elif difficulty == "hard":
        k_lo, k_hi = 4, 7
    else:
        k_lo, k_hi = 3, 6
    # Rule: split panels by full-height 8-columns; the query is the first panel,
    # find the candidate object in the second panel whose support matches the
    # query under any D4 transform, output it cropped + recolored to the query
    # color. v2.x hardcoded a fixed L + fixed 3x11 grid. Random query polyomino
    # drawn in some orientation; matching candidate = another orientation of it;
    # distractor = a dihedrally-DISJOINT shape so the match is unique.
    qshape = _rand_poly(rng, rng.randint(k_lo, k_hi))
    qset = _dihedral_set(qshape)
    for _ in range(60):
        dshape = _rand_poly(rng, rng.randint(k_lo, k_hi))
        if not (_dihedral_set(dshape) & qset):
            break
    else:
        dshape = _DISTRACTOR
    q_draw = _xform(qshape, rng.choice(_CODES))      # query as drawn (any orientation)
    cand = _xform(qshape, rng.choice(_CODES))        # matching candidate (any orientation)
    q_color, hit_color, other_color = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)

    qh = max(r for r, _ in q_draw) + 1; qw = max(c for _, c in q_draw) + 1
    ch = max(r for r, _ in cand) + 1; cw = max(c for _, c in cand) + 1
    dh = max(r for r, _ in dshape) + 1; dw = max(c for _, c in dshape) + 1
    H = max(qh, ch, dh) + rng.randint(0, 2)
    sep = qw                                          # full-height 8 column
    c_start = sep + 1                                 # candidate region
    d_start = c_start + cw + 1                        # 1-col gap -> separate component
    W = d_start + dw
    g = full_grid(H, W, 0)
    for r in range(H):
        g[r][sep] = 8
    _paint(g, rng.randint(0, H - qh), 0, q_draw, q_color)
    _paint(g, rng.randint(0, H - ch), c_start, cand, hit_color)
    _paint(g, rng.randint(0, H - dh), d_start, dshape, other_color)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(3, 11, 0)
    for r in range(3):
        g[r][3] = 8
    if name == "no_query":
        # Query panel empty — rule has no shape to match against.
        _paint(g, 0, 4, _QUERY, 4)
        _paint(g, 0, 8, _DISTRACTOR, 6)
        return g
    if name == "no_candidates":
        # Query but no candidate objects — rule's selector finds
        # nothing.
        _paint(g, 0, 0, _QUERY, 2)
        return g
    if name == "identical_candidates":
        # Both candidates identical to the query — rule's
        # "exactly one matches" tie-break ambiguous.
        _paint(g, 0, 0, _QUERY, 2)
        _paint(g, 0, 4, _QUERY, 4)
        _paint(g, 0, 8, _QUERY, 6)
        return g
    return g
