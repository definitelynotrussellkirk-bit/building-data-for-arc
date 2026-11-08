"""Generator for arc_puzzle_bank_21_set13_s:S13_H1 — dual legend chooses holes and symmetry.

Rule (verified from canonical Racket): ROW 0's count of colour-1 cells sets a
holes-target (count - 1); ROW 1's count of colour-2 cells sets a symmetry-target
via a fixed map (1->col, 2->row, 3->both, else->none). The BODY (rows 2+) holds
several shape components; the rule outputs the first (reading order) whose number
of enclosed holes equals the holes-target AND whose symmetry class equals the
symmetry-target, cropped and recoloured 8.

The previous body was the generic scatter template; its random shapes almost
never matched the (holes, symmetry) the legend asked for, so `(first (filter ...))`
crashed (~1/11). This rewrite CONSTRUCTS a legend plus a target component with the
exact holes + symmetry the legend selects, and a non-matching decoy.

Axes: which (holes, symmetry) combo, shape sizes, positions, decoy.
Degenerates: no_match, two_matches, solid_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "50190b6e8882"
RULE_HASH = "523776ad163c"  # canonical rule this generator was written against
# 2.3.0: defect-lint all_background_output — a (0,3) target could be a SOLID rect
# (both-symmetric, zero holes), whose recolored mask output is a featureless
# block. The TARGET shape is now redrawn until non-solid (plus-shape fallback);
# decoys may stay solid. (2.2.0: placement fail/redo + legend invariants.)
VERSION = "2.3.0"
TASK_ID = "50190b6e8882"

SUMMARY = ("Row 0 (colour-1 count) sets a holes-target; row 1 (colour-2 count) sets a symmetry "
           "class; the body holds shapes and the rule outputs the one matching both, recoloured "
           "8. The selected (holes, symmetry) combo, shape sizes and positions vary.")

INVARIANTS = [
    "row 0 holds (holes-target + 1) colour-1 cells; row 1 encodes the symmetry target",
    "the body contains exactly one component matching the (holes, symmetry) the legend selects",
    "decoy components differ in hole-count or symmetry class",
]

DEGENERATE_TEXTURES = ("no_match", "two_matches", "solid_only")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_w":     {"type": "int", "default": "rng 12..16", "valid": "9..20"},
    "combo":      {"type": "int", "default": "rng 0..5 (holes/sym combo)", "valid": "0..5"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|no_match|two_matches|solid_only"},
}

# (holes, sym-class): sym 3=both, 1=row-only, 2=col-only, 0=none. All pairs distinct.
_COMBOS = [(0, 3), (1, 3), (2, 3), (0, 1), (0, 2), (0, 0)]
# K2 (colour-2 count in row 1) that makes wanted-sym yield each sym class
_SYM_TO_K2 = {1: 2, 2: 1, 3: 3, 0: 4}


_FALLBACK = {
    (0, 3): [(r, c) for r in range(2) for c in range(3)],
    (1, 3): [(r, c) for r in range(3) for c in range(3) if r in (0, 2) or c in (0, 2)],
    (2, 3): ([(0, c) for c in range(5)] + [(1, 0), (1, 2), (1, 4)] + [(2, c) for c in range(5)]),
    (0, 1): [(0, 0), (1, 0), (1, 1), (2, 0)],
    (0, 2): [(0, 0), (0, 1), (0, 2), (1, 1)],
    (0, 0): [(0, 0), (1, 0), (1, 1)],
}


def _nrm(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return sorted((r - r0, c - c0) for (r, c) in cells)


def _connected(cells):
    s = set(cells); start = next(iter(s)); seen = {start}; stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p = (r + dr, c + dc)
            if p in s and p not in seen:
                seen.add(p); stack.append(p)
    return len(seen) == len(s)


def _holes(cells):
    s = set(_nrm(cells)); H = max(r for r, _ in s) + 1; W = max(c for _, c in s) + 1
    bg = {(r, c) for r in range(H) for c in range(W) if (r, c) not in s}
    seen = set(); n = 0
    for cell in bg:
        if cell in seen:
            continue
        stack = [cell]; seen.add(cell); region = []
        while stack:
            p = stack.pop(); region.append(p)
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                q = (p[0] + dr, p[1] + dc)
                if q in bg and q not in seen:
                    seen.add(q); stack.append(q)
        if all(0 < r < H - 1 and 0 < c < W - 1 for r, c in region):
            n += 1
    return n


def _symclass(cells):
    s = set(_nrm(cells)); H = max(r for r, _ in s) + 1; W = max(c for _, c in s) + 1
    rsym = all((H - 1 - r, c) in s for (r, c) in s)
    csym = all((r, W - 1 - c) in s for (r, c) in s)
    return (3 if rsym and csym else 1 if rsym else 2 if csym else 0)


def _gen_candidate(rng, sym, holes):
    """Build a shape biased toward the requested symmetry/holes (verified later)."""
    if sym == 0:                                # random asymmetric blob
        mh, mw = rng.randint(2, 4), rng.randint(2, 4)
        cells = {(rng.randint(0, mh - 1), rng.randint(0, mw - 1))}
        for _ in range(rng.randint(3, 7)):
            r, c = rng.choice(tuple(cells)); dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            if 0 <= r + dr < mh and 0 <= c + dc < mw:
                cells.add((r + dr, c + dc))
        return _nrm(cells)
    # symmetric: build a filled rectangle, optionally bumped, then mirror + poke holes
    hh = rng.randint(2, 5); ww = rng.randint(2, 5)
    base = {(r, c) for r in range(hh) for c in range(ww)}
    if sym in (1, 3):                           # ensure row-symmetry
        base = {(r, c) for (r, c) in base} | {(hh - 1 - r, c) for (r, c) in base}
    if sym in (2, 3):                           # ensure col-symmetry
        base = base | {(r, ww - 1 - c) for (r, c) in base}
    if sym == 1 and ww >= 3:                    # break col-symmetry (bump one side)
        base.add((rng.randint(0, hh - 1), ww))
        base = {(r, c) for (r, c) in base} | {(hh - 1 - r, c) for (r, c) in base}
    if sym == 2 and hh >= 3:                    # break row-symmetry
        base.add((hh, rng.randint(0, ww - 1)))
        base = base | {(r, ww - 1 - c) for (r, c) in base}
    cells = set(_nrm(base))
    H = max(r for r, _ in cells) + 1; W = max(c for _, c in cells) + 1
    # poke symmetric interior holes to hit the holes target
    interior = [(r, c) for (r, c) in cells if 0 < r < H - 1 and 0 < c < W - 1]
    rng.shuffle(interior)
    poked = 0
    for (r, c) in interior:
        if poked >= holes:
            break
        group = {(r, c)}
        if sym in (1, 3):
            group.add((H - 1 - r, c))
        if sym in (2, 3):
            group |= {(rr, W - 1 - cc) for (rr, cc) in group}
        if group <= cells and len(group) == 1:   # only poke single self-symmetric cells
            cells -= group
            poked += 1
    return _nrm(cells)


def _solid_bbox(cells):
    r1, c1, r2, c2 = _bbox(cells)
    return len(set(cells)) == (r2 - r1 + 1) * (c2 - c1 + 1)


def _shape(rng, combo, allow_solid=True):
    """Normalized cell list realising a given (holes, sym-class) combo.

    allow_solid=False rejects bbox-filling shapes — the rule's extracted TARGET
    mask must carry structure, or the recolored output is a featureless block."""
    holes, sym = combo
    for _ in range(200):
        cand = _gen_candidate(rng, sym, holes)
        if (len(cand) >= 3 and _connected(cand) and _holes(cand) == holes
                and _symclass(cand) == sym
                and (allow_solid or not _solid_bbox(cand))):
            return cand
    fb = _FALLBACK[combo]
    if not allow_solid and _solid_bbox(fb):
        # plus shape: both-symmetric, zero holes, never solid
        fb = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
    return fb


def _bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _place(g, cells, r0, c0, color, occupied):
    """Place a normalized shape with a 1-cell halo clear; return True on success."""
    h, w = len(g), len(g[0])
    abs_cells = [(r0 + r, c0 + c) for r, c in cells]
    for (r, c) in abs_cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (r + dr, c + dc) in occupied:
                    return False
    for (r, c) in abs_cells:
        g[r][c] = color
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                occupied.add((r + dr, c + dc))
    return True


def _assemble(combo, decoy_combo, w, rng):
    h_t, s_t = combo
    target = _shape(rng, combo, allow_solid=False)
    decoy = _shape(rng, decoy_combo)
    # body tall enough for the legend (2 rows) + both shapes stacked with gaps
    th = _bbox(target)[2] + 1; dh = _bbox(decoy)[2] + 1
    body_h = th + dh + 5
    h = 2 + body_h
    g = full_grid(h, w, 0)

    # legend: row 0 -> (h_t + 1) colour-1 cells; row 1 -> K2 colour-2 cells
    k1 = h_t + 1
    k2 = _SYM_TO_K2[s_t]
    for c in sorted(rng.sample(range(w), min(k1, w))):
        g[0][c] = 1
    for c in sorted(rng.sample(range(w), min(k2, w))):
        g[1][c] = 2

    # body components (rows 2+), placed with a halo so they stay separate
    occupied = set()
    order = [(target, rng.choice([3, 4, 5, 6, 7, 8, 9])),
             (decoy, rng.choice([3, 4, 5, 6, 7, 8, 9]))]
    rng.shuffle(order)
    for cells, color in order:
        bh = _bbox(cells)[2] + 1; bw = _bbox(cells)[3] + 1
        placed = False
        for _ in range(200):
            r0 = rng.randint(2, h - bh); c0 = rng.randint(0, max(0, w - bw))
            if _place(g, cells, r0, c0, color, occupied):
                placed = True
                break
        if not placed:
            return None
    return g


def _must_assemble(combo, decoy_combo, w, rng):
    for _attempt in range(60):
        g = _assemble(combo, decoy_combo, w, rng)
        if g is not None:
            return g
    raise ValueError("could not place target and decoy components for legend task")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx.draw_rng("degen"))
    if difficulty == "easy":
        w = ctx.draw_int("grid_w", 11, 13)
    elif difficulty == "hard":
        w = ctx.draw_int("grid_w", 14, 18)
    else:
        w = ctx.draw_int("grid_w", 12, 16)
    ci = ctx.draw_int("combo", 0, len(_COMBOS) - 1)
    rng = ctx.draw_rng("layout")

    combo = _COMBOS[ci]
    for _attempt in range(60):
        decoy_combo = rng.choice([c for c in _COMBOS if c != combo])
        g = _assemble(combo, decoy_combo, w, rng)
        if g is not None:
            return g
    raise ValueError("could not place exact legend-match body components")


def _draw_from_degenerate(name, rng):
    if name == "no_match":
        # legend asks for 1 hole but the body has only a solid rect (0 holes)
        g = _must_assemble((0, 3), (0, 0), 13, rng)
        for c in range(len(g[0])):
            g[0][c] = 0
        g[0][0] = 1; g[0][2] = 1
        return g
    if name == "two_matches":
        # two solid rects both match (0,3) -> first in reading order wins
        return _must_assemble((0, 3), (0, 3), 13, rng)
    return _must_assemble((0, 3), (0, 0), 12, rng)            # solid_only


def _body_components(grid):
    """Same-color 4-connected body components below the two legend rows."""
    if len(grid) <= 2:
        return []
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(2, h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 2 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    if len(grid) < 4:
        return ["legend task needs two legend rows plus body components"]
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("grid values must be digits 0..9")
    if any(v not in (0, 1) for v in grid[0]):
        errs.append("row 0 legend should contain only color 1 and background")
    if any(v not in (0, 2) for v in grid[1]):
        errs.append("row 1 legend should contain only color 2 and background")

    holes_target = sum(1 for v in grid[0] if v == 1) - 1
    k2 = sum(1 for v in grid[1] if v == 2)
    k2_to_sym = {v: k for k, v in _SYM_TO_K2.items()}
    sym_target = k2_to_sym.get(k2)
    if holes_target not in (0, 1, 2) or sym_target is None:
        errs.append("legend counts must encode a supported holes/symmetry target")
        return errs

    comps = _body_components(grid)
    if len(comps) < 2:
        errs.append("body should contain target plus at least one decoy component")
    matches = [comp for comp in comps if _holes(comp) == holes_target and _symclass(comp) == sym_target]
    if len(matches) != 1:
        errs.append("body must contain exactly one component matching the legend")
    return errs
