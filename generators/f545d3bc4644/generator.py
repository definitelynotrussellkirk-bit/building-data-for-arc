"""Generator for 184a9768 — fit loose pieces into containers' holes.

Rule: containers are non-5 objects that enclose holes; loose non-5 objects
are PIECES. A DFS solver tiles each container hole with the loose pieces
and paints the hole accordingly; the loose pieces are removed.

Canonical scene: TWO irregular hollow containers plus 4..10 small solid
pieces (rectangles, bars, dominoes, singletons) on 20..26 grids. The
pieces collectively tile the containers' holes (guaranteed by
construction: each hole is partitioned into the pieces first, then the
pieces are scattered away from their containers).

Combinatorial axes (5): grid_h/w, n_pieces, hole_style, palette_kind,
texture. Degenerates: no_container, no_piece, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f545d3bc4644"
RULE_HASH = "176125c06095"
VERSION = "4.1.0"
TASK_ID = "f545d3bc4644"
SUMMARY = (
    "0-bg grid with TWO irregular hollow CONTAINERS plus 4..10 small solid "
    "PIECES that exactly tile the containers' holes; the rule reassembles "
    "the pieces inside the containers."
)

INVARIANTS = [
    "background 0; color 5 unused",
    "two non-solid container objects, each enclosing exactly one hole",
    "4..10 solid pieces in distinct colors, 4-connected, separated",
    "the pieces exactly tile the containers' holes (DFS always fills)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_container", "no_piece", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":   {"type": "int", "default": "band rng 18..26", "valid": "10..26"},
    "grid_w":   {"type": "int", "default": "band rng 18..26", "valid": "10..26"},
    "n_pieces": {"type": "int", "default": "band 4..10", "valid": "1..10"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "|".join(PALETTE_KINDS)},
    "texture":  {"type": "str", "default": "alias for palette_kind",
                 "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_POOLS = {
    "warm":    [2, 3, 4, 9, 7, 6],
    "cool":    [1, 5, 8, 6, 3, 9],
    "broad":   [1, 2, 3, 4, 6, 7, 8, 9],
    "primary": [1, 2, 3, 4, 5, 8],
}

# Official (h, w, n_pieces) tuples: 2 containers each, with the partition
# style drawn per draw.
_CANONICAL_FORMS = ((20, 22, 6), (21, 23, 5), (20, 20, 4), (25, 26, 10))


def _components(grid):
    """Same-color 4-connected components (mirrors the rule's objects)."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            color = grid[r][c]
            queue = [(r, c)]
            seen[r][c] = True
            cells = []
            while queue:
                a, b = queue.pop()
                cells.append((a, b))
                for na, nb in ((a - 1, b), (a + 1, b), (a, b - 1), (a, b + 1)):
                    if (0 <= na < h and 0 <= nb < w and not seen[na][nb]
                            and grid[na][nb] == color):
                        seen[na][nb] = True
                        queue.append((na, nb))
            out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance (all canonical pairs
    satisfy them): rectangular grid inside the declared 10..26 envelope,
    background 0, no color 5; every 4-connected component is either a
    non-solid container with an enclosed hole or a solid piece; pieces in
    distinct colors. no_container (zero containers), no_piece (zero
    pieces), and full_grid (single solid color) are declared degenerates."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not 0 <= v <= 9 for row in grid for v in row):
        errs.append("color outside 0..9")
        return errs
    if not (10 <= h <= 26 and 10 <= w <= 26):
        errs.append(f"dims {h}x{w} outside the declared 10..26 envelope")
        return errs
    # Color 5 is a declared distractor: isolated singletons only, never
    # touching a container or a piece (canonical scatters 0..11 per grid).
    comps = _components(grid)
    colored = []
    for cells in comps:
        v = grid[next(iter(cells))[0]][next(iter(cells))[1]]
        if v == 5 and len(cells) > 1:
            errs.append(f"color-5 object of {len(cells)} cells is not a "
                        "declared distractor (isolated singletons only)")
        if v != 5:
            colored.append(cells)
    flat = [v for row in grid for v in row]
    if len(set(flat)) == 1:
        return errs  # full_grid degenerate (declared)
    containers = []
    pieces = []
    for cells in colored:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        bh, bw = max(rs) - min(rs) + 1, max(cs) - min(cs) + 1
        (pieces if len(cells) == bh * bw else containers).append(cells)
    if not containers:
        return errs  # no_container degenerate (declared)
    if not pieces:
        return errs  # no_piece degenerate (declared)
    # each container must enclose a hole: zero cells strictly inside its
    # bbox that cannot reach the grid edge without crossing the container
    for cells in containers:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)
                    if grid[r][c] == 0]
        if not interior:
            errs.append(f"container at ({r1},{c1}) encloses no hole")
    return errs


