"""gen1: icon towers over a red/green bar legend; red's count moves to green.

Scene: a non-zero background holds 3-5 towers of identical icons (one
shared icon shape per pair, distinct tower colors) in separate column
slots. The last row carries exactly one GREEN (3) and one RED (2) bar
under two different towers. Transform: stack red-tower-count copies of
the green tower's icon on top of the green tower (pitch = icon height +
1), gray out the red tower, erase both bars.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_bar_transfer_gen1"

GRAY = 5

PROGRAM = """(rule!
 ;; Towers of identical icons stand over a bottom-row bar legend: one GREEN
 ;; (3) bar and one RED (2) bar, each 1 row tall on the grid's last row.
 ;; The red-bar tower's icon count TRANSFERS to the green-bar tower: stack
 ;; that many copies of the green tower's icon on top of it (same vertical
 ;; pitch = icon height + 1); the red-bar tower grays out (5); both bars
 ;; vanish. Towers without bars are untouched.
 (lambda (g)
   (let ()
     (define h (rows g))
     (define bgc (mode g))
     (define objs (objects g bgc))
     (define (bar? o) (= (first (obj-bbox o)) (- h 1)))
     (define bars (filter bar? objs))
     (define icons (filter (lambda (o) (not (bar? o))) objs))
     (define green (find-first (lambda (o) (= (obj-color o) 3)) bars))
     (define red (find-first (lambda (o) (= (obj-color o) 2)) bars))
     (define (over bar)
       (filter (lambda (o)
                 (and (<= (second (obj-bbox o)) (nth (obj-bbox bar) 3))
                      (>= (nth (obj-bbox o) 3) (second (obj-bbox bar)))))
               icons))
     (define red-icons (over red))
     (define green-icons (over green))
     (define top
       (reduce (lambda (best o)
                 (if (< (first (obj-bbox o)) (first (obj-bbox best))) o best))
               (first green-icons) green-icons))
     (define pitch (+ (- (nth (obj-bbox top) 2) (first (obj-bbox top))) 2))
     (define erased
       (erase-cells g (append (obj-cells green) (obj-cells red)) bgc))
     (define grayed
       (reduce (lambda (o obj) (recolor-cells o (obj-cells obj) 5))
               erased red-icons))
     (for*/fold ((out grayed)) ((k (in-range (length red-icons))))
       (paint-cells out
                    (map (lambda (p) (list (- (first p) (* pitch (+ k 1)))
                                           (second p)))
                         (obj-cells top))
                    (obj-color top))))))"""


def _components(g, bg):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != bg and not seen[r][c]:
                col = g[r][c]
                comp = []
                q = deque([(r, c)])
                seen[r][c] = True
                while q:
                    x, y = q.popleft()
                    comp.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < h and 0 <= ny < w and not seen[nx][ny] \
                                and g[nx][ny] == col:
                            seen[nx][ny] = True
                            q.append((nx, ny))
                out.append((col, comp))
    return out


def _bbox(comp):
    return (min(r for r, _ in comp), min(c for _, c in comp),
            max(r for r, _ in comp), max(c for _, c in comp))


def _apply(g):
    """Python mirror of PROGRAM."""
    h = len(g)
    bgc = Counter(v for row in g for v in row if v != 0).most_common(1)[0][0]
    objs = _components(g, bgc)
    bars = [(col, comp) for col, comp in objs if _bbox(comp)[0] == h - 1]
    icons = [(col, comp) for col, comp in objs if _bbox(comp)[0] != h - 1]
    green = next((col, comp) for col, comp in bars if col == 3)
    red = next((col, comp) for col, comp in bars if col == 2)

    def over(bar):
        _, bcomp = bar
        b = _bbox(bcomp)
        return [(col, comp) for col, comp in icons
                if _bbox(comp)[1] <= b[3] and _bbox(comp)[3] >= b[1]]

    red_icons = over(red)
    green_icons = over(green)
    top = green_icons[0]
    for cand in green_icons[1:]:
        if _bbox(cand[1])[0] < _bbox(top[1])[0]:
            top = cand
    tb = _bbox(top[1])
    pitch = tb[2] - tb[0] + 2
    out = [row[:] for row in g]
    for _, comp in (green, red):
        for r, c in comp:
            out[r][c] = bgc
    for _, comp in red_icons:
        for r, c in comp:
            out[r][c] = GRAY
    for k in range(len(red_icons)):
        for r, c in top[1]:
            out[r - pitch * (k + 1)][c] = top[0]
    return out


def _make_icon(rng, ih, iw):
    """One connected ih x iw icon with a full middle row (so stacked copies
    with a 1-row gap never merge and each copy is one component)."""
    mid = ih // 2
    icon = [[0] * iw for _ in range(ih)]
    icon[mid] = [1] * iw
    for i in range(ih):
        if i == mid:
            continue
        a = rng.randint(1, iw - 2) if iw > 3 else 1
        b = rng.randint(a, iw - 2)
        for j in range(a, b + 1):
            icon[i][j] = 1
    return icon


def _build_pair(rng, difficulty):
    n_towers = {"easy": 3, "medium": 4, "hard": 5}[difficulty]
    ih = rng.randint(2, 3)
    iw = rng.randint(4, 5)
    pitch = ih + 1
    max_icons = {"easy": 3, "medium": 4, "hard": 5}[difficulty]
    h = rng.randint(24, 30)
    w_need = 1 + n_towers * (iw + 1)
    w = rng.randint(max(w_need, 22), 30)
    bg = rng.choice((1, 4, 6, 7, 8, 9))
    tower_cols = rng.sample([v for v in range(10) if v not in (0, bg, GRAY)],
                            n_towers)
    icon = _make_icon(rng, ih, iw)
    counts = [rng.randint(1, max_icons) for _ in range(n_towers)]
    gi, ri = rng.sample(range(n_towers), 2)
    # the grown green tower must still fit above the legend row
    while (counts[gi] + counts[ri]) * pitch + 1 > h - 1:
        counts[gi] = max(1, counts[gi] - 1)
        counts[ri] = max(1, counts[ri] - 1)
    g = [[bg] * w for _ in range(h)]
    slack = w - w_need
    c0 = 1 + rng.randint(0, slack)
    for ti in range(n_towers):
        base_top = h - 2 - ih  # bottom icon's top row (bar row + 1 gap)
        for k in range(counts[ti]):
            r0 = base_top - k * pitch
            for i in range(ih):
                for j in range(iw):
                    if icon[i][j]:
                        g[r0 + i][c0 + j] = tower_cols[ti]
        if ti == gi:
            for j in range(iw):
                g[h - 1][c0 + j] = 3
        elif ti == ri:
            for j in range(iw):
                g[h - 1][c0 + j] = 2
        c0 += iw + 1
    return g, _apply(g)


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    n_train = ctx.draw_int("n_train", 2, 4)
    n_test = ctx.draw_int("n_test", 1, 2)
    pairs = []
    for idx in range(n_train + n_test):
        rng = ctx.draw_rng(f"pair_{idx}")
        gin, gout = _build_pair(rng, difficulty)
        pairs.append({"input": gin, "output": gout})
    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": PROGRAM,
        "concept": "bar_transfer",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.bar_transfer import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"bar_transfer gen1 v{VERSION}")
