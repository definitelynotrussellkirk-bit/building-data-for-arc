"""gen1: workspace pieces sorted into edge-keyed bands.

Scene: a workspace (top or bottom region) holds 2-5 monochrome pieces —
solid blocks, rings with a decoration inside (the decoration is its own
piece), bars — each colored like one band's interior. Below/above sit
2-3 full-width bands (uniform interior, distinct 1-wide edge columns),
separated by workspace-bg rows. Transform: wipe the workspace; drop each
piece into its color-matched band, bottom-aligned, columns preserved,
recolored to the band's edge color.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_band_sort_gen1"

PROGRAM = """(rule!
 ;; SORT-INTO-BANDS: horizontal bands (uniform interior + 1-wide edge
 ;; columns of another color) sit below a workspace holding monochrome
 ;; pieces (nested decorations count as their own pieces). Every piece
 ;; drops into the band whose INTERIOR color equals the piece's color —
 ;; columns preserved, bottom-aligned to the band's last row — and is
 ;; recolored to that band's EDGE color. The workspace is wiped clean.
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define (band-row? r)
       (let ((e (at g r 0)) (b (at g r 1)))
         (and (!= e b)
              (= (at g r (- w 1)) e)
              (= 0 (count-if (lambda (c) (!= (at g r c) b))
                             (range 1 (- w 1)))))))
     (define bandy (map band-row? (range 0 h)))
     (define wbg
       (let ((vals (flatmap (lambda (r)
                              (if (nth bandy r)
                                  (list)
                                  (map (lambda (c) (at g r c))
                                       (range 0 w))))
                            (range 0 h))))
         (reduce (lambda (best v)
                   (if (> (count-if (lambda (u) (= u v)) vals)
                          (count-if (lambda (u) (= u best)) vals))
                       v best))
                 (first vals) vals)))
     (define (band-of color)
       ;; (edge bottom-row) of the band whose interior matches, else '()
       (let ((rows-hit (filter (lambda (r) (and (nth bandy r)
                                                (= (at g r 1) color)))
                               (range 0 h))))
         (if (null? rows-hit)
             (list)
             (list (at g (first rows-hit) 0)
                   (reduce max (first rows-hit) rows-hit)))))
     (define cells
       (filter (lambda (p) (and (not (nth bandy (first p)))
                                (!= (at g (first p) (second p)) wbg)))
               (flatmap (lambda (r) (map (lambda (c) (list r c))
                                         (range 0 w)))
                        (range 0 h))))
     (define (in? p lst)
       (< 0 (count-if (lambda (q) (and (= (first p) (first q))
                                       (= (second p) (second q))))
                      lst)))
     (define comps
       (let loop ((todo cells) (acc (list)))
         (if (null? todo)
             acc
             (let* ((seed (first todo))
                    (col (at g (first seed) (second seed)))
                    (comp (let grow ((frontier (list seed))
                                     (mine (list seed)))
                            (let ((nbrs (filter
                                         (lambda (q)
                                           (and (= (at g (first q)
                                                      (second q)) col)
                                                (< 0 (count-if
                                                      (lambda (f)
                                                        (= 1 (+ (abs (- (first q) (first f)))
                                                                (abs (- (second q) (second f))))))
                                                      frontier))
                                                (not (in? q mine))))
                                         todo)))
                              (if (null? nbrs)
                                  mine
                                  (grow nbrs (append mine nbrs)))))))
               (loop (filter (lambda (q) (not (in? q comp))) todo)
                     (append acc (list comp)))))))
     (define erased
       (reduce (lambda (o p) (set-cell o (first p) (second p) wbg))
               g cells))
     (reduce
      (lambda (out comp)
        (let* ((col (at g (first (first comp)) (second (first comp))))
               (be (band-of col)))
          (if (null? be)
              out
              (let* ((edge (first be))
                     (bot (second be))
                     (mr (reduce max (first (first comp))
                                 (map first comp)))
                     (dr (- bot mr)))
                (reduce (lambda (o p)
                          (set-cell o (+ (first p) dr) (second p) edge))
                        out comp)))))
      erased comps))))"""


def _apply(g):
    """Python mirror of PROGRAM."""
    h, w = len(g), len(g[0])

    def band_row(r):
        e, b = g[r][0], g[r][1]
        return e != b and g[r][w - 1] == e and \
            all(g[r][c] == b for c in range(1, w - 1))

    bandy = [band_row(r) for r in range(h)]
    vals = [g[r][c] for r in range(h) if not bandy[r] for c in range(w)]
    wbg = vals[0]
    for v in vals:
        if vals.count(v) > vals.count(wbg):
            wbg = v

    def band_of(color):
        rows_hit = [r for r in range(h) if bandy[r] and g[r][1] == color]
        if not rows_hit:
            return None
        return (g[rows_hit[0]][0], max(rows_hit))

    cells = [(r, c) for r in range(h) for c in range(w)
             if not bandy[r] and g[r][c] != wbg]
    cellset = set(cells)
    seen = set()
    comps = []
    for seed in cells:
        if seed in seen:
            continue
        col = g[seed[0]][seed[1]]
        q = deque([seed])
        seen.add(seed)
        comp = [seed]
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (x + dx, y + dy)
                if nb in cellset and nb not in seen \
                        and g[nb[0]][nb[1]] == col:
                    seen.add(nb)
                    q.append(nb)
                    comp.append(nb)
        comps.append(comp)
    out = [row[:] for row in g]
    for r, c in cells:
        out[r][c] = wbg
    for comp in comps:
        col = g[comp[0][0]][comp[0][1]]
        be = band_of(col)
        if be is None:
            continue
        edge, bot = be
        dr = bot - max(r for r, _ in comp)
        for r, c in comp:
            out[r + dr][c] = edge
    return out


def _build_pair(rng, difficulty):
    w = rng.randint(20, 26)
    n_bands = {"easy": 2, "medium": 3, "hard": 3}[difficulty]
    colors = rng.sample(range(10), 2 * n_bands + 1)
    wbg = colors[0]
    band_bgs = colors[1:n_bands + 1]
    band_edges = colors[n_bands + 1:]
    band_hs = [rng.randint(4, 6) for _ in range(n_bands)]
    ws_h = rng.randint(8, 11)
    h = ws_h + sum(bh + 1 for bh in band_hs)
    if h > 30:
        raise ValueError("too tall")
    g = [[wbg] * w for _ in range(h)]
    r = ws_h
    band_rows = []
    for bh, bb, be in zip(band_hs, band_bgs, band_edges):
        for rr in range(r, r + bh):
            g[rr][0] = be
            g[rr][w - 1] = be
            for c in range(1, w - 1):
                g[rr][c] = bb
        band_rows.append((bb, be, r, r + bh - 1))
        r += bh + 1
    # workspace pieces: each colored like some band interior
    occupied = set()
    n_pieces = rng.randint(2, min(4, n_bands + 2))
    for _p in range(n_pieces):
        bi = rng.randrange(n_bands)
        col = band_bgs[bi]
        kind = rng.choice(("block", "ring", "bar"))
        if kind == "block":
            ph, pw = rng.randint(1, 3), rng.randint(1, 3)
            rel = {(i, j): col for i in range(ph) for j in range(pw)}
        elif kind == "bar":
            pw = rng.randint(2, 5)
            rel = {(0, j): col for j in range(pw)}
            ph = 1
        else:
            ph, pw = rng.randint(3, 4), rng.randint(3, 6)
            rel = {(i, j): col for i in range(ph) for j in range(pw)
                   if i in (0, ph - 1) or j in (0, pw - 1)}
            icol = band_bgs[rng.randrange(n_bands)]
            if icol != col and ph >= 3 and pw >= 3:
                for j in range(1, pw - 1):
                    if rng.random() < 0.8:
                        rel[(1, j)] = icol
        for _try in range(120):
            r0 = rng.randint(0, ws_h - ph - 1)
            c0 = rng.randint(1, w - pw - 1)
            cand = {(r0 + i, c0 + j) for i, j in rel}
            near = {(rr + dr, cc + dc) for rr, cc in cand
                    for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
            if near & occupied:
                continue
            for (i, j), v in rel.items():
                g[r0 + i][c0 + j] = v
            occupied |= cand
            break
        else:
            raise ValueError("could not place a piece")
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
        "concept": "band_sort",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.band_sort import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"band_sort gen1 v{VERSION}")
