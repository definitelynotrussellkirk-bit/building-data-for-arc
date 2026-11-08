"""Generator for arc_puzzle_bank_21_set8_s:S8_H4 — match by row-occupancy signature.

Rule: there is one QUERY object in color 8. Compute its per-row occupancy
signature (per row, the sorted column offsets relative to the bbox left). Find
the first NON-8 object with the SAME signature (i.e. the identical shape). Crop
the grid to that match object's bbox — that crop is the output.

The old generator FIXED the grid at 9x14 and used 3 hard-coded ~3x3 shapes at
fixed positions, so the input shape never varied (shape-locked-in) and the
output was always 3x3 (distinct=21, all colour combos). Now: the shape S is a
RANDOM connected polyomino (varied size incl. NON-SQUARE bbox) painted as both
the color-8 query and a non-8 match; 1-3 random distractors carry DIFFERENT
signatures; the grid size varies. Output dims = bbox(S), so they vary.

Combinatorial axes: shape S (size/bbox/cells), match color, distractor
count/shapes/colors, all positions, grid size.
Degenerates: no_query, no_match, multiple_matches.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4a8c7e2bad04"
VERSION = "3.0.1"  # shape-locked-in + distinct=21: gen FIXED grid 9x14 and used 3 hard-coded shapes at fixed positions -> input never varied, output always 3x3 (only colours changed). Now S is a RANDOM polyomino (varied bbox, incl. non-square) painted as the 8-query AND a non-8 match; random different-signature distractors; varied grid. Output dims = bbox(S) so they vary.
TASK_ID = "4a8c7e2bad04"
SUMMARY = (
    "0-bg grid (size varies) with: (a) one QUERY object in color 8 (a random "
    "connected polyomino S); (b) one MATCH object in a non-8 color with the "
    "IDENTICAL shape S (same per-row column-offset signature); (c) 1-3 "
    "DISTRACTOR objects in other colors whose signatures DIFFER from S. All "
    "objects are 8-gap isolated. Rule: take the query's row signature, find "
    "the first non-8 object with the same signature, and crop to its bbox. "
    "Output = that crop (the match shape in its color). Output dims = bbox(S)."
)

INVARIANTS = [
    "exactly one color-8 query object",
    "exactly one non-8 object with the SAME per-row signature as the query",
    ">=1 distractor object with a DIFFERENT signature",
    "objects are 8-gap isolated (distinct components)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_query", "no_match", "multiple_matches")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..20"},
    "shape_cells":    {"type": "int", "default": "rng 4..8", "valid": "3..9"},
    "n_distractors":  {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "query_match_distractors",
                       "valid": "query_match_distractors"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _sig(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r1, r2, c1 = min(rs), max(rs), min(cs)
    return tuple(tuple(sorted(c - c1 for (r, c) in cells if r == rr))
                 for rr in range(r1, r2 + 1))


def _rand_poly(rng, k, maxh, maxw):
    cells = [(0, 0)]; seen = {(0, 0)}
    tries = 0
    while len(cells) < k and tries < 300:
        tries += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) in seen:
            continue
        rs = [x for x, _ in cells] + [nr]; cs = [y for _, y in cells] + [nc]
        if max(rs) - min(rs) + 1 <= maxh and max(cs) - min(cs) + 1 <= maxw:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _free(g, top, left, cells):
    h, w = len(g), len(g[0])
    for (dr, dc) in cells:
        rr, cc = top + dr, left + dc
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                nr, nc = rr + ddr, cc + ddc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1; sw = max(c for _, c in cells) + 1
    for _ in range(200):
        top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
        if _free(g, top, left, cells):
            for (r, c) in cells:
                g[top + r][left + c] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 10, 12)
        nd = ctx.draw_int("n_distractors", 1, 1); klo, khi = 4, 6
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 14, 20)
        nd = ctx.draw_int("n_distractors", 2, 3); klo, khi = 5, 9
    else:
        h = ctx.draw_int("grid_h", 9, 13); w = ctx.draw_int("grid_w", 12, 16)
        nd = ctx.draw_int("n_distractors", 1, 2); klo, khi = 4, 8
    rng = ctx.draw_rng("layout")

    for _outer in range(40):
        g = full_grid(h, w, 0)
        k = rng.randint(klo, khi)
        S = _rand_poly(rng, k, min(5, h - 2), min(5, w - 2))
        s_sig = _sig(S)
        pool = [2, 3, 4, 5, 6, 7, 9]
        rng.shuffle(pool)
        match_color = pool[0]
        # query (8) + match (same shape S, distinct colour)
        if not _place(g, rng, S, 8):
            continue
        if not _place(g, rng, S, match_color):
            continue
        # distractors: random polys whose signature differs from S
        placed_d = 0
        for di in range(nd):
            for _try in range(30):
                dk = rng.randint(3, max(3, khi))
                D = _rand_poly(rng, dk, min(5, h - 2), min(5, w - 2))
                if _sig(D) == s_sig:
                    continue
                dc = pool[1 + (placed_d % (len(pool) - 1))]
                if _place(g, rng, D, dc):
                    placed_d += 1
                break
        if placed_d >= 1:
            return g
    raise ValueError("could not realize 4a8c layout")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify query-match-distractor invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    problems = []
    flat = [v for row in grid for v in row]
    count8 = flat.count(8)
    if count8 < 1:
        problems.append(f"expected color-8 query object, found {count8} cells of color 8")
    non_bg_non8 = [v for v in flat if v not in (0, 8)]
    if len(set(non_bg_non8)) < 2:
        problems.append("expected >=2 distinct non-{0,8} colors (match + distractor)")
    return problems


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 14, 0)
    S = [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)]
    D = [(0, 0), (0, 1), (1, 1), (2, 1)]
    if name == "no_query":
        # match + distractor present but no color-8 query
        for r, c in S: g[1 + r][8 + c] = 4
        for r, c in D: g[5 + r][3 + c] = 6
        return g
    if name == "no_match":
        # query present but no other object with matching signature
        for r, c in S: g[1 + r][1 + c] = 8
        for r, c in D: g[5 + r][3 + c] = 6
        return g
    if name == "multiple_matches":
        # two non-query objects share the query's signature -> ambiguous
        for r, c in S: g[1 + r][1 + c] = 8
        for r, c in S: g[1 + r][8 + c] = 4
        for r, c in S: g[5 + r][3 + c] = 6
        return g
    return g
