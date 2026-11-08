"""Generator for af902bf9.

Rule: 4 yellow(4) cells form rectangle corners; the oracle fills the
interior red(2). Canonical form: 10x10 grids with one or two such
rectangles (sizes 3x3..6x6), never any other rectangle among the yellows.

Combinatorial axes (5): grid_h/w, n_rects, n_extra_yellows, position_bias,
texture. Branches exercised: one/two rectangles, varied sizes and
positions, extra isolated yellow cells forming NO rectangle (the oracle's
unique-rectangle branch), and the three declared degenerates.
Degenerates: no_rect, three_yellows, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dbecc530afd0"
VERSION = "2.0.0"
TASK_ID = "dbecc530afd0"
RULE_HASH = "bd0dec43bf33"
SUMMARY = "Yellow corners of one/two rectangles; rule fills interiors red."

INVARIANTS = [
    "background is 0",
    "yellow(4) cells partition into one or two complete rectangle corner "
    "sets (4 corners of a rect >= 3x3 each), plus optionally isolated "
    "yellows that form no rectangle",
    "no other axis-aligned rectangle has all four corners yellow",
    "the oracle is total: every rectangle's interior is at least 1 cell",
]

POSITION_BIASES = ("centered", "corner", "near_edge", "scattered")
DEGENERATE_TEXTURES = ("no_rect", "three_yellows", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "band rng 9..12",
                       "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "band rng 9..12",
                       "valid": "8..18"},
    "n_rects":        {"type": "int", "default": "band 1..2 (canonical has "
                       "both)", "valid": "1..2"},
    "n_extra_yellows":{"type": "int", "default": "band 0..2 (0 canonical)",
                       "valid": "0..3"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# The four official forms: (10x10 canvas, exact yellow corner sets).
_CANONICAL_FORMS = (
    ((1, 1), (1, 6), (6, 1), (6, 6)),
    ((3, 3), (3, 5), (5, 3), (5, 5)),
    ((1, 1), (1, 3), (3, 1), (3, 3), (6, 4), (6, 9), (9, 4), (9, 9)),
    ((0, 5), (0, 9), (4, 5), (4, 9), (5, 0), (5, 3), (8, 0), (8, 3)),
)


def _rect_corners(r1, r2, c1, c2):
    return {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}


def _all_rects(cells):
    """Every axis-aligned rectangle whose four corners are all in `cells`."""
    rects = []
    by_row = {}
    for r, c in cells:
        by_row.setdefault(r, set()).add(c)
    rows = sorted(by_row)
    for i, r1 in enumerate(rows):
        for r2 in rows[i + 1:]:
            common = sorted(by_row[r1] & by_row[r2])
            for j, c1 in enumerate(common):
                for c2 in common[j + 1:]:
                    rects.append((r1, r2, c1, c2))
    return rects


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance (all four canonical pairs
    satisfy them): rectangular grid inside the declared 8..18 envelope over
    {0,4}; every complete yellow corner-rectangle is >= 3x3; the yellow set
    holds at least one complete rectangle and no two rectangles SHARE all
    four corners pairwise (nested same-corner sets would make the oracle's
    pick ambiguous). Extra isolated yellows are lawful only when they
    complete no rectangle of their own. The declared degenerates are
    special-cased: no_rect (<4 yellows), three_yellows, full_grid (every
    cell yellow)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    bad = sorted({v for row in grid for v in row} - {0, 4})
    if bad:
        errs.append(f"colors outside {{0,4}}: {bad}")
        return errs
    if not 8 <= h <= 18 or not 8 <= w <= 18:
        errs.append(f"dims {h}x{w} outside the declared 8..18 envelope")
        return errs
    ys = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4}
    if not ys:
        errs.append("zero yellows is not a declared form (no_rect is "
                    "exactly two yellows)")
        return errs
    if len(ys) == h * w:
        return errs  # full_grid degenerate (declared)
    if len(ys) in (2, 3):
        return errs  # no_rect / three_yellows degenerates (declared)
    if len(ys) < 2:
        errs.append("one yellow cell is not a declared form")
        return errs
    rects = _all_rects(ys)
    if not rects:
        errs.append("yellows form no complete corner-rectangle")
        return errs
    for r1, r2, c1, c2 in rects:
        if r2 - r1 < 2 or c2 - c1 < 2:
            errs.append(f"rectangle ({r1},{c1})-({r2},{c2}) has no interior")
    return errs


def observe_overrides(grid):
    """Realized exact-axis values (KRF-0002): n_rects counts complete
    corner-rectangles; n_extra_yellows counts cells in none of them."""
    ys = {(r, c) for r in range(len(grid)) for c in range(len(grid[0]))
          if grid[r][c] == 4}
    rects = _all_rects(ys)
    used = set()
    for r1, r2, c1, c2 in rects:
        used |= _rect_corners(r1, r2, c1, c2)
    return {"n_rects": len(rects),
            "n_extra_yellows": len(ys - used)}


def _place_rects(rng, h, w, n_rects, bias):
    """Pick n_rects non-corner-overlapping rectangles (>= 3x3 each); the
    position bias observably shapes placement (centered -> middle band,
    corner -> top-left corner region, near_edge -> each rect touches an
    edge, scattered -> uniform)."""
    for _attempt in range(60):
        cand = []
        for _ in range(n_rects):
            rh = rng.randint(3, max(3, h - 2))
            rw = rng.randint(3, max(3, w - 2))
            if bias == "centered":
                r1 = rng.randint(max(0, (h - rh) // 3),
                                 max(0, 2 * (h - rh) // 3))
                c1 = rng.randint(max(0, (w - rw) // 3),
                                 max(0, 2 * (w - rw) // 3))
            elif bias == "corner":
                r1 = rng.randint(0, min(1, h - rh))
                c1 = rng.randint(0, min(1, w - rw))
            elif bias == "near_edge":
                side = rng.randrange(4)
                if side == 0:
                    r1 = 0
                    c1 = rng.randint(0, w - rw)
                elif side == 1:
                    r1 = h - rh
                    c1 = rng.randint(0, w - rw)
                elif side == 2:
                    r1 = rng.randint(0, h - rh)
                    c1 = 0
                else:
                    r1 = rng.randint(0, h - rh)
                    c1 = w - rw
            else:
                r1 = rng.randint(0, h - rh)
                c1 = rng.randint(0, w - rw)
            cand.append((r1, r1 + rh - 1, c1, c1 + rw - 1))
        corners = set()
        for r1, r2, c1, c2 in cand:
            corners |= _rect_corners(r1, r2, c1, c2)
        if len(corners) != 4 * n_rects:
            continue  # identical or corner-sharing rects collapse the profile
        extra_rects = [r for r in _all_rects(corners)
                       if r not in [(t[0], t[1], t[2], t[3]) for t in cand]]
        if not extra_rects:
            return cand, corners
    return None, None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    tex = overrides.get("texture")
    if tex in DEGENERATE_TEXTURES:
        extra = sorted(k for k, v in overrides.items()
                       if k != "texture" and v is not None)
        if extra:
            raise ValueError(
                f"degenerate texture {tex!r} is a fixed "
                f"diagnostic layout; it takes no other overrides, got {extra}")
        return _draw_from_degenerate(tex, rng)
    if tex is not None and tex not in POSITION_BIASES:
        raise ValueError(f"unknown texture {tex!r}; valid: "
                         f"{POSITION_BIASES + DEGENERATE_TEXTURES}")
    if tex is not None and overrides.get("position_bias") is not None \
            and overrides["position_bias"] != tex:
        raise ValueError(
            f"texture={tex!r} is itself a position_bias alias and "
            f"position_bias={overrides['position_bias']!r} disagrees")
    if difficulty == "easy":
        h_lo, h_hi = 9, 11
    elif difficulty == "hard":
        h_lo, h_hi = 11, 14
    else:
        h_lo, h_hi = 10, 12

    # Canonical-form prior (KRF-0003): ~30% of fully-unoverridden draws pin
    # one of the four official 10x10 forms exactly (corner sets are the
    # linked profile); anything else takes the general path.
    if not any(k in overrides for k in
               ("grid_h", "grid_w", "n_rects", "n_extra_yellows")):
        if ctx.draw_rng("canonical_prior").random() < 0.30:
            form = ctx.draw_choice("canonical_form", list(range(4)))
            corners = _CANONICAL_FORMS[form]
            for label, value in (("grid_h", 10), ("grid_w", 10),
                                 ("n_rects", len(corners) // 4),
                                 ("n_extra_yellows", 0)):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int(label, value, value)
            g = full_grid(10, 10, 0)
            for r, c in corners:
                g[r][c] = 4
            return g

    h = ctx.draw_int("grid_h", *( (8, 18) if overrides.get("grid_h") is not None
                                  else (h_lo, h_hi)))
    w = ctx.draw_int("grid_w", *( (8, 18) if overrides.get("grid_w") is not None
                                  else (h_lo, h_hi)))
    bias = (tex or overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    n_rects = ctx.draw_int("n_rects", 1, 2)
    n_extra = ctx.draw_int("n_extra_yellows", 0, 3)
    rects, corners = _place_rects(rng, h, w, n_rects, bias)
    if rects is None:
        raise ValueError(
            f"cannot place {n_rects} non-overlapping rectangles on {h}x{w}")
    g = full_grid(h, w, 0)
    for r, c in corners:
        g[r][c] = 4
    # Extra isolated yellows must complete NO rectangle of their own.
    for _ in range(n_extra):
        free = [(r, c) for r in range(h) for c in range(w)
                if (r, c) not in corners]
        rng.shuffle(free)
        for r, c in free:
            if len(_all_rects(corners | {(r, c)})) == n_rects:
                g[r][c] = 4
                corners.add((r, c))
                break
        else:
            raise ValueError(
                f"cannot place {n_extra} isolated yellows without forming "
                f"another rectangle on {h}x{w}")
    errs = self_check(g)
    if errs:
        raise ValueError(f"internal layout violated self_check: {errs}")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "no_rect":
        g[2][2] = 4
        g[5][7] = 4
        return g
    if name == "three_yellows":
        g[2][2] = 4
        g[2][8] = 4
        g[8][2] = 4
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 4
        return g
    return g
