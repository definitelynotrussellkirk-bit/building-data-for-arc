"""gen1: reverse-built jigsaw scenes.

Scene: a random connected blob is partitioned into 3-6 connected pieces
by multi-source BFS growth; the blob (one color) sits on one side of the
grid, the pieces (distinct colors, occasionally two-toned) scatter on
the other side (different background). Transform: solve the exact tiling
and output the blob bbox padded by 1 with the pieces docked in place.
Scenes resample until the solver reproduces the intended tiling.
"""
from __future__ import annotations

import random as _random
from collections import deque

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_jigsaw_pack_gen1"

PROGRAM = """(rule!
 ;; JIGSAW REPACK: the grid splits into two sides with different modal
 ;; colors — one holds a single silhouette BLOB, the other a set of loose
 ;; multicolor PIECES that exactly tile the blob (translation only).
 ;; Solve the exact tiling by backtracking (first empty blob cell must be
 ;; covered by some piece's own first cell) and output the blob's bbox
 ;; padded by 1, background = the silhouette side's modal color, blob
 ;; cells replaced by the placed pieces' colors.
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define (modal vals)
       (reduce (lambda (best v)
                 (let ((cb (count-if (lambda (u) (= u best)) vals))
                       (cv (count-if (lambda (u) (= u v)) vals)))
                   (if (or (> cv cb) (and (= cv cb) (< v best))) v best)))
               (first vals) vals))
     (define row-modals
       (map (lambda (r) (modal (map (lambda (c) (at g r c)) (range 0 w))))
            (range 0 h)))
     (define col-modals
       (map (lambda (c) (modal (map (lambda (r) (at g r c)) (range 0 h))))
            (range 0 w)))
     (define horiz
       (!= (first row-modals) (nth row-modals (- h 1))))
     (define bg1 (if horiz (first row-modals) (first col-modals)))
     (define bg2 (if horiz (nth row-modals (- h 1))
                     (nth col-modals (- w 1))))
     (define (split-score s)
       (if horiz
           (+ (count-if (lambda (p) (= (at g (first p) (second p)) bg1))
                        (flatmap (lambda (r) (map (lambda (c) (list r c))
                                                  (range 0 w)))
                                 (range 0 s)))
              (count-if (lambda (p) (= (at g (first p) (second p)) bg2))
                        (flatmap (lambda (r) (map (lambda (c) (list r c))
                                                  (range 0 w)))
                                 (range s h))))
           (+ (count-if (lambda (p) (= (at g (first p) (second p)) bg1))
                        (flatmap (lambda (r) (map (lambda (c) (list r c))
                                                  (range 0 s)))
                                 (range 0 h)))
              (count-if (lambda (p) (= (at g (first p) (second p)) bg2))
                        (flatmap (lambda (r) (map (lambda (c) (list r c))
                                                  (range s w)))
                                 (range 0 h))))))
     (define split
       (reduce (lambda (best s)
                 (if (> (split-score s) (split-score best)) s best))
               1 (range 1 (if horiz h w))))
     (define (side-cells s)
       (if horiz
           (flatmap (lambda (r) (map (lambda (c) (list r c)) (range 0 w)))
                    (if (= s 0) (range 0 split) (range split h)))
           (flatmap (lambda (r) (map (lambda (c) (list r c))
                                     (if (= s 0) (range 0 split)
                                         (range split w))))
                    (range 0 h))))
     (define (side-bg s)
       (modal (map (lambda (p) (at g (first p) (second p)))
                   (side-cells s))))
     (define (key p) (+ (* (first p) 100) (second p)))
     (define (side-comps s)
       (let* ((bg (side-bg s))
              (cells (filter (lambda (p)
                               (!= (at g (first p) (second p)) bg))
                             (side-cells s))))
         (let loop ((todo cells) (acc (list)))
           (if (null? todo)
               acc
               (let* ((seed (first todo))
                      (comp (let grow ((frontier (list seed))
                                       (mine (list seed)))
                              (let ((nbrs (filter
                                           (lambda (q)
                                             (and (< 0 (count-if
                                                        (lambda (f)
                                                          (and (<= (abs (- (first q) (first f))) 1)
                                                               (<= (abs (- (second q) (second f))) 1)))
                                                        frontier))
                                                  (= 0 (count-if
                                                        (lambda (m)
                                                          (and (= (first m) (first q))
                                                               (= (second m) (second q))))
                                                        mine))))
                                           todo)))
                                (if (null? nbrs)
                                    mine
                                    (grow nbrs (append mine nbrs)))))))
                 (loop (filter (lambda (q)
                                 (= 0 (count-if
                                       (lambda (m)
                                         (and (= (first m) (first q))
                                              (= (second m) (second q))))
                                       comp)))
                               todo)
                       (append acc (list (sort-by comp key)))))))))
     (define comps0 (side-comps 0))
     (define comps1 (side-comps 1))
     (define sil-side (if (= (length comps0) 1) 0 1))
     (define blob (first (if (= sil-side 0) comps0 comps1)))
     (define pieces
       (sort-by (if (= sil-side 0) comps1 comps0)
                (lambda (p) (key (first p)))))
     (define (in? p lst)
       (< 0 (count-if (lambda (q) (and (= (first p) (first q))
                                       (= (second p) (second q))))
                      lst)))
     (define (search rem unused)
       (if (null? rem)
           (list)
           (let ((target (first rem)))
             (let try ((ps unused))
               (if (null? ps)
                   #f
                   (let* ((pc (first ps))
                          (anchor (first pc))
                          (dr (- (first target) (first anchor)))
                          (dc (- (second target) (second anchor)))
                          (placed (map (lambda (q)
                                         (list (+ (first q) dr)
                                               (+ (second q) dc)))
                                       pc)))
                     (if (= (length placed)
                            (count-if (lambda (q) (in? q rem)) placed))
                         (let ((sub (search
                                     (filter (lambda (q)
                                               (not (in? q placed)))
                                             rem)
                                     (filter (lambda (u)
                                               (not (equal? u pc)))
                                             unused))))
                           (if sub
                               (append
                                (map (lambda (q qq)
                                       (list (first q) (second q)
                                             (at g (first qq) (second qq))))
                                     placed pc)
                                sub)
                               (try (rest ps))))
                         (try (rest ps)))))))))
     (define placements (search blob pieces))
     (define rs (map first blob))
     (define cs (map second blob))
     (define r1 (max 0 (- (reduce min (first rs) rs) 1)))
     (define c1 (max 0 (- (reduce min (first cs) cs) 1)))
     (define r2 (min (- h 1) (+ (reduce max (first rs) rs) 1)))
     (define c2 (min (- w 1) (+ (reduce max (first cs) cs) 1)))
     (define sbg (side-bg sil-side))
     (grid-from-fn (+ (- r2 r1) 1) (+ (- c2 c1) 1)
                   (lambda (i j)
                     (let* ((r (+ r1 i)) (c (+ c1 j))
                            (hit (find-first
                                  (lambda (t) (and (= (first t) r)
                                                   (= (second t) c)))
                                  placements)))
                       (if hit (nth hit 2) sbg)))))))"""


