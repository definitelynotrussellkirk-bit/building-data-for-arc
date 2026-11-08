"""gen1: in-grid demo pair teaches f; apply f to the query box.

Scene: a dense >=4-color noise field carries four one-cell-thick boxes of
equal interior size: a DEMO pair (X, f(X)) far from an EMPTY answer slot,
and a QUERY box adjacent to the slot (so the nearest-to-empty rule picks
it). f is drawn from the library (complement / connect-aligned-dots /
flip-lr / flip-ud / rotate-180); scenes are resampled until the detector
finds exactly the four intended boxes, classifies the query correctly,
and the demo pair identifies the INTENDED f unambiguously.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_demo_transfer_gen1"

PROGRAM = """(rule!
 ;; META-TASK: four small one-cell-thick boxes (uniform nonzero ring, mostly
 ;; black interior, <=2 nonzero interior colors) sit on a noisy field. One
 ;; box is EMPTY (the answer slot); the non-empty box NEAREST it is the
 ;; QUERY; the other two are an in-grid DEMO pair (X, f(X)). Identify f by
 ;; mask-testing a library (complement / connect-aligned-dots / flip-lr /
 ;; flip-ud / rotate-180) against the demo in either direction, then output
 ;; f applied to the query's interior (new cells take the query's modal
 ;; nonzero color).
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define (ring-ps r1 c1 r2 c2)
       (append (map (lambda (c) (list r1 c)) (range c1 (+ c2 1)))
               (map (lambda (c) (list r2 c)) (range c1 (+ c2 1)))
               (map (lambda (r) (list r c1)) (range r1 (+ r2 1)))
               (map (lambda (r) (list r c2)) (range r1 (+ r2 1)))))
     (define (inner-vals b)
       (flatmap (lambda (r) (map (lambda (c) (at g r c))
                                 (range (+ (second b) 1) (nth b 3))))
                (range (+ (first b) 1) (nth b 2))))
     (define (box-ok? b)
       (let ((r1 (first b)) (c1 (second b)) (r2 (nth b 2)) (c2 (nth b 3))
             (k (at g (first b) (second b))))
         (and (!= k 0)
              (let ((ps (ring-ps r1 c1 r2 c2)))
                (= (length ps)
                   (count-if (lambda (p) (= (at g (first p) (second p)) k))
                             ps)))
              (let* ((vals (inner-vals b))
                     (zeros (count-if (lambda (v) (= v 0)) vals))
                     (nz (filter (lambda (v)
                                   (< 0 (count-if (lambda (u) (= u v)) vals)))
                                 (range 1 10))))
                (and (>= (* 4 zeros) (length vals))
                     (<= (length nz) 2)
                     (not (member? k nz)))))))
     (define boxes
       (filter box-ok?
               (flatmap
                (lambda (r1)
                  (flatmap
                   (lambda (c1)
                     (flatmap
                      (lambda (dh)
                        (flatmap
                         (lambda (dw)
                           (if (and (< (+ r1 dh) h) (< (+ c1 dw) w))
                               (list (list r1 c1 (+ r1 dh) (+ c1 dw)))
                               (list)))
                         (range 5 10)))
                      (range 5 10)))
                   (range 0 w)))
                (range 0 h))))
     (define (empty-box? b)
       (= 0 (count-if (lambda (v) (!= v 0)) (inner-vals b))))
     (define hole (find-first empty-box? boxes))
     (define others (filter (lambda (b) (not (equal? b hole))) boxes))
     (define (dist2 b)
       (let ((dr (- (+ (first b) (nth b 2)) (+ (first hole) (nth hole 2))))
             (dc (- (+ (second b) (nth b 3)) (+ (second hole) (nth hole 3)))))
         (+ (* dr dr) (* dc dc))))
     (define query
       (reduce (lambda (best b) (if (< (dist2 b) (dist2 best)) b best))
               (first others) others))
     (define demos (filter (lambda (b) (not (equal? b query))) others))
     (define (inner b)
       (subgrid g (+ (first b) 1) (+ (second b) 1)
                (- (nth b 2) 1) (- (nth b 3) 1)))
     (define X (inner (first demos)))
     (define Y (inner (second demos)))
     (define Z (inner query))
     (define (mask m)
       (grid-from-fn (rows m) (cols m)
                     (lambda (r c) (if (= (at m r c) 0) 0 1))))
     (define (compl m)
       (grid-from-fn (rows m) (cols m)
                     (lambda (r c) (- 1 (at m r c)))))
     (define (connectm m)
       (let ((hh (rows m)) (ww (cols m)))
         (define (on? r c) (= (at m r c) 1))
         (define (before-row r c)
           (< 0 (count-if (lambda (j) (on? r j)) (range 0 c))))
         (define (after-row r c)
           (< 0 (count-if (lambda (j) (on? r j)) (range (+ c 1) ww))))
         (define (before-col r c)
           (< 0 (count-if (lambda (i) (on? i c)) (range 0 r))))
         (define (after-col r c)
           (< 0 (count-if (lambda (i) (on? i c)) (range (+ r 1) hh))))
         (grid-from-fn hh ww
                       (lambda (r c)
                         (if (or (on? r c)
                                 (and (before-row r c) (after-row r c))
                                 (and (before-col r c) (after-col r c)))
                             1 0)))))
     (define (mf i m)
       (cond ((= i 0) (compl m))
             ((= i 1) (connectm m))
             ((= i 2) (flip-lr m))
             ((= i 3) (flip-ud m))
             (else (rotate-180 m))))
     (define mx (mask X))
     (define my (mask Y))
     (define f-id
       (find-first (lambda (i) (or (equal? (mf i mx) my)
                                   (equal? (mf i my) mx)))
                   (list 0 1 2 3 4)))
     (define zvals (flatmap (lambda (row) row) Z))
     (define (cnt v) (count-if (lambda (u) (= u v)) zvals))
     (define modal
       (reduce (lambda (best v) (if (> (cnt v) (cnt best)) v best))
               1 (range 1 10)))
     (cond ((= f-id 0)
            (grid-from-fn (rows Z) (cols Z)
                          (lambda (r c) (if (= (at Z r c) 0) modal 0))))
           ((= f-id 1)
            (let ((cm (connectm (mask Z))))
              (grid-from-fn (rows Z) (cols Z)
                            (lambda (r c)
                              (if (!= (at Z r c) 0)
                                  (at Z r c)
                                  (if (= (at cm r c) 1) modal 0))))))
           ((= f-id 2) (flip-lr Z))
           ((= f-id 3) (flip-ud Z))
           (else (rotate-180 Z))))))"""

SIZES = (5, 10)  # ring bbox side range checked by the rule: 6..10


def _detect_boxes(g):
    """Python mirror of the rule's ring scan (same enumeration order)."""
    h, w = len(g), len(g[0])
    boxes = []
    for r1 in range(h):
        for c1 in range(w):
            for dh in range(5, 10):
                for dw in range(5, 10):
                    r2, c2 = r1 + dh, c1 + dw
                    if r2 >= h or c2 >= w:
                        continue
                    k = g[r1][c1]
                    if k == 0:
                        continue
                    if any(g[r1][c] != k or g[r2][c] != k
                           for c in range(c1, c2 + 1)):
                        continue
                    if any(g[r][c1] != k or g[r][c2] != k
                           for r in range(r1, r2 + 1)):
                        continue
                    vals = [g[r][c] for r in range(r1 + 1, r2)
                            for c in range(c1 + 1, c2)]
                    zeros = sum(1 for v in vals if v == 0)
                    nz = {v for v in vals if v}
                    if 4 * zeros >= len(vals) and len(nz) <= 2 and k not in nz:
                        boxes.append((r1, c1, r2, c2))
    return boxes


