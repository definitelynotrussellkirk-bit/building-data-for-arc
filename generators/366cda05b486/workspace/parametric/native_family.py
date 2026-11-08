"""Native contact-cluster extraction and farthest object-hop layer.

Claim labels are deterministic Python; protected native qualification and the
separate independent audit execute the exact Racket programs.
"""
from collections import deque
from pathlib import Path
import random

TASK_ID = "366cda05b486"
DEFAULT = {"scope": "cluster"}
SETTINGS = ({"scope": "cluster"}, {"scope": "farthest"})
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
CANONICAL_PREFIX = "(rule! (let ((dummy 0))"
CANONICAL_ACTION = "(extract-union g objs (sort cl <) 8)"
HOP_HELPER = """
 (define (hop-distances grid objs start)
   (let ((depths (make-hash)))
     (hash-set! depths start 0)
     (let walk ((queue (list start)))
       (if (empty? queue) depths
           (let* ((i (first queue))
                  (unseen (filter (lambda (j) (not (hash-has-key? depths j)))
                                  (neighbors grid objs i))))
             (for ([j (in-list unseen)])
               (hash-set! depths j (+ 1 (hash-ref depths i))))
             (walk (append (rest queue) unseen)))))))
"""
FARTHEST_ACTION = """(let* ((depths (hop-distances g objs seed))
                           (furthest (apply max (hash-values depths)))
                           (chosen (filter (lambda (i) (= (hash-ref depths i) furthest)) cl)))
                      (extract-union g objs (sort chosen <) 8))"""


def _setting(settings):
    if settings is None:
        return "cluster"
    if type(settings) is not dict or set(settings) != {"scope"}:
        raise ValueError("settings must name exactly scope")
    value = settings["scope"]
    if type(value) is not str or value not in ("cluster", "farthest"):
        raise ValueError("scope must be cluster or farthest")
    return value


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")


def analyze(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
            type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("native grid axes must be 1..30")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w or
           any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("native grid must be rectangular with exact integer colors 0..9")
    owner = {}
    objects = []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in owner:
                continue
            color, index, cells = grid[r][c], len(objects), set()
            queue = [(r, c)]
            owner[r, c] = index
            while queue:
                rr, cc = queue.pop()
                cells.add((rr, cc))
                for dr, dc in CARDINAL:
                    neighbor = rr + dr, cc + dc
                    nr, nc = neighbor
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and neighbor not in owner):
                        owner[neighbor] = index
                        queue.append(neighbor)
            objects.append({"color": color, "cells": frozenset(cells)})
    seeds = [i for i, obj in enumerate(objects) if obj["color"] == 1]
    if len(seeds) != 1:
        raise ValueError("exactly one monochromatic cardinal blue object is required")
    adjacency = [set() for _ in objects]
    for (r, c), index in owner.items():
        for dr, dc in CARDINAL:
            other = owner.get((r + dr, c + dc))
            if other is not None and other != index:
                adjacency[index].add(other)
    seed = seeds[0]
    distances = {seed: 0}
    queue = deque([seed])
    while queue:
        index = queue.popleft()
        for other in sorted(adjacency[index]):
            if other not in distances:
                distances[other] = distances[index] + 1
                queue.append(other)
    return objects, adjacency, seed, distances


def _crop(cells):
    r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
    c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
    return [[8 if (r, c) in cells else 0 for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)]


def transform(grid, settings=None):
    scope = _setting(settings)
    objects, adjacency, seed, distances = analyze(grid)
    depth = max(distances.values())
    selected = [index for index, value in distances.items()
                if scope == "cluster" or value == depth]
    return _crop(set().union(*(objects[index]["cells"] for index in selected)))


def program(settings=None):
    scope = _setting(settings)
    canonical = Path(__file__).with_name("canonical.rkt").read_text()
    if scope == "cluster":
        return canonical
    if canonical.count(CANONICAL_PREFIX) != 1 or canonical.count(CANONICAL_ACTION) != 1:
        raise ValueError("selected canonical source no longer has the reviewed action")
    return canonical.replace(CANONICAL_PREFIX, CANONICAL_PREFIX + HOP_HELPER, 1).replace(
        CANONICAL_ACTION, FARTHEST_ACTION, 1)


def _paint(grid, cells, color):
    for r, c in cells:
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])) or grid[r][c]:
            raise ValueError("construction has overlapping or out-of-bounds roles")
        grid[r][c] = color


