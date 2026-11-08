"""gen1: box lattices wired by a sequence strip.

Scene: a sparse lattice of framed boxes (one frame color; size 3 = single
core, 4 = 2x2 core, 5 = single core inside a frame-colored interior),
core colors mostly distinct with occasional duplicates; a strip of
isolated cells spells a non-revisiting WALK over the boxes. Transform:
bridge each consecutive pair through the clear gap along the earlier
box's core band, painted in the earlier entry's color. Scenes resample
until the rule's first-fit backtracker reproduces the intended walk.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_chain_bridge_gen1"

PROGRAM = """(rule!
 ;; SEQUENCE BRIDGES: framed boxes with a single core color sit on a
 ;; lattice; a strip of isolated cells spells a COLOR CHAIN. Consecutive
 ;; chain entries name boxes (duplicates resolved by walking: consecutive
 ;; boxes must face each other across a clear gap, no box revisited);
 ;; each pair is joined by a bridge through the gap along the earlier
 ;; box's core band, painted in the earlier entry's color.
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define allv
       (flatmap (lambda (r) (map (lambda (c) (at g r c)) (range 0 w)))
                (range 0 h)))
     (define bg
       (reduce (lambda (b v)
                 (if (> (count-if (lambda (u) (= u v)) allv)
                        (count-if (lambda (u) (= u b)) allv))
                     v b))
               (first allv) allv))
     (define (ring? r c s)
       (let ((f (at g r c)))
         (and (!= f bg) (< (+ r s) (+ h 1)) (< (+ c s) (+ w 1))
              (= 0 (count-if
                    (lambda (i) (or (!= (at g (+ r i) c) f)
                                    (!= (at g (+ r i) (+ c s -1)) f)
                                    (!= (at g r (+ c i)) f)
                                    (!= (at g (+ r s -1) (+ c i)) f)))
                    (range 0 s))))))
     (define (core-cells r c s)
       (let ((f (at g r c)))
         (filter (lambda (p) (!= (at g (first p) (second p)) f))
                 (flatmap (lambda (i)
                            (map (lambda (j) (list (+ r i) (+ c j)))
                                 (range 1 (- s 1))))
                          (range 1 (- s 1))))))
     (define raw-boxes
       (flatmap
        (lambda (r)
          (flatmap
           (lambda (c)
             (flatmap
              (lambda (s)
                (if (ring? r c s)
                    (let ((cores (core-cells r c s)))
                      (if (and (not (null? cores))
                               (= 0 (count-if
                                     (lambda (p) (= (at g (first p)
                                                        (second p)) bg))
                                     cores))
                               (= 1 (length
                                     (unique (map (lambda (p)
                                                    (at g (first p)
                                                        (second p)))
                                                  cores)))))
                          (list (list r c s
                                      (at g (first (first cores))
                                          (second (first cores)))
                                      cores))
                          (list)))
                    (list)))
              (range 3 9)))
           (range 0 w)))
        (range 0 h)))
     (define boxes
       (let loop ((cand (sort-by raw-boxes (lambda (b) (- 0 (nth b 2)))))
                  (acc (list)))
         (if (null? cand)
             acc
             (let* ((b (first cand))
                    (key (sort-by (nth b 4)
                                  (lambda (p) (+ (* (first p) 100)
                                                 (second p)))))
                    (dup (< 0 (count-if
                               (lambda (a)
                                 (equal? key
                                         (sort-by (nth a 4)
                                                  (lambda (p)
                                                    (+ (* (first p) 100)
                                                       (second p))))))
                               acc))))
               (loop (rest cand) (if dup acc (append acc (list b))))))))
     (define (in-box? r c)
       (< 0 (count-if (lambda (b)
                        (and (>= r (first b)) (< r (+ (first b) (nth b 2)))
                             (>= c (second b))
                             (< c (+ (second b) (nth b 2)))))
                      boxes)))
     (define seq
       (find-first
        (lambda (s) (>= (length s) 2))
        (map (lambda (r)
               (map (lambda (c) (at g r c))
                    (filter (lambda (c)
                              (and (!= (at g r c) bg)
                                   (not (in-box? r c))))
                            (range 0 w))))
             (range 0 h))))
     (define (rowlap? a b)
       (and (< (first a) (+ (first b) (nth b 2)))
            (< (first b) (+ (first a) (nth a 2)))))
     (define (collap? a b)
       (and (< (second a) (+ (second b) (nth b 2)))
            (< (second b) (+ (second a) (nth a 2)))))
     (define (adj a b)
       (cond
        ((rowlap? a b)
         (let* ((lo (if (< (second a) (second b)) a b))
                (hi (if (< (second a) (second b)) b a)))
           (if (or (> (+ (second lo) (nth lo 2)) (second hi))
                   (< 0 (count-if
                         (lambda (o)
                           (and (not (equal? o a)) (not (equal? o b))
                                (rowlap? o a)
                                (>= (second o) (+ (second lo) (nth lo 2)))
                                (< (second o) (second hi))))
                         boxes)))
               (list)
               (list 0 lo hi))))
        ((collap? a b)
         (let* ((lo (if (< (first a) (first b)) a b))
                (hi (if (< (first a) (first b)) b a)))
           (if (or (> (+ (first lo) (nth lo 2)) (first hi))
                   (< 0 (count-if
                         (lambda (o)
                           (and (not (equal? o a)) (not (equal? o b))
                                (collap? o a)
                                (>= (first o) (+ (first lo) (nth lo 2)))
                                (< (first o) (first hi))))
                         boxes)))
               (list)
               (list 1 lo hi))))
        (else (list))))
     (define nseq (length seq))
     (define (chain i prev used)
       (if (= i nseq)
           (list)
           (let try ((bs boxes))
             (if (null? bs)
                 #f
                 (let ((b (first bs)))
                   (if (or (member? b used)
                           (!= (nth b 3) (nth seq i))
                           (and (not (null? prev))
                                (null? (adj prev b))))
                       (try (rest bs))
                       (let ((rest-path (chain (+ i 1) b
                                               (append used (list b)))))
                         (if rest-path
                             (append (list b) rest-path)
                             (try (rest bs))))))))))
     (define path (chain 0 (list) (list)))
     (for*/fold ((out g)) ((i (in-range 0 (- nseq 1))))
       (let* ((a (nth path i))
              (b (nth path (+ i 1)))
              (kd (adj a b))
              (kind (first kd))
              (lo (second kd))
              (hi (nth kd 2))
              (col (nth seq i)))
         (if (= kind 0)
             (for*/fold ((o out))
                 ((rr (in-range 0 h)) (cc (in-range (+ (second lo)
                                                       (nth lo 2))
                                                    (second hi))))
               (if (< 0 (count-if (lambda (p) (= (first p) rr))
                                  (nth a 4)))
                   (set-cell o rr cc col)
                   o))
             (for*/fold ((o out))
                 ((rr (in-range (+ (first lo) (nth lo 2)) (first hi)))
                  (cc (in-range 0 w)))
               (if (< 0 (count-if (lambda (p) (= (second p) cc))
                                  (nth a 4)))
                   (set-cell o rr cc col)
                   o))))))))"""


def _apply(g):
    """Python mirror of PROGRAM."""
    h, w = len(g), len(g[0])
    flat = [v for row in g for v in row]
    bg = flat[0]
    for v in flat:
        if flat.count(v) > flat.count(bg):
            bg = v
    raw = []
    for r in range(h):
        for c in range(w):
            F = g[r][c]
            if F == bg:
                continue
            for s in range(3, 9):
                if r + s > h or c + s > w:
                    continue
                if not all(g[r+i][c] == F and g[r+i][c+s-1] == F and
                           g[r][c+i] == F and g[r+s-1][c+i] == F
                           for i in range(s)):
                    continue
                cores = [(r+i, c+j) for i in range(1, s-1)
                         for j in range(1, s-1) if g[r+i][c+j] != F]
                if not cores or any(g[rr][cc] == bg for rr, cc in cores):
                    continue
                if len({g[rr][cc] for rr, cc in cores}) != 1:
                    continue
                raw.append((r, c, s, g[cores[0][0]][cores[0][1]], cores))
    boxes = []
    seen = set()
    for b in sorted(raw, key=lambda b: -b[2]):
        key = tuple(sorted(b[4]))
        if key in seen:
            continue
        seen.add(key)
        boxes.append(b)

    def in_box(r, c):
        return any(b[0] <= r < b[0]+b[2] and b[1] <= c < b[1]+b[2]
                   for b in boxes)

    seq = None
    for r in range(h):
        cells = [c for c in range(w)
                 if g[r][c] != bg and not in_box(r, c)]
        if len(cells) >= 2:
            seq = [g[r][c] for c in sorted(cells)]
            break

    def rowlap(a, b):
        return a[0] < b[0]+b[2] and b[0] < a[0]+a[2]

    def collap(a, b):
        return a[1] < b[1]+b[2] and b[1] < a[1]+a[2]

    def adj(a, b):
        if rowlap(a, b):
            lo, hi = (a, b) if a[1] < b[1] else (b, a)
            if lo[1]+lo[2] > hi[1]:
                return None
            for o in boxes:
                if o is a or o is b:
                    continue
                if rowlap(o, a) and lo[1]+lo[2] <= o[1] < hi[1]:
                    return None
            return (0, lo, hi)
        if collap(a, b):
            lo, hi = (a, b) if a[0] < b[0] else (b, a)
            if lo[0]+lo[2] > hi[0]:
                return None
            for o in boxes:
                if o is a or o is b:
                    continue
                if collap(o, a) and lo[0]+lo[2] <= o[0] < hi[0]:
                    return None
            return (1, lo, hi)
        return None

    def chain(i, prev, used):
        if i == len(seq):
            return []
        for b in boxes:
            if id(b) in used or b[3] != seq[i]:
                continue
            if prev is not None and adj(prev, b) is None:
                continue
            rest = chain(i+1, b, used | {id(b)})
            if rest is not None:
                return [b] + rest
        return None

    path = chain(0, None, frozenset())
    out = [row[:] for row in g]
    for i in range(len(seq)-1):
        a, b = path[i], path[i+1]
        kind, lo, hi = adj(a, b)
        col = seq[i]
        if kind == 0:
            band = {rr for rr, _ in a[4]}
            for rr in band:
                for cc in range(lo[1]+lo[2], hi[1]):
                    out[rr][cc] = col
        else:
            band = {cc for _, cc in a[4]}
            for cc in band:
                for rr in range(lo[0]+lo[2], hi[0]):
                    out[rr][cc] = col
    return out


def _build_pair(rng, difficulty):
    s = rng.choice((3, 4, 5))
    gap = rng.randint(1, 4)
    pitch = s + gap
    gr = rng.randint(2, 3)
    gc = rng.randint(2, 4)
    bg = rng.randint(0, 9)
    F = rng.choice([v for v in range(10) if v != bg])
    core_pool = [v for v in range(10) if v not in (bg, F)]
    h = gr * pitch + 4
    w = max(gc * pitch + 2, 2 * (gr * gc) + 2)
    if h > 30 or w > 30:
        raise ValueError("too big")
    # sparse lattice
    slots = [(i, j) for i in range(gr) for j in range(gc)]
    n_boxes = rng.randint(max(4, gr * gc - 2), gr * gc)
    slots = rng.sample(slots, min(n_boxes, len(slots)))
    if len(slots) < 4:
        raise ValueError("too few boxes")
    cores = {}
    for sl in slots:
        cores[sl] = rng.choice(core_pool)
    # occasional duplicate is fine (chain resolves); build the walk
    order = []
    cur = rng.choice(slots)
    order.append(cur)
    for _ in range(rng.randint(3, len(slots) - 1)):
        cands = []
        for d in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            k = 1
            while True:
                nxt = (cur[0] + d[0] * k, cur[1] + d[1] * k)
                if not (0 <= nxt[0] < gr and 0 <= nxt[1] < gc):
                    break
                if nxt in slots:
                    if nxt not in order:
                        cands.append(nxt)
                    break
                k += 1
        if not cands:
            break
        cur = rng.choice(cands)
        order.append(cur)
    if len(order) < 3:
        raise ValueError("walk too short")
    g = [[bg] * w for _ in range(h)]
    for (i, j) in slots:
        r0, c0 = 1 + i * pitch, 1 + j * pitch
        col = cores[(i, j)]
        for a in range(s):
            for b in range(s):
                ring = a in (0, s-1) or b in (0, s-1)
                if ring:
                    g[r0+a][c0+b] = F
                elif s == 4:
                    g[r0+a][c0+b] = col
                elif (a, b) == (s // 2, s // 2):
                    g[r0+a][c0+b] = col
                else:
                    g[r0+a][c0+b] = F
    strip_r = h - 2
    for k, sl in enumerate(order):
        c = 1 + 2 * k
        if c >= w:
            raise ValueError("strip overflow")
        g[strip_r][c] = cores[sl]
    out = _apply(g)
    # well-posedness: the backtracker must reproduce the INTENDED walk's
    # bridges — verify every intended gap got painted
    for i in range(len(order) - 1):
        a, b = order[i], order[i + 1]
        col = cores[a]
        ra, ca = 1 + a[0] * pitch, 1 + a[1] * pitch
        rb, cb = 1 + b[0] * pitch, 1 + b[1] * pitch
        if a[0] == b[0]:
            cc = (min(ca, cb) + s + max(ca, cb)) // 2
            rr = ra + s // 2
        else:
            rr = (min(ra, rb) + s + max(ra, rb)) // 2
            cc = ca + s // 2
        if out[rr][cc] != col:
            raise ValueError("backtracker diverged from intended walk")
    return g, out


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
        if attempts > 100:
            raise ValueError("could not build enough pairs")
        try:
            gin, gout = _build_pair(rng, difficulty)
        except (ValueError, IndexError, TypeError):
            continue
        pairs.append({"input": gin, "output": gout})
        idx += 1
    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": PROGRAM,
        "concept": "chain_bridge",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.chain_bridge import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"chain_bridge gen1 v{VERSION}")
