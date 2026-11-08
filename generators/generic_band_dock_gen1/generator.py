"""gen1: reverse-built band docking scenes.

Scene: a full-span jagged band; one or two solid rectangles are cut into
2-3 interlocking pieces by jagged interfaces, their band-side face carves
a BITE into the band edge, then pieces scatter to loose positions (either
side). 1-2 single-cell decoy notches stay open. Transform: re-dock every
piece (first fills the bite, each next meshes per-column, stop at a flat
surface). Vertical variants transpose. Scenes resample until the
detector's output equals the intended assembly.
"""
from __future__ import annotations

from collections import Counter, deque
import hashlib

from puzzle_generators.base import gen_ctx

VERSION = "1.1.0"
TASK_ID = "generic_band_dock_gen1"
GENERATOR_ID = TASK_ID
SUMMARY = (
    "Dock scattered jagged pieces into matching bites on a full-span band, "
    "stacking interlocking layers until each local surface is flat while "
    "leaving unmatched one-cell decoy notches open."
)
INVARIANTS = (
    "one monochrome jagged band spans the full width or full height",
    "all loose pieces are monochrome, separated from the band, and preserve their colors",
    "each real bite is completed by two or three interlocking pieces",
    "one or two single-cell decoy notches remain open in the output",
    "docking preserves dimensions and the exact per-color cell inventory",
    "training demonstrations cover both band orientations and both docking sides",
)
AXES = {
    "difficulty": ("easy", "medium", "hard"),
    "orientation": ("horizontal", "vertical"),
    "stacks": (1, 2),
    "pieces_per_stack": (2, 3),
    "dock_side": ("negative", "positive"),
    "decoy_notches": (1, 2),
}
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

