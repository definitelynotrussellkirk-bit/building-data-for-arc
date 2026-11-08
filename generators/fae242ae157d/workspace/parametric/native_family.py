"""Area ranking and area-selected spatial ranking, with matched teaching inputs.

Labels here are deterministic claims. Native qualification and audit.py execute
the complete Racket programs independently. No sibling checkout is imported.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
POLICIES = ("area", "nearest_largest", "farthest_largest")
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"ranking_policy"}:
        raise ValueError("settings must contain only ranking_policy")
    value = settings["ranking_policy"]
    if type(value) is not str or value not in POLICIES:
        raise ValueError("unknown ranking_policy")
    return value


def _components(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or any(type(row) is not list for row in grid)
            or not 1 <= len(grid[0]) <= 30
            or any(len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
        raise ValueError("grid must be a rectangular list of literal ARC integers, at most 30x30")
    height, width = len(grid), len(grid[0])
    seen, objects = set(), []
    for row in range(height):
        for col in range(width):
            if not grid[row][col] or (row, col) in seen:
                continue
            cells, pending = set(), deque([(row, col)])
            seen.add((row, col))
            while pending:
                pos = pending.popleft()
                cells.add(pos)
                for dr, dc in DIRECTIONS:
                    nxt = (pos[0] + dr, pos[1] + dc)
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and grid[nxt[0]][nxt[1]] and nxt not in seen):
                        seen.add(nxt)
                        pending.append(nxt)
            if len({grid[r][c] for r, c in cells}) != 1:
                raise ValueError("objects must be separated and monochrome")
            objects.append(tuple(sorted(cells)))
    if len(objects) != 3 or any(len(obj) < 3 for obj in objects):
        raise ValueError("exactly three separated objects of at least three cells are required")
    if len({len(obj) for obj in objects}) != 3:
        raise ValueError("object occupied areas must be distinct")
    anchor = max(objects, key=len)
    if len({_distance(obj, anchor) for obj in objects if obj != anchor}) != 2:
        raise ValueError("the two minimum Manhattan distances to the largest object must differ")
    return objects


def _bbox(obj):
    return min(r for r, _ in obj), min(c for _, c in obj), max(r for r, _ in obj), max(c for _, c in obj)


def _perimeter(obj):
    occupied = set(obj)
    return sum((r + dr, c + dc) not in occupied for r, c in obj for dr, dc in DIRECTIONS)


def _distance(obj, anchor, metric="manhattan"):
    if metric == "bbox":
        ar, ac, az, aw = _bbox(obj)
        br, bc, bz, bw = _bbox(anchor)
        return max(0, ar - bz, br - az) + max(0, ac - bw, bc - aw)
    if metric == "top_left":
        ar, ac, _, _ = _bbox(obj)
        br, bc, _, _ = _bbox(anchor)
        return abs(ar - br) + abs(ac - bc)
    if metric == "centroid":
        return sum(abs(Fraction(sum(p[k] for p in obj), len(obj))
                       - Fraction(sum(p[k] for p in anchor), len(anchor))) for k in (0, 1))
    if metric == "bbox_center":
        a, b = _bbox(obj), _bbox(anchor)
        return abs(a[0] + a[2] - b[0] - b[2]) + abs(a[1] + a[3] - b[1] - b[3])
    if metric == "euclidean_squared":
        return min((r - ar) ** 2 + (c - ac) ** 2 for r, c in obj for ar, ac in anchor)
    if metric == "chebyshev":
        return min(max(abs(r - ar), abs(c - ac)) for r, c in obj for ar, ac in anchor)
    return min(abs(r - ar) + abs(c - ac) for r, c in obj for ar, ac in anchor)


def apply_claim(grid, settings):
    """Return a fresh claimed label on the common, explicitly bounded grammar."""
    policy = _settings(settings)
    objects = _components(grid)
    ranked = sorted(objects, key=len)
    if policy != "area":
        anchor = ranked[-1]
        ranked = sorted(ranked[:-1], key=lambda obj: _distance(obj, anchor),
                        reverse=policy == "farthest_largest") + [anchor]
    output = [[0] * len(grid[0]) for _ in grid]
    for color, obj in enumerate(ranked, 2):
        for row, col in obj:
            output[row][col] = color
    return output


# Scores are numerator/denominator pairs: the bridge's / is integer division.
# Cross-products keep centroid comparisons exact, including adversarial rivals.
_RACKET_HELPERS = r"""
    (define objs (__OBJECTS__ g 0))
    (define (area< a b) (< (obj-size a) (obj-size b)))
    (define by-area (sort objs area<))
    (define (box-area o) (* (obj-h o) (obj-w o)))
    (define (perimeter o)
      (apply + (map (lambda (p)
        (length (filter (lambda (d)
          (not (member (list (+ (first p) (first d)) (+ (second p) (second d))) (obj-cells o))))
          (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1))))) (obj-cells o))))
    (define (score o metric)
      (cond ((equal? metric "bbox") (box-area o))
            ((equal? metric "perimeter") (perimeter o))
            ((equal? metric "color") (obj-color o))
            ((equal? metric "color_mass") (* (obj-color o) (obj-size o)))
            (else (obj-size o))))
    (define (metric-order objects metric)
      (sort objects (lambda (a b)
        (let ((x (score a metric)) (y (score b metric)))
          (if (= x y) (area< a b) (< x y))))))
    (define (distance a b metric)
      (cond
        ((equal? metric "centroid")
          (list (+ (abs (- (* (apply + (map first (obj-cells a))) (obj-size b))
                           (* (apply + (map first (obj-cells b))) (obj-size a))))
                   (abs (- (* (apply + (map second (obj-cells a))) (obj-size b))
                           (* (apply + (map second (obj-cells b))) (obj-size a)))))
                (* (obj-size a) (obj-size b))))
        ((equal? metric "bbox")
          (list (+ (max 0 (- (obj-r1 a) (obj-r2 b)) (- (obj-r1 b) (obj-r2 a)))
                   (max 0 (- (obj-c1 a) (obj-c2 b)) (- (obj-c1 b) (obj-c2 a)))) 1))
        ((equal? metric "top_left")
          (list (+ (abs (- (obj-r1 a) (obj-r1 b))) (abs (- (obj-c1 a) (obj-c1 b)))) 1))
        ((equal? metric "bbox_center")
          (list (+ (abs (- (+ (obj-r1 a) (obj-r2 a)) (+ (obj-r1 b) (obj-r2 b))))
                   (abs (- (+ (obj-c1 a) (obj-c2 a)) (+ (obj-c1 b) (obj-c2 b))))) 1))
        (else
          (list (apply min (for*/list ((x (in-list (obj-cells a))) (y (in-list (obj-cells b))))
            (let ((dr (abs (- (first x) (first y)))) (dc (abs (- (second x) (second y)))))
              (cond ((equal? metric "euclidean_squared") (+ (* dr dr) (* dc dc)))
                    ((equal? metric "chebyshev") (max dr dc))
                    (else (+ dr dc)))))) 1))))
    (define (paint-ranked ranked)
      (let loop ((remaining ranked) (rank 2) (out (empty-grid (rows g) (cols g) 0)))
        (if (empty? remaining) out
          (loop (rest remaining) (+ rank 1) (paint-cells out (obj-cells (first remaining)) rank)))))
