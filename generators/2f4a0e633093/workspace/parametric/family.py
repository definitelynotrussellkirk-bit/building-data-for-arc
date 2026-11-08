"""Area-ranked dynamic gallery family for 2f4a0e633093.

The canonical setting reads masks from three fixed 3x3 panels.  The alternate
first discovers the three lower-region monochrome objects, turns them into
binary crops, orders those crops by pixel area, and only then renders the
shape-by-legend-color gallery.  The discovered area order is therefore a real
intermediate needed by the final gallery rows.
"""
from __future__ import annotations

from pathlib import Path

LAYOUTS = ("fixed_panels", "area_ranked")
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")


def parse_settings(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"layout"}
        or type(settings["layout"]) is not str
        or settings["layout"] not in LAYOUTS
    ):
        raise ValueError("settings must be exactly layout=fixed_panels or area_ranked")
    return {"layout": settings["layout"]}


def _validate_grid(grid):
    if type(grid) is not list or not 5 <= len(grid) <= 30 or not grid:
        raise ValueError("grid height must be in 5..30")
    if type(grid[0]) is not list or not 11 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be in 11..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer colors 0..9")


def _binary_crop_from_cells(cells):
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    crop = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        crop[r - r0][c - c0] = 1
    return crop


def _fixed_binary_crop(grid, c0):
    cells = [(r - 2, c - c0) for r in range(2, 5) for c in range(c0, c0 + 3) if grid[r][c] != 0]
    if not cells:
        return [[0]]
    return _binary_crop_from_cells(cells)


def _paste(out, mask, top, left, color):
    for r, row in enumerate(mask):
        for c, value in enumerate(row):
            if value:
                out[top + r][left + c] = color


def canonical_output(grid):
    _validate_grid(grid)
    legend = [value for value in grid[0] if value]
    masks = [_fixed_binary_crop(grid, c0) for c0 in (0, 4, 8)]
    out = [[0] * 11 for _ in range(11)]
    for i, mask in enumerate(masks):
        for j, color in enumerate(legend):
            _paste(out, mask, i * 4, j * 4, color)
    return out


def analyze(grid):
    _validate_grid(grid)
    legend = [value for value in grid[0] if value]
    if len(legend) != 3 or len(set(legend)) != 3 or 0 in legend:
        raise ValueError("top row must contain exactly three distinct legend colors")
    lower_colors = []
    for row in grid[1:]:
        for value in row:
            if value and value not in legend and value not in lower_colors:
                lower_colors.append(value)
    if len(lower_colors) != 3:
        raise ValueError("lower field must contain exactly three non-legend colors")
    entries = []
    for index, color in enumerate(lower_colors):
        cells = [(r, c) for r in range(1, len(grid)) for c in range(len(grid[0])) if grid[r][c] == color]
        if not cells:
            raise ValueError("empty lower object")
        mask = _binary_crop_from_cells(cells)
        if len(mask) > 9 or len(mask[0]) > 9:
            raise ValueError("object bounding boxes must fit 9x9 gallery cells")
        entries.append({"source_index": index, "color": color, "cells": cells,
                        "mask": mask, "area": len(cells)})
    if len({entry["area"] for entry in entries}) != 3:
        raise ValueError("object areas must be distinct")
    ordered = sorted(entries, key=lambda entry: (entry["area"], entry["source_index"]))
    permutation = tuple(entry["source_index"] for entry in ordered)
    return {"legend": legend, "entries": entries, "ordered": ordered,
            "permutation": permutation, "areas": [entry["area"] for entry in ordered]}


def area_ranked_output(grid, permutation=None):
    info = analyze(grid)
    if permutation is None:
        permutation = info["permutation"]
    if type(permutation) not in (tuple, list) or tuple(sorted(permutation)) != (0, 1, 2):
        raise ValueError("permutation must contain source indices 0,1,2 exactly once")
    ordered = [info["entries"][index] for index in permutation]
    cell_h = max(len(entry["mask"]) for entry in ordered)
    cell_w = max(len(entry["mask"][0]) for entry in ordered)
    out = [[0] * (3 * cell_w + 2) for _ in range(3 * cell_h + 2)]
    for i, entry in enumerate(ordered):
        for j, color in enumerate(info["legend"]):
            _paste(out, entry["mask"], i * (cell_h + 1), j * (cell_w + 1), color)
    return out


def apply(grid, settings):
    return canonical_output(grid) if parse_settings(settings)["layout"] == "fixed_panels" else area_ranked_output(grid)


_COMMON = r'''(let ((dummy 0))
  (define (crop-color color)
    (let* ((cells (find-color g color))
           (bb (bbox-of-cells cells))
           (r0 (first bb)) (c0 (second bb)) (r1 (third bb)) (c1 (fourth bb)))
      (grid-from-fn (+ 1 (- r1 r0)) (+ 1 (- c1 c0))
        (lambda (r c) (if (= (at g (+ r0 r) (+ c0 c)) color) 1 0)))))
  (define (recolor-grid grid color)
    (grid-from-fn (rows grid) (cols grid)
      (lambda (r c) (if (= (at grid r c) 0) 0 color))))
  (define (paste grid pat top left)
    (for*/fold ((out grid)) ((r (in-range (rows pat))) (c (in-range (cols pat))))
      (let ((v (at pat r c)) (rr (+ top r)) (cc (+ left c)))
        (if (and (not (= v 0)) (in-bounds? rr cc (rows out) (cols out)))
            (set-cell out rr cc v) out))))
  (let* ((legend (filter (lambda (v) (not (= v 0))) (first g)))
         (lower (apply append (rest g)))
         (panel-colors (remove-duplicates
           (filter (lambda (v) (and (not (= v 0)) (not (member? v legend)))) lower)))
         (entries (map (lambda (color)
                         (let ((mask (crop-color color)))
                           (list color mask (length (find-color g color)))))
                       panel-colors))
         (ordered ORDERING)
         (masks (map second ordered))
         (cell-h (apply max (map rows masks)))
         (cell-w (apply max (map cols masks))))
    (for*/fold ((out (empty-grid (+ (* 3 cell-h) 2) (+ (* 3 cell-w) 2) 0)))
               ((i (in-range 3)) (j (in-range 3)))
      (paste out (recolor-grid (list-ref masks i) (list-ref legend j))
             (* i (+ cell-h 1)) (* j (+ cell-w 1))))))'''

ALTERNATE = "(rule! " + _COMMON.replace("ORDERING", "(sort-by entries third)") + ")"
COUNTERFACTUAL = "(rule! " + _COMMON.replace("ORDERING", "(reverse (sort-by entries third))") + ")"


def program(settings):
    return CANONICAL if parse_settings(settings)["layout"] == "fixed_panels" else ALTERNATE


def counterfactual_program():
    return COUNTERFACTUAL