def _modal(vals):
    best = vals[0]
    for v in vals:
        cb = vals.count(best)
        cv = vals.count(v)
        if cv > cb or (cv == cb and v < best):
            best = v
    return best


def _apply(g):
    """Python mirror of PROGRAM."""
    h, w = len(g), len(g[0])
    row_modals = [_modal(list(g[r])) for r in range(h)]
    col_modals = [_modal([g[r][c] for r in range(h)]) for c in range(w)]
    horiz = row_modals[0] != row_modals[-1]
    bg1 = row_modals[0] if horiz else col_modals[0]
    bg2 = row_modals[-1] if horiz else col_modals[-1]

    def split_score(s):
        if horiz:
            return sum(1 for r in range(0, s) for c in range(w)
                       if g[r][c] == bg1) + \
                sum(1 for r in range(s, h) for c in range(w)
                    if g[r][c] == bg2)
        return sum(1 for r in range(h) for c in range(0, s)
                   if g[r][c] == bg1) + \
            sum(1 for r in range(h) for c in range(s, w)
                if g[r][c] == bg2)

    split = 1
    for s in range(1, h if horiz else w):
        if split_score(s) > split_score(split):
            split = s

    def side_cells(sd):
        if horiz:
            rows = range(0, split) if sd == 0 else range(split, h)
            return [(r, c) for r in rows for c in range(w)]
        cols = range(0, split) if sd == 0 else range(split, w)
        return [(r, c) for r in range(h) for c in cols]

    def side_bg(sd):
        return _modal([g[r][c] for r, c in side_cells(sd)])

    def side_comps(sd):
        bg = side_bg(sd)
        cells = [(r, c) for r, c in side_cells(sd) if g[r][c] != bg]
        cellset = set(cells)
        seen = set()
        comps = []
        for seed in cells:
            if seed in seen:
                continue
            q = deque([seed])
            seen.add(seed)
            comp = [seed]
            while q:
                x, y = q.popleft()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nb = (x + dx, y + dy)
                        if nb in cellset and nb not in seen:
                            seen.add(nb)
                            q.append(nb)
                            comp.append(nb)
            comps.append(sorted(comp, key=lambda p: p[0] * 100 + p[1]))
        return comps

    comps0 = side_comps(0)
    comps1 = side_comps(1)
    sil = 0 if len(comps0) == 1 else 1
    blob = (comps0 if sil == 0 else comps1)[0]
    pieces = sorted(comps1 if sil == 0 else comps0,
                    key=lambda pc: pc[0][0] * 100 + pc[0][1])

    def search(rem, unused):
        if not rem:
            return []
        target = rem[0]
        remset = set(rem)
        for pi, pc in enumerate(unused):
            dr = target[0] - pc[0][0]
            dc = target[1] - pc[0][1]
            placed = [(r + dr, c + dc) for r, c in pc]
            if all(q in remset for q in placed):
                sub = search([q for q in rem if q not in set(placed)],
                             unused[:pi] + unused[pi + 1:])
                if sub is not None:
                    return [(q[0], q[1], g[qq[0]][qq[1]])
                            for q, qq in zip(placed, pc)] + sub
        return None

    placements = search(blob, pieces)
    rs = [r for r, _ in blob]
    cs = [c for _, c in blob]
    r1 = max(0, min(rs) - 1)
    c1 = max(0, min(cs) - 1)
    r2 = min(h - 1, max(rs) + 1)
    c2 = min(w - 1, max(cs) + 1)
    sbg = side_bg(sil)
    pmap = {(r, c): v for r, c, v in placements}
    return [[pmap.get((r, c), sbg) for c in range(c1, c2 + 1)]
            for r in range(r1, r2 + 1)]