def _core_a():
    grid = [[0] * 19 for _ in range(9)]
    roles = [
        (1, {(3, 3), (3, 4)}),
        (2, {(3, c) for c in range(5, 11)}),
        (8, {(4, 10), (5, 10)} | {(6, c) for c in range(6, 11)}),
        (3, {(6, 5)}), (4, {(6, 4)}), (5, {(5, 4)}),
        (2, {(5, 2), (5, 3), (4, 2)}),
    ]
    for color, cells in roles:
        _paint(grid, cells, color)
    for r in range(3):
        for c in range(11, 19):
            grid[r][c] = 6 + (r + c) % 2
    return grid


def _core_b():
    grid = [[0] * 16 for _ in range(14)]
    roles = [
        (1, {(r, c) for r in (4, 5) for c in (4, 5)}),
        (2, {(r, c) for r in (4, 5) for c in (6, 7)}),
        (4, {(r, c) for r in (6, 7) for c in (6, 7)}),
        (3, {(r, c) for r in (6, 7) for c in (4, 5)}),
        (9, {(2, 3), (2, 4), (3, 4)}),
        (5, {(4, 8), (4, 9)}),
        (6, {(4, 10), (5, 10), (5, 11)}),
        (7, {(8, 4), (9, 4)}),
        (3, {(10, 4), (10, 5), (11, 5), (11, 6)}),
        (8, {(6, 12)}), (2, {(6, 13), (7, 13)}),
    ]
    for color, cells in roles:
        _paint(grid, cells, color)
    return grid


def _vary(grid, rng):
    # Preserve blue selection and explicit cyan-role teaching; vary every other hue.
    colors = [2, 3, 4, 5, 6, 7, 9]
    shuffled = colors[:]
    rng.shuffle(shuffled)
    palette = dict(zip(colors, shuffled))
    out = [[palette.get(value, value) for value in row] for row in grid]
    if rng.randrange(2):
        out = [row[::-1] for row in out]
    if rng.randrange(2):
        out = out[::-1]
    if rng.randrange(2):
        out = [list(row) for row in zip(*out)]
    return out


def _field(h, w, rng, *, thickness=2):
    grid = [[0] * w for _ in range(h)]
    selected_width = w - 6
    starts = list(range(0, h - thickness + 1, thickness + 2))
    previous_color = None
    first = True
    for band, r0 in enumerate(starts):
        columns = list(range(selected_width))
        if band % 2:
            columns.reverse()
        blocks = []
        while columns:
            width = min(len(columns), rng.randint(2, 5))
            chunk, columns = columns[:width], columns[width:]
            color = 1 if first else rng.choice([color for color in range(2, 10)
                                               if color != previous_color])
            first = False
            cells = {(r, c) for r in range(r0, r0 + thickness) for c in chunk}
            _paint(grid, cells, color)
            blocks.append((set(chunk), color))
            previous_color = color
        if band + 1 < len(starts):
            endpoint = selected_width - 1 if band % 2 == 0 else 0
            connector = {(r, endpoint) for r in range(r0 + thickness, starts[band + 1])}
            color = rng.choice([color for color in range(2, 10) if color != previous_color])
            _paint(grid, connector, color)
            previous_color = color
            if selected_width >= 6 and rng.randrange(2):
                col = rng.randrange(2, selected_width - 2)
                parent_color = next(color for columns, color in blocks if col in columns)
                leaf_color = rng.choice([color for color in range(2, 10) if color != parent_color])
                _paint(grid, {(r0 + thickness, col)}, leaf_color)
    # An independent dense cluster varies area/object count without a blue cue.
    color_a, color_b = rng.sample(range(2, 10), 2)
    for r in range(h):
        for c in range(w - 4, w):
            grid[r][c] = (color_a, color_b)[(r // 2 + (c - (w - 4)) // 2) % 2]
    return grid


def inputs(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    rng = random.Random(seed ^ 0x366CDA)
    demos = [_core_a(), _core_b(), _field(7, 9, rng), _field(15, 18, rng),
             _field(24, 27, rng), _field(30, 30, rng, thickness=2)]
    queries = [_field(8, 12, rng), _field(18, 21, rng, thickness=3),
               _field(26, 29, rng), _field(30, 30, rng, thickness=3)]
    demos = [_vary(grid, rng) for grid in demos]
    queries = [_vary(grid, rng) for grid in queries]
    random.Random(seed ^ 0xC01A).shuffle(queries)
    return demos, queries


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    chosen = (dict(random.Random(seed ^ 0xA11CE).choice(SETTINGS)) if settings is None
              else dict(settings) if type(settings) is dict else settings)
    _setting(chosen)
    demo_inputs, query_inputs = inputs(seed)
    def pairs(grids):
        return [{"input": grid, "output": transform(grid, chosen)} for grid in grids]
    return {"train": pairs(demo_inputs[:demos]), "test": pairs(query_inputs[:queries]),
            "program_solution": program(chosen), "settings": dict(chosen)}
