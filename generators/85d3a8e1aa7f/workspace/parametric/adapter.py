"""Center-selected centroid rays, with an optional color relay.

The native worker independently executes every claimed label in Racket.
Sampling uses only a local input RNG, never the private routing setting.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import random

TASK_ID = "85d3a8e1aa7f"
ROUTINGS = ("direct", "relay")
DIRS = ((-1, -1), (-1, 1), (1, 1), (1, -1))
DEMO_SIZES = (15, 21, 11, 17, 25, 30)
QUERY_SIZES = (9, 19, 27, 30)


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"routing"}
            or type(settings["routing"]) is not str
            or settings["routing"] not in ROUTINGS):
        raise ValueError("settings must be exactly routing=direct|relay")
    return settings["routing"]


def _count(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact colors 0..9")
    return grid


def _cells(grid, color):
    return [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == color]


def _direction(points, cr, cc):
    # Exact comparison matches the canonical integer division for nonnegative
    # coordinates, including its positive-direction equality convention.
    return (-1 if sum(r for r, _ in points) < len(points) * cr else 1,
            -1 if sum(c for _, c in points) < len(points) * cc else 1)


def _paint(grid, color, direction, *, full=False):
    cr, cc = len(grid) // 2, len(grid[0]) // 2
    dr, dc = direction
    return [[color if ((r - cr) * dc == (c - cc) * dr
                      and (full or (r - cr) * dr >= 0)) else 7
             for c in range(len(grid[0]))] for r in range(len(grid))]


def _hits(grid, key, direction):
    h, w = len(grid), len(grid[0])
    cr, cc = h // 2, w // 2
    dr, dc = direction
    return [(cr + k * dr, cc + k * dc) for k in range(1, max(h, w))
            if 0 <= cr + k * dr < h and 0 <= cc + k * dc < w
            and grid[cr + k * dr][cc + k * dc] not in (7, key)]


def intermediate(grid):
    """Private authoring trace, never included in the public challenge."""
    _grid(grid)
    cr, cc = len(grid) // 2, len(grid[0]) // 2
    key = grid[cr][cc]
    direction = _direction(_cells(grid, key), cr, cc)
    hits = _hits(grid, key, direction)
    hit = hits[0] if hits else None
    selected = grid[hit[0]][hit[1]] if hit else key
    return {"anchor": [cr, cc], "key_color": key,
            "first_direction": list(direction),
            "hit": list(hit) if hit else None, "relay_color": selected,
            "final_direction": list(_direction(_cells(grid, selected), cr, cc))}


def predict(grid, routing):
    """Independent integer-coordinate claim, verified by native Racket replay."""
    _settings({"routing": routing})
    trace = intermediate(grid)
    if routing == "direct":
        return _paint(grid, trace["key_color"], trace["first_direction"])
    return _paint(grid, trace["relay_color"], trace["final_direction"])


def _plurality(points, cr, cc):
    counts = [sum((r - cr) * dr > 0 and (c - cc) * dc > 0
                  for r, c in points) for dr, dc in DIRS]
    return DIRS[max(range(4), key=lambda i: counts[i])]


def rival_predictions(grid, routing):
    """Finite meaningful shortcuts; mirrors of rival_programs, for construction."""
    trace = intermediate(grid)
    cr, cc = trace["anchor"]
    key, selected = trace["key_color"], trace["relay_color"]
    first, final = tuple(trace["first_direction"]), tuple(trace["final_direction"])
    counts = Counter(v for row in grid for v in row if v != 7)
    colors = sorted(counts, key=lambda v: (-counts[v], v)) or [key]
    populated_ray = max(DIRS, key=lambda d: len(_hits(grid, key, d)))
    if routing == "direct":
        nearest = sorted((p for p in _cells(grid, key) if p != (cr, cc)),
                         key=lambda p: abs(p[0] - cr) + abs(p[1] - cc))
        result = {
            "most_frequent": _paint(grid, colors[0], _direction(_cells(grid, colors[0]), cr, cc)),
            "least_frequent": _paint(grid, colors[-1], _direction(_cells(grid, colors[-1]), cr, cc)),
            "nearest_key": _paint(grid, key, _direction(nearest[:1] or [(cr, cc)], cr, cc)),
            "plurality_quadrant": _paint(grid, key, _plurality(_cells(grid, key), cr, cc)),
            "keep_key_cells": [[v if v == key else 7 for v in row] for row in grid],
            "full_diagonal": _paint(grid, key, first, full=True),
            "most_hits_ray": _paint(grid, key, populated_ray),
        }
        result.update({f"fixed_direction_{i}": _paint(grid, key, d) for i, d in enumerate(DIRS)})
        return result
    other = [v for v in colors if v != key] or [key]
    hits = _hits(grid, key, first)
    last = grid[hits[-1][0]][hits[-1][1]] if hits else key
    near = sorted([(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
                   if v not in (7, key)], key=lambda p: abs(p[0] - cr) + abs(p[1] - cc))
    global_color = grid[near[0][0]][near[0][1]] if near else key
    offset_colors = sorted(v for v in counts if v != key and counts[v] == counts[key]-4)
    offset_color = offset_colors[0] if offset_colors else key
    populated_hits = _hits(grid, key, populated_ray)
    populated_color = grid[populated_hits[0][0]][populated_hits[0][1]] if populated_hits else key
    result = {
        "skip_relay": predict(grid, "direct"),
        "skip_second_centroid": _paint(grid, selected, first),
        "last_hit": _paint(grid, last, _direction(_cells(grid, last), cr, cc)),
        "nearest_global": _paint(grid, global_color, _direction(_cells(grid, global_color), cr, cc)),
        "most_frequent_other": _paint(grid, other[0], _direction(_cells(grid, other[0]), cr, cc)),
        "least_frequent_other": _paint(grid, other[-1], _direction(_cells(grid, other[-1]), cr, cc)),
        "plurality_quadrant": _paint(grid, selected, _plurality(_cells(grid, selected), cr, cc)),
        "keep_key_color": _paint(grid, key, final),
        "count_minus_four": _paint(grid, offset_color, _direction(_cells(grid, offset_color), cr, cc)),
        "most_hits_ray": _paint(grid, populated_color, _direction(_cells(grid, populated_color), cr, cc)),
    }
    qi = DIRS.index(first)
    result.update({f"fixed_turn_{i}": _paint(grid, selected, DIRS[(qi + i) % 4]) for i in range(4)})
    result.update({f"fixed_direction_{i}": _paint(grid, selected, d) for i, d in enumerate(DIRS)})
    for i, direction in enumerate(DIRS):
        candidates = _hits(grid, key, direction)
        color = grid[candidates[0][0]][candidates[0][1]] if candidates else key
        result[f"fixed_first_ray_{i}"] = _paint(grid, color, _direction(_cells(grid, color), cr, cc))
    return result


def _rule(routing, rival=None):
    """Materialize complete standalone Racket with bounded author-chosen edits."""
    key_expr = "(at g cr cc)"
    if routing == "direct" and rival in ("most_frequent", "least_frequent"):
        key_expr = f"({'first' if rival == 'most_frequent' else 'last'} ranked)"
    first_dr = "(if (< (for/sum ((p cells)) (first p)) (* (length cells) cr)) -1 1)"
    first_dc = "(if (< (for/sum ((p cells)) (second p)) (* (length cells) cc)) -1 1)"
    extra = ""
    if rival == "most_hits_ray":
        extra = '''(ray-count (lambda (d)
          (for/sum ((k (range 1 (max h w))))
            (let ((r (+ cr (* k (first d)))) (c (+ cc (* k (second d)))))
              (if (and (<= 0 r) (< r h) (<= 0 c) (< c w)
                       (not (= (at g r c) 7)) (not (= (at g r c) kc))) 1 0)))))
         (max-ray (first (sort '((-1 -1) (-1 1) (1 1) (1 -1))
                               (lambda (a b) (> (ray-count a) (ray-count b))))))'''
        first_dr, first_dc = "(first max-ray)", "(second max-ray)"
    if rival and rival.startswith("fixed_first_ray_"):
        dr, dc = DIRS[int(rival.rsplit('_', 1)[1])]
        first_dr, first_dc = str(dr), str(dc)
    picked = "kc" if routing == "direct" or rival == "skip_relay" else "(if (empty? hits) kc (at g (first (first hits)) (second (first hits))))"
    if rival == "last_hit":
        picked = "(if (empty? hits) kc (at g (first (last hits)) (second (last hits))))"
    if rival == "nearest_global":
        picked = "(if (empty? near) kc (at g (first (first near)) (second (first near))))"
    if rival in ("most_frequent_other", "least_frequent_other"):
        picked = f"(if (empty? other) kc ({'first' if rival.startswith('most') else 'last'} other))"
    if rival == "count_minus_four":
        picked = "(let ((eligible (filter (lambda (v) (and (not (= v kc)) (= (length (find-color g v)) (- (length cells) 4)))) palette))) (if (empty? eligible) kc (first eligible)))"
    out_dr = "(if (< (for/sum ((p target)) (first p)) (* (length target) cr)) -1 1)"
    out_dc = "(if (< (for/sum ((p target)) (second p)) (* (length target) cc)) -1 1)"
    if rival == "nearest_key":
        out_dr = "(if (and (not (empty? key-near)) (< (first (first key-near)) cr)) -1 1)"
        out_dc = "(if (and (not (empty? key-near)) (< (second (first key-near)) cc)) -1 1)"
    if rival == "plurality_quadrant":
        out_dr, out_dc = "(first majority)", "(second majority)"
    if rival == "skip_second_centroid":
        out_dr, out_dc = "dr", "dc"
    if routing == "direct" and rival == "most_hits_ray":
        out_dr, out_dc = "dr", "dc"
    if rival and rival.startswith("fixed_direction_"):
        d = DIRS[int(rival.rsplit('_', 1)[1])]
        out_dr, out_dc = str(d[0]), str(d[1])
    if rival and rival.startswith("fixed_turn_"):
        turn = int(rival.rsplit('_', 1)[1])
        out_dr, out_dc = (("dr", "dc"), ("dc", "(- dr)"),
                          ("(- dr)", "(- dc)"), ("(- dc)", "dr"))[turn]
    output_color = "kc" if rival == "keep_key_color" else "chosen"
    condition = "(and (= (* (- r cr) bc) (* (- c cc) br)) (>= (* (- r cr) br) 0))"
    if rival == "full_diagonal":
        condition = "(= (* (- r cr) bc) (* (- c cc) br))"
    if rival == "keep_key_cells":
        condition = "(= v kc)"
    return f'''(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g)) (cr (/ h 2)) (cc (/ w 2))
         (palette (filter (lambda (v) (and (not (= v 7)) (> (length (find-color g v)) 0))) (range 0 10)))
         (ranked (if (empty? palette) (list (at g cr cc))
           (sort palette (lambda (a b)
             (let ((na (length (find-color g a))) (nb (length (find-color g b))))
               (or (> na nb) (and (= na nb) (< a b))))))))
         (kc {key_expr}) (cells (find-color g kc)) {extra}
         (dr {first_dr}) (dc {first_dc})
         (hits (for/list ((k (range 1 (max h w)))
                         #:when (and (<= 0 (+ cr (* k dr))) (< (+ cr (* k dr)) h)
                                     (<= 0 (+ cc (* k dc))) (< (+ cc (* k dc)) w)
                                     (not (= (at g (+ cr (* k dr)) (+ cc (* k dc))) 7))
                                     (not (= (at g (+ cr (* k dr)) (+ cc (* k dc))) kc))))
                 (list (+ cr (* k dr)) (+ cc (* k dc)))))
         (near (sort (for*/list ((r (range 0 h)) (c (range 0 w))
                                #:when (and (not (= (at g r c) 7)) (not (= (at g r c) kc)))) (list r c))
                     (lambda (a b) (< (+ (abs (- (first a) cr)) (abs (- (second a) cc)))
                                      (+ (abs (- (first b) cr)) (abs (- (second b) cc)))))))
         (other (filter (lambda (v) (not (= v kc))) ranked))
         (chosen {picked}) (target (find-color g chosen))
         (key-near (sort (filter (lambda (p) (not (and (= (first p) cr) (= (second p) cc)))) cells)
                         (lambda (a b) (< (+ (abs (- (first a) cr)) (abs (- (second a) cc)))
                                          (+ (abs (- (first b) cr)) (abs (- (second b) cc)))))))
         (directions '((-1 -1) (-1 1) (1 1) (1 -1)))
         (majority (first (sort directions (lambda (a b)
           (> (for/sum ((p target)) (if (and (> (* (- (first p) cr) (first a)) 0) (> (* (- (second p) cc) (second a)) 0)) 1 0))
              (for/sum ((p target)) (if (and (> (* (- (first p) cr) (first b)) 0) (> (* (- (second p) cc) (second b)) 0)) 1 0)))))))
         (br {out_dr}) (bc {out_dc}))
    (cellmap g (r c v) (if {condition} {output_color} 7)))))'''


def program(settings):
    routing = _settings(settings)
    if routing == "direct":
        return Path(__file__).with_name("canonical.rkt").read_text()
    return _rule("relay")


def rival_programs(routing):
    _settings({"routing": routing})
    # Obtain names from a tiny total input; no sampled labels enter source text.
    grid = [[7] * 9 for _ in range(9)]
    grid[4][4] = 1
    return {name: _rule(routing, name) for name in rival_predictions(grid, routing)}


def _sample_grid(seed, slot, n, first_quadrant, turn, *, mixed):
    rng = random.Random(f"{TASK_ID}:input:{seed}:{slot}")
    center = n // 2
    directions = DIRS[first_quadrant], DIRS[(first_quadrant + turn) % 4]
    for attempt in range(64):
        key, *other_colors = rng.sample([v for v in range(10) if v != 7], 4)
        g = [[7] * n for _ in range(n)]
        g[center][center] = key
        reserved = {(r, c) for r in range(n) for c in range(n)
                    if abs(r - center) == abs(c - center)}
        # Identical key neighbors on all rays prevent a one-pixel direction cue.
        for dr, dc in DIRS:
            g[center + dr][center + dc] = key
        # Every ray has two eligible hits. Color multiplicity and hit depth
        # vary independently of the key-centroid direction, preventing a ray
        # occupancy or unique-marker cue from replacing the first computation.
        first_colors = other_colors + [rng.choice(other_colors)]
        rng.shuffle(first_colors)
        for index, (rr, cc) in enumerate(DIRS):
            reach = min(center if rr < 0 else n-1-center,
                        center if cc < 0 else n-1-center)
            depth = rng.randint(2, min(4, reach-1))
            first_color = first_colors[index]
            last_color = rng.choice([v for v in other_colors if v != first_color])
            g[center + depth * rr][center + depth * cc] = first_color
            g[center + (depth+1) * rr][center + (depth+1) * cc] = last_color
        relay = first_colors[first_quadrant]
        far, noise = [v for v in other_colors if v != relay]
        ok = True
        for color, (dr, dc) in zip((key, relay), directions):
            free = [(r, c) for r in range(n) for c in range(n)
                    if (r, c) not in reserved and g[r][c] == 7]
            forward = [(r, c) for r, c in free if (r-center)*dr > 0 and (c-center)*dc > 0]
            if mixed:
                close = max(3, n // 5)
                remote = max(3, n // 3)
                near = [(r, c) for r, c in free if 0 < (center-r)*dr <= close and 0 < (center-c)*dc <= close]
                distant = [(r, c) for r, c in forward if (r-center)*dr >= remote and (c-center)*dc >= remote]
                upper = min(len(distant), len(near)-1, max(5, n*n//40))
                if upper < 4:
                    ok = False
                    break
                count = rng.randint(max(4, upper//2), upper)
                chosen = rng.sample(distant, count) + rng.sample(near, count+1)
            else:
                upper = min(len(forward), max(4, n*n//18))
                count = rng.randint(max(4, upper//2), upper)
                chosen = rng.sample(forward, count)
            for r, c in chosen:
                g[r][c] = color
            if _direction(_cells(g, color), center, center) != (dr, dc):
                ok = False
                break
        if not ok:
            continue
        # Broad full-canvas distractors: sometimes sparse one color, sometimes
        # balanced; neither the center nor the relay has a fixed frequency rank.
        free = [(r, c) for r in range(n) for c in range(n)
                if (r, c) not in reserved and g[r][c] == 7]
        rng.shuffle(free)
        budget = min(len(free), int(n*n*rng.uniform(.25, .40)))
        small = max(1, min(3, budget//4))
        split = (small if slot % 3 == 0 else budget-small if slot % 3 == 1 else budget//2)
        for index, (r, c) in enumerate(free[:budget]):
            g[r][c] = far if index < split else noise
        # Ensure boundary content without altering key/relay centroid selection.
        for r, c in ((0, 1), (1, n-1), (n-1, n-2), (n-2, 0)):
            if (r, c) not in reserved and g[r][c] == 7:
                g[r][c] = noise
        trace = intermediate(g)
        if trace["relay_color"] == relay and tuple(trace["final_direction"]) == directions[1]:
            return g
    raise RuntimeError(f"bounded input construction failed: seed={seed}, slot={slot}, n={n}")


def _inputs(seed):
    start = random.Random(f"{TASK_ID}:quadrant:{seed}").randrange(4)
    # Construct the minimal teaching pair from demonstrations alone. Queries
    # are not created until all declared shortcuts are rejected under BOTH
    # settings. This preserves matched inputs and independent query prefixes.
    for attempt in range(64):
        # Both examples must be eligible for replacement: if the first scene
        # aliases a fixed ray that is correct for the second scene by design,
        # changing only the second can never eliminate that shortcut.
        first = _sample_grid(seed, 10000*attempt, DEMO_SIZES[0], start, 1, mixed=True)
        second = _sample_grid(seed, 1+100*attempt, DEMO_SIZES[1], (start+1) % 4, 3, mixed=True)
        train = [first, second]
        offsets = []
        for grid in train:
            trace = intermediate(grid)
            counts = Counter(v for row in grid for v in row)
            offsets.append(counts[trace['relay_color']] - counts[trace['key_color']])
        if offsets[0] == offsets[1]:
            continue
        taught = True
        for routing in ROUTINGS:
            gold = [predict(g, routing) for g in train]
            rivals = [rival_predictions(g, routing) for g in train]
            if any(all(row[name] == answer for row, answer in zip(rivals, gold)) for name in rivals[0]):
                taught = False
                break
        if taught:
            break
    else:
        raise RuntimeError(f"bounded demonstration selection failed: seed={seed}")
    train.extend(_sample_grid(seed, i, n, (start + (0, 1, 2, 3, 2, 0)[i]) % 4,
                              (1, 3, 2, 1, 0, 3)[i], mixed=False)
                 for i, n in enumerate(DEMO_SIZES) if i >= 2)
    test = [_sample_grid(seed, 6+i, n, (start+i) % 4, (2, 0, 3, 1)[i], mixed=False)
            for i, n in enumerate(QUERY_SIZES)]
    return train, test


def generate(seed, settings, demos=3, queries=4):
    routing = _settings(settings)
    _count(seed, 0, 2**63-1, "seed")
    _count(demos, 2, 6, "demos")
    _count(queries, 1, 4, "queries")
    train, test = _inputs(seed)
    return {"train": [{"input": g, "output": predict(g, routing)} for g in train[:demos]],
            "test": [{"input": g, "output": predict(g, routing)} for g in test[:queries]],
            "program_solution": program(settings)}
