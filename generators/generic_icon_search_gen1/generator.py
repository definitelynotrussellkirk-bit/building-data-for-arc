"""gen1: icon word-search boards with verdict strips.

Scene: an n x n board (n = 3-4) of pairwise-distinct random 3x3 icons on
a 5-cell pitch, a query strip above the first separator, a verdict strip
below the second. Scenarios: the query is a permutation of one row / one
column (success: strip + line + verdict green, swap sub-rule applies) or
a non-collinear icon set, sometimes with one icon absent from the board
(fail: matches boxed, verdict red).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_icon_search_gen1"

BG = 8
SEP = 6
ICON_COLORS = (0, 1, 2, 4, 5, 7, 9)

PROGRAM = """(rule!
 ;; ICON WORD-SEARCH with a verdict. Above the first separator line sits a
 ;; QUERY strip of 3x3 icons; between the separators a board of 3x3 icons
 ;; on a 5-cell pitch. If the query icons' matches fill exactly one board
 ;; row or column: green-light the query strip, band-highlight that line,
 ;; and green the verdict strip below the second separator; additionally
 ;; the query icon at position = line index is swapped for the icon BELOW
 ;; its match (wrapping), unless that icon already appears in the query.
 ;; Otherwise: box each individual match and paint the verdict strip red.
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define bg 8)
     (define seps
       (filter (lambda (r) (and (row-uniform? g r) (!= (at g r 0) bg)))
               (range 0 h)))
     (define s1 (first seps))
     (define s2 (nth seps (- (length seps) 1)))
     (define ncols
       (length (filter (lambda (j) (<= (+ 2 (* 5 j) 2) (- w 2)))
                       (range 0 9))))
     (define nrows
       (length (filter (lambda (i) (<= (+ s1 3 (* 5 i) 2) (- s2 2)))
                       (range 0 9))))
     (define (icon a c) (subgrid g a c (+ a 2) (+ c 2)))
     (define strip-icons
       (map (lambda (j) (icon (- s1 4) (+ 2 (* 5 j)))) (range 0 ncols)))
     (define (bicon i j) (icon (+ s1 3 (* 5 i)) (+ 2 (* 5 j))))
     (define (match-of ic)
       (find-first (lambda (ij) (equal? (bicon (first ij) (second ij)) ic))
                   (flatmap (lambda (i)
                              (map (lambda (j) (list i j))
                                   (range 0 ncols)))
                            (range 0 nrows))))
     (define matches (map match-of strip-icons))
     (define all-found (= 0 (count-if (lambda (m) (not m)) matches)))
     (define row-hit
       (and all-found
            (= (length matches) ncols)
            (= 0 (count-if (lambda (m) (!= (first m)
                                           (first (first matches))))
                           matches))
            (= ncols (length (unique (map second matches))))))
     (define col-hit
       (and all-found
            (= (length matches) nrows)
            (= 0 (count-if (lambda (m) (!= (second m)
                                           (second (first matches))))
                           matches))
            (= nrows (length (unique (map first matches))))))
     (define (hi out r1 c1 r2 c2 col)
       (for*/fold ((o out)) ((r (in-range r1 (+ r2 1)))
                             (c (in-range c1 (+ c2 1))))
         (if (and (in-bounds? r c h w) (= (at g r c) bg))
             (set-cell o r c col)
             o)))
     (define (block out i j col)
       (hi out (+ s1 2 (* 5 i)) (+ 1 (* 5 j))
           (+ s1 6 (* 5 i)) (+ 5 (* 5 j)) col))
     (if (or row-hit col-hit)
         (let* ((m (if row-hit (first (first matches))
                       (second (first matches))))
                (out1 (hi g 0 0 (- s1 1) (- w 1) 3))
                (out2 (if row-hit
                          (hi out1 (+ s1 2 (* 5 m)) 1
                              (+ s1 6 (* 5 m)) (- w 2) 3)
                          (hi out1 (+ s1 2) (+ 1 (* 5 m))
                              (- s2 1) (+ 5 (* 5 m)) 3)))
                (out3 (hi out2 (+ s2 1) 0 (- h 1) (- w 1) 3))
                (mp (nth matches m))
                (nr (modulo (+ (first mp) 1) nrows))
                (rep (bicon nr (second mp)))
                (have (< 0 (count-if (lambda (ic) (equal? ic rep))
                                     strip-icons))))
           (if have
               out3
               (for*/fold ((o out3)) ((i (in-range 3)) (j (in-range 3)))
                 (let ((v (at rep i j)))
                   (set-cell o (+ (- s1 4) i) (+ 2 (* 5 m) j)
                             (if (= v bg) 3 v))))))
         (let ((out1
                (reduce (lambda (o mj)
                          (if mj
                              (block o (first mj) (second mj) 3)
                              o))
                        g matches)))
           (hi out1 (+ s2 1) 0 (- h 1) (- w 1) 2))))))"""


def _apply(g):
    """Python mirror of PROGRAM."""
    h, w = len(g), len(g[0])
    seps = [r for r in range(h)
            if len({v for v in g[r]}) == 1 and g[r][0] != BG]
    s1, s2 = seps[0], seps[-1]
    ncols = len([j for j in range(9) if 2 + 5 * j + 2 <= w - 2])
    nrows = len([i for i in range(9) if s1 + 3 + 5 * i + 2 <= s2 - 2])

    def icon(a, c):
        return tuple(tuple(g[a + i][c + j] for j in range(3))
                     for i in range(3))

    strip = [icon(s1 - 4, 2 + 5 * j) for j in range(ncols)]

    def bicon(i, j):
        return icon(s1 + 3 + 5 * i, 2 + 5 * j)

    def match_of(ic):
        for i in range(nrows):
            for j in range(ncols):
                if bicon(i, j) == ic:
                    return (i, j)
        return None

    matches = [match_of(ic) for ic in strip]
    all_found = all(m is not None for m in matches)
    row_hit = all_found and len(matches) == ncols and \
        len({m[0] for m in matches}) == 1 and \
        len({m[1] for m in matches}) == ncols
    col_hit = all_found and len(matches) == nrows and \
        len({m[1] for m in matches}) == 1 and \
        len({m[0] for m in matches}) == nrows
    out = [row[:] for row in g]

    def hi(r1, c1, r2, c2, col):
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if 0 <= r < h and 0 <= c < w and g[r][c] == BG:
                    out[r][c] = col

    if row_hit or col_hit:
        m = matches[0][0] if row_hit else matches[0][1]
        hi(0, 0, s1 - 1, w - 1, 3)
        if row_hit:
            hi(s1 + 2 + 5 * m, 1, s1 + 6 + 5 * m, w - 2, 3)
        else:
            hi(s1 + 2, 1 + 5 * m, s2 - 1, 5 + 5 * m, 3)
        hi(s2 + 1, 0, h - 1, w - 1, 3)
        mp = matches[m]
        rep = bicon((mp[0] + 1) % nrows, mp[1])
        if not any(ic == rep for ic in strip):
            for i in range(3):
                for j in range(3):
                    v = rep[i][j]
                    out[s1 - 4 + i][2 + 5 * m + j] = 3 if v == BG else v
    else:
        for mj in matches:
            if mj:
                hi(s1 + 2 + 5 * mj[0], 1 + 5 * mj[1],
                   s1 + 6 + 5 * mj[0], 5 + 5 * mj[1], 3)
        hi(s2 + 1, 0, h - 1, w - 1, 2)
    return out


def _rand_icon(rng):
    col = rng.choice(ICON_COLORS)
    while True:
        cells = rng.sample([(i, j) for i in range(3) for j in range(3)],
                           rng.randint(4, 7))
        ic = tuple(tuple(col if (i, j) in cells else BG for j in range(3))
                   for i in range(3))
        return ic


def _build_pair(rng, difficulty):
    n = {"easy": 3, "medium": 4, "hard": 4}[difficulty]
    w = 5 * n + 2
    s1 = 5
    s2 = s1 + 5 * n + 2
    h = s2 + 3
    icons = []
    seen = set()
    for _ in range(n * n):
        for _try in range(80):
            ic = _rand_icon(rng)
            if ic not in seen:
                seen.add(ic)
                icons.append(ic)
                break
        else:
            raise ValueError("could not build distinct icons")
    board = [[icons[i * n + j] for j in range(n)] for i in range(n)]
    mode = rng.random()
    if mode < 0.35:
        i = rng.randrange(n)
        strip = [board[i][j] for j in rng.sample(range(n), n)]
    elif mode < 0.7:
        j = rng.randrange(n)
        strip = [board[i][j] for i in rng.sample(range(n), n)]
    else:
        for _try in range(60):
            picks = rng.sample([(i, j) for i in range(n) for j in range(n)],
                               n)
            rowset = {i for i, _ in picks}
            colset = {j for _, j in picks}
            if len(rowset) > 1 and len(colset) > 1:
                break
        else:
            raise ValueError("could not pick a fail set")
        strip = [board[i][j] for i, j in picks]
        if rng.random() < 0.35:
            for _try in range(60):
                ic = _rand_icon(rng)
                if ic not in seen:
                    strip[rng.randrange(n)] = ic
                    break
    g = [[BG] * w for _ in range(h)]
    for c in range(w):
        g[s1][c] = SEP
        g[s2][c] = SEP

    def stamp(ic, a, c0):
        for i in range(3):
            for j in range(3):
                g[a + i][c0 + j] = ic[i][j]

    for p, ic in enumerate(strip):
        stamp(ic, s1 - 4, 2 + 5 * p)
    for i in range(n):
        for j in range(n):
            stamp(board[i][j], s1 + 3 + 5 * i, 2 + 5 * j)
    return g, _apply(g)


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    n_train = ctx.draw_int("n_train", 3, 5)
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
        "concept": "icon_search",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.icon_search import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"icon_search gen1 v{VERSION}")