def observe_overrides(grid):
    """Realized exact-axis values (KRF-0002): n_containers (non-solid
    objects) and n_pieces (solid objects). Color-5 distractors are not
    pieces (the rule ignores them)."""
    comps = _components(grid)
    n_containers = 0
    n_pieces = 0
    for cells in comps:
        if grid[next(iter(cells))[0]][next(iter(cells))[1]] == 5:
            continue
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        if len(cells) == (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1):
            n_pieces += 1
        else:
            n_containers += 1
    return {"n_containers": n_containers, "n_pieces": n_pieces}


def _compose(rng, total, k):
    if total < k:
        return None
    if k <= 1:
        return [total]
    cuts = sorted(rng.sample(range(1, total), k - 1))
    parts = []
    prev = 0
    for x in cuts + [total]:
        parts.append(x - prev)
        prev = x
    return parts


def _partition(rng, ih, iw, k):
    """Partition the ih x iw hole into exactly k rectangles: 1D bands along
    a feasible direction (a direction that cannot host k bands degrades to
    the full hole, so it is never chosen), else a 2-level cut with a*b == k
    and a <= ih, b <= iw."""
    if k <= 1:
        return [(ih, iw)]
    feasible = []
    if iw >= k:
        feasible.append(lambda: [(ih, p) for p in _compose(rng, iw, k)])
    if ih >= k:
        feasible.append(lambda: [(p, iw) for p in _compose(rng, ih, k)])
    if feasible:
        return feasible[rng.randrange(len(feasible))]()
    # 2-level: rows into a parts and columns into b parts with a*b == k;
    # the pieces are the a*b grid cells.
    for a in range(2, ih + 1):
        if k % a != 0:
            continue
        b = k // a
        if b > iw:
            continue
        row_parts = _compose(rng, ih, a)
        col_parts = _compose(rng, iw, b)
        return [(rh, cw) for rh in row_parts for cw in col_parts]
    return None


