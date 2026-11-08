"""gen1: shape progressions + gray-bracket window, two shape families.

Scene: n=3-5 shapes march along one axis with constant gap and affine
sizes, anchored on a shared top/bottom line, colored by a 2-3 color
cycle. Families: PERIODIC TOWERS (constant width, unit rows tiled i+base
times, optional cap row) and GROWING ARMS (t-like: spine column full
height, full rows at fixed anchor-distances, width and height +1 per
step). Two gray corner brackets frame the bbox (or a row-crop of it) of
the NEXT element (or the one BEFORE the first); output = its content.
Vertical variants transpose the whole scene. Scenes resample until the
detector's output equals the intended construction.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_sequence_window_gen1"

PROGRAM = """(rule!
 ;; SEQUENCE EXTRAPOLATION INTO A MARKED WINDOW. Shapes form a progression
 ;; along one axis (constant gap, affine widths/heights, common top /
 ;; bottom / center anchor line); two gray corner brackets frame a window
 ;; over a missing element (ahead of the last or before the first shape).
 ;; Each column-offset's content along the anchor-distance axis is read
 ;; from the deepest donor shape and extended by: shortest verified
 ;; period, else a phase-shift onto a longer column, else full-block
 ;; repetition. Per-column support extents extrapolate affinely (falling
 ;; back to same-parity shapes when they zigzag); single-colored shapes
 ;; recolor by their observed color cycle. Output the window's content.
 (lambda (g)
   (let ()
     (define (solve-h g W)
       (let ()
         (define h (rows g))
         (define w (cols g))
         (define (gray? o)
           (= (obj-size o)
              (count-if (lambda (p) (= (at g (first p) (second p)) 5))
                        (obj-cells o))))
         (define shapes
           (sort-by (filter (lambda (o) (not (gray? o)))
                            (objects-multicolor g 0))
                    (lambda (o) (second (obj-bbox o)))))
         (define n (length shapes))
         (define bbs (map obj-bbox shapes))
         (define (bb k) (nth bbs k))
         (define tops (map first bbs))
         (define bots (map (lambda (b) (nth b 2)) bbs))
         (define anchor
           (cond ((= 0 (count-if (lambda (t) (!= t (first tops))) tops)) 0)
                 ((= 0 (count-if (lambda (t) (!= t (first bots))) bots)) 1)
                 (else 2)))
         (define A2 (+ (first (first bbs)) (nth (first bbs) 2)))
         (define widths (map (lambda (b) (+ (- (nth b 3) (second b)) 1)) bbs))
         (define heights (map (lambda (b) (+ (- (nth b 2) (first b)) 1)) bbs))
         (define gap (- (second (nth bbs 1)) (+ (nth (first bbs) 3) 1)))
         (define dw (- (nth widths 1) (first widths)))
         (define dh (- (nth heights 1) (first heights)))
         (define colsets
           (map (lambda (o)
                  (unique (map (lambda (p) (at g (first p) (second p)))
                               (obj-cells o))))
                shapes))
         (define single (= 0 (count-if (lambda (cs) (!= (length cs) 1))
                                       colsets)))
         (define seqc (map first colsets))
         (define L
           (if single
               (find-first
                (lambda (cand)
                  (= 0 (count-if
                        (lambda (i) (!= (nth seqc i)
                                        (nth seqc (modulo i cand))))
                        (range 0 n))))
                (range 1 (+ n 1)))
               1))
         (define (dof k r)
           (cond ((= anchor 0) (- r (first (bb k))))
                 ((= anchor 1) (- (nth (bb k) 2) r))
                 (else (quotient (abs (- (* 2 r) A2)) 2))))
         (define (rof k d)
           (cond ((= anchor 0) (+ (first (bb k)) d))
                 ((= anchor 1) (- (nth (bb k) 2) d))
                 (else (+ (quotient A2 2) d))))
         (define (extent k j)
           (let* ((cc (+ (second (bb k)) j))
                  (ds (map (lambda (p) (dof k (first p)))
                           (filter (lambda (p) (= (second p) cc))
                                   (obj-cells (nth shapes k))))))
             (if (null? ds) -1 (reduce max (first ds) ds))))
         (define (vval k j d) (at g (rof k d) (+ (second (bb k)) j)))
         (define (geom m)
           (if (and (>= m 0) (< m n))
               (nth bbs m)
               (let* ((fwd (>= m n))
                      (sw (let loop ((k (if fwd n 0))
                                     (s (if fwd (+ (nth (nth bbs (- n 1)) 3)
                                                   1 gap)
                                            (second (first bbs))))
                                     (wd (if fwd (+ (nth widths (- n 1)) dw)
                                             (first widths)))
                                     (ht (if fwd (+ (nth heights (- n 1)) dh)
                                             (first heights))))
                            (if fwd
                                (if (< k m)
                                    (loop (+ k 1) (+ s wd gap) (+ wd dw)
                                          (+ ht dh))
                                    (list s wd ht))
                                (if (> k m)
                                    (loop (- k 1) (- s (+ gap (- wd dw)))
                                          (- wd dw) (- ht dh))
                                    (list s wd ht)))))
                      (s (first sw)) (wd (second sw)) (ht (nth sw 2))
                      (r1 (cond ((= anchor 0) (first (first bbs)))
                                ((= anchor 1) (+ (- (nth (first bbs) 2) ht) 1))
                                (else (quotient (- A2 (- ht 1)) 2)))))
                 (list r1 s (+ r1 (- ht 1)) (+ s (- wd 1))))))
         (define (overlap b)
           (* (max 0 (+ (- (min (nth W 3) (nth b 3))
                           (max (second W) (second b))) 1))
              (max 0 (+ (- (min (nth W 2) (nth b 2))
                           (max (first W) (first b))) 1))))
         (define m
           (reduce (lambda (best cand)
                     (if (> (overlap (geom cand)) (overlap (geom best)))
                         cand best))
                   (- 0 5)
                   (range (- 0 5) (+ n 8))))
         (define mb (geom m))
         (define wm (+ (- (nth mb 3) (second mb)) 1))
         (define (role k j) (min j (- (nth widths k) 1)))
         (define (dmax-m j)
           (let* ((es (map (lambda (k) (extent k (role k j))) (range 0 n)))
                  (diffs (map (lambda (i) (- (nth es (+ i 1)) (nth es i)))
                              (range 0 (- n 1)))))
             (if (= 0 (count-if (lambda (dd) (!= dd (first diffs))) diffs))
                 (+ (nth es (- n 1)) (* (first diffs) (- m (- n 1))))
                 (let ((sp (filter (lambda (k) (= 0 (modulo (- k m) 2)))
                                   (range 0 n))))
                   (if (>= (length sp) 2)
                       (let* ((k1 (nth sp (- (length sp) 2)))
                              (k2 (nth sp (- (length sp) 1)))
                              (e1 (nth es k1)) (e2 (nth es k2)))
                         (if (= 0 (modulo (- e2 e1) (- k2 k1)))
                             (+ e2 (* (quotient (- e2 e1) (- k2 k1))
                                      (- m k2)))
                             (nth es (- n 1))))
                       (nth es (- n 1)))))))
         (define (cseq j)
           (let* ((bk (reduce (lambda (best k)
                                (if (> (extent k (role k j))
                                       (extent best (role best j)))
                                    k best))
                              0 (range 0 n)))
                  (e (extent bk (role bk j))))
             (map (lambda (d) (vval bk (role bk j) d)) (range 0 (+ e 1)))))
         (define (seq-period seq)
           (let ((e (- (length seq) 1)))
             (find-first
              (lambda (p)
                (= 0 (count-if (lambda (x) (!= (nth seq x)
                                               (nth seq (- x p))))
                               (range p (+ e 1)))))
              (range 1 (+ (quotient (+ e 1) 2) 1)))))
         (define (extended j d)
           (let* ((seq (cseq j)) (e (- (length seq) 1)))
             (if (<= d e)
                 (nth seq d)
                 (let ((p (seq-period seq)))
                   (if p
                       (nth seq (+ (modulo (- d (+ e 1)) p)
                                   (- (+ e 1) p)))
                       (let ((hit
                              (find-first
                               (lambda (js)
                                 (let* ((j2 (first js)) (sig (second js))
                                        (s2 (cseq j2))
                                        (ov (filter (lambda (x)
                                                      (< (+ x sig)
                                                         (length s2)))
                                                    (range 0 (length seq)))))
                                   (and (> (length s2) (length seq))
                                        (>= (length ov) 3)
                                        (= 0 (count-if
                                              (lambda (x)
                                                (!= (nth seq x)
                                                    (nth s2 (+ x sig))))
                                              ov)))))
                               (flatmap (lambda (j2)
                                          (map (lambda (sig) (list j2 sig))
                                               (range 0 30)))
                                        (range 0 wm)))))
                         (if hit
                             (let ((s2 (cseq (first hit))))
                               (nth s2 (modulo (+ d (second hit))
                                               (length s2))))
                             (nth seq (modulo d (+ e 1))))))))))
         (define target (if single (nth seqc (modulo m L)) 0))
         (grid-from-fn (+ (- (nth W 2) (first W)) 1)
                       (+ (- (nth W 3) (second W)) 1)
                       (lambda (i jj)
                         (let ((r (+ (first W) i)) (c (+ (second W) jj)))
                           (if (not (and (<= (first mb) r) (<= r (nth mb 2))
                                         (<= (second mb) c)
                                         (<= c (nth mb 3))))
                               0
                               (let* ((j (- c (second mb)))
                                      (d (cond ((= anchor 0) (- r (first mb)))
                                               ((= anchor 1) (- (nth mb 2) r))
                                               (else (quotient
                                                      (abs (- (* 2 r) A2))
                                                      2)))))
                                 (if (> d (dmax-m j))
                                     0
                                     (let ((v (extended j d)))
                                       (if (and single (!= v 0))
                                           target v))))))))))
     (define marks
       (filter (lambda (o)
                 (= (obj-size o)
                    (count-if (lambda (p)
                                (= (at g (first p) (second p)) 5))
                              (obj-cells o))))
               (objects-multicolor g 0)))
     (define mcells (flatmap obj-cells marks))
     (define mrs (map first mcells))
     (define mcs (map second mcells))
     (define W0 (list (reduce min (first mrs) mrs)
                      (reduce min (first mcs) mcs)
                      (reduce max (first mrs) mrs)
                      (reduce max (first mcs) mcs)))
     (define others
       (sort-by (filter (lambda (o)
                          (< (count-if (lambda (p)
                                         (= (at g (first p) (second p)) 5))
                                       (obj-cells o))
                             (obj-size o)))
                        (objects-multicolor g 0))
                (lambda (o) (second (obj-bbox o)))))
     (define horiz
       (= 0 (count-if
             (lambda (i)
               (>= (nth (obj-bbox (nth others i)) 3)
                   (second (obj-bbox (nth others (+ i 1))))))
             (range 0 (- (length others) 1)))))
     (if horiz
         (solve-h g W0)
         (transpose
          (solve-h (transpose g)
                   (list (second W0) (first W0)
                         (nth W0 3) (nth W0 2))))))))"""


def _mc_comps(g):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != 0 and not seen[r][c]:
                comp = []
                q = deque([(r, c)])
                seen[r][c] = True
                while q:
                    x, y = q.popleft()
                    comp.append((x, y))
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < h and 0 <= ny < w \
                                    and not seen[nx][ny] and g[nx][ny] != 0:
                                seen[nx][ny] = True
                                q.append((nx, ny))
                out.append(comp)
    return out


def _transpose(g):
    return [list(row) for row in zip(*g)]


def _apply(g):
    """Python mirror of PROGRAM."""
    allc = _mc_comps(g)
    marks = [c for c in allc if all(g[r][cc] == 5 for r, cc in c)]
    mk = [x for c in marks for x in c]
    W = (min(r for r, _ in mk), min(c for _, c in mk),
         max(r for r, _ in mk), max(c for _, c in mk))
    shapes = [c for c in allc if not all(g[r][cc] == 5 for r, cc in c)]
    bbs = sorted(((min(r for r, _ in c), min(cc for _, cc in c),
                   max(r for r, _ in c), max(cc for _, cc in c))
                  for c in shapes), key=lambda b: b[1])
    horiz = all(bbs[i][3] < bbs[i + 1][1] for i in range(len(bbs) - 1))
    if not horiz:
        return _transpose(_apply_h(_transpose(g),
                                   (W[1], W[0], W[3], W[2])))
    return _apply_h(g, W)


def _apply_h(g, W):
    allc = _mc_comps(g)
    shapes = [c for c in allc if not all(g[r][cc] == 5 for r, cc in c)]
    shapes.sort(key=lambda c: min(cc for _, cc in c))
    bbs = [(min(r for r, _ in c), min(cc for _, cc in c),
            max(r for r, _ in c), max(cc for _, cc in c)) for c in shapes]
    n = len(shapes)
    if len({b[0] for b in bbs}) == 1:
        anchor = 0
    elif len({b[2] for b in bbs}) == 1:
        anchor = 1
    else:
        anchor = 2
    A2 = bbs[0][0] + bbs[0][2]
    widths = [b[3] - b[1] + 1 for b in bbs]
    heights = [b[2] - b[0] + 1 for b in bbs]
    gap = bbs[1][1] - bbs[0][3] - 1
    dw = widths[1] - widths[0]
    dh = heights[1] - heights[0]
    colsets = [sorted({g[r][c] for r, c in comp}) for comp in shapes]
    single = all(len(cs) == 1 for cs in colsets)
    seqc = [cs[0] for cs in colsets]
    L = 1
    if single:
        for cand in range(1, n + 1):
            if all(seqc[i] == seqc[i % cand] for i in range(n)):
                L = cand
                break

    def dof(k, r):
        if anchor == 0:
            return r - bbs[k][0]
        if anchor == 1:
            return bbs[k][2] - r
        return abs(2 * r - A2) // 2

    def rof(k, d):
        if anchor == 0:
            return bbs[k][0] + d
        if anchor == 1:
            return bbs[k][2] - d
        return (A2 // 2) + d

    def extent(k, j):
        c = bbs[k][1] + j
        ds = [dof(k, r) for r, cc in shapes[k] if cc == c]
        return max(ds) if ds else -1

    def val(k, j, d):
        return g[rof(k, d)][bbs[k][1] + j]

    def geom(m):
        if 0 <= m < n:
            return bbs[m]
        if m >= n:
            s = bbs[-1][3] + 1 + gap
            wd = widths[-1] + dw
            ht = heights[-1] + dh
            k = n
            while k < m:
                s = s + wd + gap
                wd += dw
                ht += dh
                k += 1
        else:
            s = bbs[0][1]
            wd = widths[0]
            ht = heights[0]
            k = 0
            while k > m:
                wd -= dw
                ht -= dh
                s = s - gap - wd
                k -= 1
        if anchor == 0:
            r1 = bbs[0][0]
        elif anchor == 1:
            r1 = bbs[0][2] - ht + 1
        else:
            r1 = (A2 - (ht - 1)) // 2
        return (r1, s, r1 + ht - 1, s + wd - 1)

    def overlap(b):
        return max(0, min(W[3], b[3]) - max(W[1], b[1]) + 1) * \
            max(0, min(W[2], b[2]) - max(W[0], b[0]) + 1)

    m = -5
    for cand in range(-5, n + 8):
        if overlap(geom(cand)) > overlap(geom(m)):
            m = cand
    mb = geom(m)
    wm = mb[3] - mb[1] + 1

    def role(k, j):
        return min(j, widths[k] - 1)

    def dmax_m(j):
        es = [extent(k, role(k, j)) for k in range(n)]
        diffs = [es[i + 1] - es[i] for i in range(n - 1)]
        if all(d == diffs[0] for d in diffs):
            return es[-1] + diffs[0] * (m - (n - 1))
        sp = [k for k in range(n) if (k - m) % 2 == 0]
        if len(sp) >= 2:
            k1, k2 = sp[-2], sp[-1]
            e1, e2 = es[k1], es[k2]
            if (e2 - e1) % (k2 - k1) == 0:
                return e2 + ((e2 - e1) // (k2 - k1)) * (m - k2)
        return es[-1]

    seqs = {}

    def cseq(j):
        if j not in seqs:
            bk = 0
            for k in range(n):
                if extent(k, role(k, j)) > extent(bk, role(bk, j)):
                    bk = k
            e = extent(bk, role(bk, j))
            seqs[j] = [val(bk, role(bk, j), d) for d in range(e + 1)]
        return seqs[j]

    def extended(j, d):
        seq = cseq(j)
        e = len(seq) - 1
        if d <= e:
            return seq[d]
        for p in range(1, (e + 1) // 2 + 1):
            if all(seq[x] == seq[x - p] for x in range(p, e + 1)):
                return seq[(d - (e + 1)) % p + (e + 1 - p)]
        for j2 in range(wm):
            s2 = cseq(j2)
            if len(s2) <= len(seq):
                continue
            for sig in range(0, 30):
                ov = [x for x in range(len(seq)) if x + sig < len(s2)]
                if len(ov) >= 3 and all(seq[x] == s2[x + sig] for x in ov):
                    return s2[(d + sig) % len(s2)]
        return seq[d % (e + 1)]

    target = seqc[m % L] if single else 0
    out = []
    for r in range(W[0], W[2] + 1):
        row = []
        for c in range(W[1], W[3] + 1):
            if not (mb[0] <= r <= mb[2] and mb[1] <= c <= mb[3]):
                row.append(0)
                continue
            j = c - mb[1]
            if anchor == 0:
                d = r - mb[0]
            elif anchor == 1:
                d = mb[2] - r
            else:
                d = abs(2 * r - A2) // 2
            if d > dmax_m(j):
                row.append(0)
                continue
            v = extended(j, d)
            row.append(target if (single and v != 0) else v)
        out.append(row)
    return out


def _tower_family(rng):
    """shape i = optional cap row + unit rows tiled (base+i) times."""
    wd = rng.randint(2, 4)
    p = rng.randint(1, 2)
    unit = [[1 if rng.random() < 0.7 else 0 for _ in range(wd)]
            for _ in range(p)]
    unit[0] = [1] * wd  # keep every tiling connected + column extents full
    cap = [[1] * wd] if rng.random() < 0.5 else []
    base = rng.randint(1, 2)

    def shape(i):
        rows = [r[:] for r in cap]
        for _ in range(base + i):
            rows += [r[:] for r in unit]
        return rows
    return shape, wd, 0


def _arm_family(rng):
    """t-like: spine column + full rows at fixed anchor-distances."""
    hb = rng.randint(3, 4)
    wb = rng.randint(2, 3)
    arms = sorted(rng.sample(range(0, 3), 2))
    if 0 not in arms:
        arms[0] = 0

    def shape(i):
        h, w = hb + i, wb + i
        rows = [[0] * w for _ in range(h)]
        for r in range(h):
            rows[r][0] = 1
        for a in arms:
            for c in range(w):
                rows[h - 1 - a][c] = 1
        return rows
    return shape, None, 1


def _build_pair(rng, difficulty):
    n = rng.randint(3, {"easy": 3, "medium": 4, "hard": 5}[difficulty])
    fam = rng.choice((_tower_family, _arm_family))
    shape, _, dwmode = fam(rng)
    L = rng.randint(2, 3)
    cycle = rng.sample([v for v in range(1, 10) if v != 5], L)
    gap = rng.randint(1, 2)
    anchor = rng.choice((0, 1))  # top / bottom aligned
    m = rng.choice((n, -1)) if n >= 3 else n
    if m == -1 and dwmode == 1 and shape(-1)[0].count(0) < 0:
        m = n
    idxs = list(range(n)) + [m]
    mats = {i: shape(i) for i in idxs}
    if m == -1 and (len(mats[-1]) < 2 or len(mats[-1][0]) < 1):
        raise ValueError("backward shape degenerate")
    heights = {i: len(mats[i]) for i in idxs}
    widths = {i: len(mats[i][0]) for i in idxs}
    maxh = max(heights.values())
    total_w = sum(widths[i] + gap for i in idxs) - gap
    h = maxh + rng.randint(4, 8)
    w = total_w + rng.randint(2, 6)
    if h > 30 or w > 30:
        raise ValueError("scene too large")
    g = [[0] * w for _ in range(h)]
    anchor_row = rng.randint(2, h - maxh - 1) + (maxh - 1 if anchor == 1
                                                 else 0)
    order = ([m] + list(range(n))) if m == -1 else (list(range(n)) + [m])
    c0 = rng.randint(1, w - total_w - 1)
    boxes = {}
    for i in order:
        ht, wd = heights[i], widths[i]
        r1 = anchor_row if anchor == 0 else anchor_row - ht + 1
        boxes[i] = (r1, c0, r1 + ht - 1, c0 + wd - 1)
        if i != m:
            col = cycle[i % L]
            for rr in range(ht):
                for cc in range(wd):
                    if mats[i][rr][cc]:
                        g[r1 + rr][c0 + cc] = col
        c0 += wd + gap
    # window: full bbox of shape m, or a crop along rows
    r1, c1, r2, c2 = boxes[m]
    if rng.random() < 0.4 and r2 - r1 >= 3:
        cut = rng.randint(1, r2 - r1 - 1)
        if anchor == 0:
            r2 -= cut
        else:
            r1 += cut
    if r2 - r1 < 1 or c2 - c1 < 1:
        raise ValueError("window too small")
    # gray corner brackets
    for rr, cc in ((r1, c1), (r1, c1 + 1), (r1 + 1, c1),
                   (r2, c2), (r2, c2 - 1), (r2 - 1, c2)):
        if g[rr][cc] != 0:
            raise ValueError("marker collides")
        g[rr][cc] = 5
    # intended output: shape m content, cropped to the window
    col_m = cycle[m % L]
    mb = boxes[m]
    out = []
    for r in range(r1, r2 + 1):
        row = []
        for c in range(c1, c2 + 1):
            rr, cc = r - mb[0], c - mb[1]
            row.append(col_m if mats[m][rr][cc] else 0)
        out.append(row)
    if rng.random() < 0.5:
        g = _transpose(g)
        out = _transpose(out)
    got = _apply(g)
    if got != out:
        raise ValueError("detector output differs from construction")
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
        "concept": "sequence_window",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.sequence_window import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"sequence_window gen1 v{VERSION}")
