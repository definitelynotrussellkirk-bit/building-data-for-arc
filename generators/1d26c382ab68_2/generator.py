"""Generator for 5ed28e33.

Rule: a full color-9 row separates a top color-1 TEMPLATE shape from
lower candidate OBJECTS. Each lower object whose cropped shape matches
the template under SOME ROTATION (0/90/180/270 — no reflections) is
recolored 2; non-matching objects are preserved. (Identical rule to
sibling 1d26c382ab68.)

Combinatorial axes: grid size, separator position, the template shape,
and the lower objects (rotations of the template = matches, different
shapes = distractors) + their colors/positions.
Degenerates: no_template, no_candidates, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1d26c382ab68_2"
VERSION = "2.0.1"  # diversity: random template + rotated matches + distractors + grid (was ~6 fixed)
TASK_ID = "1d26c382ab68_2"
SUMMARY = (
    "0-bg grid (size varies). A full COLOR-9 (maroon) separator row "
    "splits a top COLOR-1 (blue) TEMPLATE shape from a lower region of "
    "2-5 candidate OBJECTS (each a single-color connected shape in colors "
    "3..8, placed apart). Some candidates are ROTATIONS of the template "
    "(0/90/180/270) and some are different shapes (distractors, including "
    "reflections that are NOT rotations). Rule: recolor every candidate "
    "matching the template under rotation to COLOR 2 (red); preserve the "
    "rest. The grid size, separator row, template shape, and the "
    "candidates' shapes/colors/positions all vary freely (was a "
    "near-fixed layout giving ~6 distinct)."
)

INVARIANTS = [
    "one full color-9 separator row splits template (above) from candidates (below)",
    "the top template is a connected color-1 shape",
    ">=1 lower object is a rotation of the template (a match) and >=1 is not",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_template", "no_candidates", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_CAND_COLORS = (3, 4, 5, 6, 7, 8)

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..16"},
    "candidate_color":{"type": "color", "default": "varies", "valid": "3..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varies", "valid": "3..6"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|"
                                "no_template|no_candidates|full_grid"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _rot_cw(cells):
    return [(c, -r) for r, c in cells]


def _rotations(cells):
    out = []
    cur = list(cells)
    for _ in range(4):
        out.append(_norm(cur))
        cur = _rot_cw(cur)
    return set(out)


def _conn_poly(rng, size, maxd):
    for _ in range(80):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        n = _norm(cells)
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return sorted(n)
    return [(0, 0), (0, 1), (1, 0)]


def _reserve(occ, cells, h, w):
    cset = set(cells)
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w) or occ[r][c]:
            return False
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (rr, cc) in cset:
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    for (r, c) in cells:
        occ[r][c] = True
    return True


def _place_in_region(rng, occ, g, shape_cells, color, r_lo, r_hi, w, h):
    bh = max(r for r, c in shape_cells) + 1
    bw = max(c for r, c in shape_cells) + 1
    if bh > (r_hi - r_lo + 1) or bw > w:
        return False
    for _t in range(40):
        top = rng.randint(r_lo, r_hi - bh + 1)
        left = rng.randint(0, w - bw)
        cells = [(top + r, left + c) for r, c in shape_cells]
        if _reserve(occ, cells, h, w):
            for r, c in cells:
                g[r][c] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, ncr, szr, md = (12, 14), (10, 12), (2, 3), (3, 4), 3
    elif difficulty == "hard":
        hr, wr, ncr, szr, md = (15, 18), (12, 16), (3, 5), (4, 6), 4
    else:
        hr, wr, ncr, szr, md = (13, 16), (11, 14), (2, 4), (3, 5), 4

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        template = _conn_poly(rng, rng.randint(*szr), md)
        tpl_rots = _rotations(template)

        sep = rng.randint(4, h - 6)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)

        if not _place_in_region(rng, occ, g, template, 1, 0, sep - 1, w, h):
            continue

        for c in range(w):
            g[sep][c] = 9
            occ[sep][c] = True

        n_cand = rng.randint(*ncr)
        kinds = ["match", "distractor"]
        while len(kinds) < n_cand:
            kinds.append(rng.choice(["match", "distractor"]))
        rng.shuffle(kinds)

        matches = 0; distractors = 0
        for kind in kinds:
            if kind == "match":
                rot = rng.choice(sorted(tpl_rots, key=sorted))
                shape = sorted(rot)
            else:
                shape = None
                for _s in range(30):
                    cand = _conn_poly(rng, rng.randint(*szr), md)
                    if not (_rotations(cand) & tpl_rots):
                        shape = cand; break
                if shape is None:
                    continue
            color = rng.choice(_CAND_COLORS)
            if _place_in_region(rng, occ, g, shape, color, sep + 1, h - 1, w, h):
                if kind == "match":
                    matches += 1
                else:
                    distractors += 1
        if matches >= 1 and distractors >= 1:
            return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: separator row of color-9 present; color-1 template above; candidates below."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    sep_row = next((r for r in range(h) if all(grid[r][c] == 9 for c in range(w))), None)
    if sep_row is None:
        errs.append("no full color-9 separator row found")
        return errs
    c1 = any(grid[r][c] == 1 for r in range(sep_row) for c in range(w))
    cands = any(grid[r][c] != 0 for r in range(sep_row + 1, h) for c in range(w))
    if not c1:
        errs.append("no color-1 template cells above separator")
    if not cands:
        errs.append("no candidate cells below separator")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 13, 0)

    def _paint_t(gg, r, c, color):
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 1)]:
            gg[r + dr][c + dc] = color

    if name == "no_template":
        for c in range(13):
            g[5][c] = 9
        g[8][4] = 4
        return g
    if name == "no_candidates":
        for c in range(13):
            g[5][c] = 9
        _paint_t(g, 1, 3, 1)
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(13):
                g[r][c] = 9
        return g
    return g