"""


def _rule(policy, *, anchor="area", metric="manhattan", rank_metric=None, eight=False):
    helpers = _RACKET_HELPERS.replace("__OBJECTS__", "objects-8" if eight else "objects")
    if rank_metric is not None:
        if rank_metric == "scan":
            order = "objs"
        elif rank_metric == "reverse_scan":
            order = "(reverse objs)"
        elif rank_metric == "descending_area":
            order = "(reverse by-area)"
        else:
            order = f'(metric-order objs "{rank_metric}")'
        body = f"(paint-ranked {order})"
    elif policy == "area":
        body = "(paint-ranked by-area)"
    else:
        choose = {"area": "(last by-area)", "smallest": "(first by-area)",
                  "middle": "(list-ref by-area (quotient (length by-area) 2))",
                  "first_scan": "(first objs)", "last_scan": "(last objs)"}.get(anchor)
        if choose is None:
            choose = f'(last (metric-order objs "{anchor}"))'
        compare = ">" if policy == "farthest_largest" else "<"
        body = f"""
    (define anchor {choose})
    (define candidates (filter (lambda (o) (not (equal? o anchor))) objs))
    (define measured (map (lambda (o) (list o (distance o anchor \"{metric}\"))) candidates))
    (define ordered (sort measured (lambda (a b)
      (let* ((x (second a)) (y (second b))
             (left (* (first x) (second y))) (right (* (first y) (second x))))
        (if (= left right) (area< (first a) (first b)) ({compare} left right))))))
    (paint-cells (paint-ranked (map first ordered)) (obj-cells anchor) 4)
"""
    return "(rule! (lambda (g) (let ((dummy 0))\n" + helpers + body + ")))"


def program(settings):
    policy = _settings(settings)
    return CANONICAL if policy == "area" else _rule(policy)


def rivals(settings):
    """Extra finite rivals; the audit separately screens the declared settings."""
    policy = _settings(settings)
    candidates = {}
    candidates.update({"rank_" + name: _rule("area", rank_metric=name) for name in
                       ("descending_area", "scan", "reverse_scan", "bbox", "perimeter", "color")})
    candidates["identity"] = "(rule! (lambda (g) g))"
    candidates["absolute_456"] = """(rule! (let loop ((remaining (objects g 0)) (out (empty-grid (rows g) (cols g) 0)))
      (if (empty? remaining) out (let* ((o (first remaining)) (s (obj-size o))
      (color (cond ((= s 4) 2) ((= s 5) 3) ((= s 6) 4) (else 1))))
      (loop (rest remaining) (paint-cells out (obj-cells o) color))))))"""
    candidates["eight_connected_objects"] = _rule(policy, eight=True)
    if policy != "area":
        candidates.update({"anchor_" + name: _rule(policy, anchor=name) for name in
                           ("smallest", "middle", "first_scan", "last_scan", "bbox",
                            "perimeter", "color", "color_mass")})
        candidates.update({"distance_" + name: _rule(policy, metric=name) for name in
                           ("bbox", "top_left", "centroid", "bbox_center", "euclidean_squared", "chebyshev")})
    return candidates


def _rng(seed, split, slot, retry):
    raw = json.dumps(["fae242ae157d-native-v1", seed, split, slot, retry], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _cross(row, col):
    return {(row, col), (row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)}


def _rect(top, left, height, width):
    return {(r, c) for r in range(top, top + height) for c in range(left, left + width)}


def _ring_growth(top, left, height, width, count, rng):
    """Connected, boundary-spanning objects with variable internal voids."""
    cells = {(r, c) for r in range(height) for c in range(width)
             if r in (0, height - 1) or c in (0, width - 1)}
    if not len(cells) <= count <= height * width:
        raise ValueError("invalid ring-growth target")
    while len(cells) < count:
        frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in DIRECTIONS
                           if 0 <= r + dr < height and 0 <= c + dc < width
                           and (r + dr, c + dc) not in cells})
        cells.add(rng.choice(frontier))
    return {(r + top, c + left) for r, c in cells}


def _transform(grid, symmetry):
    grid = deepcopy(grid)
    if symmetry >= 4:
        grid = [row[::-1] for row in grid]
    for _ in range(symmetry % 4):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def _scene(seed, split, slot, retry):
    rng = _rng(seed, split, slot, retry)
    profile = slot if split == "train" and slot < 3 else 3 + (slot % 4)
    if profile in (0, 2):
        end_r, end_c = rng.randint(16, 18), rng.randint(16, 18)
        anchor = {(1, c) for c in range(1, end_c + 1)} | {(r, 1) for r in range(2, end_r + 1)}
        if profile == 0:
            small, middle = _cross(3, end_c + 1), _rect(10, 6, 3, 3)
        else:
            small, middle = _cross(11, 8), _rect(3, 13, 3, 3)
        dims = (21 + rng.randrange(3), 21 + rng.randrange(3))
        colors = (rng.choice((6, 7, 8)),) * 3 if profile == 0 else (9, 8, 1)
    elif profile == 1:
        small = {(5, c) for c in range(12, 18)}
        middle = {(6, c) for c in range(1, 10)} | {(r, 1) for r in range(7, 13)}
        anchor = _rect(11, 11, 4, 5)
        dims, colors = (20 + rng.randrange(3), 20 + rng.randrange(3)), (4, 2, 3)
    elif profile == 3:
        small, middle, anchor = _rect(0, 8, 2, 2), _cross(3, 2), _rect(6, 0, 2, 3)
        dims, colors = (9, 11), tuple(rng.sample(range(1, 10), 3))
    elif profile == 4:
        small = _ring_growth(0, 0, 5, 7, rng.randint(23, 28), rng)
        middle = _ring_growth(0, 14, 7, 10, rng.randint(38, 48), rng)
        anchor = _ring_growth(10, 2, 8, 20, rng.randint(80, 110), rng)
        dims, colors = (18, 24), tuple(rng.sample(range(1, 10), 3))
    elif profile == 5:
        small = _ring_growth(0, 0, 8, 7, rng.randint(30, 36), rng)
        middle = _ring_growth(1, 14, 9, 10, rng.randint(45, 55), rng)
        anchor = _ring_growth(14, 0, 10, 24, rng.randint(115, 155), rng)
        dims, colors = (24, 24), (rng.choice((1, 5, 6, 7, 8, 9)),) * 3
    else:
        small = _ring_growth(0, 0, 13, 13, rng.randint(75, 95), rng)
        middle = _ring_growth(0, 16, 11, 14, rng.randint(105, 125), rng)
        anchor = _ring_growth(17, 0, 13, 30, rng.randint(190, 230), rng)
        dims, colors = (30, 30), tuple(rng.sample(range(1, 10), 3))
    grid = [[0] * dims[1] for _ in range(dims[0])]
    for cells, color in zip((small, middle, anchor), colors):
        for r, c in cells:
            grid[r][c] = color
    start = rng.randrange(8)
    if profile in (0, 1):
        # Preserve the teaching property under geometry augmentation. Merely
        # rotating a useful example can erase a top-left or scan-order conflict.
        # This examines at most eight symmetries of one constructed scene; it
        # neither rejects whole lessons nor consumes query labels.
        for offset in range(8):
            candidate = _transform(grid, (start + offset) % 8)
            objects = _components(candidate)
            small, middle, anchor = sorted(objects, key=len)
            if profile == 0 and not (_distance(small, anchor, "top_left")
                                     > _distance(middle, anchor, "top_left")):
                continue
            if profile == 1 and objects.index(anchor) != 1:
                continue
            return candidate
        raise AssertionError("constructed teaching symmetry has no lawful witness")
    return _transform(grid, start)


def generate(seed, settings, demos, queries):
    policy = _settings(settings)
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    if type(demos) is not int or not 3 <= demos <= 6:
        raise ValueError("demos must be a literal integer in 3..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be a literal integer in 1..4")
    banks, seen = {}, set()
    # Always construct the complete banks before slicing. Neither counts nor
    # settings can perturb the input stream, and each call owns all its arrays.
    for split, count in (("train", 6), ("test", 4)):
        pairs = []
        for slot in range(count):
            for retry in range(64):
                grid = _scene(seed, split, slot, retry)
                key = json.dumps(grid, separators=(",", ":"))
                if key not in seen:
                    output = apply_claim(grid, {"ranking_policy": policy})
                    seen.add(key)
                    pairs.append({"input": grid, "output": output})
                    break
            else:
                raise RuntimeError("bounded distinct-input construction exhausted 64 attempts")
        banks[split] = pairs
    return {"train": banks["train"][:demos], "test": banks["test"][:queries],
            "program_solution": program(settings)}


def describe(grid, settings):
    policy = _settings(settings)
    objects = _components(grid)
    anchor = max(objects, key=len)
    occupied = {p for obj in objects for p in obj}
    return {"ranking_policy": policy, "input_shape": [len(grid), len(grid[0])],
            "output_shape": [len(grid), len(grid[0])],
            "areas_by_scan": [len(obj) for obj in objects],
            "anchor_scan_index": objects.index(anchor),
            "anchor_cells": [list(p) for p in anchor],
            "distances_by_scan": [_distance(obj, anchor) for obj in objects],
            "occupied_cells": len(occupied),
            "boundary_contacts": {"top": any(r == 0 for r, _ in occupied),
                                  "bottom": any(r == len(grid) - 1 for r, _ in occupied),
                                  "left": any(c == 0 for _, c in occupied),
                                  "right": any(c == len(grid[0]) - 1 for _, c in occupied)}}


def public_turn(episode, index):
    if type(index) is not int or not 0 <= index < len(episode["test"]):
        raise ValueError("query index must select one existing query")
    return {"train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])}
                      for p in episode["train"]],
            "test": [{"input": deepcopy(episode["test"][index]["input"])}]}
