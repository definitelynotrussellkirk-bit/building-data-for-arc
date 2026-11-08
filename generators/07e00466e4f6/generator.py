"""Generator for arc_puzzle_bank_21_set16_s:S16_H5 — majority-orientation span.

Rule (ACTUAL): split at full color-9 COLUMNS into panels. In each
panel take the FIRST TWO nonzero points (scan order) and classify the
pair: orientation 0 = same row, 1 = same col, 2 = diagonal; span
length = chebyshev+1. Find the MAJORITY orientation over panels; among
those panels pick the LONGEST span; output the span rendered in color
8, cropped to its bbox (1xL bar, Lx1 bar, or LxL diagonal).

Combinatorial axes: panel layout, orientations, texture
(plain|diag_major|extra_points|all_same).
Degenerates: none kept — a panel with <2 points crashes the rule
((second pts) -> #f) and is never generated.
The old generator was a WRONG-TASK motif-scatter (3rd copy of the
gallery template): no 9-columns, so the whole grid was one panel and
the output was the span between two scan-adjacent points.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "07e00466e4f6"
VERSION = "2.2.0"  # add executable majority/span self_check
TASK_ID = "07e00466e4f6"

SUMMARY = (
    "Panels split by 9-columns, each holding a 2-point pair (row / "
    "col / diagonal aligned); the majority orientation wins and its "
    "longest span is drawn in 8 on a cropped canvas. extra_points "
    "panels carry a third point the rule ignores. (Was: random motif "
    "scatter with no panels at all - the rule degenerated to the span "
    "between two scan-adjacent points.)"
)

# Rivals: 'longest span overall' refuted by a longer span in a
# MINORITY orientation that loses. 'first panel wins' refuted by the
# majority/longest selection. 'all points count' refuted by
# extra_points (third point ignored). 'output keeps point colors'
# refuted by the 8-render. 4 demos.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "every panel has >=2 nonzero points (fewer crash the rule)",
    "the majority orientation is strict and its longest span unique (mirror-verified)",
    "diagonal pairs are true 45-degree (|dr| == |dc|)",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ("plain", "diag_major", "extra_points", "all_same")

AXES = {
    "panel_h":  {"type": "int", "default": "rng 7..10", "valid": "6..12"},
    "n_panels": {"type": "int", "default": "rng 3..5", "valid": "2..5"},
    "texture":  {"type": "str", "default": "rng helpful",
                 "valid": "plain|diag_major|extra_points|all_same",
                 "doc": "diag_major: diagonal majority (LxL output); "
                        "extra_points: one panel has an ignored 3rd point; "
                        "all_same: every panel shares the orientation."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)


def _span_cells(a, b):
    (r1, c1), (r2, c2) = a, b
    dr = (r2 > r1) - (r2 < r1)
    dc = (c2 > c1) - (c2 < c1)
    n = max(abs(r2 - r1), abs(c2 - c1))
    return [(r1 + i * dr, c1 + i * dc) for i in range(n + 1)]


def _mirror(g):
    h, w = len(g), len(g[0])
    sep = [c for c in range(w) if all(g[r][c] == 9 for r in range(h))]
    bounds = [-1] + sep + [w]
    panels = []
    for i in range(len(bounds) - 1):
        lo, hi = bounds[i] + 1, bounds[i + 1] - 1
        if lo <= hi:
            panels.append([row[lo:hi + 1] for row in g])
    infos = []
    for p in panels:
        pts = sorted((r, c) for r in range(len(p)) for c in range(len(p[0]))
                     if p[r][c] != 0)
        if len(pts) < 2:
            return None
        a, b = pts[0], pts[1]
        ori = 0 if a[0] == b[0] else (1 if a[1] == b[1] else 2)
        infos.append((ori, len(_span_cells(a, b)), a, b))
    oris = [i[0] for i in infos]
    uniq = []
    for o in oris:
        if o not in uniq:
            uniq.append(o)
    majority = sorted(uniq, key=lambda o: -oris.count(o))[0]
    cands = sorted([i for i in infos if i[0] == majority],
                   key=lambda i: -i[1])
    _, _, a, b = cands[0]
    cells = _span_cells(a, b)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    hh = max(r for r, _ in cells) - r0 + 1
    ww = max(c for _, c in cells) - c0 + 1
    out = [[0] * ww for _ in range(hh)]
    for r, c in cells:
        out[r - r0][c - c0] = 8
    return out


def _pair_in_panel(rng, ph, pw, ori, length):
    """Two points with the given orientation and span length."""
    if ori == 0:
        if length > pw:
            return None
        r = rng.randrange(ph)
        c1 = rng.randint(0, pw - length)
        return (r, c1), (r, c1 + length - 1)
    if ori == 1:
        if length > ph:
            return None
        c = rng.randrange(pw)
        r1 = rng.randint(0, ph - length)
        return (r1, c), (r1 + length - 1, c)
    if length > ph or length > pw:
        return None
    r1 = rng.randint(0, ph - length)
    c1 = rng.randint(0, pw - length)
    if rng.random() < 0.5:
        return (r1, c1), (r1 + length - 1, c1 + length - 1)
    return (r1, c1 + length - 1), (r1 + length - 1, c1)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify panel split, strict majority orientation, and unique longest winning span."""
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["expected a nonempty rectangular panel grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large for ARC palette task: {h}x{w}")
    vals = {v for row in grid for v in row}
    bad = sorted(v for v in vals if not isinstance(v, int) or v < 0 or v > 9)
    if bad:
        errs.append(f"cell values outside ARC palette: {bad}")
    sep = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not sep:
        errs.append("need at least one full color-9 separator column")
    bounds = [-1] + sep + [w]
    panels = []
    for i in range(len(bounds) - 1):
        lo, hi = bounds[i] + 1, bounds[i + 1] - 1
        if lo <= hi:
            panels.append([row[lo:hi + 1] for row in grid])
    if len(panels) < 2:
        errs.append(f"expected at least two panels, got {len(panels)}")
    infos = []
    for idx, p in enumerate(panels):
        pts = sorted((r, c) for r in range(len(p)) for c in range(len(p[0])) if p[r][c] != 0)
        if any(p[r][c] == 9 for r in range(len(p)) for c in range(len(p[0]))):
            errs.append(f"panel {idx} contains separator color 9 inside the panel")
        if len(pts) < 2:
            errs.append(f"panel {idx} has fewer than two nonzero points")
            continue
        a, b = pts[0], pts[1]
        ori = 0 if a[0] == b[0] else (1 if a[1] == b[1] else 2)
        if ori == 2 and abs(a[0] - b[0]) != abs(a[1] - b[1]):
            errs.append(f"panel {idx} first pair is diagonal but not 45-degree: {a}, {b}")
        infos.append((ori, len(_span_cells(a, b))))
    if infos:
        counts = {o: sum(1 for x, _ in infos if x == o) for o in (0, 1, 2)}
        top = max(counts.values())
        if list(counts.values()).count(top) != 1:
            errs.append(f"majority orientation is not strict: {counts}")
        majority = max(counts, key=lambda o: counts[o])
        win_lengths = [ln for ori, ln in infos if ori == majority]
        if win_lengths and win_lengths.count(max(win_lengths)) != 1:
            errs.append(f"winning orientation {majority} lacks a unique longest span: {win_lengths}")
    out = _mirror(grid)
    if out is None:
        errs.append("mirror rule could not produce an output")
    else:
        opal = {v for row in out for v in row}
        if not opal <= {0, 8} or 8 not in opal:
            errs.append(f"mirror output should be a cropped color-8 span on zero bg, got palette {sorted(opal)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "diag_major", "extra_points",
                        "all_same"))
    if difficulty == "easy":
        ph = ctx.draw_int("panel_h", 7, 8)
        n = ctx.draw_int("n_panels", 3, 3)
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_h", 9, 10)
        n = ctx.draw_int("n_panels", 4, 5)
    else:
        # wider panel_h range -> longer vertical/diagonal spans; the
        # output is a single 8-colored span so (orientation, length,
        # diag-direction) is the diversity axis -- widen length reach.
        ph = ctx.draw_int("panel_h", 7, 12)
        n = ctx.draw_int("n_panels", 2, 5)
    rng = ctx.draw_rng("layout")

    for _attempt in range(200):
        wcap = max(4, min(9, (28 - (n - 1)) // n))
        widths = [rng.randint(4, wcap) for _ in range(n)]
        if sum(widths) + n - 1 > 29:
            continue
        major = (2 if texture == "diag_major"
                 else rng.choice((0, 1, 2)))
        k_major = n if texture == "all_same" else (n // 2 + 1)
        oris = [major] * k_major
        minors = [o for o in (0, 1, 2) if o != major]
        while len(oris) < n:
            oris.append(rng.choice(minors))
        rng.shuffle(oris)

        lengths = []
        pairs = []
        ok = True
        for i, ori in enumerate(oris):
            cap = widths[i] if ori == 0 else (ph if ori == 1 else min(ph, widths[i]))
            if cap < 2:
                ok = False
                break
            length = rng.randint(2, cap)
            pr = _pair_in_panel(rng, ph, widths[i], ori, length)
            if pr is None:
                ok = False
                break
            pairs.append(pr)
            lengths.append(length)
        if not ok:
            continue
        # unique longest among the majority panels
        mlens = [lengths[i] for i in range(n) if oris[i] == major]
        if mlens.count(max(mlens)) != 1:
            continue
        # strict majority
        if texture != "all_same" and \
                sum(1 for o in oris if o == major) <= max(
                    (oris.count(o) for o in (0, 1, 2) if o != major)):
            continue

        panels = []
        for i in range(n):
            p = [[0] * widths[i] for _ in range(ph)]
            (a, b) = pairs[i]
            ca, cb = rng.choice(_COLORS), rng.choice(_COLORS)
            p[a[0]][a[1]] = ca
            p[b[0]][b[1]] = cb
            if texture == "extra_points" and i == 0:
                # a third point strictly AFTER both in scan order
                for _try in range(60):
                    r = rng.randint(b[0], ph - 1)
                    c = rng.randrange(widths[i])
                    if (r, c) > b and p[r][c] == 0:
                        p[r][c] = rng.choice(_COLORS)
                        break
            panels.append(p)

        w = sum(widths) + n - 1
        g = full_grid(ph, w, 0)
        c0 = 0
        for i, p in enumerate(panels):
            for r in range(ph):
                for c in range(widths[i]):
                    g[r][c0 + c] = p[r][c]
            c0 += widths[i]
            if i < n - 1:
                for r in range(ph):
                    g[r][c0] = 9
                c0 += 1
        if _mirror(g) is None:
            continue
        return g
    raise ValueError("could not realize majority-span board")