def _make_blob(rng, bh, bw):
    """Connected union of 2-4 rectangles inside bh x bw."""
    cells = set()
    for _i in range(rng.randint(2, 4)):
        rh = rng.randint(2, max(2, bh - 2))
        rw = rng.randint(2, max(2, bw - 2))
        r0 = rng.randint(0, bh - rh)
        c0 = rng.randint(0, bw - rw)
        rect = {(r, c) for r in range(r0, r0 + rh)
                for c in range(c0, c0 + rw)}
        if not cells or rect & {(r + dr, c + dc) for r, c in cells
                                for dr in (-1, 0, 1) for dc in (-1, 0, 1)}:
            cells |= rect
    # connectivity check (4-conn)
    start = next(iter(cells))
    seen = {start}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (x + dx, y + dy)
            if nb in cells and nb not in seen:
                seen.add(nb)
                q.append(nb)
    if len(seen) != len(cells):
        raise ValueError("blob disconnected")
    return cells


def _partition(rng, cells, k):
    """Multi-source BFS growth into k connected pieces."""
    cells = set(cells)
    seeds = rng.sample(sorted(cells), k)
    owner = {s: i for i, s in enumerate(seeds)}
    frontier = deque(seeds)
    while frontier:
        p = frontier.popleft()
        nbs = [(p[0] + dr, p[1] + dc)
               for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        rng.shuffle(nbs)
        for nb in nbs:
            if nb in cells and nb not in owner:
                owner[nb] = owner[p]
                frontier.append(nb)
    pieces = {}
    for p, i in owner.items():
        pieces.setdefault(i, []).append(p)
    out = list(pieces.values())
    if len(out) != k or any(len(pc) < 2 for pc in out):
        raise ValueError("bad partition")
    return out


def _build_pair(rng, difficulty):
    k = {"easy": 3, "medium": 4, "hard": 6}[difficulty]
    bh = rng.randint(6, 9)
    bw = rng.randint(6, 9)
    blob_rel = _make_blob(rng, bh, bw)
    pieces_rel = _partition(rng, blob_rel, k)
    horiz = rng.random() < 0.5
    bg1, bg2, blobc = rng.sample(range(10), 3)
    pcolors = rng.sample([v for v in range(10) if v not in (bg1, bg2)], k)
    # sides: side0 = silhouette, side1 = content (orientation randomized
    # by transposing at the end)
    sil_h = bh + 4
    con_h = rng.randint(bh + 6, bh + 10)
    w = max(bw + 6, 14)
    w = min(w + rng.randint(0, 6), 28)
    h = sil_h + con_h
    if h > 30:
        raise ValueError("too tall")
    g = [[bg1 if r < sil_h else bg2 for c in range(w)] for r in range(h)]
    br0 = rng.randint(1, sil_h - bh - 1)
    bc0 = rng.randint(1, w - bw - 1)
    for r, c in blob_rel:
        g[br0 + r][bc0 + c] = blobc
    intended = {}
    occupied = set()
    for pc, col in zip(pieces_rel, pcolors):
        r0 = min(r for r, _ in pc)
        c0 = min(c for _, c in pc)
        rel = [(r - r0, c - c0) for r, c in pc]
        ph = max(r for r, _ in rel) + 1
        pw = max(c for _, c in rel) + 1
        two_tone = rng.random() < 0.3
        col2 = rng.choice([v for v in range(10)
                           if v not in (bg1, bg2, col)]) if two_tone else col
        colors = {(r, c): (col2 if two_tone and (r + c) % 2 else col)
                  for r, c in rel}
        placed = False
        for _try in range(300):
            rr = rng.randint(sil_h + 1, h - ph - 1)
            cc = rng.randint(1, w - pw - 1)
            cand = {(rr + r, cc + c) for r, c in rel}
            near = {(r + dr, c + dc) for r, c in cand
                    for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
            if near & occupied:
                continue
            for r, c in rel:
                g[rr + r][cc + c] = colors[(r, c)]
            occupied |= cand
            placed = True
            break
        if not placed:
            raise ValueError("could not scatter a piece")
        for (r, c) in pc:
            intended[(br0 + r, bc0 + c)] = colors[(r - r0, c - c0)]
    # intended output
    rs = [br0 + r for r, _ in blob_rel]
    cs = [bc0 + c for _, c in blob_rel]
    r1, c1 = max(0, min(rs) - 1), max(0, min(cs) - 1)
    r2, c2 = min(h - 1, max(rs) + 1), min(w - 1, max(cs) + 1)
    out = [[intended.get((r, c), bg1) for c in range(c1, c2 + 1)]
           for r in range(r1, r2 + 1)]
    if not horiz:
        g = [list(row) for row in zip(*g)]
        out = [list(row) for row in zip(*out)]
    got = _apply(g)
    if got != out:
        raise ValueError("solver found a different tiling")
    return g, out


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    n_train = ctx.draw_int("n_train", 2, 3)
    n_test = ctx.draw_int("n_test", 1, 2)
    pairs = []
    idx = 0
    attempts = 0
    while len(pairs) < n_train + n_test:
        rng = ctx.draw_rng(f"pair_{idx}_{attempts}")
        attempts += 1
        if attempts > 150:
            raise ValueError("could not build enough pairs")
        try:
            gin, gout = _build_pair(rng, difficulty)
        except (ValueError, IndexError):
            continue
        pairs.append({"input": gin, "output": gout})
        idx += 1
    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": PROGRAM,
        "concept": "jigsaw_pack",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.jigsaw_pack import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"jigsaw_pack gen1 v{VERSION}")
