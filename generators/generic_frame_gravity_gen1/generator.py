"""gen1: frame-keyed horizontal gravity scenes.

Scene: 4-8 framed square pieces (uniform ring in cyan-8 or red-2, solid
core in another color) scattered on a uniform background. Transform:
cyan-framed pieces slide fully left, red-framed fully right, keeping
rows, stacking only against same-direction pieces (left lane settles
leftmost-first, right lane rightmost-first), lanes merged left-over-right.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_frame_gravity_gen1"

PROGRAM = """(rule!
 ;; FRAME GRAVITY: framed square pieces (uniform ring + inner core) slide
 ;; horizontally by frame color — cyan (8) frames slide LEFT, red (2)
 ;; frames slide RIGHT — keeping their rows, stacking against the edge
 ;; and against already-settled pieces whose row ranges overlap. Left
 ;; sliders settle leftmost-first, right sliders rightmost-first.
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
     (define (ring-at r c s)
       (let ((f (at g r c)))
         (and (or (= f 8) (= f 2))
              (< (+ r s -1) h) (< (+ c s -1) w)
              (= 0 (count-if
                    (lambda (i) (or (!= (at g (+ r i) c) f)
                                    (!= (at g (+ r i) (+ c s -1)) f)
                                    (!= (at g r (+ c i)) f)
                                    (!= (at g (+ r s -1) (+ c i)) f)))
                    (range 0 s)))
              (!= (at g (+ r 1) (+ c 1)) f)
              (!= (at g (+ r 1) (+ c 1)) bg))))
     (define pieces
       (flatmap
        (lambda (r)
          (flatmap
           (lambda (c)
             (flatmap (lambda (s)
                        (if (ring-at r c s) (list (list r c s)) (list)))
                      (range 4 9)))
           (range 0 w)))
        (range 0 h)))
     (define lefts
       (sort-by (filter (lambda (p) (= (at g (first p) (second p)) 8))
                        pieces)
                second))
     (define rights
       (sort-by (filter (lambda (p) (= (at g (first p) (second p)) 2))
                        pieces)
                (lambda (p) (- 0 (second p)))))
     (define out0 (empty-grid h w bg))
     (define (paint out p nc)
       (let ((r (first p)) (c (second p)) (s (nth p 2)))
         (for*/fold ((o out)) ((i (in-range 0 s)) (j (in-range 0 s)))
           (set-cell o (+ r i) (+ nc j) (at g (+ r i) (+ c j))))))
     (define (free? out p nc)
       (let ((r (first p)) (s (nth p 2)))
         (and (>= nc 0) (<= (+ nc s) w)
              (= 0 (count-if
                    (lambda (q) (!= (at out (first q) (second q)) bg))
                    (flatmap (lambda (i)
                               (map (lambda (j) (list (+ r i) (+ nc j)))
                                    (range 0 s)))
                             (range 0 s)))))))
     (define after-l
       (reduce (lambda (out p)
                 (let slide ((nc (second p)))
                   (if (free? out p (- nc 1))
                       (slide (- nc 1))
                       (paint out p nc))))
               out0 lefts))
     (define after-r
       (reduce (lambda (out p)
                 (let slide ((nc (second p)))
                   (if (free? out p (+ nc 1))
                       (slide (+ nc 1))
                       (paint out p nc))))
               out0 rights))
     (grid-from-fn h w
                   (lambda (r c)
                     (if (!= (at after-l r c) bg)
                         (at after-l r c)
                         (at after-r r c)))))))"""


def _apply(g):
    """Python mirror of PROGRAM."""
    h, w = len(g), len(g[0])
    flat = [v for row in g for v in row]
    bg = flat[0]
    for v in flat:
        if flat.count(v) > flat.count(bg):
            bg = v
    pieces = []
    for r in range(h):
        for c in range(w):
            f = g[r][c]
            if f not in (2, 8):
                continue
            for s in range(4, 9):
                if r + s > h or c + s > w:
                    continue
                ok = all(g[r + i][c] == f and g[r + i][c + s - 1] == f and
                         g[r][c + i] == f and g[r + s - 1][c + i] == f
                         for i in range(s))
                if ok and g[r + 1][c + 1] != f and g[r + 1][c + 1] != bg:
                    pieces.append((r, c, s))
    lefts = sorted([p for p in pieces if g[p[0]][p[1]] == 8],
                   key=lambda p: p[1])
    rights = sorted([p for p in pieces if g[p[0]][p[1]] == 2],
                    key=lambda p: -p[1])

    def simulate(group, step):
        out = [[bg] * w for _ in range(h)]
        for r, c, s in group:
            nc = c
            while True:
                t = nc + step
                if t < 0 or t + s > w:
                    break
                if any(out[r + i][t + j] != bg
                       for i in range(s) for j in range(s)):
                    break
                nc = t
            for i in range(s):
                for j in range(s):
                    out[r + i][nc + j] = g[r + i][c + j]
        return out

    L = simulate(lefts, -1)
    R = simulate(rights, 1)
    return [[L[r][c] if L[r][c] != bg else R[r][c] for c in range(w)]
            for r in range(h)]


def _build_pair(rng, difficulty):
    h = rng.randint(18, 26)
    w = rng.randint(18, 26)
    bg = rng.choice([v for v in range(10) if v not in (2, 8)])
    n = {"easy": 4, "medium": 6, "hard": 8}[difficulty]
    g = [[bg] * w for _ in range(h)]
    placed = []
    cores = [v for v in range(10) if v not in (2, 8, bg)]
    for _p in range(n):
        s = rng.choice((5, 5, 5, 6))
        f = rng.choice((2, 8))
        core = rng.choice(cores)
        for _try in range(150):
            r0 = rng.randint(0, h - s)
            c0 = rng.randint(0, w - s)
            if any(not (r0 + s + 1 <= pr or pr + ps + 1 <= r0 or
                        c0 + s + 1 <= pc or pc + ps + 1 <= c0)
                   for pr, pc, ps in placed):
                continue
            for i in range(s):
                for j in range(s):
                    ring = i in (0, s - 1) or j in (0, s - 1)
                    g[r0 + i][c0 + j] = f if ring else core
            placed.append((r0, c0, s))
            break
        else:
            if len(placed) < 3:
                raise ValueError("could not place pieces")
            break
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
        "concept": "frame_gravity",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.frame_gravity import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"frame_gravity gen1 v{VERSION}")
