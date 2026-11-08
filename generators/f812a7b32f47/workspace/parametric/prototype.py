"""Crossing completion, optionally followed by selection of co-largest groups.

The separate parametric grammar permits preexisting interior color-7 fragments.
They make completion alter connectivity and component ranking. Production's
empty-interior generator and canonical Racket authority are unchanged.
Python results are claims; audit/qualification re-execute real protected Racket.
"""
from __future__ import annotations

from pathlib import Path

MODES = ("all", "largest")
RIVALS = (
    "all", "largest", "identity", "smallest", "first_largest",
    "last_largest", "bbox_area", "eight_connected", "select_before_fill",
    "ignore_anchors", "keep_original", "markers_anywhere_all",
    "markers_anywhere_largest", "fixed_eight", "at_least_eight",
)


def validate_settings(settings):
    if type(settings) is not dict or set(settings) != {"selection"}:
        raise ValueError("settings must contain exactly selection")
    if type(settings["selection"]) is not str or settings["selection"] not in MODES:
        raise ValueError("selection must be all or largest")
    return settings["selection"]


def _box(grid):
    cells = [(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value != 0]
    if not cells:
        raise ValueError("a nonzero frame is required")
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _fill(grid, anywhere=False):
    r0, c0, r1, c1 = _box(grid)
    if anywhere:
        corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
        rr = {r for r, row in enumerate(grid) for c, v in enumerate(row)
              if v == 2 and (r, c) not in corners}
        cc = {c for r, row in enumerate(grid) for c, v in enumerate(row)
              if v == 3 and (r, c) not in corners}
    else:
        rr = [r for r in range(r0 + 1, r1) if grid[r][c0] == 2]
        cc = [c for c in range(c0 + 1, c1) if grid[r0][c] == 3]
    result = [row[:] for row in grid]
    for r in rr:
        for c in cc:
            result[r][c] = 7
    return result


def _components(grid, diagonal=False):
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, v in enumerate(row) if v == 7}
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonal:
        directions += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells, frontier = {start}, [start]
        while frontier:
            r, c = frontier.pop()
            for dr, dc in directions:
                neighbor = r + dr, c + dc
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    frontier.append(neighbor)
        components.append(cells)
    return components


def describe_components(grid):
    return [{"size": len(cells), "cells": [list(p) for p in sorted(cells)]}
            for cells in _components(grid)]


def _select(grid, kind="largest"):
    components = _components(grid, diagonal=kind == "eight_connected")
    if not components:
        return [row[:] for row in grid]
    def score(cells):
        if kind == "bbox_area":
            return ((max(r for r, _ in cells) - min(r for r, _ in cells) + 1)
                    * (max(c for _, c in cells) - min(c for _, c in cells) + 1))
        return len(cells)
    extreme = (min if kind == "smallest" else max)(map(score, components))
    winners = [cells for cells in components if score(cells) == extreme]
    if kind == "fixed_eight":
        winners = [cells for cells in components if len(cells) == 8]
    elif kind == "at_least_eight":
        winners = [cells for cells in components if len(cells) >= 8]
    if kind == "first_largest":
        winners = winners[:1]
    elif kind == "last_largest":
        winners = winners[-1:]
    selected = set().union(*winners)
    return [[0 if v == 7 and (r, c) not in selected else v
             for c, v in enumerate(row)] for r, row in enumerate(grid)]


def solve(grid, selection):
    validate_settings({"selection": selection})
    completed = _fill(grid)
    return completed if selection == "all" else _select(completed)


def rival_solutions(grid):
    completed = _fill(grid)
    selected = _select(completed)
    stripped = [[0 if v == 7 else v for v in row] for row in grid]
    anywhere = _fill(grid, anywhere=True)
    result = {"all": completed, "largest": selected,
              "identity": [row[:] for row in grid]}
    for name in ("smallest", "first_largest", "last_largest", "bbox_area", "eight_connected",
                 "fixed_eight", "at_least_eight"):
        result[name] = _select(completed, name)
    result["select_before_fill"] = _fill(_select(grid))
    result["ignore_anchors"] = _select(_fill(stripped))
    result["keep_original"] = [[7 if grid[r][c] == 7 else v
                                for c, v in enumerate(row)]
                               for r, row in enumerate(selected)]
    result["markers_anywhere_all"] = anywhere
    result["markers_anywhere_largest"] = _select(anywhere)
    return result


