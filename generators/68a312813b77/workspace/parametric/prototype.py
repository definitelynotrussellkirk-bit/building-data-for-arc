"""Native bbox completion with optional object-derived diagonal gap filling.

The canonical program is unchanged.  The separate native grammar extends to
30x30 and up to twenty original monochrome 8-connected objects.  It preserves
all foreground, never uses fill color 7 in an input, and derives every bridge
from the ORIGINAL objects, before any bbox cells are painted.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import random


VERSION = "1.0.0"
CANONICAL = "(rule! (lambda (g) (fill-object-bboxes-8 g 7)))"
COLORS = (1, 2, 3, 4, 5, 6, 8, 9)


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"completion"}
            or type(settings["completion"]) is not str
            or settings["completion"] not in ("bbox", "diagonal_gaps")):
        raise ValueError("settings must contain exactly completion=bbox or diagonal_gaps")
    return settings["completion"]


def _integer(value, lower, upper, name):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an exact integer in {lower}..{upper}")


def _shape(grid):
    if type(grid) is not list or not grid or any(type(row) is not list for row in grid):
        raise ValueError("grid must contain nonempty list rows")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30 or any(len(row) != w for row in grid):
        raise ValueError("grid must be rectangular with sides 1..30")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return h, w


def components(grid, connectivity=8):
    """Same-color nonzero components, in row-major discovery order."""
    h, w = _shape(grid)
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if connectivity == 8:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            pending, cells = [(r, c)], []
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.append([rr, cc])
                for dr, dc in steps:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            cells.sort()
            result.append({"color": color, "cells": cells,
                           "bbox": [min(x[0] for x in cells), min(x[1] for x in cells),
                                    max(x[0] for x in cells), max(x[1] for x in cells)]})
    return result


def _extent(obj):
    us = [r + c for r, c in obj["cells"]]
    vs = [r - c for r, c in obj["cells"]]
    return min(us), max(us), min(vs), max(vs)


def transform(grid, settings):
    """Deterministic authoring mirror; protected execution supplies authority."""
    policy = _setting(settings)
    h, w = _shape(grid)
    objects = components(grid)
    result = deepcopy(grid)
    for obj in objects:
        r0, c0, r1, c1 = obj["bbox"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if result[r][c] == 0:
                    result[r][c] = 7
    if policy == "diagonal_gaps":
        extents = [_extent(obj) for obj in objects]
        gaps = [(a[1], b[0], max(a[2], b[2]), min(a[3], b[3]))
                for a in extents for b in extents
                if a[1] < b[0] and max(a[2], b[2]) <= min(a[3], b[3])]
        for r in range(h):
            for c in range(w):
                if grid[r][c] == 0 and any(lo < r+c < hi and v0 <= r-c <= v1
                                            for lo, hi, v0, v1 in gaps):
                    result[r][c] = 7
    return result


def program(settings):
    if _setting(settings) == "bbox":
        return CANONICAL
    return """(rule! (lambda (g)
  (define original-objects (objects-8 g 0))
  (define (extent obj)
    (let* ((us (map (lambda (p) (+ (first p) (second p))) (obj-cells obj)))
           (vs (map (lambda (p) (- (first p) (second p))) (obj-cells obj))))
      (list (apply min us) (apply max us) (apply min vs) (apply max vs))))
  (define spans (map extent original-objects))
  (define gaps
    (filter (lambda (span) (and (< (first span) (second span))
                               (<= (third span) (fourth span))))
      (for*/list ((a (in-list spans)) (b (in-list spans)))
        (list (second a) (first b)
              (max (third a) (third b)) (min (fourth a) (fourth b))))))
  (define base (fill-object-bboxes-8 g 7))
  (grid-from-fn (rows g) (cols g)
    (lambda (r c)
      (if (and (= (at g r c) 0)
               (for/or ((span (in-list gaps)))
                 (and (< (first span) (+ r c)) (< (+ r c) (second span))
                      (<= (third span) (- r c)) (<= (- r c) (fourth span)))))
          7 (at base r c))))))"""


def _rng(seed, label):
    raw = f"68a312813b77:{VERSION}:{seed}:{label}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _band(r, c, length, thickness=1):
    return {(r+i+t, c-i) for i in range(length) for t in range(thickness)}


def _u_shape(r, c, height, width, rng):
    cells = {(r+i, c) for i in range(height)}
    cells |= {(r, c+j) for j in range(width)}
    cells |= {(r+i, c+width-1) for i in range(height)}
    candidates = [(r+i, c+j) for i in range(1, height-1) for j in range(1, width-1)]
    rng.shuffle(candidates)
    cells.update(candidates[:rng.randrange(len(candidates) + 1)])
    return cells


def _place(grid, cells, color):
    h, w = len(grid), len(grid[0])
    for r, c in cells:
        if not 0 <= r < h or not 0 <= c < w or grid[r][c] != 0:
            raise RuntimeError("constructive scene objects overlap or leave the canvas")
        grid[r][c] = color


def _motif(rng, *, mixed, nearest=False, thin=False, dense=False):
    """Four or five objects in a 14-square with active and inactive pairs."""
    grid = [[0] * 14 for _ in range(14)]
    palette = rng.sample(COLORS, 4)
    if nearest:
        # Broad/narrow/broad: the first and third need a non-nearest bridge.
        a = rng.choice((3, 4))
        c = rng.choice((8, 9))
        shapes = [_band(a, a, rng.choice(tuple(length for length in (4, 5) if length <= a+1)), 2), _band(6, 6, 2),
                  _band(c, c, rng.choice((3, 4)), 2),
                  _u_shape(0, 11, 3, 3, rng), _u_shape(0, 0, 3, 3, rng)]
        colors = [palette[0], palette[0], palette[1] if mixed else palette[0],
                  palette[2], palette[3]]
    else:
        # Partial projected overlap. The final two objects have disjoint-v roles.
        length = rng.choice((4, 5) if dense else (3, 4, 5))
        a_thickness = 1 if thin else 2 if dense else rng.choice((1, 2))
        a_col = 6 if thin else rng.choice((5, 6, 7))
        first = _band(0, a_col, length, a_thickness)
        vlow, vhigh = -a_col, -a_col + 2*(length-1) + a_thickness-1
        options = []
        for r in range(4, 8):
            for c in range(9, 13):
                for size in ((4, 5) if dense else (3, 4, 5)):
                    for thick in ((1,) if thin else (2,) if dense else (1, 2)):
                        cells = _band(r, c, size, thick)
                        if (max(rr for rr, _ in cells) > 12 or min(cc for _, cc in cells) < 5
                                or not vlow < r-c < vhigh
                                or r-c + 2*(size-1) + thick-1 <= vhigh
                                or (thin and (r+c) % 2 != a_col % 2)
                                or any(max(abs(x-a), abs(y-b)) <= 1
                                       for x, y in first for a, b in cells)):
                            continue
                        options.append(cells)
        if not options:
            raise RuntimeError("no constructive partial-overlap band pair")
        shapes = [first, rng.choice(options),
                  _band(0, 13, 3), _u_shape(10, 0, 4, 4, rng)]
        colors = [palette[0], palette[1] if mixed else palette[0], palette[2], palette[3]]
    for cells, color in zip(shapes, colors):
        _place(grid, cells, color)
    return grid


def _teacher(rng, *, mixed, nearest):
    """Three disjoint projection bands expose the sampler's semantic branches."""
    grid = [[0] * 24 for _ in range(20)]
    core = _motif(rng, mixed=mixed, nearest=nearest, thin=not nearest)
    for r, row in enumerate(core):
        for c, value in enumerate(row):
            grid[r][c+10] = value
    colors = rng.sample(COLORS, 4)
    # Same u/v intervals but different colors touch diagonally: merging colors
    # incorrectly fills (7,3), outside both individual boxes and their true bridge.
    _place(grid, {(7, 0), (8, 0), (8, 1)}, colors[0])
    _place(grid, {(9, 2), (10, 2), (10, 3)}, colors[1])
    # Own bbox fill creates new color-7 components with v=13. Resegmenting the
    # painted result incorrectly bridges those; originals have only v=14..15.
    gap = rng.choice((3, 4))
    _place(grid, {(14, 0), (15, 0), (15, 1)}, colors[2])
    _place(grid, {(14+gap, gap), (15+gap, gap), (15+gap, gap+1)}, colors[3])
    return grid


