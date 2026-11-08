"""Generator for arc_puzzle_bank_nineteenth21:H129 — growth-delta transfer.

Rule: 3 equal panels (arithmetic slicing): BEFORE, AFTER, QUERY. The
delta = AFTER's normalized support minus BEFORE's (each normalized to
its own bbox min). The delta cells are stamped onto the QUERY panel at
query-bbox-min + offset, in the QUERY object's color; out-of-bounds
stamps clip. Output = the query panel with the growth applied.

Combinatorial axes: panel_h/w, texture (plain|diff_query|clip).
Degenerates: no_growth (AFTER == BEFORE: delta empty, output = query
panel unchanged). Empty panels CRASH the rule ((first '())) — the old
wrong-task generator (5th gallery-template copy) crashed 10/24 smoke
boards that way; panels are now always non-empty.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "094d4f976dd5"
VERSION = "2.0.2"
TASK_ID = "094d4f976dd5"

SUMMARY = (
    "BEFORE->AFTER demonstrates a shape growth; the same delta stamps "
    "onto the QUERY object in the query's color. diff_query boards "
    "give the query a DIFFERENT shape (the delta is positional, "
    "anchored at bbox mins, not shape-aware); clip boards push the "
    "query so grown cells fall off the panel. (Was: random motif "
    "scatter - 10/24 smoke boards CRASHED on empty panel slices.)"
)

# Rivals: 'copy AFTER onto the query' refuted by diff_query (only the
# DELTA transfers). 'delta keeps demo colors' refuted by query-color
# stamps. 'growth must fit' refuted by clip. 3-4 demos.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "all three panels hold exactly one object (empty panels crash the rule)",
    "AFTER = BEFORE + delta cells that never shift the bbox min",
    "main-path stamps land in-panel; clip boards lose >=1 grown cell",
]

DEGENERATE_TEXTURES = ("no_growth",)
HELPFUL_TEXTURES = ("plain", "diff_query", "clip")

AXES = {
    "panel_h": {"type": "int", "default": "rng 8..12", "valid": "7..14"},
    "panel_w": {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|diff_query|clip|no_growth",
                "doc": "diff_query: query shape differs from BEFORE (the "
                       "delta is purely positional); clip: grown cells "
                       "fall outside the query panel."},
}


def _grow(rng, k, max_h, max_w):
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(200):
        if len(cells) >= k:
            break
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        p = (r + dr, c + dc)
        if p in seen:
            continue
        rs = [q[0] for q in seen] + [p[0]]
        cs = [q[1] for q in seen] + [p[1]]
        if max(rs) - min(rs) + 1 > max_h or max(cs) - min(cs) + 1 > max_w:
            continue
        cells.append(p)
        seen.add(p)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _mirror(g):
    h, w = len(g), len(g[0])
    pw = (w - 2) // 3
    panels = [[row[i * (pw + 1):i * (pw + 1) + pw] for row in g]
              for i in range(3)]

    def first_obj(p):
        ph2, pw2 = len(p), len(p[0])
        seen = set()
        for r0 in range(ph2):
            for c0 in range(pw2):
                v = p[r0][c0]
                if v == 0 or (r0, c0) in seen:
                    continue
                stack = [(r0, c0)]
                seen.add((r0, c0))
                cells = []
                while stack:
                    r, c = stack.pop()
                    cells.append((r, c))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < ph2 and 0 <= cc < pw2 \
                                and (rr, cc) not in seen and p[rr][cc] == v:
                            seen.add((rr, cc))
                            stack.append((rr, cc))
                return cells, v
        return None, None

    before, after, query = panels
    bc, _ = first_obj(before)
    ac, _ = first_obj(after)
    qc, qcolor = first_obj(query)
    if bc is None or ac is None or qc is None:
        return None
    bmin = (min(r for r, _ in bc), min(c for _, c in bc))
    amin = (min(r for r, _ in ac), min(c for _, c in ac))
    qmin = (min(r for r, _ in qc), min(c for _, c in qc))
    sb = {(r - bmin[0], c - bmin[1]) for r, c in bc}
    sa = [(r - amin[0], c - amin[1]) for r, c in ac]
    delta = [p for p in sa if p not in sb]
    out = [row[:] for row in query]
    for r, c in delta:
        rr, cc = qmin[0] + r, qmin[1] + c
        if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
            out[rr][cc] = qcolor
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "diff_query", "clip"))
    if difficulty == "easy":
        ph = ctx.draw_int("panel_h", 8, 9)
        pw = ctx.draw_int("panel_w", 4, 4)
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_h", 10, 12)
        pw = ctx.draw_int("panel_w", 5, 5)
    else:
        ph = ctx.draw_int("panel_h", 8, 12)
        pw = ctx.draw_int("panel_w", 4, 5)
    rng = ctx.draw_rng("layout")
    w = 3 * pw + 2

    for _attempt in range(200):
        base = _grow(rng, rng.randint(3, 5), ph - 2, pw - 1)
        bset = set(base)
        # delta: 1-3 cells adjacent to the shape, never shifting mins
        cands = sorted({(r + dr, c + dc) for r, c in base
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))}
                       - bset)
        cands = [(r, c) for r, c in cands if r >= 0 and c >= 0]
        rng.shuffle(cands)
        if texture == "clip":
            # clipping needs growth EXTENDING the bbox past the query
            bh0 = max(r for r, _ in base) + 1
            bw0 = max(c for _, c in base) + 1
            extend = [(r, c) for r, c in cands if r >= bh0 or c >= bw0]
            if not extend:
                continue
            delta = list(dict.fromkeys([extend[0]] + cands[:rng.randint(0, 2)]))
        else:
            delta = cands[:rng.randint(1, 3)]
        if not delta:
            continue
        grown = sorted(bset | set(delta))
        gh = max(r for r, _ in grown) + 1
        gw = max(c for _, c in grown) + 1
        if gh > ph or gw > pw:
            continue

        cb, ca_, cq = (rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
                       for _ in range(3))
        if texture == "diff_query":
            # The pedagogical point of this texture is that the QUERY shape is
            # not the BEFORE shape; otherwise the board collapses back to the
            # plain transfer case and fails to refute shape-copy rivals.
            qshape = None
            for _qtry in range(80):
                cand = _grow(rng, rng.randint(3, 5), ph - 2, pw - 1)
                if set(cand) != bset:
                    qshape = cand
                    break
            if qshape is None:
                continue
        else:
            qshape = list(base)
        qh = max(r for r, _ in qshape) + 1
        qw = max(c for _, c in qshape) + 1

        # query placement: grown extent must fit (or clip for clip)
        ext_h = max(qh, gh)
        ext_w = max(qw, gw)
        if texture == "clip":
            r_lo = max(0, ph - ext_h + 1)
            c_lo = max(0, pw - ext_w + 1)
            if r_lo > ph - qh and c_lo > pw - qw:
                continue  # neither axis can clip with this geometry
            qr = rng.randint(r_lo, ph - qh) if r_lo <= ph - qh \
                else rng.randint(0, ph - qh)
            qc0 = rng.randint(c_lo, pw - qw) if c_lo <= pw - qw \
                else rng.randint(0, pw - qw)
            stamps = [(qr + r, qc0 + c) for r, c in delta]
            if all(0 <= r < ph and 0 <= c < pw for r, c in stamps):
                continue
            if not any(0 <= r < ph and 0 <= c < pw for r, c in stamps):
                continue
        else:
            if ph - ext_h < 0 or pw - ext_w < 0:
                continue
            qr = rng.randint(0, ph - ext_h)
            qc0 = rng.randint(0, pw - ext_w)

        panels = []
        for shape, color in ((base, cb), (grown, ca_), (None, None)):
            p = [[0] * pw for _ in range(ph)]
            if shape is not None:
                sh = max(r for r, _ in shape) + 1
                sw = max(c for _, c in shape) + 1
                r0 = rng.randint(0, ph - sh)
                c0 = rng.randint(0, pw - sw)
                for r, c in shape:
                    p[r0 + r][c0 + c] = color
            panels.append(p)
        qp = [[0] * pw for _ in range(ph)]
        for r, c in qshape:
            qp[qr + r][qc0 + c] = cq
        panels[2] = qp

        g = full_grid(ph, w, 0)
        for i, p in enumerate(panels):
            left = i * (pw + 1)
            for r in range(ph):
                for c in range(pw):
                    g[r][left + c] = p[r][c]
        out = _mirror(g)
        if out is None:
            continue
        qpanel = panels[2]
        if texture != "clip" and out == qpanel:
            continue  # growth must be visible
        return g
    raise ValueError("could not realize growth-transfer board")


def _draw_from_degenerate(name, ctx):
    """no_growth — AFTER == BEFORE: empty delta, the output is the
    query panel unchanged. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    ph = ctx.draw_int("panel_h", 8, 10)
    pw = ctx.draw_int("panel_w", 4, 5)
    w = 3 * pw + 2
    g = full_grid(ph, w, 0)
    base = _grow(rng, rng.randint(3, 5), ph - 1, pw)
    sh = max(r for r, _ in base) + 1
    sw = max(c for _, c in base) + 1
    for i, color in enumerate(rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)):
        left = i * (pw + 1)
        r0 = rng.randint(0, ph - sh)
        c0 = rng.randint(0, pw - sw)
        for r, c in base:
            g[r0 + r][left + c0 + c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Three non-empty panels; AFTER adds a visible delta to the QUERY panel."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if (w - 2) % 3 != 0:
        return ["width does not split into 3 equal panels plus separators"]
    pw = (w - 2) // 3
    panels = [[row[i * (pw + 1):i * (pw + 1) + pw] for row in grid]
              for i in range(3)]

    def obj_cells(panel):
        seen = set()
        objs = []
        for r0 in range(h):
            for c0 in range(pw):
                v = panel[r0][c0]
                if v == 0 or (r0, c0) in seen:
                    continue
                stack = [(r0, c0)]
                seen.add((r0, c0))
                cells = []
                while stack:
                    r, c = stack.pop()
                    cells.append((r, c))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < h and 0 <= cc < pw and (rr, cc) not in seen and panel[rr][cc] == v:
                            seen.add((rr, cc))
                            stack.append((rr, cc))
                objs.append(cells)
        return objs

    objs = [obj_cells(p) for p in panels]
    errs = []
    for name, comp in zip(("BEFORE", "AFTER", "QUERY"), objs):
        if len(comp) != 1:
            errs.append(f"{name} panel should contain exactly one object, found {len(comp)}")
    if errs:
        return errs

    def norm(cells):
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        return {(r - r0, c - c0) for r, c in cells}

    before, after, query = (norm(objs[i][0]) for i in range(3))
    delta = after - before
    if not delta:
        errs.append("AFTER adds no normalized delta cells; default board is no-growth")
    if not before < after:
        errs.append("AFTER should be BEFORE plus growth cells without losing existing support")
    out = _mirror(grid)
    if out is None:
        errs.append("rule mirror failed — likely an empty panel")
    elif out == panels[2]:
        errs.append("growth is not visible on the query panel")
    return errs
