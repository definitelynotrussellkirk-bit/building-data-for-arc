"""gen1: header-programmed cursor excursion scenes.

Scene: a 6-row header of nb boxes (bar side = turn hand, bar color =
target); a field with 3-4 rects and a 2x2 cyan cursor. Sequence colors
are axis-aligned targets with clear legs (plus occasionally an absent or
unaligned color -> straight-up excursion). Transform: paint each
excursion (leg, hand turn, bounce runs to an edge). Scenes resample
until the mirror terminates within a step cap and every leg reaches its
intended target.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_cursor_route_gen1"

PROGRAM = """(rule!
 ;; CURSOR EXCURSIONS: the header strip (rows 0-5) holds boxes whose side
 ;; bar gives a target color and a turn hand (bar left = turn left, right
 ;; = turn right). On the field below, a 2x2 cursor sends one excursion
 ;; per box from its HOME: a straight leg to the axis-aligned target,
 ;; the hand turn on arrival, then a run that BOUNCES off blocking rects
 ;; (sliding toward the blocker's farther extension) until a grid edge.
 ;; Targets absent or not axis-aligned just send the cursor up to the top
 ;; edge. Output the field with the cyan trail painted.
 (lambda (g)
   (let ()
     (define hh (rows g))
     (define w (cols g))
     (define h (- hh 6))
     (define (fat r c) (at g (+ r 6) c))
     (define seq
       (map (lambda (b)
              (let ((c (find-first
                        (lambda (cc) (and (!= (at g 1 cc) 5)
                                          (!= (at g 1 cc) 0)))
                        (range (* 6 b) (+ (* 6 b) 6)))))
                (list (at g 1 c) (if (<= (- c (* 6 b)) 2) 0 1))))
            (range 0 (quotient w 6))))
     (define vals
       (flatmap (lambda (r) (map (lambda (c) (fat r c)) (range 0 w)))
                (range 0 h)))
     (define bg
       (reduce (lambda (best v)
                 (if (> (count-if (lambda (u) (= u v)) vals)
                        (count-if (lambda (u) (= u best)) vals))
                     v best))
               (first vals) vals))
     (define (bbox-of v)
       (let ((cells (filter (lambda (p) (= (fat (first p) (second p)) v))
                            (flatmap (lambda (r)
                                       (map (lambda (c) (list r c))
                                            (range 0 w)))
                                     (range 0 h)))))
         (if (null? cells)
             (list)
             (list (reduce min h (map first cells))
                   (reduce min w (map second cells))
                   (reduce max 0 (map first cells))
                   (reduce max 0 (map second cells))))))
     (define cur (bbox-of 8))
     (define (mv pos d)
       (let ((dr (cond ((= d 0) -1) ((= d 1) 1) (else 0)))
             (dc (cond ((= d 2) -1) ((= d 3) 1) (else 0))))
         (list (+ (first pos) dr) (+ (second pos) dc)
               (+ (nth pos 2) dr) (+ (nth pos 3) dc))))
     (define (lturn d) (cond ((= d 0) 2) ((= d 2) 1) ((= d 1) 3) (else 0)))
     (define (rturn d) (cond ((= d 0) 3) ((= d 3) 1) ((= d 1) 2) (else 0)))
     (define (blockage pos)
       (if (or (< (first pos) 0) (< (second pos) 0)
               (>= (nth pos 2) h) (>= (nth pos 3) w))
           1
           (if (< 0 (count-if
                     (lambda (p) (and (!= (fat (first p) (second p)) bg)
                                      (!= (fat (first p) (second p)) 8)))
                     (flatmap (lambda (r)
                                (map (lambda (c) (list r c))
                                     (range (second pos) (+ (nth pos 3) 1))))
                              (range (first pos) (+ (nth pos 2) 1)))))
               2 0)))
     (define (paint out pos)
       (for*/fold ((o out)) ((r (in-range (first pos) (+ (nth pos 2) 1)))
                             (c (in-range (second pos) (+ (nth pos 3) 1))))
         (set-cell o r c 8)))
     (define (blocker-bbox pos d)
       (let ((np (mv pos d)))
         (find-first
          (lambda (b)
            (and (not (null? b))
                 (<= (first b) (nth np 2)) (>= (nth b 2) (first np))
                 (<= (second b) (nth np 3)) (>= (nth b 3) (second np))))
          (map bbox-of (filter (lambda (v) (and (!= v bg) (!= v 8)))
                               (range 0 10))))))
     (define out0
       (grid-from-fn h w (lambda (r c) (fat r c))))
     (reduce
      (lambda (out step)
        (let* ((color (first step))
               (side (second step))
               (R (bbox-of color))
               (aligned
                (and (not (null? R))
                     (or (and (<= (first R) (first cur))
                              (<= (nth cur 2) (nth R 2)))
                         (and (<= (second R) (second cur))
                              (<= (nth cur 3) (nth R 3)))))))
          (if (not aligned)
              (let up ((o out) (pos cur))
                (if (= 0 (blockage (mv pos 0)))
                    (up (paint o (mv pos 0)) (mv pos 0))
                    o))
              (let* ((d0 (if (and (<= (first R) (first cur))
                                  (<= (nth cur 2) (nth R 2)))
                             (if (< (nth R 3) (second cur)) 2 3)
                             (if (< (nth R 2) (first cur)) 0 1)))
                     (legged
                      (let leg ((o out) (pos cur))
                        (if (= 0 (blockage (mv pos d0)))
                            (leg (paint o (mv pos d0)) (mv pos d0))
                            (list o pos))))
                     (o1 (first legged))
                     (pos1 (second legged))
                     (d1 (if (= side 1) (rturn d0) (lturn d0))))
                (let run ((o o1) (pos pos1) (d d1))
                  (let ((b (blockage (mv pos d))))
                    (cond ((= b 0) (run (paint o (mv pos d)) (mv pos d) d))
                          ((= b 1) o)
                          (else
                           (let ((blk (blocker-bbox pos d)))
                             (if (or (= d 0) (= d 1))
                                 (run o pos
                                      (if (> (- (nth blk 3) (nth pos 3))
                                             (- (second pos) (second blk)))
                                          3 2))
                                 (run o pos
                                      (if (> (- (first pos) (first blk))
                                             (- (nth blk 2) (nth pos 2)))
                                          0 1))))))))))))
      out0 seq))))"""

DIRS = {0: (-1, 0), 1: (1, 0), 2: (0, -1), 3: (0, 1)}
LTURN = {0: 2, 2: 1, 1: 3, 3: 0}
RTURN = {0: 3, 3: 1, 1: 2, 2: 0}


def _apply(g, max_steps=2000):
    """Python mirror of PROGRAM (step-capped; generator resamples on cap)."""
    hh, w = len(g), len(g[0])
    h = hh - 6
    field = [row[:] for row in g[6:]]
    seq = []
    for b in range(w // 6):
        for c in range(6 * b, 6 * b + 6):
            if g[1][c] not in (5, 0):
                seq.append((g[1][c], 1 if c - 6 * b > 2 else 0))
                break
    vals = [field[r][c] for r in range(h) for c in range(w)]
    bg = vals[0]
    for v in vals:
        if vals.count(v) > vals.count(bg):
            bg = v

    def bbox_of(v):
        cells = [(r, c) for r in range(h) for c in range(w)
                 if field[r][c] == v]
        if not cells:
            return None
        return [min(r for r, _ in cells), min(c for _, c in cells),
                max(r for r, _ in cells), max(c for _, c in cells)]

    cur = bbox_of(8)

    def mv(pos, d):
        dr, dc = DIRS[d]
        return [pos[0] + dr, pos[1] + dc, pos[2] + dr, pos[3] + dc]

    def blockage(pos):
        if pos[0] < 0 or pos[1] < 0 or pos[2] >= h or pos[3] >= w:
            return 1
        for r in range(pos[0], pos[2] + 1):
            for c in range(pos[1], pos[3] + 1):
                if field[r][c] != bg and field[r][c] != 8:
                    return 2
        return 0

    def blocker_bbox(pos, d):
        np_ = mv(pos, d)
        for v in range(10):
            if v == bg or v == 8:
                continue
            b = bbox_of(v)
            if b and b[0] <= np_[2] and b[2] >= np_[0] \
                    and b[1] <= np_[3] and b[3] >= np_[1]:
                return b
        return None

    out = [row[:] for row in field]

    def paint(pos):
        for r in range(pos[0], pos[2] + 1):
            for c in range(pos[1], pos[3] + 1):
                out[r][c] = 8

    steps = 0
    for color, side in seq:
        R = bbox_of(color)
        aligned = R is not None and (
            (R[0] <= cur[0] and cur[2] <= R[2]) or
            (R[1] <= cur[1] and cur[3] <= R[3]))
        pos = list(cur)
        if not aligned:
            while blockage(mv(pos, 0)) == 0:
                pos = mv(pos, 0)
                paint(pos)
                steps += 1
                if steps > max_steps:
                    raise RuntimeError("step cap")
            continue
        if R[0] <= cur[0] and cur[2] <= R[2]:
            d = 2 if R[3] < cur[1] else 3
        else:
            d = 0 if R[2] < cur[0] else 1
        while blockage(mv(pos, d)) == 0:
            pos = mv(pos, d)
            paint(pos)
            steps += 1
            if steps > max_steps:
                raise RuntimeError("step cap")
        d = RTURN[d] if side == 1 else LTURN[d]
        while True:
            b = blockage(mv(pos, d))
            if b == 0:
                pos = mv(pos, d)
                paint(pos)
                steps += 1
                if steps > max_steps:
                    raise RuntimeError("step cap")
            elif b == 1:
                break
            else:
                blk = blocker_bbox(pos, d)
                if d in (0, 1):
                    d = 3 if (blk[3] - pos[3]) > (pos[1] - blk[1]) else 2
                else:
                    d = 0 if (pos[0] - blk[0]) > (blk[2] - pos[2]) else 1
                steps += 1
                if steps > max_steps:
                    raise RuntimeError("step cap")
    return out


def _build_pair(rng, difficulty):
    nb = {"easy": 3, "medium": 4, "hard": 4}[difficulty]
    w = 6 * nb
    h = rng.randint(16, 23)
    bg = rng.choice([v for v in range(1, 10) if v not in (5, 8)])
    pool = [v for v in range(1, 10) if v not in (bg, 5, 8)]
    rng.shuffle(pool)
    n_rects = min(nb, rng.randint(3, 4), len(pool))
    field = [[bg] * w for _ in range(h)]
    cr = rng.randint(6, h - 7)
    cc = rng.randint(6, w - 7)
    for r in (cr, cr + 1):
        for c in (cc, cc + 1):
            field[r][c] = 8
    rects = {}
    dirs = rng.sample((0, 1, 2, 3), min(4, n_rects))
    for i in range(n_rects):
        col = pool[i]
        for _try in range(120):
            if i < len(dirs):
                d = dirs[i]
                if d in (0, 1):  # above/below, vertically aligned
                    rw = rng.randint(3, 8)
                    rh = rng.randint(2, 4)
                    c1 = rng.randint(max(0, cc + 1 - rw + 1),
                                     min(w - rw, cc))
                    r1 = rng.randint(0, cr - rh - 2) if d == 0 else \
                        rng.randint(cr + 4, h - rh)
                else:
                    rh = rng.randint(3, 8)
                    rw = rng.randint(2, 4)
                    r1 = rng.randint(max(0, cr + 1 - rh + 1),
                                     min(h - rh, cr))
                    c1 = rng.randint(0, cc - rw - 2) if d == 2 else \
                        rng.randint(cc + 4, w - rw)
            else:
                rh, rw = rng.randint(2, 5), rng.randint(2, 5)
                r1 = rng.randint(0, h - rh)
                c1 = rng.randint(0, w - rw)
            if r1 < 0 or c1 < 0 or r1 + rh > h or c1 + rw > w:
                continue
            zone = [(r, c) for r in range(max(0, r1 - 1),
                                          min(h, r1 + rh + 1))
                    for c in range(max(0, c1 - 1), min(w, c1 + rw + 1))]
            if any(field[r][c] != bg for r, c in zone):
                continue
            for r in range(r1, r1 + rh):
                for c in range(c1, c1 + rw):
                    field[r][c] = col
            rects[col] = (r1, c1, r1 + rh - 1, c1 + rw - 1)
            break
        else:
            raise ValueError("could not place rect")
    # header sequence: the rect colors (+ absent filler if nb > n_rects)
    seq_cols = [pool[i] for i in range(n_rects)]
    while len(seq_cols) < nb:
        seq_cols.append(rng.choice([v for v in pool[n_rects:]] or pool))
    rng.shuffle(seq_cols)
    g = [[5] * w for _ in range(6)] + field
    for b, col in enumerate(seq_cols):
        side = rng.randint(0, 1)
        for r in range(1, 5):
            for c in range(6 * b + 2, 6 * b + 5):
                g[r][c] = 0
            g[r][6 * b + (5 if side else 1)] = col
    try:
        out = _apply(g)
    except RuntimeError:
        raise ValueError("non-terminating excursion")
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
        except (ValueError, IndexError):
            continue
        pairs.append({"input": gin, "output": gout})
        idx += 1
    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": PROGRAM,
        "concept": "cursor_route",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.cursor_route import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"cursor_route gen1 v{VERSION}")