PROGRAM = """(rule!
 ;; TETRIS-DOCKING: a jagged full-span band has BITE notches on its edges;
 ;; loose pieces drop against the band, the first piece filling a bite
 ;; exactly, each next piece meshing per-column with the stack's surface
 ;; (no gaps), until the surface is FLAT — a completed rectangle. Decoy
 ;; bites that fit no piece stay open. Output keeps only the band and the
 ;; docked stacks; vertical bands are handled by transposing in and out.
 (lambda (g)
   (let ()
     (define (solve-h gg)
       (let ()
         (define h (rows gg))
         (define w (cols gg))
         (define allc (objects-multicolor gg 0))
         (define band
           (reduce (lambda (b o) (if (> (obj-size o) (obj-size b)) o b))
                   (first allc) allc))
         (define bc (at gg (first (first (obj-cells band)))
                        (second (first (obj-cells band)))))
         (define bb (obj-bbox band))
         (define br1 (first bb))
         (define br2 (nth bb 2))
         (define band-cells (obj-cells band))
         (define pieces
           (sort-by
            (map (lambda (o)
                   (let* ((cs (obj-cells o))
                          (r0 (reduce min (first (first cs)) (map first cs)))
                          (c0 (reduce min (second (first cs))
                                      (map second cs)))
                          (rel (map (lambda (p) (list (- (first p) r0)
                                                      (- (second p) c0)))
                                    cs)))
                     (list (at gg (first (first cs)) (second (first cs)))
                           rel
                           (+ (reduce max 0 (map second rel)) 1)
                           r0 c0)))
                 (filter (lambda (o) (not (equal? o band))) allc))
            (lambda (p) (+ (* (nth p 3) 100) (nth p 4)))))
         (define (cluster-of r c seenl)
           (connected-region gg r c
                             (lambda (rr cc vv)
                               (and (= vv 0) (>= rr br1) (<= rr br2)))
                             4))
         (define clusters
           (let loop ((r br1) (c 0) (seen (list)) (acc (list)))
             (cond ((> r br2) acc)
                   ((>= c w) (loop (+ r 1) 0 seen acc))
                   ((and (= (at gg r c) 0)
                         (not (member? (list r c) seen)))
                    (let ((cl (cluster-of r c seen)))
                      (loop r (+ c 1) (append seen cl) (append acc (list cl)))))
                   (else (loop r (+ c 1) seen acc)))))
         (define sorted-clusters
           (sort-by clusters
                    (lambda (cl)
                      (+ (* (- 999 (length cl)) 1000000)
                         (* (reduce min 999 (map first cl)) 1000)
                         (reduce min 999 (map second cl))))))
         (define out0
           (reduce (lambda (o p) (set-cell o (first p) (second p) bc))
                   (empty-grid h w 0) band-cells))
         (define (surf0 side c)
           (if (not (in-bounds? br1 c h w))
               -999
               (let ((rs (filter (lambda (r) (= (at gg r c) bc))
                                 (range br1 (+ br2 1)))))
                 (if (null? rs)
                     -999
                     (if (= side 0)
                         (reduce min (first rs) rs)
                         (reduce max (first rs) rs))))))
         (define (try-place p coff sf side out)
           (let* ((rel (nth p 1))
                  (cjs (unique (map second rel)))
                  (prof (map (lambda (j)
                               (let ((is (map first
                                              (filter (lambda (q)
                                                        (= (second q) j))
                                                      rel))))
                                 (if (= side 0)
                                     (reduce max (first is) is)
                                     (reduce min (first is) is))))
                             cjs))
                  (svals (map (lambda (j) (sf (+ coff j))) cjs))
                  (deltas (map (lambda (j s)
                                 (if (= side 0)
                                     (- (- s 1) j)
                                     (- (+ s 1) j)))
                               prof svals)))
             (if (or (< 0 (count-if (lambda (s) (= s -999)) svals))
                     (< 0 (count-if (lambda (d) (!= d (first deltas)))
                                    deltas)))
                 (list)
                 (let* ((d (first deltas))
                        (cells (map (lambda (q) (list (+ (first q) d)
                                                      (+ (second q) coff)))
                                    rel)))
                   (if (< 0 (count-if
                             (lambda (q)
                               (or (not (in-bounds? (first q) (second q) h w))
                                   (!= (at out (first q) (second q)) 0)))
                             cells))
                       (list)
                       cells)))))
         (define (paint out p cells)
           (reduce (lambda (o q) (set-cell o (first q) (second q)
                                           (first p)))
                   out cells))
         (define (upd-surf sf cells side w1 w2)
           (lambda (c)
             (let ((mine (map first (filter (lambda (q) (= (second q) c))
                                            cells))))
               (if (null? mine)
                   (sf c)
                   (if (= side 0)
                       (reduce min (first mine) mine)
                       (reduce max (first mine) mine))))))
         (let cluster-loop ((cls sorted-clusters) (out out0) (used (list)))
           (if (null? cls)
               out
               (let* ((cl (first cls))
                      (top (< 0 (count-if (lambda (p) (= (first p) br1))
                                          cl)))
                      (bot (< 0 (count-if (lambda (p) (= (first p) br2))
                                          cl))))
                 (if (or (and top bot) (and (not top) (not bot)))
                     (cluster-loop (rest cls) out used)
                     (let* ((side (if top 0 1))
                            (bcmin (reduce min 999 (map second cl)))
                            (bcmax (reduce max 0 (map second cl)))
                            (fst
                             (find-first
                              (lambda (pc) (not (null? (nth pc 2))))
                              (flatmap
                               (lambda (pi)
                                 (let ((p (nth pieces pi)))
                                   (if (member? pi used)
                                       (list)
                                       (map (lambda (coff)
                                              (list pi coff
                                                    (try-place
                                                     p coff
                                                     (lambda (c)
                                                       (surf0 side c))
                                                     side out)))
                                            (range (+ (- bcmax (nth p 2)) 1)
                                                   (+ bcmin 1))))))
                               (range 0 (length pieces))))))
                       (if (not fst)
                           (cluster-loop (rest cls) out used)
                           (let* ((pi (first fst))
                                  (p (nth pieces pi))
                                  (coff (second fst))
                                  (cells (nth fst 2))
                                  (w1 coff)
                                  (w2 (+ coff (- (nth p 2) 1))))
                             (let stack-loop
                                 ((out2 (paint out p cells))
                                  (sf (upd-surf (lambda (c) (surf0 side c))
                                                cells side w1 w2))
                                  (used2 (append used (list pi))))
                               (let ((svals (map sf (range w1 (+ w2 1)))))
                                 (if (= 0 (count-if
                                           (lambda (s) (!= s (first svals)))
                                           svals))
                                     (cluster-loop (rest cls) out2 used2)
                                     (let ((nxt
                                            (find-first
                                             (lambda (pc)
                                               (not (null? (nth pc 2))))
                                             (flatmap
                                              (lambda (pi2)
                                                (let ((p2 (nth pieces pi2)))
                                                  (if (member? pi2 used2)
                                                      (list)
                                                      (map (lambda (c2)
                                                             (list pi2 c2
                                                                   (try-place
                                                                    p2 c2 sf
                                                                    side out2)))
                                                           (range w1
                                                                  (+ (- w2 (nth p2 2)) 2))))))
                                              (range 0 (length pieces))))))
                                       (if (not nxt)
                                           (cluster-loop (rest cls) out2 used2)
                                           (let* ((pi2 (first nxt))
                                                  (p2 (nth pieces pi2))
                                                  (cells2 (nth nxt 2)))
                                             (stack-loop
                                              (paint out2 p2 cells2)
                                              (upd-surf sf cells2 side w1 w2)
                                              (append used2
                                                      (list pi2))))))))))))))))))
     (let* ((allc (objects-multicolor g 0))
            (band (reduce (lambda (b o)
                            (if (> (obj-size o) (obj-size b)) o b))
                          (first allc) allc))
            (bb (obj-bbox band)))
       (if (= (+ (- (nth bb 3) (second bb)) 1) (cols g))
           (solve-h g)
           (transpose (solve-h (transpose g))))))))"""


def _normalized_rule_text(source):
    """Comment/whitespace-normalized authority text for evidence invalidation."""
    code = "\n".join(line.split(";", 1)[0] for line in source.splitlines())
    return " ".join(code.split())


