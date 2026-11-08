"""gen1: donor window's icon transplanted onto receiver window's markers.

Scene: a striped field (1-wide stripes, adjacent colors differ) carries
two 1-thick framed windows. The DONOR holds 2-3 copies of a multicolor
icon (body color + exactly one anchor-colored cell); the RECEIVER holds
2-4 single cells of the anchor color. Transform: crop the receiver window
(frame included) and expand every marker into the full icon, aligned on
the icon's anchor cell. Scenes resample until the detector's output
equals the intended construction.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_window_transplant_gen1"

PROGRAM = """(rule!
 ;; Two 1-thick framed WINDOWS sit on a striped field: the DONOR holds
 ;; full multicolor icons; the RECEIVER holds single-cell MARKERS whose
 ;; color appears exactly once inside the icon. Output the receiver
 ;; window (frame included) with every marker expanded to the full icon,
 ;; aligned so the icon's marker-colored cell lands on the marker.
 (lambda (g)
   (let ()
     (define h (rows g))
     (define w (cols g))
     (define (ring-full? r1 c1 r2 c2 k)
       (and (= 0 (count-if (lambda (c) (or (!= (at g r1 c) k)
                                           (!= (at g r2 c) k)))
                           (range c1 (+ c2 1))))
            (= 0 (count-if (lambda (r) (or (!= (at g r c1) k)
                                           (!= (at g r c2) k)))
                           (range r1 (+ r2 1))))))
     (define (window-at r1 c1)
       (let ((k (at g r1 c1)))
         (if (or (>= (+ r1 4) h) (>= (+ c1 4) w)
                 (!= (safe-at g (+ r1 1) c1 -1) k)
                 (!= (safe-at g r1 (+ c1 1) -1) k)
                 (= (safe-at g (+ r1 1) (+ c1 1) -1) k))
             (list)
             (let* ((c2 (let loop ((c c1))
                          (if (and (< (+ c 1) w) (= (at g r1 (+ c 1)) k))
                              (loop (+ c 1)) c)))
                    (r2 (let loop ((r (+ r1 1)))
                          (cond ((>= r h) -1)
                                ((!= (at g r c1) k) -1)
                                ((= 0 (count-if
                                       (lambda (c) (!= (at g r c) k))
                                       (range c1 (+ c2 1))))
                                 r)
                                (else (loop (+ r 1)))))))
               (if (and (> r2 (+ r1 3)) (> c2 (+ c1 3))
                        (ring-full? r1 c1 r2 c2 k))
                   (list (list r1 c1 r2 c2))
                   (list))))))
     (define windows
       (flatmap (lambda (r1) (flatmap (lambda (c1) (window-at r1 c1))
                                      (range 0 (- w 4))))
                (range 0 (- h 4))))
     (define (interior b)
       (subgrid g (+ (first b) 1) (+ (second b) 1)
                (- (nth b 2) 1) (- (nth b 3) 1)))
     (define (interior-bg sub)
       (let ((vals (flatmap (lambda (row) row) sub)))
         (reduce (lambda (best v)
                   (if (> (count-if (lambda (u) (= u v)) vals)
                          (count-if (lambda (u) (= u best)) vals))
                       v best))
                 (first vals) vals)))
     (define (decos b)
       (objects-multicolor (interior b) (interior-bg (interior b))))
     (define (max-deco b)
       (reduce (lambda (n o) (max n (obj-size o))) 0 (decos b)))
     (define real
       (filter (lambda (b) (< 0 (length (decos b)))) windows))
     (define donor
       (reduce (lambda (best b)
                 (if (> (max-deco b) (max-deco best)) b best))
               (first real) real))
     (define receiver
       (find-first (lambda (b) (and (not (equal? b donor))
                                    (= 1 (max-deco b))))
                   real))
     (define dsub (interior donor))
     (define icon (first (decos donor)))
     (define rsub (interior receiver))
     (define markers (decos receiver))
     (define m (let ((p (first (obj-cells (first markers)))))
                 (at rsub (first p) (second p))))
     (define anchor
       (find-first (lambda (p) (= (at dsub (first p) (second p)) m))
                   (obj-cells icon)))
     (define out0
       (subgrid g (first receiver) (second receiver)
                (nth receiver 2) (nth receiver 3)))
     (reduce
      (lambda (out mk)
        (let ((mp (first (obj-cells mk))))
          (reduce (lambda (o p)
                    (set-cell o
                              (+ (+ (first mp) 1) (- (first p) (first anchor)))
                              (+ (+ (second mp) 1) (- (second p) (second anchor)))
                              (at dsub (first p) (second p))))
                  out (obj-cells icon))))
      out0 markers))))"""


def _window_at(g, r1, c1):
    h, w = len(g), len(g[0])
    k = g[r1][c1]
    if r1 + 4 >= h or c1 + 4 >= w:
        return None

    def sa(r, c):
        return g[r][c] if 0 <= r < h and 0 <= c < w else -1

    if sa(r1 + 1, c1) != k or sa(r1, c1 + 1) != k or sa(r1 + 1, c1 + 1) == k:
        return None
    c2 = c1
    while c2 + 1 < w and g[r1][c2 + 1] == k:
        c2 += 1
    r2 = -1
    r = r1 + 1
    while r < h:
        if g[r][c1] != k:
            break
        if all(g[r][c] == k for c in range(c1, c2 + 1)):
            r2 = r
            break
        r += 1
    if not (r2 > r1 + 3 and c2 > c1 + 3):
        return None
    if any(g[r1][c] != k or g[r2][c] != k for c in range(c1, c2 + 1)):
        return None
    if any(g[r][c1] != k or g[r][c2] != k for r in range(r1, r2 + 1)):
        return None
    return (r1, c1, r2, c2)


def _mc_comps(sub, bg):
    """8-connected multicolor components of non-bg cells."""
    h, w = len(sub), len(sub[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if sub[r][c] != bg and not seen[r][c]:
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
                                    and sub[nx][ny] != bg:
                                seen[nx][ny] = True
                                q.append((nx, ny))
                out.append(comp)
    return out


def _apply(g):
    """Python mirror of PROGRAM."""
    h, w = len(g), len(g[0])
    windows = []
    for r1 in range(0, h - 4):
        for c1 in range(0, w - 4):
            b = _window_at(g, r1, c1)
            if b:
                windows.append(b)

    def interior(b):
        return [row[b[1] + 1:b[3]] for row in g[b[0] + 1:b[2]]]

    def interior_bg(sub):
        vals = [v for row in sub for v in row]
        best = vals[0]
        for v in vals:
            if vals.count(v) > vals.count(best):
                best = v
        return best

    def decos(b):
        sub = interior(b)
        return _mc_comps(sub, interior_bg(sub))

    def max_deco(b):
        return max((len(c) for c in decos(b)), default=0)

    real = [b for b in windows if decos(b)]
    donor = real[0]
    for b in real[1:]:
        if max_deco(b) > max_deco(donor):
            donor = b
    receiver = next(b for b in real
                    if b != donor and max_deco(b) == 1)
    dsub = interior(donor)
    icon = decos(donor)[0]
    rsub = interior(receiver)
    markers = decos(receiver)
    mp0 = markers[0][0]
    m = rsub[mp0[0]][mp0[1]]
    anchor = next(p for p in icon if dsub[p[0]][p[1]] == m)
    out = [row[receiver[1]:receiver[3] + 1]
           for row in g[receiver[0]:receiver[2] + 1]]
    for mk in markers:
        mr, mc = mk[0]
        for pr, pc in icon:
            out[mr + 1 + pr - anchor[0]][mc + 1 + pc - anchor[1]] = \
                dsub[pr][pc]
    return out


def _make_icon(rng, body, m):
    """8-connected 4-8 cell icon: body cells + exactly one anchor cell."""
    cells = {(0, 0)}
    while len(cells) < rng.randint(4, 7):
        r, c = rng.choice(sorted(cells))
        nb = (r + rng.choice((-1, 0, 1)), c + rng.choice((-1, 0, 1)))
        cells.add(nb)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    cells = sorted((r - r0, c - c0) for r, c in cells)
    anchor = rng.choice(cells)
    return [(r, c, m if (r, c) == anchor else body) for r, c in cells], anchor


def _build_pair(rng, difficulty):
    h = rng.randint(24, 30)
    w = rng.randint(24, 30)
    vert = rng.random() < 0.5
    # striped field, adjacent stripes differ
    stripe_pal = list(range(0, 10))
    stripes = []
    prev = -1
    for _ in range(max(h, w)):
        col = rng.choice([v for v in stripe_pal if v != prev])
        stripes.append(col)
        prev = col
    if vert:
        g = [[stripes[c] for c in range(w)] for _ in range(h)]
    else:
        g = [[stripes[r] for _ in range(w)] for r in range(h)]
    fr_d, fr_r, bg_d, bg_r, body, m = rng.sample(range(1, 10), 6)
    icon, anchor = _make_icon(rng, body, m)
    ih = max(r for r, _, _ in icon) + 1
    iw = max(c for _, c, _ in icon) + 1
    # window sizes: interiors fit icons with margin
    dih = rng.randint(ih + 3, ih + 7)
    diw = rng.randint(iw + 4, iw + 9)
    rih = rng.randint(ih + 3, ih + 7)
    riw = rng.randint(iw + 4, iw + 9)
    if dih + rih + 5 > h or max(diw, riw) + 4 > w:
        raise ValueError("windows do not fit")
    # stack windows vertically with a stripe gap
    dr0 = rng.randint(0, 1)
    dc0 = rng.randint(0, w - diw - 3)
    rr0 = dr0 + dih + 2 + rng.randint(1, h - (dr0 + dih + rih + 5))
    rc0 = rng.randint(0, w - riw - 3)

    def stamp_window(r0, c0, ihh, iww, fr, bgc):
        for r in range(r0, r0 + ihh + 2):
            for c in range(c0, c0 + iww + 2):
                on_ring = r in (r0, r0 + ihh + 1) or c in (c0, c0 + iww + 1)
                g[r][c] = fr if on_ring else bgc

    stamp_window(dr0, dc0, dih, diw, fr_d, bg_d)
    stamp_window(rr0, rc0, rih, riw, fr_r, bg_r)
    # donor icons (identical), bbox separation >= 2 (8-conn isolation)
    n_icons = rng.randint(2, 3)
    placed = []
    for _ in range(n_icons):
        for _try in range(120):
            ir = rng.randint(0, dih - ih)
            ic = rng.randint(0, diw - iw)
            if all(abs(ir - pr) >= ih + 2 or abs(ic - pc) >= iw + 2
                   for pr, pc in placed):
                for r, c, col in icon:
                    g[dr0 + 1 + ir + r][dc0 + 1 + ic + c] = col
                placed.append((ir, ic))
                break
    if len(placed) < 2:
        raise ValueError("could not place donor icons")
    # receiver markers: icon must fit around the anchor
    n_marks = rng.randint(2, {"easy": 2, "medium": 3, "hard": 4}[difficulty])
    marks = []
    for _ in range(n_marks):
        for _try in range(200):
            mr = rng.randint(anchor[0], rih - (ih - anchor[0]))
            mc = rng.randint(anchor[1], riw - (iw - anchor[1]))
            if all(abs(mr - pr) >= ih + 2 or abs(mc - pc) >= iw + 2
                   for pr, pc in marks):
                g[rr0 + 1 + mr][rc0 + 1 + mc] = m
                marks.append((mr, mc))
                break
    if len(marks) < 2:
        raise ValueError("could not place markers")
    # intended output
    out = [row[rc0:rc0 + riw + 2] for row in g[rr0:rr0 + rih + 2]]
    out = [r[:] for r in out]
    for mr, mc in marks:
        for r, c, col in icon:
            out[1 + mr + r - anchor[0]][1 + mc + c - anchor[1]] = col
    try:
        got = _apply(g)
    except (StopIteration, IndexError):
        # a stripe run hid a window corner from the detector — resample
        raise ValueError("detector could not classify the windows")
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
        if attempts > 100:
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
        "concept": "window_transplant",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.window_transplant import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"window_transplant gen1 v{VERSION}")
