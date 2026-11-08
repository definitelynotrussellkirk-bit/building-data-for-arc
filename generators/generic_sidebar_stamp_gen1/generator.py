"""gen1: sidebar-recipe stamp scenes.

Scene: 1-2 sidebars (5 wide, magenta-walled) each holding a 2-color 3x3
swatch, a 1-color glyph (rows 4-11), a corner dot in the first box and a
2-cell rotation bar in the second; the field carries simple stripes or
blobs. Transform: stamp each glyph x3, textured with the swapped swatch
(block-local phase), rotated per the bar, anchored at the dot's corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_sidebar_stamp_gen1"

PROGRAM = """(rule!
 ;; SIDEBAR STAMP: each sidebar (walled off by a full-height magenta
 ;; column) is a stamp recipe — a 3x3 texture swatch (applied with its
 ;; two colors SWAPPED), a glyph, a dot whose corner inside its box picks
 ;; the field corner to anchor at, and a 2-cell bar whose orientation
 ;; picks the rotation (horizontal = rotate the glyph clockwise). The
 ;; output is the field with each glyph upscaled x3 and painted in the
 ;; swapped swatch texture (block-local phase) at its anchored corner.
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define seps
       (filter (lambda (c) (= h (count-if (lambda (r) (= (at g r c) 6))
                                          (range 0 h))))
               (range 0 w)))
     (define bounds (append (list -1) seps (list w)))
     (define regions
       (filter (lambda (rg) (> (second rg) 0))
               (map (lambda (i) (list (+ (nth bounds i) 1)
                                      (- (nth bounds (+ i 1))
                                         (+ (nth bounds i) 1))))
                    (range 0 (- (length bounds) 1)))))
     (define field
       (reduce (lambda (b rg) (if (> (second rg) (second b)) rg b))
               (first regions) regions))
     (define fc (first field))
     (define fw (second field))
     (define sidebars
       (filter (lambda (rg) (not (equal? rg field))) regions))
     (define out0
       (grid-from-fn h fw (lambda (r c) (at g r (+ fc c)))))
     (reduce
      (lambda (out sb)
        (let* ((bc (first sb))
               (tile0 (map (lambda (r)
                             (map (lambda (c) (at g r (+ bc c)))
                                  (range 1 4)))
                           (range 1 4)))
               (tvals (unique (flatmap (lambda (row) row) tile0)))
               (ta (first tvals))
               (tb (nth tvals (- (length tvals) 1)))
               (tile (map (lambda (row)
                            (map (lambda (v) (if (= v ta) tb ta)) row))
                          tile0))
               (gcells (filter (lambda (p)
                                 (!= (at g (first p) (+ bc (second p))) 0))
                               (flatmap (lambda (r)
                                          (map (lambda (c) (list r c))
                                               (range 0 5)))
                                        (range 4 12))))
               (gr1 (reduce min 99 (map first gcells)))
               (gc1 (reduce min 99 (map second gcells)))
               (gr2 (reduce max 0 (map first gcells)))
               (gc2 (reduce max 0 (map second gcells)))
               (dot (find-first
                     (lambda (p) (= (at g (first p) (+ bc (second p))) 4))
                     (flatmap (lambda (r)
                                (map (lambda (c) (list r c))
                                     (range 1 4)))
                              (range 13 16))))
               (bar (filter
                     (lambda (p) (= (at g (first p) (+ bc (second p))) 7))
                     (flatmap (lambda (r)
                                (map (lambda (c) (list r c))
                                     (range 0 5)))
                              (range 17 20))))
               (horiz (= (first (first bar)) (first (nth bar 1))))
               (rot (if horiz
                        (if (< 0 (count-if (lambda (p) (= (second p) 3))
                                           bar))
                            1 3)
                        (if (< 0 (count-if (lambda (p) (= (first p) 17))
                                           bar))
                            0 2)))
               (mh0 (+ (- gr2 gr1) 1))
               (mw0 (+ (- gc2 gc1) 1))
               (mh (if horiz mw0 mh0))
               (mw (if horiz mh0 mw0))
               (mask-at
                (lambda (i j)
                  (cond ((= rot 0)
                         (!= (at g (+ gr1 i) (+ bc gc1 j)) 0))
                        ((= rot 2)
                         (!= (at g (+ gr1 (- mh0 1 i))
                                 (+ bc gc1 (- mw0 1 j))) 0))
                        ((= rot 1)
                         (!= (at g (+ gr1 (- mh0 1 j)) (+ bc gc1 i)) 0))
                        (else
                         (!= (at g (+ gr1 j) (+ bc gc1 (- mw0 1 i))) 0)))))
               (r0 (if (= (first dot) 13) 0 (- h (* 3 mh))))
               (c0 (if (= (second dot) 1) 0 (- fw (* 3 mw)))))
          (for*/fold ((o out)) ((i (in-range 0 mh)) (j (in-range 0 mw))
                                (a (in-range 0 3)) (b (in-range 0 3)))
            (if (mask-at i j)
                (set-cell o (+ r0 (* 3 i) a) (+ c0 (* 3 j) b)
                          (nth (nth tile a) b))
                o))))
      out0 sidebars))))"""


def _apply(g):
    """Python mirror of PROGRAM."""
    h, w = len(g), len(g[0])
    seps = [c for c in range(w) if all(g[r][c] == 6 for r in range(h))]
    bounds = [-1] + seps + [w]
    regions = [(bounds[i] + 1, bounds[i + 1] - bounds[i] - 1)
               for i in range(len(bounds) - 1)]
    regions = [rg for rg in regions if rg[1] > 0]
    field = regions[0]
    for rg in regions[1:]:
        if rg[1] > field[1]:
            field = rg
    fc, fw = field
    out = [[g[r][fc + c] for c in range(fw)] for r in range(h)]
    for bc, bw in regions:
        if (bc, bw) == field:
            continue
        tile0 = [[g[r][bc + c] for c in range(1, 4)] for r in range(1, 4)]
        tv = []
        for row in tile0:
            for v in row:
                if v not in tv:
                    tv.append(v)
        ta, tb = tv[0], tv[-1]
        tile = [[tb if v == ta else ta for v in row] for row in tile0]
        gcells = [(r, c) for r in range(4, 12) for c in range(5)
                  if g[r][bc + c] != 0]
        gr1 = min(r for r, _ in gcells)
        gc1 = min(c for _, c in gcells)
        gr2 = max(r for r, _ in gcells)
        gc2 = max(c for _, c in gcells)
        dot = next((r, c) for r in range(13, 16) for c in range(1, 4)
                   if g[r][bc + c] == 4)
        bar = [(r, c) for r in range(17, 20) for c in range(5)
               if g[r][bc + c] == 7]
        horiz = bar[0][0] == bar[1][0]
        if horiz:
            rot = 1 if any(c == 3 for _, c in bar) else 3
        else:
            rot = 0 if any(r == 17 for r, _ in bar) else 2
        mh0, mw0 = gr2 - gr1 + 1, gc2 - gc1 + 1
        mh, mw = (mw0, mh0) if horiz else (mh0, mw0)

        def mask_at(i, j):
            if rot == 0:
                return g[gr1 + i][bc + gc1 + j] != 0
            if rot == 2:
                return g[gr1 + mh0 - 1 - i][bc + gc1 + mw0 - 1 - j] != 0
            if rot == 1:
                return g[gr1 + mh0 - 1 - j][bc + gc1 + i] != 0
            return g[gr1 + j][bc + gc1 + mw0 - 1 - i] != 0

        r0 = 0 if dot[0] == 13 else h - 3 * mh
        c0 = 0 if dot[1] == 1 else fw - 3 * mw
        if r0 < 0 or c0 < 0 or 3 * mh > h or 3 * mw > fw:
            raise ValueError("stamp exceeds field")
        for i in range(mh):
            for j in range(mw):
                if not mask_at(i, j):
                    continue
                for a in range(3):
                    for b in range(3):
                        out[r0 + 3 * i + a][c0 + 3 * j + b] = tile[a][b]
    return out


def _glyph(rng):
    """Connected glyph in a 5-8 row x 3-5 col bbox, corners touched."""
    gh = rng.randint(5, 6)
    gw = rng.randint(3, 5)
    while True:
        cells = {(0, 0)}
        for _ in range(gh * gw):
            r, c = rng.choice(sorted(cells))
            nb = (r + rng.choice((-1, 0, 1)), c + rng.choice((-1, 0, 1)))
            if 0 <= nb[0] < gh and 0 <= nb[1] < gw:
                cells.add(nb)
        rs = {r for r, _ in cells}
        cs = {c for _, c in cells}
        if rs == set(range(gh)) and cs == set(range(gw)) \
                and len(cells) < gh * gw:
            return gh, gw, cells


def _build_pair(rng, difficulty):
    n_side = 1 if difficulty == "easy" else rng.randint(1, 2)
    h = 20
    fw = rng.randint(20, 24)
    w = fw + 6 * n_side
    if w > 30:
        n_side = 1
        w = fw + 6
    g = [[0] * w for _ in range(h)]
    # field: horizontal stripes
    fcols = rng.sample([v for v in range(10) if v not in (6, 0)], 2)
    stripe_h = rng.randint(3, 6)
    fstart = 6 * n_side if False else (6 if n_side >= 1 else 0)
    # sidebars on the left (one or two), field after
    fc0 = 6 * n_side
    for r in range(h):
        for c in range(fw):
            g[r][fc0 + c] = fcols[(r // stripe_h) % 2]
    corners = rng.sample([(13, 1), (13, 3), (15, 1), (15, 3)], n_side)
    for si in range(n_side):
        bc = 6 * si
        g_r = range(h)
        for r in g_r:
            g[r][bc + 5] = 6
        # swatch
        sc = rng.sample([v for v in range(1, 10) if v != 6], 2)
        for r in range(1, 4):
            for c in range(1, 4):
                g[r][bc + c] = sc[0] if rng.random() < 0.6 else sc[1]
        # ensure both colors present
        g[1][bc + 1] = sc[0]
        g[2][bc + 2] = sc[1]
        # glyph
        gh, gw, cells = _glyph(rng)
        gcol = rng.choice([v for v in range(1, 10) if v != 6])
        gr0 = 4 + rng.randint(0, 8 - gh)
        gc0 = rng.randint(0, 5 - gw)
        for (r, c) in cells:
            g[gr0 + r][bc + gc0 + c] = gcol
        # boxes
        for c in range(5):
            g[12][bc + c] = 6
            g[16][bc + c] = 6
        for r in range(12, 20):
            g[r][bc] = 6
            g[r][bc + 4] = 6
        dr, dc = corners[si]
        g[dr][bc + dc] = 4
        rot = rng.randint(0, 3)
        if rot == 0:
            g[17][bc + 2] = 7
            g[18][bc + 2] = 7
        elif rot == 2:
            g[18][bc + 2] = 7
            g[19][bc + 2] = 7
        elif rot == 1:
            g[18][bc + 2] = 7
            g[18][bc + 3] = 7
        else:
            g[18][bc + 1] = 7
            g[18][bc + 2] = 7
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
        except (ValueError, IndexError):
            continue
        pairs.append({"input": gin, "output": gout})
        idx += 1
    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": PROGRAM,
        "concept": "sidebar_stamp",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.sidebar_stamp import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"sidebar_stamp gen1 v{VERSION}")