RULE_HASH = hashlib.sha256(
    _normalized_rule_text(PROGRAM).encode("utf-8")
).hexdigest()


def _comps(g):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != 0 and not seen[r][c]:
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
                                    and not seen[nx][ny] and g[nx][ny] != 0:
                                seen[nx][ny] = True
                                q.append((nx, ny))
                out.append(comp)
    return out


def _transpose(g):
    return [list(row) for row in zip(*g)]


def _apply(g):
    """Python mirror of PROGRAM."""
    cs = _comps(g)
    band = max(cs, key=len)
    c1 = min(c for _, c in band)
    c2 = max(c for _, c in band)
    if c2 - c1 + 1 == len(g[0]):
        return _apply_h(g)
    return _transpose(_apply_h(_transpose(g)))


def _apply_h(g):
    h, w = len(g), len(g[0])
    cs = _comps(g)
    band = max(cs, key=len)
    bc = g[band[0][0]][band[0][1]]
    br1 = min(r for r, _ in band)
    br2 = max(r for r, _ in band)
    pieces = []
    for comp in cs:
        if comp is band:
            continue
        r0 = min(r for r, _ in comp)
        c0 = min(c for _, c in comp)
        rel = [(r - r0, c - c0) for r, c in comp]
        pieces.append({'col': g[comp[0][0]][comp[0][1]], 'rel': rel,
                       'w': max(c for _, c in rel) + 1, 'r0': r0, 'c0': c0,
                       'used': False})
    pieces.sort(key=lambda p: p['r0'] * 100 + p['c0'])
    seen = set()
    clusters = []
    for r in range(br1, br2 + 1):
        for c in range(w):
            if g[r][c] == 0 and (r, c) not in seen:
                q = deque([(r, c)])
                seen.add((r, c))
                cl = [(r, c)]
                while q:
                    x, y = q.popleft()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if br1 <= nx <= br2 and 0 <= ny < w \
                                and g[nx][ny] == 0 and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            q.append((nx, ny))
                            cl.append((nx, ny))
                clusters.append(cl)
    clusters.sort(key=lambda cl: (999 - len(cl)) * 1000000 +
                  min(r for r, _ in cl) * 1000 + min(c for _, c in cl))
    out = [[0] * w for _ in range(h)]
    for r, c in band:
        out[r][c] = bc

    def surf0(side, c):
        if not 0 <= c < w:
            return None
        rs = [r for r in range(br1, br2 + 1) if g[r][c] == bc]
        if not rs:
            return None
        return min(rs) if side == 0 else max(rs)

    def try_place(p, coff, sf, side):
        rel = p['rel']
        cjs = sorted({j for _, j in rel})
        deltas = set()
        for j in cjs:
            s = sf(coff + j)
            if s is None:
                return None
            if side == 0:
                deltas.add(s - 1 - max(i for i, jj in rel if jj == j))
            else:
                deltas.add(s + 1 - min(i for i, jj in rel if jj == j))
        if len(deltas) != 1:
            return None
        d = deltas.pop()
        cells = [(i + d, j + coff) for i, j in rel]
        if any(not (0 <= r < h and 0 <= c_ < w) or out[r][c_] != 0
               for r, c_ in cells):
            return None
        return cells

    for cl in clusters:
        top = any(r == br1 for r, _ in cl)
        bot = any(r == br2 for r, _ in cl)
        if top == bot:
            continue
        side = 0 if top else 1
        bcmin = min(c for _, c in cl)
        bcmax = max(c for _, c in cl)
        first = None
        for p in pieces:
            if p['used']:
                continue
            for coff in range(bcmax - p['w'] + 1, bcmin + 1):
                cells = try_place(p, coff, lambda c: surf0(side, c), side)
                if cells:
                    first = (p, coff, cells)
                    break
            if first:
                break
        if not first:
            continue
        p, coff, cells = first
        p['used'] = True
        for r, c in cells:
            out[r][c] = p['col']
        w1, w2 = coff, coff + p['w'] - 1
        surf = {}
        for c in range(w1, w2 + 1):
            mine = [r for r, cc in cells if cc == c]
            surf[c] = (min(mine) if side == 0 else max(mine)) if mine \
                else surf0(side, c)
        while len({surf[c] for c in range(w1, w2 + 1)}) != 1:
            nxt = None
            for p2 in pieces:
                if p2['used']:
                    continue
                for c2 in range(w1, w2 - p2['w'] + 2):
                    cells2 = try_place(p2, c2, lambda c: surf.get(c), side)
                    if cells2:
                        nxt = (p2, c2, cells2)
                        break
                if nxt:
                    break
            if not nxt:
                break
            p2, c2, cells2 = nxt
            p2['used'] = True
            for r, c in cells2:
                out[r][c] = p2['col']
            for c in range(w1, w2 + 1):
                mine = [r for r, cc in cells2 if cc == c]
                if mine:
                    surf[c] = min(mine) if side == 0 else max(mine)
    return out