def _mask(m):
    return tuple(tuple(1 if v else 0 for v in row) for row in m)


def _compl(m):
    return tuple(tuple(1 - v for v in row) for row in m)


def _connect(m):
    hh, ww = len(m), len(m[0])
    def on(r, c):
        return m[r][c] == 1
    out = []
    for r in range(hh):
        row = []
        for c in range(ww):
            fill = on(r, c) \
                or (any(on(r, j) for j in range(c)) and
                    any(on(r, j) for j in range(c + 1, ww))) \
                or (any(on(i, c) for i in range(r)) and
                    any(on(i, c) for i in range(r + 1, hh)))
            row.append(1 if fill else 0)
        out.append(tuple(row))
    return tuple(out)


def _flip_lr(m):
    return tuple(tuple(reversed(row)) for row in m)


def _flip_ud(m):
    return tuple(reversed([tuple(row) for row in m]))


def _rot180(m):
    return _flip_lr(_flip_ud(m))


_LIB = (_compl, _connect, _flip_lr, _flip_ud, _rot180)


def _apply(g):
    """Python mirror of PROGRAM."""
    boxes = _detect_boxes(g)

    def inner(b):
        r1, c1, r2, c2 = b
        return [row[c1 + 1:c2] for row in g[r1 + 1:r2]]

    hole = next(b for b in boxes
                if all(v == 0 for row in inner(b) for v in row))
    others = [b for b in boxes if b != hole]

    def dist2(b):
        dr = (b[0] + b[2]) - (hole[0] + hole[2])
        dc = (b[1] + b[3]) - (hole[1] + hole[3])
        return dr * dr + dc * dc

    query = others[0]
    for b in others[1:]:
        if dist2(b) < dist2(query):
            query = b
    demos = [b for b in others if b != query]
    X, Y, Z = inner(demos[0]), inner(demos[1]), inner(query)
    mx, my = _mask(X), _mask(Y)
    f_id = next(i for i, f in enumerate(_LIB)
                if f(mx) == my or f(my) == mx)
    zvals = [v for row in Z for v in row]

    def cnt(v):
        return sum(1 for u in zvals if u == v)

    modal = 1
    for v in range(1, 10):
        if cnt(v) > cnt(modal):
            modal = v
    if f_id == 0:
        return [[modal if v == 0 else 0 for v in row] for row in Z]
    if f_id == 1:
        cm = _connect(_mask(Z))
        return [[Z[r][c] if Z[r][c] else (modal if cm[r][c] else 0)
                 for c in range(len(Z[0]))] for r in range(len(Z))]
    if f_id == 2:
        return [list(reversed(row)) for row in Z]
    if f_id == 3:
        return [list(row) for row in reversed(Z)]
    return [list(reversed(row)) for row in reversed(Z)]