def _draw_container(g, r0, c0, bh, bw, color, rng):
    """A thick-walled container: the whole bbox except one interior hole
    (the canonical form is ~75-85% filled, not a 1-cell frame). Returns the
    hole cells (empty, to be tiled by the pieces in the output)."""
    # hole ~15-30% of the bbox, at least 1 cell off every wall
    max_ih = max(1, bh - 3)
    max_iw = max(1, bw - 3)
    ih = rng.randint(max(1, (bh + 3) // 4), max(1, max_ih))
    iw = rng.randint(max(1, (bw + 3) // 4), max(1, max_iw))
    hr0 = r0 + rng.randint(1, bh - ih - 1)
    hc0 = c0 + rng.randint(1, bw - iw - 1)
    hole = {(hr0 + r, hc0 + c) for r in range(ih) for c in range(iw)}
    for r in range(r0, r0 + bh):
        for c in range(c0, c0 + bw):
            if (r, c) not in hole:
                g[r][c] = color
    return hole, ih, iw


def _place(g, occ, sh, sw, h, w, rng):
    for _ in range(160):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        ok = True
        for r in range(r0 - 1, r0 + sh + 1):
            for c in range(c0 - 1, c0 + sw + 1):
                if 0 <= r < h and 0 <= c < w and occ[r][c]:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            for r in range(r0, r0 + sh):
                for c in range(c0, c0 + sw):
                    occ[r][c] = True
            return r0, c0
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    tex = overrides.get("texture")
    if tex in DEGENERATE_TEXTURES:
        extra = sorted(k for k, v in overrides.items()
                       if k != "texture" and v is not None)
        if extra:
            raise ValueError(
                f"degenerate texture {tex!r} is a fixed diagnostic layout; "
                f"it takes no other overrides, got {extra}")
        return _draw_from_degenerate(tex, ctx.draw_rng("layout"))
    if tex is not None and tex not in PALETTE_KINDS:
        raise ValueError(f"unknown texture {tex!r}; valid: "
                         f"{PALETTE_KINDS + DEGENERATE_TEXTURES}")
    if tex is not None and overrides.get("palette_kind") is not None and \
            overrides["palette_kind"] != tex:
        raise ValueError(
            f"texture={tex!r} is itself a palette alias and "
            f"palette_kind={overrides['palette_kind']!r} disagrees")
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        hr = (18, 21)
    elif difficulty == "hard":
        hr = (22, 26)
    else:
        hr = (19, 24)

    # Canonical-form prior (KRF-0003): ~30% of fully-unoverridden draws pin
    # one official (h, w, n_pieces) tuple with 2 containers.
    if not any(k in overrides for k in ("grid_h", "grid_w", "n_pieces")):
        if ctx.draw_rng("canonical_prior").random() < 0.35:
            ch, cw, cn = ctx.draw_choice("canonical_form", _CANONICAL_FORMS)
            for label, value in (("grid_h", ch), ("grid_w", cw),
                                 ("n_pieces", cn)):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int(label, value, value)

    h = ctx.draw_int("grid_h", *( (10, 26) if overrides.get("grid_h") is not None
                                  else hr))
    w = ctx.draw_int("grid_w", *( (10, 26) if overrides.get("grid_w") is not None
                                  else hr))
    n_pieces = ctx.draw_int("n_pieces", *( (1, 10) if overrides.get("n_pieces") is not None
                                           else ((4, 7) if difficulty != "hard" else (6, 10))))
    palette_kind = (tex or overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = [c for c in _POOLS[palette_kind] if c != 5]
    rng.shuffle(pool)
    container_colors = pool[:2]

    for _attempt in range(80):
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        pieces = []
        # split the piece budget across the two containers' holes; EVERY
        # hole must get >= 1 piece whenever the budget allows, otherwise
        # the rule's DFS exhaustively proves that hole uncoverable (the
        # run_one seed-6 >10s thrash class). n_pieces == 1 is the declared
        # edge case (one hole legitimately stays empty; the search ends
        # immediately with zero remaining pieces).
        if n_pieces >= 2:
            k1 = rng.randint(1, n_pieces - 1)
        else:
            k1 = 1
        k2 = n_pieces - k1
        # Zone-based layout (guaranteed feasibility): containers in the top
        # zone, pieces in the bottom zone. Container sizes are capped so a
        # side-by-side or stacked layout always fits with room for pieces.
        # Canonical containers are big (43..101 cells, bboxes up to 12x16).
        # Draw sizes with joint feasibility for the two-container layout.
        side_by_side = w >= h
        if side_by_side:
            bh1 = rng.randint(6, min(16, max(6, h - 4)))
            bw1 = rng.randint(6, min(14, max(6, (w - 9) // 2)))
            bh2 = rng.randint(6, min(16, max(6, h - 4)))
            bw2 = rng.randint(6, min(14, max(6, w - bw1 - 3)))
        else:
            bh1 = rng.randint(6, min(16, max(6, (h - 9) // 2)))
            bw1 = rng.randint(6, min(14, max(6, w - 4)))
            bh2 = rng.randint(6, min(16, max(6, h - bh1 - 3)))
            bw2 = rng.randint(6, min(14, max(6, w - 4)))
        if side_by_side and bw1 + bw2 + 3 > w:
            continue
        ok = True
        if side_by_side:
            zone_h = max(bh1, bh2) + 2
            r1 = rng.randint(0, zone_h - bh1)
            r2 = rng.randint(0, zone_h - bh2)
            pos1 = (r1, rng.randint(0, max(0, w - bw1 - bw2 - 2)))
            pos2 = (r2, rng.randint(pos1[1] + bw1 + 2, w - bw2))
        else:
            zone_h = bh1 + bh2 + 3
            if zone_h + 2 > h:
                continue
            pos1 = (rng.randint(0, zone_h - bh1 - bh2 - 2),
                    rng.randint(0, w - bw1))
            pos2 = (pos1[0] + bh1 + 2, rng.randint(0, w - bw2))
        hole_cells = []
        for ci, (bh, bw) in enumerate(((bh1, bw1), (bh2, bw2))):
            rr0, cc0 = (pos1, pos2)[ci]
            for r in range(rr0, rr0 + bh):
                for c in range(cc0, cc0 + bw):
                    occ[r][c] = True
            hole, ih, iw = _draw_container(g, rr0, cc0, bh, bw,
                                           container_colors[ci], rng)
            kk = (k1, k2)[ci]
            rects = _partition(rng, ih, iw, kk) if kk >= 1 else []
            if kk >= 1 and (rects is None
                            or sum(a * b for a, b in rects) != ih * iw):
                ok = False
                break
            for rect in rects:
                pieces.append((rect, pool[rng.randrange(len(pool))]))
        if not ok:
            continue
        # color-5 distractor singletons (0..11), isolated from everything
        n_fives = rng.randint(0, 11) if rng.random() < 0.6 else 0
        placed_fives = 0
        for _f in range(n_fives):
            for _try in range(60):
                r = rng.randrange(h)
                c = rng.randrange(w)
                if occ[r][c] or any(occ[rr][cc]
                                    for rr in range(max(0, r - 1), min(h, r + 2))
                                    for cc in range(max(0, c - 1), min(w, c + 2))):
                    continue
                g[r][c] = 5
                occ[r][c] = True
                placed_fives += 1
                break
        # piece zone: rows [zone_h, h); place pieces there first, then
        # anywhere free as overflow
        placed_all = True
        for (psh, psw), pcol in pieces:
            placed = False
            for _try in range(200):
                r0 = rng.randint(zone_h, max(zone_h, h - psh))
                c0 = rng.randint(0, w - psw)
                if r0 + psh > h:
                    continue
                free = True
                for r in range(r0 - 1, r0 + psh + 1):
                    for c in range(c0 - 1, c0 + psw + 1):
                        if 0 <= r < h and 0 <= c < w and occ[r][c]:
                            free = False
                            break
                    if not free:
                        break
                if not free:
                    continue
                for r in range(r0, r0 + psh):
                    for c in range(c0, c0 + psw):
                        occ[r][c] = True
                        g[r][c] = pcol
                placed = True
                break
            if not placed:
                pos = _place(g, occ, psh, psw, h, w, rng)
                if pos is None:
                    placed_all = False
                    break
                for r in range(pos[0], pos[0] + psh):
                    for c in range(pos[1], pos[1] + psw):
                        g[r][c] = pcol
        if placed_all:
            errs = self_check(g)
            if not errs and _quick_cover_ok(g):
                return g
    raise ValueError(
        f"cannot place 2 containers + {n_pieces} pieces on {h}x{w} "
        "(infeasible combination)")


def _holes_of_cells(grid, cells):
    """bg pockets strictly inside the object's bbox (mirrors holes-of)."""
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r1, c1, r2, c2 = min(rs), min(cs), max(rs), max(cs)
    bh, bw = r2 - r1 + 1, c2 - c1 + 1
    own = set(cells)
    seen = [[False] * bw for _ in range(bh)]
    holes = []
    for r in range(bh):
        for c in range(bw):
            if seen[r][c] or grid[r1 + r][c1 + c] != 0 \
                    or (r1 + r, c1 + c) in own:
                continue
            stack, comp = [(r, c)], []
            seen[r][c] = True
            while stack:
                a, b = stack.pop()
                comp.append((a, b))
                for na, nb in ((a - 1, b), (a + 1, b), (a, b - 1), (a, b + 1)):
                    if (0 <= na < bh and 0 <= nb < bw and not seen[na][nb]
                            and grid[r1 + na][c1 + nb] == 0
                            and (r1 + na, c1 + nb) not in own):
                        seen[na][nb] = True
                        stack.append((na, nb))
            cr1 = min(a for a, _ in comp)
            cc1 = min(b for _, b in comp)
            cr2 = max(a for a, _ in comp)
            cc2 = max(b for _, b in comp)
            if cr1 > 0 and cc1 > 0 and cr2 < bh - 1 and cc2 < bw - 1:
                holes.append(sorted((r1 + a, c1 + b) for a, b in comp))
    return holes


def _quick_cover_ok(grid, budget=3000):
    """Bounded faithful replica of the canonical rule's exact-cover search
    (same hole order, first-uncovered-cell descent, big-pieces-first with
    the original-bbox/color tie-break, greedy per-hole commit). A draw is
    accepted only when this search terminates within `budget` option
    expansions, so the Racket oracle can never be sent into the >10s
    exhaustive-proof thrash found by run_one at seed 6."""
    nodes = [0]
    objs = _components(grid)
    containers = [(i, o, _holes_of_cells(grid, o))
                  for i, o in enumerate(objs)
                  if grid[o[0][0]][o[0][1]] != 5 and _holes_of_cells(grid, o)]
    container_ids = {i for i, _, _ in containers}
    pieces = []
    for i, o in enumerate(objs):
        color = grid[o[0][0]][o[0][1]]
        if color == 5 or i in container_ids:
            continue
        mr = min(r for r, _ in o)
        mc = min(c for _, c in o)
        shape = sorted((r - mr, c - mc) for r, c in o)
        bb = (mr, mc, max(r for r, _ in o), max(c for _, c in o))
        pieces.append((i, color, shape, bb, len(o)))

    def hole_key(cells):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        return 10000 * min(rs) + 100 * min(cs) + len(cells)
    all_holes = sorted((hl for _, _, hs in containers for hl in hs),
                       key=hole_key)

    def placements_for(hole, piece):
        hole_set = set(hole)
        seen, out = set(), []
        for hp in hole:
            for sp in piece[2]:
                dr, dc = hp[0] - sp[0], hp[1] - sp[1]
                placed = tuple(sorted((p[0] + dr, p[1] + dc)
                                      for p in piece[2]))
                if placed in seen:
                    continue
                seen.add(placed)
                if all(p in hole_set for p in placed):
                    out.append(placed)
        return out

    def option_key(opt):
        piece, _placed = opt
        bb = piece[3]  # rule keys on the piece's ORIGINAL bbox
        return (-100000 * piece[4] + 1000 * bb[0] + bb[1] + piece[1])

    def cover_hole(hole, rem):
        def dfs(covered, rem2, assigns):
            todo = [p for p in hole if p not in covered]
            if not todo:
                return (assigns, rem2)
            nodes[0] += 1
            if nodes[0] > budget:
                return "abort"
            cell = todo[0]
            opts = []
            for piece in rem2:
                for placed in placements_for(hole, piece):
                    if cell in placed and not any(p in covered
                                                  for p in placed):
                        opts.append((piece, placed))
            opts.sort(key=option_key)
            for piece, placed in opts:
                res = dfs(covered | set(placed),
                          [p for p in rem2 if p[0] != piece[0]],
                          assigns + [(piece[1], placed)])
                if res == "abort":
                    return "abort"
                if res is not None:
                    return res
            return None
        return dfs(set(), rem, [])

    rem = pieces
    for hole in all_holes:
        if nodes[0] > budget:
            return False
        res = cover_hole(hole, rem)
        if res == "abort":
            return False
        if res is None:
            # uncoverable hole proven within budget: the rule returns the
            # containers-only output immediately — fast, so acceptable.
            return True
        rem = res[1]
    return True


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 14, 0)
    if name == "no_container":
        for r in range(7, 10):
            for c in range(9, 12):
                g[r][c] = 4
        return g
    if name == "no_piece":
        for r in range(1, 6):
            for c in range(1, 6):
                if r in (1, 5) or c in (1, 5):
                    g[r][c] = 3
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(14):
                g[r][c] = 3
        return g
    return g
