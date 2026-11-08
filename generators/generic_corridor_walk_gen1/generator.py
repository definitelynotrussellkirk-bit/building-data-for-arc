"""gen1: staircase corridors walked with repeating patterns.

Scene: a bg terrain holds 1-2 one-wide staircase CORRIDORS of a second
terrain (segments >= 3, non-consecutive cells kept >= 2 apart) plus a few
detached corridor-colored blobs; a legend row of 2x2 swatches (pattern),
a 2x2 turn-marker square, and a pattern[0]-colored single cell at each
corridor's border mouth. Transform: walk each corridor painting the
pattern, stamp the marker color ahead at each turn, dissolve the legend
squares. Scenes resample until the walk covers the constructed corridor
exactly.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_corridor_walk_gen1"

PROGRAM = """(rule!
 ;; CORRIDOR WALK: two terrain colors; a legend row of 2x2 swatches (top-
 ;; left) gives a repeating path PATTERN; another 2x2 square gives the
 ;; TURN-MARKER color; single border cells are path STARTS. Each path
 ;; walks inward through the corridor terrain, painting the pattern;
 ;; when the cell ahead leaves the corridor it is stamped with the marker
 ;; color and the walk turns into the perpendicular corridor run of
 ;; length >= 2 (longest wins), stopping at dead ends or the grid edge.
 ;; Legend and marker squares dissolve into their surrounding terrain.
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define (cnt v)
       (count-if (lambda (p) (= (at g (first p) (second p)) v))
                 (flatmap (lambda (r) (map (lambda (c) (list r c))
                                           (range 0 w)))
                          (range 0 h))))
     (define ta
       (reduce (lambda (b v) (if (> (cnt v) (cnt b)) v b)) 0 (range 0 10)))
     (define tb
       (reduce (lambda (b v) (if (and (!= v ta) (or (= b ta)
                                                    (> (cnt v) (cnt b))))
                                 v b))
               ta (range 0 10)))
     (define (terr? v) (or (= v ta) (= v tb)))
     (define (sq? r c)
       (let ((v (at g r c)))
         (and (< (+ r 1) h) (< (+ c 1) w)
              (not (terr? v))
              (= (at g (+ r 1) c) v) (= (at g r (+ c 1)) v)
              (= (at g (+ r 1) (+ c 1)) v)
              (!= (safe-at g (- r 1) c -1) v)
              (!= (safe-at g r (- c 1) -1) v)
              (!= (safe-at g (+ r 2) c -1) v)
              (!= (safe-at g r (+ c 2) -1) v))))
     (define squares
       (filter (lambda (p) (sq? (first p) (second p)))
               (flatmap (lambda (r) (map (lambda (c) (list r c))
                                         (range 0 w)))
                        (range 0 h))))
     (define toprow (reduce min h (map first squares)))
     (define legend
       (sort-by (filter (lambda (p) (= (first p) toprow)) squares)
                second))
     (define pattern
       (map (lambda (p) (at g (first p) (second p))) legend))
     (define lp (length pattern))
     (define gcol
       (let ((gs (filter (lambda (p) (!= (first p) toprow)) squares)))
         (at g (first (first gs)) (second (first gs)))))
     (define marks
       (filter (lambda (p)
                 (let ((r (first p)) (c (second p)))
                   (and (or (= r 0) (= r (- h 1)) (= c 0) (= c (- w 1)))
                        (not (terr? (at g r c)))
                        (= 0 (count-if
                              (lambda (q) (= (at g r c)
                                             (safe-at g (+ r (first q))
                                                      (+ c (second q)) -1)))
                              (list (list -1 0) (list 1 0)
                                    (list 0 -1) (list 0 1)))))))
               (flatmap (lambda (r) (map (lambda (c) (list r c))
                                         (range 0 w)))
                        (range 0 h))))
     (define erased
       (reduce
        (lambda (out p)
          (let* ((r0 (first p)) (c0 (second p))
                 (ring (filter (lambda (q)
                                 (and (in-bounds? (first q) (second q) h w)
                                      (terr? (at g (first q) (second q)))))
                               (flatmap (lambda (rr)
                                          (map (lambda (cc) (list rr cc))
                                               (range (- c0 1) (+ c0 3))))
                                        (range (- r0 1) (+ r0 3)))))
                 (na (count-if (lambda (q) (= (at g (first q) (second q))
                                              ta))
                               ring))
                 (rep (if (> na (- (length ring) na)) ta tb)))
            (for*/fold ((o out)) ((rr (in-range r0 (+ r0 2)))
                                  (cc (in-range c0 (+ c0 2))))
              (set-cell o rr cc rep))))
        g squares))
     (define (run-len r c dr dc corr)
       (let loop ((rr r) (cc c) (n 0))
         (if (and (in-bounds? rr cc h w) (= (at g rr cc) corr))
             (loop (+ rr dr) (+ cc dc) (+ n 1))
             n)))
     (reduce
      (lambda (out0 mk)
        (let* ((mr (first mk)) (mc (second mk))
               (d0 (cond ((= mc 0) (list 0 1))
                         ((= mc (- w 1)) (list 0 -1))
                         ((= mr 0) (list 1 0))
                         (else (list -1 0))))
               (corr (at g (+ mr (first d0)) (+ mc (second d0)))))
          (let walk ((out (set-cell out0 mr mc (first pattern)))
                     (pr mr) (pc mc)
                     (dr (first d0)) (dc (second d0))
                     (k 0) (fuel 900))
            (if (= fuel 0)
                out
                (let ((nr (+ pr dr)) (nc (+ pc dc)))
                  (cond
                   ((not (in-bounds? nr nc h w)) out)
                   ((= (at g nr nc) corr)
                    (walk (set-cell out nr nc
                                    (nth pattern (modulo (+ k 1) lp)))
                          nr nc dr dc (+ k 1) (- fuel 1)))
                   (else
                    (let* ((out2 (set-cell out nr nc gcol))
                           (perp (if (= dr 0)
                                     (list (list -1 0) (list 1 0))
                                     (list (list 0 -1) (list 0 1))))
                           (good
                            (filter
                             (lambda (pd)
                               (>= (run-len (+ pr (first pd))
                                            (+ pc (second pd))
                                            (first pd) (second pd) corr)
                                   2))
                             perp)))
                      (cond
                       ((null? good) out2)
                       ((= (length good) 1)
                        (walk out2 pr pc (first (first good))
                              (second (first good)) k (- fuel 1)))
                       (else
                        (let* ((r1 (run-len (+ pr (first (first good)))
                                            (+ pc (second (first good)))
                                            (first (first good))
                                            (second (first good)) corr))
                               (r2 (run-len (+ pr (first (second good)))
                                            (+ pc (second (second good)))
                                            (first (second good))
                                            (second (second good)) corr)))
                          (if (= r1 r2)
                              out2
                              (let ((pd (if (> r1 r2) (first good)
                                            (second good))))
                                (walk out2 pr pc (first pd) (second pd)
                                      k (- fuel 1)))))))))))))))
      erased marks))))"""


def _apply(g):
    """Python mirror of PROGRAM."""
    h, w = len(g), len(g[0])
    flat = [v for row in g for v in row]

    def cnt(v):
        return flat.count(v)

    ta = 0
    for v in range(10):
        if cnt(v) > cnt(ta):
            ta = v
    tb = ta
    for v in range(10):
        if v != ta and (tb == ta or cnt(v) > cnt(tb)):
            tb = v

    def terr(v):
        return v == ta or v == tb

    def sa(r, c):
        return g[r][c] if 0 <= r < h and 0 <= c < w else -1

    squares = []
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if r + 1 < h and c + 1 < w and not terr(v) \
                    and g[r + 1][c] == v and g[r][c + 1] == v \
                    and g[r + 1][c + 1] == v \
                    and sa(r - 1, c) != v and sa(r, c - 1) != v \
                    and sa(r + 2, c) != v and sa(r, c + 2) != v:
                squares.append((r, c))
    toprow = min(r for r, _ in squares)
    legend = sorted([p for p in squares if p[0] == toprow],
                    key=lambda p: p[1])
    pattern = [g[r][c] for r, c in legend]
    lp = len(pattern)
    gcol = next(g[r][c] for r, c in squares if r != toprow)
    marks = []
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if (r in (0, h - 1) or c in (0, w - 1)) and not terr(v):
                if all(sa(r + dr, c + dc) != v
                       for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                    marks.append((r, c))
    out = [row[:] for row in g]
    for r0, c0 in squares:
        ring = [(r, c) for r in range(r0 - 1, r0 + 3)
                for c in range(c0 - 1, c0 + 3)
                if 0 <= r < h and 0 <= c < w and terr(g[r][c])]
        na = sum(1 for r, c in ring if g[r][c] == ta)
        rep = ta if na > len(ring) - na else tb
        for r in range(r0, r0 + 2):
            for c in range(c0, c0 + 2):
                out[r][c] = rep

    def run_len(r, c, dr, dc, corr):
        n = 0
        while 0 <= r < h and 0 <= c < w and g[r][c] == corr:
            n += 1
            r += dr
            c += dc
        return n

    for mr, mc in marks:
        if mc == 0:
            dr, dc = 0, 1
        elif mc == w - 1:
            dr, dc = 0, -1
        elif mr == 0:
            dr, dc = 1, 0
        else:
            dr, dc = -1, 0
        corr = g[mr + dr][mc + dc]
        out[mr][mc] = pattern[0]
        pr, pc, k = mr, mc, 0
        for _fuel in range(900):
            nr, nc = pr + dr, pc + dc
            if not (0 <= nr < h and 0 <= nc < w):
                break
            if g[nr][nc] == corr:
                k += 1
                pr, pc = nr, nc
                out[nr][nc] = pattern[k % lp]
                continue
            out[nr][nc] = gcol
            perp = [(-1, 0), (1, 0)] if dr == 0 else [(0, -1), (0, 1)]
            good = [(pd, run_len(pr + pd[0], pc + pd[1], pd[0], pd[1],
                                 corr))
                    for pd in perp]
            good = [x for x in good if x[1] >= 2]
            if not good:
                break
            if len(good) == 2:
                if good[0][1] == good[1][1]:
                    break
                good.sort(key=lambda x: -x[1])
            dr, dc = good[0][0]
        else:
            raise RuntimeError("fuel out")
    return out


def _build_path(rng, h, w):
    """Staircase path from a border mouth; returns cells (in walk order)
    with non-consecutive cells >= 2 Chebyshev apart, or None."""
    side = rng.randint(0, 3)
    if side == 0:
        start = (rng.randint(5, h - 6), 0)
        d = (0, 1)
    elif side == 1:
        start = (rng.randint(5, h - 6), w - 1)
        d = (0, -1)
    elif side == 2:
        start = (0, rng.randint(5, w - 6))
        d = (1, 0)
    else:
        start = (h - 1, rng.randint(5, w - 6))
        d = (-1, 0)
    cells = [start]
    pos = start
    n_seg = rng.randint(2, 4)
    for si in range(n_seg):
        seg = rng.randint(3, 8)
        for _s in range(seg):
            np_ = (pos[0] + d[0], pos[1] + d[1])
            if not (0 <= np_[0] < h and 0 <= np_[1] < w):
                return cells if len(cells) >= 6 else None
            if any(max(abs(np_[0] - r), abs(np_[1] - c)) < 2
                   for r, c in cells[:-2]):
                return None
            cells.append(np_)
            pos = np_
        if si < n_seg - 1:
            perp = [(-1, 0), (1, 0)] if d[0] == 0 else [(0, -1), (0, 1)]
            d = perp[rng.randint(0, 1)]
    return cells if len(cells) >= 6 else None


def _build_pair(rng, difficulty):
    h = rng.randint(20, 26)
    w = rng.randint(20, 26)
    colors = rng.sample(range(10), 7)
    ta_, tb_ = colors[0], colors[1]
    lp = rng.randint(2, 3)
    pattern = [rng.choice(colors[2:5]) for _ in range(lp)]
    pattern[0] = colors[2]
    gcol = colors[5]
    g = [[ta_] * w for _ in range(h)]
    n_paths = 1 if difficulty == "easy" else rng.randint(1, 2)
    paths = []
    occupied = set()
    for _p in range(n_paths):
        for _try in range(80):
            cells = _build_path(rng, h, w)
            if cells is None:
                continue
            if any(any(max(abs(r - rr), abs(c - cc)) < 3 for rr, cc in
                       occupied) for r, c in cells):
                continue
            paths.append(cells)
            occupied |= set(cells)
            break
        else:
            if not paths:
                raise ValueError("no path")
    for cells in paths:
        for r, c in cells[1:]:
            g[r][c] = tb_
        g[cells[0][0]][cells[0][1]] = pattern[0]
    # detached corridor blobs (keep 3+ away from paths)
    for _b in range(rng.randint(2, 4)):
        for _try in range(60):
            bh, bw = rng.randint(2, 4), rng.randint(2, 5)
            r0 = rng.randint(1, h - bh - 1)
            c0 = rng.randint(1, w - bw - 1)
            zone = {(r, c) for r in range(r0 - 2, r0 + bh + 2)
                    for c in range(c0 - 2, c0 + bw + 2)}
            if any((r, c) in zone for r, c in occupied):
                continue
            for r in range(r0, r0 + bh):
                for c in range(c0, c0 + bw):
                    g[r][c] = tb_
            occupied |= {(r, c) for r in range(r0, r0 + bh)
                         for c in range(c0, c0 + bw)}
            break
    # legend + goal squares on clear bg
    def place_sq(col, rlo, rhi):
        for _try in range(120):
            r0 = rng.randint(rlo, rhi)
            c0 = rng.randint(1, w - 4)
            zone = {(r, c) for r in range(r0 - 1, r0 + 3)
                    for c in range(c0 - 1, c0 + 3)}
            if any(p in zone for p in occupied) or \
                    any(g[r][c] != ta_ for r, c in zone
                        if 0 <= r < h and 0 <= c < w):
                continue
            for r in range(r0, r0 + 2):
                for c in range(c0, c0 + 2):
                    g[r][c] = col
            occupied.update({(r, c) for r in range(r0 - 1, r0 + 3)
                             for c in range(c0 - 1, c0 + 3)})
            return (r0, c0)
        raise ValueError("no square spot")
    anchors = []
    c_prev = 1
    for pc_ in pattern:
        for _try in range(120):
            c0 = rng.randint(c_prev, min(c_prev + 4, w - 4))
            zone = {(r, c) for r in range(0, 4)
                    for c in range(c0 - 1, c0 + 3)}
            if any(p in zone for p in occupied) or \
                    any(g[r][c] != ta_ for r, c in zone
                        if 0 <= r < h and 0 <= c < w):
                c_prev += 1
                if c_prev > w - 5:
                    raise ValueError("legend overflow")
                continue
            for r in range(1, 3):
                for c in range(c0, c0 + 2):
                    g[r][c] = pc_
            occupied.update(zone)
            anchors.append((1, c0))
            c_prev = c0 + 3
            break
        else:
            raise ValueError("no legend spot")
    place_sq(gcol, 5, h - 3)
    # terrain dominance sanity: ta strictly top, tb strictly second
    flat = [v for row in g for v in row]
    counts = {v: flat.count(v) for v in set(flat)}
    top = sorted(counts.items(), key=lambda x: -x[1])
    if top[0][0] != ta_ or top[1][0] != tb_ or top[1][1] == top[2][1] \
            if len(top) > 2 else False:
        raise ValueError("terrain counts off")
    try:
        out = _apply(g)
    except RuntimeError:
        raise ValueError("walk did not terminate")
    # well-posedness: every constructed corridor cell painted
    for cells in paths:
        for r, c in cells:
            if out[r][c] == tb_:
                raise ValueError("walk missed corridor cells")
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
        if attempts > 150:
            raise ValueError("could not build enough pairs")
        try:
            gin, gout = _build_pair(rng, difficulty)
        except (ValueError, IndexError, StopIteration):
            continue
        pairs.append({"input": gin, "output": gout})
        idx += 1
    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": PROGRAM,
        "concept": "corridor_walk",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.corridor_walk import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"corridor_walk gen1 v{VERSION}")