def _cell_groups(cells):
    """Return 4-connected groups from an iterable of coordinates."""
    remaining = set(cells)
    groups = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        group = [start]
        q = deque([start])
        while q:
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    group.append(nxt)
                    q.append(nxt)
        groups.append(group)
    return groups


def _mono_components(g, *, ignored=(0,)):
    """4-connected monochrome components, excluding ignored colors."""
    h, w = len(g), len(g[0])
    ignored = set(ignored)
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = g[r][c]
            if color in ignored or (r, c) in seen:
                continue
            cells = []
            q = deque([(r, c)])
            seen.add((r, c))
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < h and 0 <= ny < w \
                            and (nx, ny) not in seen and g[nx][ny] == color:
                        seen.add((nx, ny))
                        q.append((nx, ny))
            out.append((color, cells))
    return out


def _band_descriptor(g):
    comps = _comps(g)
    if not comps:
        raise ValueError("scene has no non-background object")
    sizes = sorted((len(comp), index) for index, comp in enumerate(comps))
    if len(sizes) > 1 and sizes[-1][0] == sizes[-2][0]:
        raise ValueError("largest component is not a unique band")
    band_index = sizes[-1][1]
    band = comps[band_index]
    colors = {g[r][c] for r, c in band}
    if len(colors) != 1:
        raise ValueError("largest component is not monochrome")
    bc = next(iter(colors))
    h, w = len(g), len(g[0])
    r1, r2 = min(r for r, _ in band), max(r for r, _ in band)
    c1, c2 = min(c for _, c in band), max(c for _, c in band)
    horizontal = c1 == 0 and c2 == w - 1 and r2 - r1 + 1 < h
    vertical = r1 == 0 and r2 == h - 1 and c2 - c1 + 1 < w
    if horizontal == vertical:
        raise ValueError("band must span exactly one full grid axis")
    return {
        "components": comps,
        "band_index": band_index,
        "band": band,
        "band_color": bc,
        "bbox": (r1, c1, r2, c2),
        "orientation": "horizontal" if horizontal else "vertical",
    }


def _flat_color_counts(g):
    return Counter(value for row in g for value in row)


def _scene_features(g):
    """Return observable scene facts plus structural errors.

    The checker deliberately derives every axis from the grid and recomputes the
    selected rule. It never trusts generation metadata.
    """
    errors = []
    if not isinstance(g, list) or not g or not all(isinstance(row, list) for row in g):
        return {}, ["grid must be a non-empty list of rows"]
    width = len(g[0])
    if width == 0 or any(len(row) != width for row in g):
        return {}, ["grid must be rectangular and non-empty"]
    h, w = len(g), width
    if not (24 <= h <= 30 and 24 <= w <= 30):
        errors.append(f"grid dimensions {h}x{w} fall outside 24..30")
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9
           for row in g for v in row):
        errors.append("grid values must be integer ARC colors 0..9")
        return {}, errors

    try:
        desc = _band_descriptor(g)
    except Exception as exc:
        return {}, errors + [str(exc)]
    normalized = g if desc["orientation"] == "horizontal" else _transpose(g)
    try:
        ndesc = _band_descriptor(normalized)
    except Exception as exc:
        return {}, errors + [f"normalized scene: {exc}"]
    br1, _, br2, _ = ndesc["bbox"]
    thickness = br2 - br1 + 1
    if not 3 <= thickness <= 6:
        errors.append(f"band thickness {thickness} is outside 3..6")
    bc = ndesc["band_color"]
    if bc == 0:
        errors.append("band color must be nonzero")
    for c in range(len(normalized[0])):
        if not any(normalized[r][c] == bc for r in range(br1, br2 + 1)):
            errors.append(f"band has no cell in normalized column {c}")
            break

    loose = [comp for index, comp in enumerate(ndesc["components"])
             if index != ndesc["band_index"]]
    if not 2 <= len(loose) <= 6:
        errors.append(f"expected 2..6 loose pieces, found {len(loose)}")
    for index, comp in enumerate(loose):
        colors = {normalized[r][c] for r, c in comp}
        if len(colors) != 1 or bc in colors:
            errors.append(f"loose piece {index} must be monochrome and differ from the band")
            continue
        rows = [r for r, _ in comp]
        cols = [c for _, c in comp]
        if not (max(rows) <= br1 - 2 or min(rows) >= br2 + 2):
            errors.append(f"loose piece {index} is not separated from the band")
        pw = max(cols) - min(cols) + 1
        if not 3 <= pw <= 6:
            errors.append(f"loose piece {index} width {pw} is outside 3..6")
        for c in range(min(cols), max(cols) + 1):
            rs = sorted(r for r, cc in comp if cc == c)
            if not rs or rs != list(range(rs[0], rs[-1] + 1)):
                errors.append(f"loose piece {index} is not column-solid")
                break

    before = [row[:] for row in g]
    try:
        out = _apply(g)
    except Exception as exc:
        return {}, errors + [f"selected rule raised {type(exc).__name__}: {exc}"]
    if g != before:
        errors.append("selected rule mutates its input")
    if len(out) != h or any(len(row) != w for row in out):
        errors.append("selected rule changes grid dimensions")
        return {}, errors
    if out == g:
        errors.append("scene is an identity transformation")
    if _flat_color_counts(out) != _flat_color_counts(g):
        errors.append("docking does not preserve the exact color inventory")
    if len(_comps(out)) != 1:
        errors.append("docked output is not one connected assembly")

    outn = out if desc["orientation"] == "horizontal" else _transpose(out)
    input_band_zeros = sum(
        normalized[r][c] == 0
        for r in range(br1, br2 + 1)
        for c in range(len(normalized[0]))
    )
    output_band_zeros = sum(
        outn[r][c] == 0
        for r in range(br1, br2 + 1)
        for c in range(len(outn[0]))
    )
    if input_band_zeros <= output_band_zeros:
        errors.append("no real bite is filled by docking")
    if not 1 <= output_band_zeros <= 2:
        errors.append(
            f"expected 1..2 surviving decoy notches, found {output_band_zeros}"
        )

    piece_cells = [
        (r, c) for r, row in enumerate(outn) for c, value in enumerate(row)
        if value not in (0, bc)
    ]
    stacks = _cell_groups(piece_cells)
    if not 1 <= len(stacks) <= 2:
        errors.append(f"expected 1..2 docked stacks, found {len(stacks)}")
    mono = _mono_components(outn, ignored=(0, bc))
    if len(mono) != len(loose):
        errors.append(
            f"docked piece count {len(mono)} differs from loose count {len(loose)}"
        )
    piece_counts = []
    sides = set()
    for index, stack in enumerate(stacks):
        stack_set = set(stack)
        count = sum(1 for _, comp in mono if comp and comp[0] in stack_set)
        piece_counts.append(count)
        if not 2 <= count <= 3:
            errors.append(f"docked stack {index} has {count} pieces, expected 2..3")
        above = min(r for r, _ in stack) < br1
        below = max(r for r, _ in stack) > br2
        if above == below:
            errors.append(f"docked stack {index} does not occupy exactly one band side")
        else:
            sides.add("negative" if above else "positive")

    return {
        "orientation": desc["orientation"],
        "band_color": bc,
        "band_thickness": thickness,
        "loose_pieces": len(loose),
        "stacks": len(stacks),
        "pieces_per_stack": tuple(sorted(piece_counts)),
        "dock_sides": tuple(sorted(sides)),
        "input_band_zeros": input_band_zeros,
        "decoy_notches": output_band_zeros,
        "output": out,
    }, errors


