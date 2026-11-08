"""gen1: slotted template + scattered shape vote.

Scene: a big tc-colored rectangle on a bg field, pierced by 3-8 slots
drawn from 2-4 shape classes (dot / bar2 / bar3 / L3 / square / T4 / Z4 /
plus / bracket5 — pairwise distinct under D8). Outside its bbox, each
used class scatters in 2+ colors with one strictly-modal color; slots may
be any D8 orientation of their class. Transform: crop the template bbox
and recolor every slot to its class's modal scattered color.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx

VERSION = "1.0.0"
TASK_ID = "generic_slot_match_gen1"

PROGRAM = """(rule!
 ;; A large TEMPLATE rectangle (the biggest object) is pierced by SLOTS of
 ;; the field's background color; small shapes lie scattered outside it.
 ;; Each slot takes the MODAL color of the scattered shapes with the same
 ;; shape up to rotation/reflection. Output is the template's bounding box
 ;; with every slot recolored.
 (lambda (g)
   (let ()
     (define bg (mode g))
     (define objs (objects g bg))
     (define tmpl
       (reduce (lambda (b o) (if (> (obj-size o) (obj-size b)) o b))
               (first objs) objs))
     (define bb (obj-bbox tmpl))
     (define r1 (first bb))
     (define c1 (second bb))
     (define r2 (nth bb 2))
     (define c2 (nth bb 3))
     (define sub (subgrid g r1 c1 r2 c2))
     (define tc (obj-color tmpl))
     (define slots
       (filter (lambda (o) (= (obj-color o) bg)) (objects sub tc)))
     (define scat
       (filter (lambda (o)
                 (let ((b (obj-bbox o)))
                   (not (and (>= (first b) r1) (<= (nth b 2) r2)
                             (>= (second b) c1) (<= (nth b 3) c2)))))
               objs))
     (reduce
      (lambda (out slot)
        (let* ((cands (filter (lambda (o)
                                (if (match-transform (obj-cells o)
                                                     (obj-cells slot))
                                    #t #f))
                              scat))
               (cnt (lambda (col)
                      (count-if (lambda (q) (= (obj-color q) col)) cands)))
               (best (reduce (lambda (bc o)
                               (if (> (cnt (obj-color o)) (cnt bc))
                                   (obj-color o) bc))
                             (obj-color (first cands)) cands)))
          (recolor-cells out (obj-cells slot) best)))
      sub slots))))"""

SHAPES = {
    "dot": ((0, 0),),
    "bar2": ((0, 0), (1, 0)),
    "bar3": ((0, 0), (0, 1), (0, 2)),
    "L3": ((0, 0), (1, 0), (1, 1)),
    "square": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "T4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "Z4": ((0, 1), (0, 2), (1, 0), (1, 1)),
    "plus": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "bracket5": ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
}


def _norm(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _d8_variants(cells):
    out = []
    cur = list(cells)
    for _ in range(4):
        cur = [(c, -r) for r, c in cur]
        out.append(_norm(cur))
        out.append(_norm([(r, -c) for r, c in cur]))
    return out


def _same_class(a, b):
    return _norm(b) in _d8_variants(a)


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


def _apply(g):
    """Python mirror of PROGRAM (same orders, strict-> tie-breaks)."""
    bg = Counter(v for row in g for v in row if v != 0).most_common(1)[0][0]
    objs = _components(g, bg)
    tmpl = objs[0]
    for o in objs[1:]:
        if len(o[1]) > len(tmpl[1]):
            tmpl = o
    tc, tcomp = tmpl
    r1 = min(r for r, _ in tcomp)
    c1 = min(c for _, c in tcomp)
    r2 = max(r for r, _ in tcomp)
    c2 = max(c for _, c in tcomp)
    sub = [row[c1:c2 + 1] for row in g[r1:r2 + 1]]
    slots = [(col, comp) for col, comp in _components(sub, tc) if col == bg]

    def outside(comp):
        rr1 = min(r for r, _ in comp)
        cc1 = min(c for _, c in comp)
        rr2 = max(r for r, _ in comp)
        cc2 = max(c for _, c in comp)
        return not (rr1 >= r1 and rr2 <= r2 and cc1 >= c1 and cc2 <= c2)

    scat = [(col, comp) for col, comp in objs if outside(comp)]
    out = [row[:] for row in sub]
    for _, scomp in slots:
        cands = [(col, comp) for col, comp in scat
                 if _same_class(comp, scomp)]

        def cnt(col):
            return sum(1 for c2_, _ in cands if c2_ == col)

        best = cands[0][0]
        for col, _ in cands:
            if cnt(col) > cnt(best):
                best = col
        for r, c in scomp:
            out[r][c] = best
    return out


def _stamp_ok(g, cells, r0, c0, h, w):
    """1-cell clearance against any non-bg cell (bg encoded as None here)."""
    for r, c in cells:
        rr, cc = r0 + r, c0 + c
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                ar, ac = rr + dr, cc + dc
                if 0 <= ar < h and 0 <= ac < w and g[ar][ac] is not None:
                    return False
    return True


def _build_pair(rng, difficulty):
    n_classes = {"easy": 2, "medium": 3, "hard": 4}[difficulty]
    classes = rng.sample(list(SHAPES), n_classes)
    h = rng.randint(27, 30)
    w = rng.randint(27, 30)
    th = rng.randint(10, 13)
    tw = rng.randint(10, 13)
    bg, tc = rng.sample(range(1, 10), 2)
    tr = rng.choice((0, 1))
    tcc = rng.choice((0, 1, w - tw - 1, w - tw))
    # template canvas: None = free background
    field = [[None] * w for _ in range(h)]
    for r in range(tr, tr + th):
        for c in range(tcc, tcc + tw):
            field[r][c] = tc
    # carve slots (inside template, 1-margin, mutual clearance)
    slot_specs = []
    for cls in classes:
        for _ in range(rng.randint(1, 2)):
            slot_specs.append(cls)
    carved = []
    for cls in slot_specs:
        cells = rng.choice(_d8_variants(SHAPES[cls]))
        for _try in range(80):
            sh = max(r for r, _ in cells) + 1
            sw = max(c for _, c in cells) + 1
            r0 = rng.randint(tr + 1, tr + th - sh - 1)
            c0 = rng.randint(tcc + 1, tcc + tw - sw - 1)
            abs_cells = [(r0 + r, c0 + c) for r, c in cells]
            near = {(r + dr, c + dc) for r, c in abs_cells
                    for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
            if any(field[r][c] != tc for r, c in near):
                continue
            for r, c in abs_cells:
                field[r][c] = bg
            carved.append(cls)
            break
    if len(set(carved)) != n_classes:
        raise ValueError("failed to carve all classes")
    # scatter: per class, one strict-modal color + minority colors
    intended = {}
    for cls in classes:
        colors = rng.sample([v for v in range(1, 10)
                             if v not in (bg, tc)], rng.randint(2, 3))
        modal = colors[0]
        counts = {modal: rng.randint(2, 3)}
        for c in colors[1:]:
            counts[c] = rng.randint(1, counts[modal] - 1)
        intended[cls] = (modal, counts)
        for col, n in counts.items():
            placed = 0
            for _try in range(300):
                if placed == n:
                    break
                cells = rng.choice(_d8_variants(SHAPES[cls]))
                r0 = rng.randint(0, h - 1)
                c0 = rng.randint(0, w - 1)
                if not _stamp_ok(field, cells, r0, c0, h, w):
                    continue
                # keep fully outside the template bbox
                if any(tr <= r0 + r <= tr + th - 1 and
                       tcc <= c0 + c <= tcc + tw - 1 for r, c in cells):
                    continue
                for r, c in cells:
                    field[r0 + r][c0 + c] = col
                placed += 1
            if placed < n:
                raise ValueError("could not scatter enough shapes")
    g = [[bg if v is None else v for v in row] for row in field]
    out = _apply(g)
    # well-posedness: every slot must have gotten a scattered color
    sub_expect = [row[tcc:tcc + tw] for row in g[tr:tr + th]]
    for r in range(th):
        for c in range(tw):
            if sub_expect[r][c] == bg:
                if out[r][c] == bg or out[r][c] == tc:
                    raise ValueError("slot not filled")
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
        "concept": "slot_match",
        "difficulty": difficulty,
    }


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.slot_match import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"slot_match gen1 v{VERSION}")
