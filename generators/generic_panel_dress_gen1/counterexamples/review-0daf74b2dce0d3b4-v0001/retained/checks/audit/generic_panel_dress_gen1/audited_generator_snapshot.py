"""gen1: dotted panels dressed with hole-matched shapes.

Scene: a block of touching solid panels (2-4, sizes 6-8), each pierced
by 1-4 field-colored dots (pairwise separated so each is its own
enclosed hole); loose filled rectangles with the matching number of
enclosed holes sit isolated on the field. Transform: output the panel
block with each panel refilled solid and its count-matched shape pasted
centered, holes showing the panel color.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_panel_dress_gen1"

PROGRAM = """(rule!
 ;; PANEL DRESS-UP: solid color PANELS tile a block (they touch each
 ;; other), each pierced by field-colored dots; isolated SHAPES with
 ;; enclosed holes lie on the field. Each panel takes the shape whose
 ;; hole count equals its dot count: output the panel block with every
 ;; panel refilled solid, its shape pasted centered (color kept, holes
 ;; showing the panel color).
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define bg (mode g))
     (define objs (objects g bg))
     (define (touches? a b)
       (< 0 (count-if
             (lambda (p)
               (< 0 (count-if
                     (lambda (q)
                       (= 1 (+ (abs (- (first p) (first q)))
                               (abs (- (second p) (second q))))))
                     (obj-cells b))))
             (obj-cells a))))
     (define panels
       (filter (lambda (o)
                 (< 0 (count-if (lambda (u) (and (not (equal? u o))
                                                 (touches? o u)))
                                objs)))
               objs))
     (define shapes
       (filter (lambda (o)
                 (= 0 (count-if (lambda (p) (equal? p o)) panels)))
               objs))
     (define (holes o)
       ;; enclosed bg regions in o's padded bbox (count, cells kept)
       (let* ((bb (obj-bbox o))
              (r1 (first bb)) (c1 (second bb))
              (r2 (nth bb 2)) (c2 (nth bb 3))
              (mask (paint-cells
                     (empty-grid (+ (- r2 r1) 3) (+ (- c2 c1) 3) 1)
                     (map (lambda (p) (list (+ (- (first p) r1) 1)
                                            (+ (- (second p) c1) 1)))
                          (obj-cells o))
                     0)))
         (length (filter (lambda (q) (not (bordering? q mask)))
                         (objects mask 0)))))
     (define prs (flatmap (lambda (o) (map first (obj-cells o))) panels))
     (define pcs (flatmap (lambda (o) (map second (obj-cells o))) panels))
     (define br1 (reduce min (first prs) prs))
     (define bc1 (reduce min (first pcs) pcs))
     (define br2 (reduce max (first prs) prs))
     (define bc2 (reduce max (first pcs) pcs))
     (reduce
      (lambda (out pan)
        (let* ((pb (obj-bbox pan))
               (pr1 (first pb)) (pc1 (second pb))
               (pr2 (nth pb 2)) (pc2 (nth pb 3))
               (pcol (obj-color pan))
               (ndots (holes pan))
               (shp (find-first (lambda (s) (= (holes s) ndots)) shapes))
               (sb (obj-bbox shp))
               (mr (quotient (- (- pr2 pr1) (- (nth sb 2) (first sb))) 2))
               (mc (quotient (- (- pc2 pc1) (- (nth sb 3) (second sb))) 2))
               (filled
                (for*/fold ((o out)) ((r (in-range pr1 (+ pr2 1)))
                                      (c (in-range pc1 (+ pc2 1))))
                  (set-cell o (- r br1) (- c bc1) pcol))))
          (reduce (lambda (o p)
                    (set-cell o
                              (+ (- (+ pr1 mr) br1)
                                 (- (first p) (first sb)))
                              (+ (- (+ pc1 mc) bc1)
                                 (- (second p) (second sb)))
                              (at g (first p) (second p))))
                  filled (obj-cells shp))))
      (empty-grid (+ (- br2 br1) 1) (+ (- bc2 bc1) 1) 0)
      panels))))"""


def _comps(g, bg):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]
                q = deque([(r, c)])
                seen[r][c] = True
                comp = [(r, c)]
                while q:
                    x, y = q.popleft()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < h and 0 <= ny < w \
                                and not seen[nx][ny] and g[nx][ny] == col:
                            seen[nx][ny] = True
                            q.append((nx, ny))
                            comp.append((nx, ny))
                out.append(comp)
    return out


def _holes(comp):
    cells = set(comp)
    r1 = min(r for r, _ in comp) - 1
    c1 = min(c for _, c in comp) - 1
    r2 = max(r for r, _ in comp) + 1
    c2 = max(c for _, c in comp) + 1
    hh, ww = r2 - r1 + 1, c2 - c1 + 1
    seen = [[False] * ww for _ in range(hh)]
    n = 0
    for i in range(hh):
        for j in range(ww):
            if not seen[i][j] and (i + r1, j + c1) not in cells:
                q = deque([(i, j)])
                seen[i][j] = True
                border = False
                while q:
                    x, y = q.popleft()
                    if x in (0, hh - 1) or y in (0, ww - 1):
                        border = True
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < hh and 0 <= ny < ww \
                                and not seen[nx][ny] \
                                and (nx + r1, ny + c1) not in cells:
                            seen[nx][ny] = True
                            q.append((nx, ny))
                if not border:
                    n += 1
    return n


def _apply(g):
    """Python mirror of PROGRAM."""
    from collections import Counter
    bg = Counter(v for row in g for v in row if v != 0).most_common(1)[0][0]
    objs = _comps(g, bg)
    cellsets = [set(o) for o in objs]

    def touches(i, j):
        return any((r + dr, c + dc) in cellsets[j]
                   for r, c in objs[i]
                   for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    panel_ix = [i for i in range(len(objs))
                if any(i != j and touches(i, j) for j in range(len(objs)))]
    shapes = [objs[i] for i in range(len(objs)) if i not in panel_ix]
    panels = [objs[i] for i in panel_ix]
    prs = [r for o in panels for r, _ in o]
    pcs = [c for o in panels for _, c in o]
    br1, bc1, br2, bc2 = min(prs), min(pcs), max(prs), max(pcs)
    out = [[0] * (bc2 - bc1 + 1) for _ in range(br2 - br1 + 1)]
    for pan in panels:
        pr1 = min(r for r, _ in pan)
        pc1 = min(c for _, c in pan)
        pr2 = max(r for r, _ in pan)
        pc2 = max(c for _, c in pan)
        pcol = g[pan[0][0]][pan[0][1]]
        nd = _holes(pan)
        shp = next(s for s in shapes if _holes(s) == nd)
        sr1 = min(r for r, _ in shp)
        sc1 = min(c for _, c in shp)
        sr2 = max(r for r, _ in shp)
        sc2 = max(c for _, c in shp)
        mr = ((pr2 - pr1) - (sr2 - sr1)) // 2
        mc = ((pc2 - pc1) - (sc2 - sc1)) // 2
        for r in range(pr1, pr2 + 1):
            for c in range(pc1, pc2 + 1):
                out[r - br1][c - bc1] = pcol
        for r, c in shp:
            out[pr1 + mr - br1 + r - sr1][pc1 + mc - bc1 + c - sc1] = \
                g[r][c]
    return out


def _build_pair(rng, difficulty):
    n = {"easy": 2, "medium": 3, "hard": 4}[difficulty]
    gr, gc = {2: (1, 2), 3: (1, 3), 4: (2, 2)}[n]
    if rng.random() < 0.5:
        gr, gc = gc, gr
    ps = rng.randint(6, min(8, 26 // max(gr, gc)))
    ss = ps - 2
    F = rng.randint(1, 9)
    colors = rng.sample([v for v in range(10) if v != F], 2 * n)
    pcols, scols = colors[:n], colors[n:]
    counts = rng.sample(range(1, min(n + 2, 5)), n)
    h = min(30, max(24, gr * ps + 2 * (ss + 2) + 2))
    w = min(30, max(24, gc * ps + ss + 6))
    g = [[F] * w for _ in range(h)]
    # panel block at top-left
    for pi in range(n):
        bi, bj = divmod(pi, gc)
        r0, c0 = bi * ps, bj * ps
        for r in range(r0, r0 + ps):
            for c in range(c0, c0 + ps):
                g[r][c] = pcols[pi]
        # dots: pairwise Chebyshev >= 2, interior
        spots = [(i, j) for i in range(1, ps - 1) for j in range(1, ps - 1)]
        rng.shuffle(spots)
        dots = []
        for sp in spots:
            if len(dots) == counts[pi]:
                break
            if all(max(abs(sp[0] - a), abs(sp[1] - b)) >= 2
                   for a, b in dots):
                dots.append(sp)
        if len(dots) < counts[pi]:
            raise ValueError("could not place dots")
        for i, j in dots:
            g[r0 + i][c0 + j] = F
    # shapes: filled ss x ss rects with counts[pi] single holes, isolated
    occupied = {(r, c) for r in range(gr * ps + 1) for c in range(gc * ps + 1)}
    for pi in range(n):
        for _try in range(200):
            r0 = rng.randint(0, h - ss - 1)
            c0 = rng.randint(0, w - ss - 1)
            zone = {(r, c) for r in range(r0 - 1, r0 + ss + 1)
                    for c in range(c0 - 1, c0 + ss + 1)}
            if zone & occupied:
                continue
            spots = [(i, j) for i in range(1, ss - 1)
                     for j in range(1, ss - 1)]
            rng.shuffle(spots)
            holes = []
            for sp in spots:
                if len(holes) == counts[pi]:
                    break
                if all(max(abs(sp[0] - a), abs(sp[1] - b)) >= 2
                       for a, b in holes):
                    holes.append(sp)
            if len(holes) < counts[pi]:
                continue
            for r in range(r0, r0 + ss):
                for c in range(c0, c0 + ss):
                    g[r][c] = scols[pi]
            for i, j in holes:
                g[r0 + i][c0 + j] = F
            occupied |= zone
            break
        else:
            raise ValueError("could not place a shape")
    return g, _apply(g)


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    n_train = ctx.draw_int("n_train", 2, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    pairs = []
    idx = 0
    attempts = 0
    while len(pairs) < n_train + n_test:
        rng = ctx.draw_rng(f"pair_{idx}_{attempts}")
        attempts += 1
        if attempts > 80:
            raise ValueError("could not build enough pairs")
        try:
            gin, gout = _build_pair(rng, difficulty)
        except ValueError:
            continue
        pairs.append({"input": gin, "output": gout})
        idx += 1
    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": PROGRAM,
        "concept": "panel_dress",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.panel_dress import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"panel_dress gen1 v{VERSION}")
