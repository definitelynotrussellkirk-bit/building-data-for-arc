"""Generator for d2de45f40d31 — recolour the candidate panel that matches the source.

Rule (verified from canonical Racket): split on full color-9 columns into a
SOURCE panel (first) and CANDIDATE panels (rest). Compute the four rotations of
the source's occupancy (normalised). The first candidate whose normalised
occupancy equals one of those rotations is recoloured to color 8 (output is that
candidate panel); if none matches the output is blank.

The previous body was the generic "6 panels, find the matching pair" template,
whose random panels rarely matched any rotation of the source, so the rule output
a near-constant blank (rule_smoke distinct_out=4 -- degenerate). This 2.2.0
rewrite CONSTRUCTS valid inputs: a source shape, exactly one candidate that is a
rotated copy of it, and distractor candidates with a DIFFERENT cell count (so
they cannot match). The matched shape (recoloured) varies.

Axes: source shape, candidate count, matched index/rotation, panel size.
Degenerates: min_cands, big_shape, many_cands.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d2de45f40d31"
# 2.4.0: the rule matches a candidate iff `normalize-cells(panel-occ cand)` (a
# SORTED, bbox-shifted list) is list-equal to one of the src's rotation
# variants. But `normalize-cells` does NOT re-sort, and the rotated variants are
# emitted in ROTATED (unsorted) order, while `panel-occ` always sorts the
# candidate -> only the rot0 (un-rotated) variant is list-equal to a sorted
# candidate. 2.3.0 placed the matched candidate ROTATED, so it usually failed to
# match -> blank output (fired 7/24, lint all_background_output). 2.4.0 places
# the matched candidate as an IDENTICAL (un-rotated) copy of the source, which
# reliably equals variant[0], so the recolour always fires.
VERSION = "2.4.0"
TASK_ID = "d2de45f40d31"

SUMMARY = (
    "A source panel and several candidate panels (color-9 columns between); "
    "exactly one candidate is an identical copy of the source, the rest have a "
    "different cell count. Rule: recolour the matching candidate to color 8. "
    "Source shape and candidate count vary."
)

INVARIANTS = [
    "panels SRC then >=2 candidates, all same size, separated by color-9 columns",
    "exactly one candidate's occupancy equals the source occupancy",
    "every other candidate has a different cell count (cannot match)",
]

DEGENERATE_TEXTURES = ("min_cands", "big_shape", "many_cands")
HELPFUL_TEXTURES = ("varied", "wide", "tall")

AXES = {
    "panel_h":    {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "panel_w":    {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "n_cands":    {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "shape_size": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "texture":    {"type": "str", "default": "rng helpful",
                   "valid": "varied|wide|tall|min_cands|big_shape|many_cands"},
}


def _walk(rng, k, hmax, wmax):
    for _ in range(20):
        cells = [(0, 0)]; seen = {(0, 0)}; tries = 0
        while len(cells) < k and tries < 60:
            tries += 1
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nc = (r + dr, c + dc)
            if nc not in seen:
                cells.append(nc); seen.add(nc)
        cells = _norm(cells)
        h, w = _dims(cells)
        if h <= hmax and w <= wmax and len(cells) == k:
            return cells
    return _norm([(0, 0)])


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _rot_cw(cells):
    return _norm([(c, -r) for r, c in cells])


def _rot(cells, k):
    out = list(cells)
    for _ in range(k % 4):
        out = _rot_cw(out)
    return out


def _dims(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _place(g, ph, pw, panel_k, cells, color, rng):
    h, w = _dims(cells)
    base = panel_k * (pw + 1)
    tr = rng.randint(0, max(0, ph - h))
    tc = rng.randint(0, max(0, pw - w))
    for (dr, dc) in cells:
        if tr + dr < ph and tc + dc < pw:
            g[tr + dr][base + tc + dc] = color


def _build(rng, ph, pw, n_cands, k):
    n_cands = max(2, min(n_cands, (30 - (pw + 1)) // (pw + 1)))   # total width <= 30
    n_panels = 1 + n_cands
    W = n_panels * pw + (n_panels - 1)
    g = full_grid(ph, W, 0)
    for kk in range(1, n_panels):
        sc = kk * (pw + 1) - 1
        for r in range(ph):
            g[r][sc] = 9
    src = _walk(rng, k, ph, pw)
    _place(g, ph, pw, 0, src, rng.choice([1, 2, 3, 4, 5, 6, 7]), rng)
    match_idx = rng.randint(0, n_cands - 1)
    for ci in range(n_cands):
        if ci == match_idx:
            # identical (un-rotated) copy: the rule's variant[0] is the only one
            # list-equal to a sorted panel-occ, so only an un-rotated copy
            # reliably matches.
            cells = list(src)
        else:
            kk = k + rng.choice((-1, 1, 2))      # different cell count -> cannot match
            kk = max(1, kk)
            cells = _walk(rng, kk, ph, pw)
        _place(g, ph, pw, 1 + ci, cells, rng.choice([1, 2, 3, 4, 5, 6, 7]), rng)
    return g


def _panels_occ(grid):
    """Per panel (split on full color-9 columns), the sorted, bbox-normalised
    occupancy (non-0, non-9 cells)."""
    h = len(grid); w = len(grid[0])
    divs = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    bounds = []
    start = 0
    for c in range(w + 1):
        if c == w or c in divs:
            if start < c:
                bounds.append((start, c - 1))
            start = c + 1
    occs = []
    for c0, c1 in bounds:
        cells = sorted((r, c - c0) for r in range(h) for c in range(c0, c1 + 1)
                       if grid[r][c] not in (0, 9))
        if cells:
            mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
            cells = sorted((r - mr, c - mc) for r, c in cells)
        occs.append(cells)
    return occs


def self_check(grid, *, difficulty=None, meta=None):
    """>=1 source + >=2 candidate panels, and exactly one candidate whose
    occupancy equals the source's (so the rule's rot0 match fires)."""
    occs = _panels_occ(grid)
    if len(occs) < 3:
        return [f"expected SRC + >=2 candidates, got {len(occs)} panels"]
    src, cands = occs[0], occs[1:]
    if not src:
        return ["source panel is empty"]
    matches = [i for i, c in enumerate(cands) if c == src]
    if len(matches) != 1:
        return [f"expected exactly 1 candidate equal to source, got {len(matches)}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    # output = the matched candidate (a rotation of src) recoloured to 8 on a panel.
    # k/panels were small -> few distinct src shapes -> dup 42%. Widen shape size + dims.
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi, k_lo, k_hi = 4, 6, 4, 6, 2, 3, 3, 5
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi, k_lo, k_hi = 6, 9, 5, 8, 3, 6, 5, 9
    else:
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi, k_lo, k_hi = 5, 7, 4, 7, 3, 5, 4, 7

    ph = ctx.draw_int("panel_h", h_lo, h_hi)
    pw = ctx.draw_int("panel_w", w_lo, w_hi)
    n = ctx.draw_int("n_cands", n_lo, n_hi)
    k = ctx.draw_int("shape_size", k_lo, min(k_hi, ph * pw - 1))
    return _build(rng, ph, pw, n, k)


def _draw_from_degenerate(name, rng):
    if name == "min_cands":
        return _build(rng, 5, 5, 2, 4)
    if name == "big_shape":
        return _build(rng, 6, 6, 3, 6)
    return _build(rng, 5, 4, 5, 4)               # many_cands