_FILL = """
    (define (fill grid)
      (let* ((cells (filter (lambda (p) (not (= (at grid (first p) (second p)) 0))) (grid-positions grid)))
             (bb (bbox-of-cells cells))
             (r0 (first bb)) (c0 (second bb)) (r1 (third bb)) (c1 (fourth bb))
             (marked-rows ROWS) (marked-cols COLS))
        (for/fold ((out grid)) ((r (in-list marked-rows)))
          (paint-cells out (map (lambda (c) (list r c)) marked-cols) 7))))
"""
_ROWS = "(filter (lambda (r) (= (at grid r c0) 2)) (range (+ r0 1) r1))"
_COLS = "(filter (lambda (c) (= (at grid r0 c) 3)) (range (+ c0 1) c1))"
_ANY_ROWS = """(filter (lambda (r)
  (any? (lambda (c) (and (= (at grid r c) 2)
    (not (and (or (= r r0) (= r r1)) (or (= c c0) (= c c1)))))) (range (cols grid)))) (range (rows grid)))"""
_ANY_COLS = """(filter (lambda (c)
  (any? (lambda (r) (and (= (at grid r c) 3)
    (not (and (or (= r r0) (= r r1)) (or (= c c0) (= c c1)))))) (range (rows grid)))) (range (cols grid)))"""
_SELECT = """
    (define (strip grid)
      (grid-from-fn (rows grid) (cols grid)
        (lambda (r c) (if (= (at grid r c) 7) 0 (at grid r c)))))
    (define (score obj) SCORE)
    (define (select grid)
      (let ((groups (filter (lambda (obj) (= (obj-color obj) 7)) (OBJECTS grid))))
        (if (empty? groups) grid
          (let* ((best (apply EXTREME (map score groups)))
                 (winners (filter (lambda (obj) (= (score obj) best)) groups))
                 (chosen CHOSEN))
            (for/fold ((out (strip grid))) ((obj (in-list chosen)))
              (paint-cells out (obj-cells obj) 7))))))
"""


def rival_program(name):
    if name not in RIVALS:
        raise ValueError(f"unknown rival {name!r}")
    if name == "all":
        return (Path(__file__).parent / "canonical.rkt").read_text()
    if name == "identity":
        return "(rule! (lambda (g) g))"
    anywhere = name.startswith("markers_anywhere_")
    fill = _FILL.replace("ROWS", _ANY_ROWS if anywhere else _ROWS).replace(
        "COLS", _ANY_COLS if anywhere else _COLS)
    score = "(obj-size obj)"
    if name == "bbox_area":
        score = "(let ((b (obj-bbox obj))) (* (+ 1 (- (third b) (first b))) (+ 1 (- (fourth b) (second b)))))"
    chosen = "winners"
    if name == "first_largest":
        chosen = "(list (first winners))"
    elif name == "last_largest":
        chosen = "(list (first (reverse winners)))"
    select = (_SELECT.replace("SCORE", score)
              .replace("OBJECTS", "objects-8" if name == "eight_connected" else "objects")
              .replace("EXTREME", "min" if name == "smallest" else "max")
              .replace("CHOSEN", chosen))
    if name in ("fixed_eight", "at_least_eight"):
        predicate = "(= (obj-size obj) 8)" if name == "fixed_eight" else "(>= (obj-size obj) 8)"
        select = select.replace("(= (score obj) best)", predicate)
    final = "(select (fill g))"
    if name == "select_before_fill":
        final = "(fill (select g))"
    elif name == "ignore_anchors":
        final = "(select (fill (strip g)))"
    elif name == "keep_original":
        final = "(let ((out (select (fill g)))) (grid-from-fn (rows g) (cols g) (lambda (r c) (if (= (at g r c) 7) 7 (at out r c)))))"
    elif name == "markers_anywhere_all":
        final = "(fill g)"
    return "(rule! (let ()\n" + fill + select + "\n    " + final + "))"


def program(settings):
    return rival_program(validate_settings(settings))
