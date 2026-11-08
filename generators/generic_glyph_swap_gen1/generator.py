"""gen1: framed boxes of solid squares + glyph samples + pair legends.

Scene: a 1-thick frame encloses a grid of solid s x s squares in 2-3
source colors; outside sit one s x s sample GLYPH per source color (a
connected pattern in that color) and one two-color legend chunk per
source (source cells touching target cells). Transform: output the box
with every square replaced by its glyph in the mapped target color.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_glyph_swap_gen1"

PROGRAM = """(rule!
 ;; GLYPH SUBSTITUTION: a framed box holds solid squares; outside sit
 ;; two-color legend chunks (source-target color pairs) and one sample
 ;; GLYPH per source color. Output the box with every solid square
 ;; replaced by its color's glyph, repainted in the mapped target color.
 (lambda (g)
   (let ()
     (define bg (mode g))
     (define comps (objects-multicolor g bg))
     (define (bb-area o)
       (let ((b (obj-bbox o)))
         (* (+ (- (nth b 2) (first b)) 1)
            (+ (- (nth b 3) (second b)) 1))))
     (define frame
       (reduce (lambda (b o) (if (> (bb-area o) (bb-area b)) o b))
               (first comps) comps))
     (define fb (obj-bbox frame))
     (define (inside? o)
       (let ((b (obj-bbox o)))
         (and (not (equal? o frame))
              (> (first b) (first fb)) (< (nth b 2) (nth fb 2))
              (> (second b) (second fb)) (< (nth b 3) (nth fb 3)))))
     (define squares (filter inside? comps))
     (define outs
       (filter (lambda (o) (and (not (equal? o frame))
                                (not (inside? o))))
               comps))
     (define (colors-of o)
       (unique (map (lambda (p) (at g (first p) (second p)))
                    (obj-cells o))))
     (define pairs
       (filter (lambda (o) (= 2 (length (colors-of o)))) outs))
     (define glyphs
       (filter (lambda (o) (= 1 (length (colors-of o)))) outs))
     (define (target-for src)
       (let ((pr (find-first (lambda (o) (member? src (colors-of o)))
                             pairs)))
         (find-first (lambda (cc) (!= cc src)) (colors-of pr))))
     (define (glyph-for src)
       (find-first (lambda (o) (= (first (colors-of o)) src)) glyphs))
     (define out0
       (subgrid g (first fb) (second fb) (nth fb 2) (nth fb 3)))
     (reduce
      (lambda (out sq)
        (let* ((src (first (colors-of sq)))
               (tgt (target-for src))
               (gl (glyph-for src))
               (gb (obj-bbox gl))
               (sb (obj-bbox sq))
               (erased (reduce (lambda (o p)
                                 (set-cell o (- (first p) (first fb))
                                           (- (second p) (second fb)) bg))
                               out (obj-cells sq))))
          (reduce (lambda (o p)
                    (set-cell o
                              (+ (- (first sb) (first fb))
                                 (- (first p) (first gb)))
                              (+ (- (second sb) (second fb))
                                 (- (second p) (second gb)))
                              tgt))
                  erased (obj-cells gl))))
      out0 squares))))"""


def _mc_comps(g, bg):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != bg and not seen[r][c]:
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
                                    and not seen[nx][ny] \
                                    and g[nx][ny] != bg:
                                seen[nx][ny] = True
                                q.append((nx, ny))
                out.append(comp)
    return out


def _apply(g):
    """Python mirror of PROGRAM."""
    from collections import Counter
    h, w = len(g), len(g[0])
    bg = Counter(v for row in g for v in row if v != 0).most_common(1)[0][0]
    comps = _mc_comps(g, bg)

    def bbox(o):
        return (min(r for r, _ in o), min(c for _, c in o),
                max(r for r, _ in o), max(c for _, c in o))

    def bb_area(o):
        b = bbox(o)
        return (b[2] - b[0] + 1) * (b[3] - b[1] + 1)

    frame = comps[0]
    for o in comps[1:]:
        if bb_area(o) > bb_area(frame):
            frame = o
    fb = bbox(frame)

    def inside(o):
        b = bbox(o)
        return o is not frame and b[0] > fb[0] and b[2] < fb[2] \
            and b[1] > fb[1] and b[3] < fb[3]

    squares = [o for o in comps if inside(o)]
    outs = [o for o in comps if o is not frame and not inside(o)]

    def colors_of(o):
        seen_c = []
        for r, c in o:
            if g[r][c] not in seen_c:
                seen_c.append(g[r][c])
        return seen_c

    prs = [o for o in outs if len(colors_of(o)) == 2]
    gls = [o for o in outs if len(colors_of(o)) == 1]
    out = [row[fb[1]:fb[3] + 1] for row in g[fb[0]:fb[2] + 1]]
    out = [r[:] for r in out]
    for sq in squares:
        src = colors_of(sq)[0]
        pr = next(o for o in prs if src in colors_of(o))
        tgt = next(cc for cc in colors_of(pr) if cc != src)
        gl = next(o for o in gls if colors_of(o)[0] == src)
        gb = bbox(gl)
        sb = bbox(sq)
        for r, c in sq:
            out[r - fb[0]][c - fb[1]] = bg
        for r, c in gl:
            out[sb[0] - fb[0] + r - gb[0]][sb[1] - fb[1] + c - gb[1]] = tgt
    return out


def _rand_glyph(rng, s):
    """Connected s x s glyph mask touching all bbox sides."""
    while True:
        cells = {(rng.randrange(s), rng.randrange(s))}
        target = rng.randint(s * s // 2 - 1, s * s - 2)
        for _ in range(200):
            if len(cells) >= target:
                break
            r, c = rng.choice(sorted(cells))
            nb = (r + rng.choice((-1, 0, 1)), c + rng.choice((-1, 0, 1)))
            if 0 <= nb[0] < s and 0 <= nb[1] < s:
                cells.add(nb)
        rs = {r for r, _ in cells}
        cs = {c for _, c in cells}
        if 0 in rs and s - 1 in rs and 0 in cs and s - 1 in cs \
            and len(cells) < s * s:
            return cells


def _build_pair(rng, difficulty):
    n_src = {"easy": 2, "medium": 2, "hard": 3}[difficulty]
    s = rng.randint(3, 4)
    gr = rng.randint(2, 3)
    gc = rng.randint(2, 3)
    bg = rng.randint(1, 9)
    frame_c = rng.choice([v for v in range(10) if v != bg])
    pool = [v for v in range(10) if v not in (bg, frame_c)]
    rng.shuffle(pool)
    srcs = pool[:n_src]
    tgts = pool[n_src:2 * n_src]
    glyphs = {c: _rand_glyph(rng, s) for c in srcs}
    # box dims: gr x gc squares with 1-cell gaps + frame
    bh = gr * (s + 1) + 1 + 2
    bw = gc * (s + 1) + 1 + 2
    top_h = s + 3          # room for glyph samples + legends above the box
    h = top_h + bh + rng.randint(1, 3)
    w = max(bw + 4, (n_src * (s + 5)) + n_src * 5 + 2)
    if h > 30 or w > 30:
        raise ValueError("too big")
    g = [[bg] * w for _ in range(h)]
    # frame + squares
    br0 = top_h
    bc0 = rng.randint(0, w - bw)
    for r in range(br0, br0 + bh):
        for c in range(bc0, bc0 + bw):
            on_ring = r in (br0, br0 + bh - 1) or c in (bc0, bc0 + bw - 1)
            if on_ring:
                g[r][c] = frame_c
    used_srcs = set()
    for i in range(gr):
        for j in range(gc):
            col = rng.choice(srcs)
            used_srcs.add(col)
            if rng.random() < 0.25 and (i, j) != (0, 0):
                continue  # some slots stay empty
            r0 = br0 + 2 + i * (s + 1)
            c0 = bc0 + 2 + j * (s + 1)
            for r in range(r0, r0 + s):
                for c in range(c0, c0 + s):
                    g[r][c] = col
    if len(used_srcs) < n_src:
        raise ValueError("not all sources used")
    # glyph samples + legend chunks in the top strip
    c0 = 1
    for src, tgt in zip(srcs, tgts):
        for r, c in glyphs[src]:
            g[1 + r][c0 + c] = src
        c0 += s + 2
        # legend chunk: 2x2 half-and-half
        g[1][c0] = src
        g[2][c0] = src
        g[1][c0 + 1] = tgt
        g[2][c0 + 1] = tgt
        c0 += 4
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
        "concept": "glyph_swap",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.glyph_swap import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"glyph_swap gen1 v{VERSION}")