def _stretch(grid, height, width):
    """Expand component geometry across a canvas, preserving its source colors."""
    h, w = len(grid), len(grid[0])
    return [[grid[r*h//height][c*w//width] for c in range(width)] for r in range(height)]


def _symmetry(grid, rng):
    # Transposition and 180-degree rotation preserve the chosen diagonal frame.
    if rng.randrange(2):
        grid = [list(row) for row in zip(*grid)]
    if rng.randrange(2):
        grid = [row[::-1] for row in grid[::-1]]
    return grid


def _scene(seed, label, shape, *, mixed, nearest=False, large=False, teaching=False):
    rng = _rng(seed, label)
    h, w = shape
    grid = [[0] * w for _ in range(h)]
    if large:
        # Four populated motifs and two central shapes occupy the full 30-square.
        for index, (dr, dc) in enumerate(((0, 0), (0, 16), (16, 0), (16, 16))):
            motif = _motif(rng, mixed=index % 2 == 1, nearest=False, dense=True)
            for r, row in enumerate(motif):
                for c, value in enumerate(row):
                    if value:
                        grid[r+dr][c+dc] = value
        color_a, color_b = rng.sample(COLORS, 2)
        _place(grid, {(14, c) for c in range(4, 12)} | {(15, 4), (15, 11)}, color_a)
        _place(grid, {(r, 14) for r in range(4, 12)} | {(4, 15), (11, 15)}, color_b)
    elif teaching:
        motif = _teacher(rng, mixed=mixed, nearest=nearest)
        # Keep first-two witness geometry exact. Later demos can be larger,
        # with placement varying while the required source partitions persist.
        dr, dc = h-20, 0
        for r, row in enumerate(motif):
            for c, value in enumerate(row):
                grid[r+dr][c+dc] = value
    else:
        grid = _stretch(_motif(rng, mixed=mixed, nearest=nearest), h, w)
    return _symmetry(grid, rng)


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63-1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    _setting(settings)
    padding = _rng(seed, "shape").randrange(2)
    demo_shapes = [(20, 24), (21, 25), (22, 26), (23, 27), (24, 28), (25, 29)]
    query_shapes = [(14, 17), (17, 20), (24, 27), (30, 30)]
    train_inputs = [_scene(seed, f"demo-{i}", (h+padding, w+padding),
                          mixed=i % 2 == 1, nearest=i % 2 == 1, teaching=True)
                    for i, (h, w) in enumerate(demo_shapes[:demos])]
    test_inputs = [_scene(seed, f"query-{i}", (h+padding, w+padding) if i < 3 else (h, w),
                         mixed=True, nearest=i == 1, large=i == 3)
                   for i, (h, w) in enumerate(query_shapes[:queries])]
    def pairs(inputs):
        return [{"input": grid, "output": transform(grid, settings)} for grid in inputs]
    return {"train": pairs(train_inputs), "test": pairs(test_inputs),
            "program_solution": program(settings),
            "meta": {"seed": seed, "settings": dict(settings), "version": VERSION,
                     "grammar": "zero background; no input7; same-color8 objects; sizes14..30; at most20 objects",
                     "authoring_focus": {"source_task_id": "7666fa5d", "source_split": "evaluation",
                                         "relationship_verified": False, "training_admitted": False}}}
