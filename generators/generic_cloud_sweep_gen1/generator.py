"""gen1: cloudy fields swept by an edge bar.

Scene: a dominant background with random cloud blobs in one color, and a
4-colored bar (width 3-6) on the top or bottom edge. Transform: clear all
cloud cells in the bar's column channel (except the bar row), then stamp
the bar every 2 rows marching away from its edge; every 3rd stamp is
green and additionally paints every maximal cloud run in its row green.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_cloud_sweep_gen1"

PROGRAM = """(rule!
 ;; A yellow (4) bar sits on the top or bottom edge of a cloudy field.
 ;; It stamps copies of itself every 2 rows marching away from its edge;
 ;; every 3rd stamp is GREEN (3) instead, and a green stamp also paints
 ;; every cloud RUN in its row green (whole maximal non-background runs).
 ;; Yellow stamps simply overwrite their 4-cell zone.
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define bar (find-color g 4))
     (define r0 (first (first bar)))
     (define cs (map second bar))
     (define c1 (reduce min (first cs) cs))
     (define c2 (reduce max (first cs) cs))
     (define bg (mode g))
     (define dir (if (> r0 (quotient h 2)) -1 1))
     (define (stamp out r green)
       (let ((zone (for*/fold ((o out)) ((c (in-range c1 (+ c2 1))))
                     (set-cell o r c (if green 3 4)))))
         (if green
             (for*/fold ((o zone)) ((c (in-range 0 w)))
               (if (and (!= (at g r c) bg) (!= (at g r c) 4))
                   (set-cell o r c 3)
                   o))
             zone)))
     (define cleared
       (for*/fold ((out g)) ((r (in-range 0 h)) (c (in-range c1 (+ c2 1))))
         (if (and (!= r r0) (!= (at g r c) bg))
             (set-cell out r c bg)
             out)))
     (for*/fold ((out cleared)) ((k (in-range 1 h)))
       (let ((r (+ r0 (* dir 2 k))))
         (if (in-bounds? r 0 h w)
             (stamp out r (= (modulo k 3) 2))
             out))))))"""


def _apply(g):
    """Python mirror of PROGRAM."""
    h, w = len(g), len(g[0])
    bar = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row)
           if v == 4]
    r0 = bar[0][0]
    c1 = min(c for _, c in bar)
    c2 = max(c for _, c in bar)
    from collections import Counter
    bg = Counter(v for row in g for v in row if v != 0).most_common(1)[0][0]
    d = -1 if r0 > h // 2 else 1
    out = [row[:] for row in g]
    for r in range(h):
        for c in range(c1, c2 + 1):
            if r != r0 and g[r][c] != bg:
                out[r][c] = bg
    for k in range(1, h):
        r = r0 + d * 2 * k
        if not (0 <= r < h):
            continue
        green = (k % 3) == 2
        for c in range(c1, c2 + 1):
            out[r][c] = 3 if green else 4
        if green:
            for c in range(w):
                if g[r][c] != bg and g[r][c] != 4:
                    out[r][c] = 3
    return out


def _build_pair(rng, difficulty):
    h = rng.randint(22, 30)
    w = rng.randint(20, 28)
    bg, cloud = rng.sample([v for v in range(10) if v not in (3, 4)], 2)
    g = [[bg] * w for _ in range(h)]
    n_blobs = {"easy": 5, "medium": 7, "hard": 9}[difficulty]
    for _b in range(n_blobs):
        bh = rng.randint(2, 4)
        bw = rng.randint(3, 8)
        r0b = rng.randint(1, h - bh - 1)
        c0b = rng.randint(0, w - bw)
        for r in range(r0b, r0b + bh):
            lo = c0b + rng.randint(0, 2)
            hi = c0b + bw - 1 - rng.randint(0, 2)
            for c in range(lo, hi + 1):
                g[r][c] = cloud
    bar_w = rng.randint(3, 6)
    bc = rng.randint(1, w - bar_w - 1)
    br = rng.choice((0, h - 1))
    for c in range(bc, bc + bar_w):
        g[br][c] = 4
    # bg must strictly dominate for (mode g)
    from collections import Counter
    counts = Counter(v for row in g for v in row if v != 0)
    top = counts.most_common(2)
    if top[0][0] != bg or (len(top) > 1 and top[1][1] >= top[0][1]):
        raise ValueError("background not dominant")
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
        "concept": "cloud_sweep",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.cloud_sweep import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"cloud_sweep gen1 v{VERSION}")