def strict_canonical_like(grid):
    """Reject malformed or shortcut-hiding band-docking inputs."""
    _, errors = _scene_features(grid)
    return errors


def _identity_rival(grid):
    return [row[:] for row in grid]


def _band_only_rival(grid):
    desc = _band_descriptor(grid)
    out = [[0] * len(grid[0]) for _ in grid]
    for r, c in desc["band"]:
        out[r][c] = desc["band_color"]
    return out


def _monochrome_dock_rival(grid):
    desc = _band_descriptor(grid)
    bc = desc["band_color"]
    out = _apply(grid)
    return [[bc if value != 0 else 0 for value in row] for row in out]


def _fill_every_notch_rival(grid):
    desc = _band_descriptor(grid)
    out = _apply(grid)
    r1, c1, r2, c2 = desc["bbox"]
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if out[r][c] == 0:
                out[r][c] = desc["band_color"]
    return out


def _witness_docking_changes_layout(grid):
    features, errors = _scene_features(grid)
    return not errors and features["output"] != grid


def _witness_piece_colors_are_semantic(grid):
    features, errors = _scene_features(grid)
    if errors:
        return False
    return len(set(value for row in features["output"] for value in row) - {0}) >= 3


def _witness_decoy_notch_survives(grid):
    features, errors = _scene_features(grid)
    return not errors and 1 <= features["decoy_notches"] <= 2


