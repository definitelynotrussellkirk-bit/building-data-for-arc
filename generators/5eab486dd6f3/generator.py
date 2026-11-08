"""Generator for arc_additional_puzzles_21_set6:H37 — dihedral exemplar transform.

Two color-2 exemplar objects define a dihedral transform. A color-3 query
object is transformed the same way by the rule.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: identity_transform (exemplars identical → 8 valid ops fix
A; rule cannot infer which transform), symmetric_base (base is point-
symmetric → multiple transforms map A→B; rule's inference is ambiguous),
no_query (no color-3 component → rule has nothing to transform).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5eab486dd6f3"
VERSION = "2.1.0"  # require uniquely inferable exemplar transform and visibly transformed query  # distinct=22 + shape-locked-in: fixed 14x20 grid + _SHAPES bank. Rule infers A->B dihedral transform (2 color-2 exemplars) and applies to color-3 query. Now random D4-asymmetric base + random query + varied grid -> distinct 22->87, in 1->30.
TASK_ID = "5eab486dd6f3"
SUMMARY = "Two color-2 exemplars show a symmetry transform applied to a color-3 query."

INVARIANTS = [
    "exactly two separated color-2 exemplar components",
    "exactly one color-3 query component",
    "the exemplar components differ by one rotation/reflection transform",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identity_transform", "symmetric_base", "no_query")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "transform":      {"type": "int", "default": "rng 1..7", "valid": "1..7"},
    "shape":          {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "query_shape":    {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "two_exemplars_one_query",
                       "valid": "two_exemplars_one_query"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1), (3, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 2)],
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (2, 3)],
    [(0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (3, 0)],
]


def _normalize(cells):
    r0 = min(r for r, _c in cells)
    c0 = min(c for _r, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _transform(cells, code):
    raw = []
    for r, c in cells:
        if code == 1:
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
        elif code == 7:
            raw.append((-c, -r))
        else:
            raw.append((r, c))
    return _normalize(raw)


def _stamp(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    for _ in range(200):
        if len(cells) >= k:
            break
        br, bc = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = br + dr, bc + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return _normalize(cells)


def _is_d4_asym(cells):
    """All 8 dihedral images distinct -> the inferred transform is unambiguous."""
    return len({tuple(_transform(cells, code)) for code in range(8)}) == 8


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        code = ctx.draw_int("transform", 1, 4); h = ctx.draw_int("grid_h", 11, 13); w = ctx.draw_int("grid_w", 13, 16)
    elif difficulty == "hard":
        code = ctx.draw_int("transform", 1, 7); h = ctx.draw_int("grid_h", 15, 20); w = ctx.draw_int("grid_w", 18, 24)
    else:
        code = ctx.draw_int("transform", 1, 7); h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 15, 20)
    # D4-asymmetric base so the transform code is uniquely inferable from A->B.
    base = None
    for _ in range(200):
        cand = _rand_poly(rng, rng.randint(4, 7))
        if _is_d4_asym(cand) and _transform(cand, code) != cand:
            base = cand
            break
    if base is None:
        raise ValueError("could not build D4-asymmetric exemplar")
    query = None
    for _ in range(200):
        cand = _rand_poly(rng, rng.randint(3, 7))
        if _transform(cand, code) != cand:
            query = cand
            break
    if query is None:
        raise ValueError("could not build visibly-transforming query")
    exemplar_b = _transform(base, code)
    g = full_grid(h, w, 0)
    bw = max(c for _, c in base) + 1
    ew = max(c for _, c in exemplar_b) + 1
    _stamp(g, 1, 1, base, 2)
    _stamp(g, 1, min(w - ew, bw + 4), exemplar_b, 2)   # 2nd exemplar, separated
    qh = max(r for r, _ in query) + 1; qw = max(c for _, c in query) + 1
    qr = rng.randint(h // 2, h - qh); qc = rng.randint(0, w - qw)
    _stamp(g, qr, qc, query, 3)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 14, 20
    g = full_grid(h, w, 0)
    if name == "identity_transform":
        # Exemplars are identical — 8 valid ops fix A; rule's
        # transform-inference cannot pick a unique op.
        base = _normalize(_SHAPES[0])
        _stamp(g, 2, 1, base, 2)
        _stamp(g, 2, 8, base, 2)
        _stamp(g, 8, 5, _normalize(_SHAPES[1]), 3)
        return g
    if name == "symmetric_base":
        # Base is its own 180° rotation (a 2x2 square works);
        # multiple transforms map A→B identically.
        sq = [(0, 0), (0, 1), (1, 0), (1, 1)]
        _stamp(g, 2, 1, sq, 2)
        _stamp(g, 2, 8, sq, 2)
        _stamp(g, 8, 5, _normalize(_SHAPES[1]), 3)
        return g
    if name == "no_query":
        # No color-3 query — rule has nothing to transform; output
        # equals input.
        base = _normalize(_SHAPES[0])
        _stamp(g, 2, 1, base, 2)
        _stamp(g, 2, 8, _transform(base, 2), 2)
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    from puzzle_generators.helpers.selfcheck import components_cells as components, normalize, d4_transform
    twos = sorted(components([[v if v == 2 else 0 for v in row] for row in grid]),
                  key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))
    threes = components([[v if v == 3 else 0 for v in row] for row in grid])
    if len(twos) != 2 or len(threes) != 1:
        return [f"expected two exemplar components and one query, found {len(twos)} / {len(threes)}"]
    a, b, q = normalize(twos[0]), normalize(twos[1]), normalize(threes[0])
    codes = [code for code in range(8) if d4_transform(a, code) == b]
    msgs = []
    if len(codes) != 1 or codes[0] == 0:
        msgs.append("exemplar transform is ambiguous or identity")
    if len(codes) == 1 and d4_transform(q, codes[0]) == q:
        msgs.append("query shape is unchanged by the inferred transform")
    return msgs
