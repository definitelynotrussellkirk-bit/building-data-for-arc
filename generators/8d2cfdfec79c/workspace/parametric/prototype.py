"""Rectangle outlines, optionally followed by an occlusion-dependent fill.

The Python mirror supplies claims for native independent protected-Racket
verification. A raw generate() call is not label verification or acceptance.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import random


MODES = ("outline", "fill_most_visible")
CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")

FILL_PROGRAM = """(rule!
  (let* ((colors
           (remove-duplicates
             (filter (lambda (v) (not (= v 0)))
               (map (lambda (p) (at g (first p) (second p)))
                    (grid-positions g))))))
    (define (box color) (bbox-of-cells (find-color g color)))
    (define (border bb)
      (for*/list ((r (in-range (first bb) (+ (third bb) 1)))
                  (c (in-range (second bb) (+ (fourth bb) 1)))
                  #:when (or (= r (first bb)) (= r (third bb))
                             (= c (second bb)) (= c (fourth bb))))
        (list r c)))
    (define outlines
      (for/fold ((out (empty-grid (rows g) (cols g) 0)))
                ((color (in-list colors)))
        (paint-cells out (border (box color)) color)))
    (define (score color) (length (find-color outlines color)))
    (define winner
      (for/fold ((best (first colors))) ((color (in-list (rest colors))))
        (if (> (score color) (score best)) color best)))
    (define bb (box winner))
    (paint-cells outlines
      (for*/list ((r (in-range (+ (first bb) 1) (third bb)))
                  (c (in-range (+ (second bb) 1) (fourth bb)))
                  #:when (= (at outlines r c) 0))
        (list r c))
      winner)))"""


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str or settings["mode"] not in MODES):
        raise ValueError(f"settings must contain exactly mode in {MODES}")
    return settings["mode"]


def program(settings):
    return CANONICAL_PROGRAM if _mode(settings) == "outline" else FILL_PROGRAM


def _groups(grid):
    groups = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                groups.setdefault(color, []).append((r, c))
    return groups


def _box(cells):
    return (min(p[0] for p in cells), min(p[1] for p in cells),
            max(p[0] for p in cells), max(p[1] for p in cells))


def _border(box):
    r0, c0, r1, c1 = box
    return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)]


def intermediate(grid):
    """Private authoring metadata for the outline-to-fill dependency."""
    groups = _groups(grid)
    boxes = {color: _box(cells) for color, cells in groups.items()}
    outlines = [[0] * len(grid[0]) for _ in grid]
    for color, box in boxes.items():
        for r, c in _border(box):
            outlines[r][c] = color
    counts = Counter(color for row in outlines for color in row if color)
    visible = {color: counts[color] for color in groups}
    winner = max(groups, key=lambda color: visible[color])
    raw = max(groups, key=lambda color: len(_border(boxes[color])))
    return {"reading_order": list(groups), "boxes": boxes, "outlines": outlines,
            "visible_counts": visible, "winner": winner, "raw_perimeter_winner": raw}


def predict(grid, mode="outline"):
    """Diagnostic mirror, never a substitute for Racket verification."""
    _mode({"mode": mode})
    state = intermediate(grid)
    out = state["outlines"]
    if mode == "fill_most_visible":
        winner = state["winner"]
        r0, c0, r1, c1 = state["boxes"][winner]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if out[r][c] == 0:
                    out[r][c] = winner
    return out


def validate_input(grid):
    if (type(grid) is not list or not 8 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 10 <= len(grid[0]) <= 30):
        raise ValueError("parametric canvas must be 8..30 rows by 10..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("rectangular exact-integer ARC grid required")
    groups = _groups(grid)
    if not 2 <= len(groups) <= 6:
        raise ValueError("expected 2..6 rectangle colors")
    for cells in groups.values():
        if (len(cells) != 2 or cells[0][0] == cells[1][0]
                or cells[0][1] == cells[1][1]):
            raise ValueError("each color must mark two diagonal corners")


def _scene(h, w, boxes, diagonals, colors):
    grid = [[0] * w for _ in range(h)]
    for (r0, c0, r1, c1), opposite, color in zip(boxes, diagonals, colors):
        pair = ((r0, c1), (r1, c0)) if opposite else ((r0, c0), (r1, c1))
        for r, c in pair:
            if grid[r][c]:
                raise ValueError("rectangle clue collision")
            grid[r][c] = color
    validate_input(grid)
    return grid


def inversion_scene(rng, h, w, *, distractors=0):
    """Raw largest perimeter loses most of its horizontal borders to B."""
    boxes = [(0, 0, h - 1, w - 1), (0, 1, h - 1, w - 3)]
    for k in range(distractors):
        inset = k + 2
        boxes.append((inset, inset + 1, h - 1 - inset, w - 4 - inset))
    return _scene(h, w, boxes, [False, True] + [False] * distractors,
                  rng.sample(range(1, 10), len(boxes)))


def teaching_inversion(rng, h, w):
    """B wins after occlusion; smaller fillable C crosses B and must survive."""
    boxes = [(0, 0, h - 1, w - 1), (0, 1, h - 1, w - 3),
             (2, 3, h - 3, w - 2)]
    low, middle, high = sorted(rng.sample(range(1, 10), 3))
    other = [low, high]
    rng.shuffle(other)
    return _scene(h, w, boxes, [False, True, False], [other[0], middle, other[1]])


def tie_scene(rng, h, w):
    """Thin A ties fillable B at 12 pixels; A wins and B overwrites an A clue."""
    top, left = rng.randrange(h - 5), rng.randrange(w - 8)
    base = [(0, 0, 1, 6), (1, 5, 4, 8), (4, 0, 5, 1)]
    boxes = [(r0 + top, c0 + left, r1 + top, c1 + left)
             for r0, c0, r1, c1 in base]
    low, middle, high = sorted(rng.sample(range(1, 10), 3))
    other = [low, high]
    rng.shuffle(other)
    grid = _scene(h, w, boxes, [False, False, False], [other[0], middle, other[1]])
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    return grid


def varied_scene(rng, h, w, kind):
    if kind == "inversion":
        return inversion_scene(rng, h, w, distractors=2 if min(h, w) >= 16 else 0)
    if kind == "tie":
        return tie_scene(rng, h, w)
    if kind == "nested":
        number = rng.randint(3, min(6, (min(h, w) - 2) // 2))
        boxes = [(k, k, h - 1 - k, w - 1 - k) for k in range(number - 1)]
        top = (h - 2) // 2
        boxes.append((top, number - 1, top + 1, w - number))
        diagonals = [bool(rng.randrange(2)) for _ in boxes]
    elif kind == "disjoint":
        rm, cm = h // 2, w // 2
        tiles = [(0, 0, rm - 1, cm - 1), (0, cm, rm - 1, w - 1),
                 (rm, 0, h - 1, cm - 1), (rm, cm, h - 1, w - 1)]
        rng.shuffle(tiles)
        boxes = []
        for r0, c0, r1, c1 in tiles[:rng.randint(2, 4)]:
            rr = sorted(rng.sample(range(r0, r1 + 1), 2))
            cc = sorted(rng.sample(range(c0, c1 + 1), 2))
            boxes.append((rr[0], cc[0], rr[1], cc[1]))
        diagonals = [bool(rng.randrange(2)) for _ in boxes]
    elif kind == "crossing":
        number = rng.randint(3, min(6, (min(h, w) - 2) // 2))
        boxes = [(0, 1, h - 1, w - 2), (0, 0, h - 2, w - 1)]
        for k in range(2, number - 1):
            boxes.append((k, k, h - 1 - k, w - 1 - k))
        top = (h - 2) // 2
        boxes.append((top, number - 1, top + 1, w - number))
        diagonals = [False, True] + [False] * (len(boxes) - 2)
    else:
        raise ValueError("unknown geometry family")
    return _scene(h, w, boxes, diagonals, rng.sample(range(1, 10), len(boxes)))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")


def generate(seed, settings, demos=3, queries=4):
    mode = _mode(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    # Streams do not depend on hidden mode, requested counts, or global RNG.
    demo_rng = random.Random(f"8d2cfdfec79c/demo/v1/{seed}")
    query_rng = random.Random(f"8d2cfdfec79c/query/v1/{seed}")
    inputs = [teaching_inversion(demo_rng, demo_rng.randint(8, 13), demo_rng.randint(10, 15)),
              tie_scene(demo_rng, demo_rng.randint(8, 13), demo_rng.randint(10, 15))]
    # Materialize the bounded demo prefix independently of requested demo count.
    kinds = ("nested", "disjoint", "crossing", "inversion")
    for kind in kinds:
        inputs.append(varied_scene(demo_rng, demo_rng.randint(8, 15),
                                   demo_rng.randint(10, 17), kind))
    seen = {repr(grid) for grid in inputs}
    if len(seen) != len(inputs):
        raise RuntimeError("constructive demonstration inputs unexpectedly collided")
    query_inputs = []
    for index in range(queries):
        for attempt in range(32):
            if index == 0:
                h, w = query_rng.randint(8, 13), query_rng.randint(10, 14)
                kind = query_rng.choice(("crossing", "nested", "disjoint"))
            elif index == 1:
                h, w = query_rng.randint(16, 22), query_rng.randint(17, 24)
                kind = query_rng.choice(("crossing", "nested", "disjoint"))
            elif index == 2:
                h, w, kind = 30, 30, "inversion"
            else:
                h, w = query_rng.randint(21, 30), query_rng.randint(21, 30)
                kind = query_rng.choice(("crossing", "nested", "disjoint", "inversion"))
            grid = varied_scene(query_rng, h, w, kind)
            key = repr(grid)
            if key not in seen:
                seen.add(key)
                query_inputs.append(grid)
                break
        else:
            raise RuntimeError("distinct query budget exhausted after 32 attempts")
    def pair(grid):
        return {"input": grid, "output": predict(grid, mode)}
    return {"train": [pair(grid) for grid in inputs[:demos]],
            "test": [pair(grid) for grid in query_inputs],
            "program_solution": program(settings)}