def _rand_mask(rng, s, density):
    while True:
        m = tuple(tuple(1 if rng.random() < density else 0 for _ in range(s))
                  for _ in range(s))
        n = sum(v for row in m for v in row)
        if 2 <= n <= int(s * s * 0.55):
            return m


def _dots_mask(rng, s):
    """3-5 sparse points with at least one row/col-aligned distant pair."""
    while True:
        pts = rng.sample([(r, c) for r in range(s) for c in range(s)],
                         rng.randint(3, 5))
        aligned = any((a[0] == b[0] and abs(a[1] - b[1]) > 1) or
                      (a[1] == b[1] and abs(a[0] - b[0]) > 1)
                      for a in pts for b in pts if a != b)
        if not aligned:
            continue
        m = [[0] * s for _ in range(s)]
        for r, c in pts:
            m[r][c] = 1
        return tuple(tuple(row) for row in m)


def _unique_f(mx, my, f_id):
    hits = [i for i, f in enumerate(_LIB) if f(mx) == my or f(my) == mx]
    return hits and hits[0] == f_id


def _stamp_box(g, r0, c0, ring, pat, color):
    s = len(pat)
    for i in range(s + 2):
        for j in range(s + 2):
            on_ring = i in (0, s + 1) or j in (0, s + 1)
            g[r0 + i][c0 + j] = ring if on_ring else \
                (color if pat[i - 1][j - 1] else 0)


def _build_pair(rng, difficulty):
    s = {"easy": 4, "medium": 4, "hard": 5}[difficulty]
    bs = s + 2
    f_id = rng.randrange(len(_LIB))
    for _attempt in range(120):
        mx = _dots_mask(rng, s) if f_id == 1 else _rand_mask(rng, s, 0.4)
        my = _LIB[f_id](mx)
        nmy = sum(v for row in my for v in row)
        if not (1 <= nmy <= int(s * s * 0.75)):
            continue
        if not _unique_f(mx, my, f_id):
            continue
        mz = _dots_mask(rng, s) if f_id == 1 else _rand_mask(rng, s, 0.4)
        h = rng.randint(26, 30)
        w = rng.randint(26, 30)
        noise_pal = rng.sample(range(1, 10), 4)
        g = [[rng.choice(noise_pal) for _ in range(w)] for _ in range(h)]
        ring = rng.choice([v for v in range(1, 10)])
        dcol = rng.choice([v for v in range(1, 10) if v != ring])
        qcol = rng.choice([v for v in range(1, 10) if v != ring])
        # demo pair top-left, query + empty slot bottom-right
        gap = rng.randint(1, 2)
        _stamp_box(g, 1, 1, ring, mx, dcol)
        _stamp_box(g, 1, 1 + bs + gap, ring, my, dcol)
        qr = h - bs - 1
        qc = w - 2 * bs - gap - 1
        _stamp_box(g, qr, qc, ring, mz, qcol)
        empty = tuple(tuple(0 for _ in range(s)) for _ in range(s))
        _stamp_box(g, qr, qc + bs + gap, ring, empty, 0)
        boxes = _detect_boxes(g)
        if len(boxes) != 4:
            continue
        expected = sorted([(1, 1), (1, 1 + bs + gap),
                           (qr, qc), (qr, qc + bs + gap)])
        if sorted((b[0], b[1]) for b in boxes) != expected:
            continue
        out = _apply(g)
        intended = _apply_f(f_id, mz, qcol)
        if out != intended:
            continue
        return g, out
    raise ValueError("could not build a well-posed scene")


def _apply_f(f_id, mz, qcol):
    Z = [[qcol if v else 0 for v in row] for row in mz]
    if f_id == 0:
        return [[qcol if v == 0 else 0 for v in row] for row in Z]
    if f_id == 1:
        cm = _connect(_mask(Z))
        return [[Z[r][c] if Z[r][c] else (qcol if cm[r][c] else 0)
                 for c in range(len(Z[0]))] for r in range(len(Z))]
    if f_id == 2:
        return [list(reversed(row)) for row in Z]
    if f_id == 3:
        return [list(row) for row in reversed(Z)]
    return [list(reversed(row)) for row in reversed(Z)]


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
        "concept": "demo_transfer",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.demo_transfer import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"demo_transfer gen1 v{VERSION}")
