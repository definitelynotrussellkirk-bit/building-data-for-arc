"""Generator for d09fae8197f6 (ARC task 79369cc6) -- template-match stamping in dense noise.

Rule (canonical): the bounding box of the yellow(4) cells IS the template
(always 3x3 in the demos: color-4 body cells plus color-6 marker cells, no
holes). For each of the 8 dihedral orientations of the template, slide it
over the grid -- positions may overhang the bottom/right edge by one row or
column. A position matches when every in-bounds template-6 cell sits on a
grid-6 cell, no in-bounds template-4 cell sits on a grid-6 cell, and at
least 2 template-6 cells hit a grid-6. On a match, every in-bounds
template-4 cell is painted 4.

Canonical demos are DENSE: a 12..19 x 12..19 field of noise colors 0/1/8
with magenta 6s scattered at ~10-13%, plus exactly one 3x3 template whose
yellows live nowhere else. Matches emerge from the noise (3..18 cells
stamped per demo). The generator reproduces that field and additionally
PLANTS 1..3 guaranteed match windows (an orientation's 6-pattern with non-6
cells under its 4-positions) so every draw fires the rule at least once.

Combinatorial axes: grid_h, grid_w, mag_count, template_r, template_c,
noise_6_pct, texture. Planted-match count/orientations/positions are
internal draws (not exactly observable from a returned grid, so not
declared axes per KRF-0002).
Branches witnessed: emergent noise matches, planted matches in all 8
orientations, bottom/right edge-overhang matches, template touching any
edge, varied noise proportions (modal color 0, 1, or 8).
Degenerates: minimal, no_noise, edge_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d09fae8197f6"
VERSION = "3.1.0"  # canonical-profile prior (exact dim set, {0,1} modal, exact density, 1 non-edge plant) for the strict empirical-manifold conjunction; generalized/edge branches retained
TASK_ID = "d09fae8197f6"
RULE_HASH = "be26cdb395f0"
SUMMARY = (
    "Dense field (h 12..22, w 12..22) of noise colors 0/1/8 with magenta-6 "
    "cells at ~6..16% and exactly one 3x3 template (yellow-4 body + "
    "magenta-6 markers, 3..5 markers, yellows spanning the bbox; yellow "
    "appears nowhere else). Rule: for every dihedral orientation of the "
    "template, stamp its yellow cells wherever its magenta pattern matches "
    "grid 6s (>=2 hits, no conflicts; bottom/right 1-cell overhang "
    "allowed). The generator plants 1..3 guaranteed match windows in the "
    "noise so the rule always fires; emergent noise matches add more, "
    "matching the canonical 3..18 stamped-cell range."
)

INVARIANTS = [
    "palette stays within {0, 1, 4, 6, 8} (noise colors 0/1/8; a draw may lack a noise color)",
    "yellow(4) appears only inside the template",
    "the yellow bounding box (the template) is exactly 3x3 and holds only 4/6 cells",
    "the template has 3..5 magenta cells and its yellows span all four bbox edges",
    "noise cells are drawn from {0, 1, 6, 8} only",
    "at least one orientation window matches, so the output differs from the input",
]

DEGENERATE_TEXTURES = ("minimal", "no_noise", "edge_match")
HELPFUL_TEXTURES = ()

AXES = {
    "grid_h":      {"type": "int", "default": "band rng 12..22", "valid": "12..22"},
    "grid_w":      {"type": "int", "default": "band rng 12..22", "valid": "12..22"},
    "mag_count":   {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "template_r":  {"type": "int", "default": "rng 0..h-3", "valid": "0..19"},
    "template_c":  {"type": "int", "default": "rng 0..w-3", "valid": "0..19"},
    "noise_6_pct": {"type": "float", "default": "rng 0.08..0.13",
                    "valid": "0.06..0.16"},
    "texture":     {"type": "str", "default": "none",
                    "valid": "|".join(DEGENERATE_TEXTURES)},
}

_DIRS8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


def _rot_cw(shape):
    return [list(row) for row in zip(*shape[::-1])]


def _flip_lr(shape):
    return [list(reversed(row)) for row in shape]


def _orientations(shape):
    variants = [shape]
    for _ in range(3):
        variants.append(_rot_cw(variants[-1]))
    variants.append(_flip_lr(shape))
    for _ in range(3):
        variants.append(_rot_cw(variants[-1]))
    return variants


def _make_template(rng, k):
    """3x3 of 4/6 with exactly k magenta cells and yellows spanning all
    four bbox edges (so the yellow bbox IS the whole 3x3 -- the rule takes
    the yellow bbox as the template)."""
    allc = [(r, c) for r in range(3) for c in range(3)]
    for _ in range(300):
        mag = frozenset(rng.sample(allc, k))
        yells = [p for p in allc if p not in mag]
        rs = [r for r, c in yells]
        cs = [c for r, c in yells]
        if min(rs) == 0 and max(rs) == 2 and min(cs) == 0 and max(cs) == 2:
            return [[6 if (r, c) in mag else 4 for c in range(3)] for r in range(3)]
    return None


def _yellow_bbox(grid):
    ys = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4]
    if not ys:
        return None
    return (min(r for r, c in ys), min(c for r, c in ys),
            max(r for r, c in ys), max(c for r, c in ys))


def _rule_output(grid):
    """Independent Python re-implementation of the canonical oracle:
    yellow bbox = template; 8 dihedral orientations slide over the grid
    (bottom/right 1-cell overhang allowed); a window matches when no
    in-bounds template-6 sits on a non-6, no in-bounds template-4 sits on
    a 6, and >=2 template-6 cells hit a 6; matches paint template-4 cells 4."""
    h, w = len(grid), len(grid[0])
    bbox = _yellow_bbox(grid)
    if bbox is None:
        return [row[:] for row in grid]
    r1, c1, r2, c2 = bbox
    template = [[grid[r][c] if grid[r][c] in (4, 6) else -1
                 for c in range(c1, c2 + 1)] for r in range(r1, r2 + 1)]
    out = [row[:] for row in grid]
    for tmpl in _orientations(template):
        th, tw = len(tmpl), len(tmpl[0])
        for r in range(0, min(h, h + 2 - th)):
            for c in range(0, min(w, w + 2 - tw)):
                mag_hits = 0
                mismatch = False
                for tr in range(th):
                    for tc in range(tw):
                        gr, gc = r + tr, c + tc
                        if not (0 <= gr < h and 0 <= gc < w):
                            continue
                        tv = tmpl[tr][tc]
                        if tv == 6:
                            if grid[gr][gc] == 6:
                                mag_hits += 1
                            else:
                                mismatch = True
                        elif tv == 4 and grid[gr][gc] == 6:
                            mismatch = True
                if not mismatch and mag_hits >= 2:
                    for tr in range(th):
                        for tc in range(tw):
                            gr, gc = r + tr, c + tc
                            if 0 <= gr < h and 0 <= gc < w and tmpl[tr][tc] == 4:
                                out[gr][gc] = 4
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared 12..22 envelope on both axes; palette within {0,1,4,6,8}
    (a draw may lack a noise color, e.g. the no_noise texture); at least
    one yellow(4) cell (the oracle indexes the yellow bbox and crashes on
    an empty one); the yellow bbox is exactly 3x3 and contains only 4/6
    cells with 3..5 magentas and yellows spanning all four edges; noise
    colors outside the template come from {0,1,6,8} only; and the rule
    visibly fires (some orientation window stamps at least one new 4, so
    identity/no-op instances are rejected along with destructive template
    or palette mutations)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 22 or w > 22:
        errs.append(f"outside declared 12..22 envelope: {h}x{w}")
    if h < 12 or w < 12:
        errs.append(f"below 12x12 canonical floor: {h}x{w}")
    flat = [v for row in grid for v in row]
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for v in flat):
        errs.append("color outside 0..9")
    if set(flat) - {0, 1, 4, 6, 8}:
        errs.append("palette outside {0, 1, 4, 6, 8}")
    if errs:
        return errs
    bbox = _yellow_bbox(grid)
    if bbox is None:
        return ["no yellow cells: oracle cannot build a template"]
    r1, c1, r2, c2 = bbox
    if r2 - r1 != 2 or c2 - c1 != 2:
        errs.append(f"yellow bbox is {r2 - r1 + 1}x{c2 - c1 + 1}, not 3x3")
        return errs
    tmpl = [[grid[r][c] for c in range(c1, c2 + 1)] for r in range(r1, r2 + 1)]
    if any(v not in (4, 6) for row in tmpl for v in row):
        errs.append("template bbox contains a non-4/6 cell (canonical has none)")
    mag = sum(1 for row in tmpl for v in row if v == 6)
    if not 3 <= mag <= 5:
        errs.append(f"template has {mag} magentas, outside canonical 3..5")
    yells = [(r, c) for r in range(3) for c in range(3) if tmpl[r][c] == 4]
    if yells:
        if not (min(r for r, c in yells) == 0 and max(r for r, c in yells) == 2
                and min(c for r, c in yells) == 0 and max(c for r, c in yells) == 2):
            errs.append("template yellows do not span all four bbox edges")
    if errs:
        return errs
    if _rule_output(grid) == grid:
        errs.append("identity draw: no orientation window stamps a new 4")
    return errs


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0001/0002),
    derived from the grid itself: the template top-left is the yellow bbox
    corner; mag_count is the number of 6 cells inside that bbox."""
    bbox = _yellow_bbox(grid)
    if bbox is None:
        return {"mag_count": 0, "template_r": -1, "template_c": -1}
    r1, c1, r2, c2 = bbox
    mag = sum(1 for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
              if grid[r][c] == 6)
    return {"mag_count": mag, "template_r": r1, "template_c": c1}


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; an override must execute exactly on any
    band, so it is validated against the full declared range (KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _band_params(difficulty):
    """(h range, w range, planted-match count, edge-plant probability,
    canonical-profile prior probability). The prior draws reproduce the
    exact official profile -- one of the four canonical dimension pairs,
    one non-edge planted match, realized magenta density 0.097..0.125, and
    the modal noise color forced to 0 or 1 -- while generalized grids,
    edge-overhang plants, and wider density/noise branches stay available."""
    if difficulty == "easy":
        return (12, 16), (12, 16), 1, 0.0, 0.5
    if difficulty == "hard":
        return (16, 22), (16, 22), (2, 3), 0.25, 0.35
    return (14, 19), (13, 17), (1, 2), 0.15, 0.5     # medium / default


_CANONICAL_DIMS = ((18, 16), (19, 12), (17, 17), (16, 15))


def _noise_field(rng, h, w, p6):
    """Dense canonical-style noise: 6 at probability p6; the remaining mass
    split randomly between 0, 1 and 8 (proportions vary per draw, so the
    modal noise color varies across {0,1,8} like the canonical demos)."""
    rest = 1.0 - p6
    p0 = rng.uniform(0.25, 0.45) * rest
    p1 = rng.uniform(0.20, 0.40) * rest
    g = full_grid(h, w, 0)
    for r in range(h):
        row = g[r]
        for c in range(w):
            u = rng.random()
            if u < p6:
                row[c] = 6
            elif u < p6 + p0:
                row[c] = 0
            elif u < p6 + p0 + p1:
                row[c] = 1
            else:
                row[c] = 8
    return g


def _canonicalize_noise(g, rng, h, w, protected):
    """Canonical-profile noise geometry (default-prior draws): the realized
    total magenta count lands exactly in [0.097, 0.125] of the grid, and the
    modal noise color is forced to 0 or 1 (the canonical demos' modals).
    Only unprotected noise cells are flipped -- the template and planted
    match windows keep their match semantics; 4/6 cell classes never change,
    so planted matches and the template survive intact."""
    modal_target = rng.choice((0, 1))
    cells = [(r, c) for r in range(h) for c in range(w)
             if (r, c) not in protected]
    lo = -(-(int(0.097 * h * w * 1000)) // 1000)     # ceil(0.097 * h * w)
    hi = int(0.125 * h * w)                          # floor(0.125 * h * w)
    target_total = rng.randint(lo, max(lo, hi))
    # the strict density counts TOTAL magenta (template + planted + noise)
    protected_six = sum(1 for (r, c) in protected if g[r][c] == 6)
    target = max(0, target_total - protected_six)
    sixes = [(r, c) for (r, c) in cells if g[r][c] == 6]
    while len(sixes) < target:
        pool = [(r, c) for (r, c) in cells
                if g[r][c] in (0, 1, 8) and g[r][c] != modal_target]
        if not pool:
            break
        r, c = pool[rng.randrange(len(pool))]
        g[r][c] = 6
        sixes.append((r, c))
    while len(sixes) > target:
        r, c = sixes.pop(rng.randrange(len(sixes)))
        g[r][c] = modal_target
    # modal enforcement: modal_target strictly outnumbers both other channels
    for _ in range(2 * h * w):
        cnt = {v: sum(1 for (r, c) in cells if g[r][c] == v) for v in (0, 1, 8)}
        rivals = [v for v in (0, 1, 8) if v != modal_target]
        top = max(rivals, key=lambda v: cnt[v])
        if cnt[modal_target] > cnt[top]:
            return
        pool = [(r, c) for (r, c) in cells if g[r][c] == top]
        r, c = pool[rng.randrange(len(pool))]
        g[r][c] = modal_target


def _plant_match(g, rng, template, boxes, edge):
    """Plant one guaranteed match window: pick a dihedral orientation and a
    3x3 window (optionally overhanging the bottom/right edge by one cell,
    which the rule's extended scan range covers), disjoint from every box in
    `boxes`; set template-6 cells to 6 and template-4 cells to a non-6
    noise color. Returns the window box or None after bounded retries."""
    h, w = len(g), len(g[0])
    variants = _orientations(template)
    for _try in range(200):
        o = rng.randint(0, 7)
        tmpl = variants[o]
        if edge:
            side = rng.random() < 0.5
            if side and h >= 4:
                r, c = h - 2, rng.randint(0, w - 3)
                over_rows = {2}
                over_cols = set()
            elif not side and w >= 4:
                r, c = rng.randint(0, h - 3), w - 2
                over_rows, over_cols = set(), {2}
            else:
                continue
            # the overhung row/col must leave >=2 magentas in bounds
            in_mag = sum(1 for tr in range(3) for tc in range(3)
                         if tmpl[tr][tc] == 6 and tr not in over_rows
                         and tc not in over_cols)
            if in_mag < 2:
                continue
        else:
            r = rng.randint(0, h - 3)
            c = rng.randint(0, w - 3)
            over_rows, over_cols = set(), set()
        if any(not (r + 2 < br or br + 2 < r or c + 2 < bc or bc + 2 < c)
               for br, bc in boxes):
            continue
        for tr in range(3):
            for tc in range(3):
                gr, gc = r + tr, c + tc
                if not (0 <= gr < h and 0 <= gc < w):
                    continue
                tv = tmpl[tr][tc]
                if tv == 6:
                    g[gr][gc] = 6
                else:
                    g[gr][gc] = rng.choice((0, 1, 8))
        box = (r, c)
        boxes.append(box)
        return box
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    if texture is not None:
        if texture in DEGENERATE_TEXTURES:
            extra = sorted(k for k, v in overrides.items()
                           if k != "texture" and v is not None)
            if extra:
                raise ValueError(
                    f"degenerate texture {texture!r} is a fixed diagnostic "
                    f"layout; it takes no other overrides, got {extra}")
            return _draw_from_degenerate(texture, rng)
        raise ValueError(f"unknown texture {texture!r}; "
                         f"valid: {DEGENERATE_TEXTURES}")

    hr, wr, planted_spec, edge_p, p_canon = _band_params(difficulty)
    canon = ctx.draw_rng("canon_prior").random() < p_canon

    # Template position vs grid dims: an explicit position forces the grid
    # to fit it (or fails loudly when both are pinned incompatibly). The
    # canonical-profile prior draws an exact canonical dimension pair for
    # any dimension the caller did not pin.
    tr_ov = overrides.get("template_r")
    tc_ov = overrides.get("template_c")
    if canon and (tr_ov is None and tc_ov is None
                  and overrides.get("grid_h") is None
                  and overrides.get("grid_w") is None):
        # exact canonical pair, always inside the declared 12..22 envelope.
        # KRF-0004 provenance: record the chosen dimensions through dedicated
        # keyed draws (typed override injection; no RNG consumed).
        h, w = _CANONICAL_DIMS[rng.randrange(len(_CANONICAL_DIMS))]
        ctx.overrides["grid_h"] = h
        ctx.draw_int("grid_h", 12, 22)
        ctx.overrides["grid_w"] = w
        ctx.draw_int("grid_w", 12, 22)
    else:
        h = _banded_int(ctx, overrides, "grid_h",
                        max(hr[0], (tr_ov or 0) + 3), max(hr[1], (tr_ov or 0) + 3),
                        12, 22)
        w = _banded_int(ctx, overrides, "grid_w",
                        max(wr[0], (tc_ov or 0) + 3), max(wr[1], (tc_ov or 0) + 3),
                        12, 22)
    tr = ctx.draw_int("template_r", 0, 19) if tr_ov is not None \
        else ctx.draw_int("template_r", 0, h - 3)
    tc = ctx.draw_int("template_c", 0, 19) if tc_ov is not None \
        else ctx.draw_int("template_c", 0, w - 3)
    if tr > h - 3 or tc > w - 3:
        raise ValueError(
            f"template position ({tr}, {tc}) needs grid >= {tr + 3}x{tc + 3}, "
            f"got {h}x{w}")
    k = _banded_int(ctx, overrides, "mag_count", 3, 5, 3, 5)
    p6_ov = overrides.get("noise_6_pct")
    if p6_ov is not None:
        p6 = float(p6_ov)
        if not 0.06 <= p6 <= 0.16:
            raise ValueError(f"noise_6_pct must lie in [0.06, 0.16], got {p6_ov}")
    else:
        p6 = ctx.draw_rng("noise_6_pct").uniform(0.08, 0.13)
    n_planted = (1 if canon else
                 (planted_spec if isinstance(planted_spec, int)
                  else rng.randint(*planted_spec)))
    edge_p_eff = 0.0 if canon else edge_p

    template = _make_template(rng, k)
    if template is None:
        raise ValueError(f"could not build a spanning 3x3 template (k={k})")
    # Planted windows and the template add their own magentas; discount the
    # noise budget so the realized magenta density stays near p6 (canonical
    # demos run 9.7..12.5% total magenta).
    p6_eff = max(0.02, p6 - (n_planted * k + k) / (h * w))
    g = _noise_field(rng, h, w, p6_eff)
    for r in range(3):
        for c in range(3):
            g[tr + r][tc + c] = template[r][c]

    boxes = [(tr, tc)]
    for i in range(n_planted):
        edge = rng.random() < edge_p_eff
        if _plant_match(g, rng, template, boxes, edge) is None:
            if i == 0:
                raise ValueError(f"could not plant a match window on {h}x{w}")
            break

    if canon and p6_ov is None:
        # Canonical-profile prior: exact realized density 0.097..0.125 and a
        # {0,1} modal noise color; template + planted windows are protected.
        protected = {(tr + r, tc + c) for r in range(3) for c in range(3)}
        for (br, bc) in boxes[1:]:
            protected |= {(br + r, bc + c) for r in range(3) for c in range(3)}
        _canonicalize_noise(g, rng, h, w, protected)

    errs = self_check(g, difficulty=difficulty)
    if errs:
        raise ValueError(f"internal layout violated self_check: {errs}")
    return g


def _draw_from_degenerate(name, rng):
    """Fixed minimal layouts; every one is a lawful, self_check-clean draw."""
    template = [[6, 4, 6],
                [4, 6, 4],
                [4, 4, 6]]
    if name == "minimal":
        g = _noise_field(rng, 12, 12, 0.09)
        for r in range(3):
            for c in range(3):
                g[3 + r][3 + c] = template[r][c]
        boxes = [(3, 3)]
        _plant_match(g, rng, template, boxes, False)
        return g
    if name == "no_noise":
        g = full_grid(12, 12, 0)
        for r in range(3):
            for c in range(3):
                g[1 + r][1 + c] = template[r][c]
        boxes = [(1, 1)]
        _plant_match(g, rng, template, boxes, False)
        _plant_match(g, rng, template, boxes, False)
        return g
    if name == "edge_match":
        g = _noise_field(rng, 14, 14, 0.10)
        for r in range(3):
            for c in range(3):
                g[2 + r][2 + c] = template[r][c]
        boxes = [(2, 2)]
        if _plant_match(g, rng, template, boxes, True) is None:
            _plant_match(g, rng, template, boxes, False)
        return g
    raise ValueError(f"unknown degenerate texture {name!r}")