SEMANTIC_WITNESSES = {
    "docking_changes_layout": _witness_docking_changes_layout,
    "piece_colors_are_semantic": _witness_piece_colors_are_semantic,
    "decoy_notch_survives": _witness_decoy_notch_survives,
}
SEMANTIC_RIVALS = {
    "identity": _identity_rival,
    "erase_loose_pieces": _band_only_rival,
    "recolor_all_docked_pieces_as_band": _monochrome_dock_rival,
    "fill_every_band_notch": _fill_every_notch_rival,
}
WITNESS_RIVALS = {
    "docking_changes_layout": ["identity", "erase_loose_pieces"],
    "piece_colors_are_semantic": ["recolor_all_docked_pieces_as_band"],
    "decoy_notch_survives": ["fill_every_band_notch"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"identity": _identity_rival}


def lesson_identifiable(demos, query=None):
    """Require demonstrations that eliminate named rivals and cover query axes."""
    errors = []
    if len(demos or []) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    demo_features = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is not an input/output pair")
            continue
        features, findings = _scene_features(pair["input"])
        if findings:
            errors.append(f"demo {index} malformed: {findings[0]}")
            continue
        if pair["output"] != features["output"]:
            errors.append(f"demo {index} output disagrees with the selected rule")
            continue
        demo_features.append(features)
    if errors:
        return errors

    survivors = [
        name for name, rival in SEMANTIC_RIVALS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
    ]
    if survivors:
        errors.append("named rival survives all demonstrations: " + ", ".join(survivors))
    orientations = {f["orientation"] for f in demo_features}
    if orientations != {"horizontal", "vertical"}:
        errors.append("demonstrations must include horizontal and vertical bands")
    sides = {side for f in demo_features for side in f["dock_sides"]}
    if sides != {"negative", "positive"}:
        errors.append("demonstrations must include docking on both band sides")

    if query is not None:
        if not isinstance(query, dict) or "input" not in query or "output" not in query:
            errors.append("query is not an input/output pair")
        else:
            qf, findings = _scene_features(query["input"])
            if findings:
                errors.append(f"query malformed: {findings[0]}")
            elif query["output"] != qf["output"]:
                errors.append("query output disagrees with the selected rule")
            else:
                if qf["stacks"] == 2 and not any(f["stacks"] == 2 for f in demo_features):
                    errors.append("two-stack query has no two-stack demonstration")
                qmax = max(qf["pieces_per_stack"], default=0)
                if qmax == 3 and not any(
                    max(f["pieces_per_stack"], default=0) == 3 for f in demo_features
                ):
                    errors.append("three-piece query has no three-piece demonstration")
    return errors


def self_check_task(task):
    """Validate structure, oracle agreement, diversity, and lesson sufficiency."""
    if not isinstance(task, dict):
        return ["task is not a dictionary"]
    errors = []
    difficulty = task.get("difficulty")
    if difficulty not in DIFFICULTY_SPECS:
        return ["task difficulty must be easy, medium, or hard"]
    train = list(task.get("train") or [])
    test = list(task.get("test") or [])
    expected_tests = 2 if difficulty == "hard" else 1
    if len(train) != EXAMPLES_NEEDED:
        errors.append(f"task must contain exactly {EXAMPLES_NEEDED} training pairs")
    if len(test) != expected_tests:
        errors.append(f"{difficulty} task must contain exactly {expected_tests} test pairs")
    if task.get("program") != PROGRAM:
        errors.append("task program is not the selected band-dock rule")
    if task.get("concept") != "band_dock":
        errors.append("task concept must be band_dock")
    meta = task.get("meta") or {}
    if meta.get("version") != VERSION:
        errors.append("task meta.version is stale")
    if meta.get("difficulty") != difficulty:
        errors.append("task meta.difficulty is inconsistent")
    if meta.get("rule_hash") != RULE_HASH:
        errors.append("task meta.rule_hash is stale")

    signatures = set()
    feature_rows = {"train": [], "test": []}
    lo, hi = DIFFICULTY_SPECS[difficulty]["dims"]
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            name = f"{split}[{index}]"
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                errors.append(f"{name} is not an input/output pair")
                continue
            grid = pair["input"]
            signature = repr(grid)
            if signature in signatures:
                errors.append(f"{name} duplicates an earlier input")
            signatures.add(signature)
            if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
                errors.append(f"{name} input is not a grid")
                continue
            h, w = len(grid), len(grid[0])
            if not (lo <= h <= hi and lo <= w <= hi):
                errors.append(f"{name} dimensions {h}x{w} violate {difficulty} range {lo}..{hi}")
            features, findings = _scene_features(grid)
            errors.extend(f"{name}: {finding}" for finding in findings)
            if findings:
                continue
            feature_rows[split].append(features)
            if pair["output"] != features["output"]:
                errors.append(f"{name} output disagrees with the selected rule")

    train_features = feature_rows["train"]
    if len(train_features) == len(train):
        orientations = {f["orientation"] for f in train_features}
        if orientations != {"horizontal", "vertical"}:
            errors.append("training split does not cover both orientations")
        sides = {side for f in train_features for side in f["dock_sides"]}
        if sides != {"negative", "positive"}:
            errors.append("training split does not cover both docking sides")
        stack_counts = {f["stacks"] for f in train_features}
        piece_counts = {n for f in train_features for n in f["pieces_per_stack"]}
        if difficulty == "easy":
            if stack_counts != {1} or piece_counts != {2}:
                errors.append("easy training must use one two-piece stack per pair")
        elif difficulty == "medium":
            if stack_counts != {1, 2}:
                errors.append("medium training must cover one- and two-stack scenes")
            if not {2, 3}.issubset(piece_counts):
                errors.append("medium training must cover two- and three-piece stacks")
        else:
            if stack_counts != {2}:
                errors.append("hard training must use two stacks per pair")
            if not {2, 3}.issubset(piece_counts):
                errors.append("hard training must cover two- and three-piece stacks")

    if len(train) >= EXAMPLES_NEEDED:
        for index, query in enumerate(test):
            errors.extend(
                f"test[{index}] lesson: {finding}"
                for finding in lesson_identifiable(train, query)
            )
    return errors

def _connected(cells):
    if not cells:
        return False
    cellset = set(cells)
    seen = {cells[0]}
    q = deque([cells[0]])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (x + dx, y + dy)
            if nb in cellset and nb not in seen:
                seen.add(nb)
                q.append(nb)
    return len(seen) == len(cells)


DIFFICULTY_SPECS = {
    "easy": {"dims": (24, 25), "band": (3, 4), "stack_width": (3, 4),
             "decoys": (1, 1), "margin": 9},
    "medium": {"dims": (26, 27), "band": (3, 5), "stack_width": (3, 5),
               "decoys": (1, 2), "margin": 9},
    "hard": {"dims": (28, 30), "band": (4, 5), "stack_width": (4, 5),
             "decoys": (2, 2), "margin": 9},
}


def _build_pair(rng, difficulty, *, orientation=None, n_stacks=None,
                side_plan=None, piece_counts=None):
    spec = DIFFICULTY_SPECS[difficulty]
    dlo, dhi = spec["dims"]
    h = rng.randint(dlo, dhi)
    w = rng.randint(dlo, dhi)
    bt = rng.randint(*spec["band"])
    margin = spec["margin"]
    br1 = rng.randint(margin, h - margin - bt)
    br2 = br1 + bt - 1
    bc = rng.randint(1, 9)
    g = [[0] * w for _ in range(h)]
    for r in range(br1, br2 + 1):
        for c in range(w):
            g[r][c] = bc

    if n_stacks is None:
        if difficulty == "easy":
            n_stacks = 1
        elif difficulty == "hard":
            n_stacks = 2
        else:
            n_stacks = rng.randint(1, 2)
    if n_stacks not in (1, 2):
        raise ValueError("n_stacks must be 1 or 2")
    sides = list(side_plan) if side_plan is not None \
        else rng.sample((0, 1), n_stacks)
    if len(sides) != n_stacks or len(set(sides)) != len(sides) \
            or any(side not in (0, 1) for side in sides):
        raise ValueError("side_plan must name distinct sides 0/1")
    if piece_counts is not None and (len(piece_counts) != n_stacks or
                                     any(k not in (2, 3) for k in piece_counts)):
        raise ValueError("piece_counts must provide 2 or 3 for each stack")

    windows = []
    all_pieces = []   # (color, abs cells at DOCKED position)
    for stack_index, side in enumerate(sides):
        sw = rng.randint(*spec["stack_width"])
        placed_window = False
        for _try in range(80):
            wc = rng.randint(1, w - sw - 1)
            if all(wc + sw + 2 < ow or ow + osw + 2 < wc
                   for ow, osw in windows):
                placed_window = True
                break
        if not placed_window:
            raise ValueError("could not place separated stack windows")
        windows.append((wc, sw))
        k = piece_counts[stack_index] if piece_counts is not None \
            else (2 if difficulty == "easy" else
                  (3 if difficulty == "hard" else rng.randint(2, 3)))
        # Bite profile carved into the band edge.
        bite = [rng.randint(0, 2) for _ in range(sw)]
        if max(bite) == 0:
            bite[rng.randrange(sw)] = 1
        if min(bite) == max(bite):
            bite[rng.randrange(sw)] = max(0, bite[0] - 1)
        edge = br1 if side == 0 else br2
        sgn = -1 if side == 0 else 1
        for j, depth in enumerate(bite):
            for d in range(depth):
                g[edge - sgn * d][wc + j] = 0
        # Interfaces are cumulative jagged profiles measured out from the bite.
        base = [-depth for depth in bite]
        profiles = [base]
        for _i in range(k - 1):
            prev = profiles[-1]
            step = rng.randint(2, 3)
            profiles.append([
                prev[j] + step + rng.randint(0, 1) for j in range(sw)
            ])
        top = max(profiles[-1]) + rng.randint(1, 2)
        profiles.append([top] * sw)
        piece_cells = []
        ok = True
        for i in range(k):
            cells = []
            for j in range(sw):
                for dd in range(profiles[i][j], profiles[i + 1][j]):
                    r = edge + sgn * (1 + dd)
                    if not 0 <= r < h:
                        ok = False
                    cells.append((r, wc + j))
            if not ok or not cells or not _connected(sorted(cells)):
                ok = False
                break
            piece_cells.append(cells)
        if not ok:
            raise ValueError("bad piece cut")
        cols = rng.sample([value for value in range(1, 10) if value != bc], k)
        for color, cells in zip(cols, piece_cells):
            all_pieces.append((color, cells))

    # One or two unmatched one-cell notches, kept away from every real bite.
    for _d in range(rng.randint(*spec["decoys"])):
        placed_decoy = False
        for _try in range(60):
            side = rng.choice((0, 1))
            edge = br1 if side == 0 else br2
            c = rng.randint(0, w - 1)
            if any(wc - 2 <= c <= wc + sw + 1 for wc, sw in windows):
                continue
            if g[edge][c] == bc:
                g[edge][c] = 0
                placed_decoy = True
                break
        if not placed_decoy:
            raise ValueError("could not place a decoy notch")

    intended = [row[:] for row in g]
    for color, cells in all_pieces:
        for r, c in cells:
            intended[r][c] = color

    # Scatter the pieces as separated loose objects away from band rows.
    occupied = [[value != 0 for value in row] for row in g]
    for color, cells in all_pieces:
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        rel = [(r - r0, c - c0) for r, c in cells]
        ph = max(r for r, _ in rel) + 1
        pw = max(c for _, c in rel) + 1
        placed = False
        for _try in range(300):
            rr = rng.randint(0, h - ph)
            cc = rng.randint(0, w - pw)
            if rr + ph > br1 - 1 and rr < br2 + 2:
                continue
            good = True
            for i, j in rel:
                for di in (-1, 0, 1):
                    for dj in (-1, 0, 1):
                        ar, ac = rr + i + di, cc + j + dj
                        if 0 <= ar < h and 0 <= ac < w and occupied[ar][ac]:
                            good = False
            if not good:
                continue
            for i, j in rel:
                g[rr + i][cc + j] = color
                occupied[rr + i][cc + j] = True
            placed = True
            break
        if not placed:
            raise ValueError("could not scatter a piece")

    orientation = orientation or rng.choice(("horizontal", "vertical"))
    if orientation == "vertical":
        g2, intended2 = _transpose(g), _transpose(intended)
    elif orientation == "horizontal":
        g2, intended2 = g, intended
    else:
        raise ValueError("orientation must be horizontal or vertical")
    if _apply(g2) != intended2:
        raise ValueError("detector output differs from construction")
    return g2, intended2

def _training_plan(difficulty, index, rng):
    if difficulty == "easy":
        plans = (
            {"orientation": "horizontal", "n_stacks": 1,
             "side_plan": (0,), "piece_counts": (2,)},
            {"orientation": "vertical", "n_stacks": 1,
             "side_plan": (1,), "piece_counts": (2,)},
            {"orientation": rng.choice(("horizontal", "vertical")),
             "n_stacks": 1, "side_plan": (rng.choice((0, 1)),),
             "piece_counts": (2,)},
        )
    elif difficulty == "medium":
        plans = (
            {"orientation": "horizontal", "n_stacks": 1,
             "side_plan": (0,), "piece_counts": (2,)},
            {"orientation": "vertical", "n_stacks": 1,
             "side_plan": (1,), "piece_counts": (3,)},
            {"orientation": rng.choice(("horizontal", "vertical")),
             "n_stacks": 2, "side_plan": (0, 1),
             "piece_counts": (2, 3)},
        )
    else:
        plans = (
            {"orientation": "horizontal", "n_stacks": 2,
             "side_plan": (0, 1), "piece_counts": (2, 3)},
            {"orientation": "vertical", "n_stacks": 2,
             "side_plan": (1, 0), "piece_counts": (3, 2)},
            {"orientation": rng.choice(("horizontal", "vertical")),
             "n_stacks": 2, "side_plan": (0, 1),
             "piece_counts": (3, 3)},
        )
    return plans[index]


def generate_task(seed, *, difficulty="medium"):
    if difficulty not in DIFFICULTY_SPECS:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    n_train = EXAMPLES_NEEDED
    n_test = 2 if difficulty == "hard" else 1
    pairs = []
    attempts = 0
    target_count = n_train + n_test
    while len(pairs) < target_count:
        index = len(pairs)
        rng = ctx.draw_rng(f"pair_{index}_{attempts}")
        attempts += 1
        if attempts > 300:
            raise ValueError("could not build enough pairs")
        kwargs = {}
        if index < n_train:
            kwargs = _training_plan(difficulty, index, rng)
        elif difficulty == "easy":
            kwargs = {"n_stacks": 1, "side_plan": (rng.choice((0, 1)),),
                      "piece_counts": (2,)}
        elif difficulty == "hard":
            kwargs = {"n_stacks": 2, "side_plan": (0, 1),
                      "piece_counts": (3, 3)}
        try:
            gin, gout = _build_pair(rng, difficulty, **kwargs)
        except (ValueError, IndexError):
            continue
        pairs.append({"input": gin, "output": gout})
    task = {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": PROGRAM,
        "concept": "band_dock",
        "difficulty": difficulty,
        "meta": {
            "version": VERSION,
            "difficulty": difficulty,
            "rule_hash": RULE_HASH,
        },
    }
    findings = self_check_task(task)
    if findings:
        raise ValueError("generated invalid task: " + "; ".join(findings[:3]))
    return task


if __name__ == "__main__":
    from puzzle_generators.generic.concepts.band_dock import parity_check
    parity_check(generate_task, n=25,
                 version_label=f"band_dock gen1 v{VERSION}")
