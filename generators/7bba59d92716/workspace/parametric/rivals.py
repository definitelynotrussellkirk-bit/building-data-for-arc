"""Independent, bounded hypotheses for the marker-selected line family.

This module imports neither the production generator nor the prototype.  Each
hypothesis has a Python interpretation and a standalone native ``rule!`` program.
Marker-measurement rivals coincide with the intended fixed-five setting; their
survival there is expected and is not treated as evidence of ambiguity.
"""
from __future__ import annotations


NAMES = (
    "run_ignores_branches",
    "any_shape",
    "all_odd_vertical",
    "eight_connectivity",
    "marker_bbox_area",
    "marker_height",
    "marker_boundary_cells",
)
DESCRIPTIONS = {
    "run_ignores_branches": "Mark maximal vertical blue runs of the selected length, ignoring side branches.",
    "any_shape": "Mark the row-major middle cell of any blue component of the selected size, regardless of orientation.",
    "all_odd_vertical": "Mark every vertical blue component of odd size, ignoring the selected length.",
    "eight_connectivity": "Use same-color eight-connected blue components instead of four-connected components.",
    "marker_bbox_area": "For marker_size, use the marker bounding-box area instead of its cell count.",
    "marker_height": "For marker_size, use the marker height instead of its cell count.",
    "marker_boundary_cells": "For marker_size, count occupied marker cells with at least one four-neighbor outside the component.",
}


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"length_rule"}
            or type(settings["length_rule"]) is not str
            or settings["length_rule"] not in ("fixed_five", "marker_size")):
        raise ValueError("settings must contain exactly length_rule=fixed_five|marker_size")
    return settings["length_rule"]


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError("expected a rectangular ARC grid of exact integer colors")
    return [row[:] for row in grid]


def components(grid, color, connectivity=4):
    """Independent same-color flood fill, with explicit connectivity."""
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be four or eight")
    height, width = len(grid), len(grid[0])
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    seen, result = set(), []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            todo, cells = [(row, col)], []
            seen.add((row, col))
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for dr, dc in deltas:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(sorted(cells))
    return result


def marker_cells(grid):
    markers = components(grid, 6)
    if len(markers) != 1:
        raise ValueError("the admitted grammar needs exactly one color-6 component")
    return markers[0]


def selected_length(grid, settings, rival=None):
    mode = _setting(settings)
    if mode == "fixed_five":
        return 5
    cells = marker_cells(grid)
    height = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
    width = max(c for _, c in cells) - min(c for _, c in cells) + 1
    if rival == "marker_bbox_area":
        return height * width
    if rival == "marker_height":
        return height
    if rival == "marker_boundary_cells":
        occupied = set(cells)
        return sum(any((r + dr, c + dc) not in occupied
                       for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
                   for r, c in cells)
    return len(cells)


def reference(grid, settings):
    """Independent Python claim for the intended transformation, not authority."""
    return _predict(None, grid, settings)


def predict(name, grid, settings):
    if name not in NAMES:
        raise ValueError(f"unknown rival: {name!r}")
    return _predict(name, grid, settings)


def _predict(name, grid, settings):
    out = _grid(grid)
    k = selected_length(grid, settings, name)
    if name == "run_ignores_branches":
        for col in range(len(grid[0])):
            row = 0
            while row < len(grid):
                if grid[row][col] != 1:
                    row += 1
                    continue
                start = row
                while row < len(grid) and grid[row][col] == 1:
                    row += 1
                if row - start == k:
                    out[start + (k - 1) // 2][col] = 2
        return out
    for cells in components(grid, 1, 8 if name == "eight_connectivity" else 4):
        vertical = len({c for _, c in cells}) == 1
        size_matches = len(cells) % 2 == 1 if name == "all_odd_vertical" else len(cells) == k
        if size_matches and (vertical or name == "any_shape"):
            row, col = cells[(len(cells) - 1) // 2]
            out[row][col] = 2
    return out


def _length_expression(name, settings):
    if _setting(settings) == "fixed_five":
        return "5"
    marker = "(first (filter (lambda (o) (= (obj-color o) 6)) (objects g 0)))"
    if name == "marker_bbox_area":
        return f"(let ([marker {marker}]) (* (obj-h marker) (obj-w marker)))"
    if name == "marker_height":
        return f"(obj-h {marker})"
    if name == "marker_boundary_cells":
        return f"(length (obj-boundary-cells {marker} 4))"
    return f"(obj-size {marker})"


def program(name, settings):
    """Return one complete native rule, without referring to prototype helpers."""
    if name not in NAMES:
        raise ValueError(f"unknown rival: {name!r}")
    k = _length_expression(name, settings)
    if name == "run_ignores_branches":
        return f"""(rule!
  (lambda (g)
    (let ([k {k}])
      (for*/fold ([out g]) ([r (range (rows g))] [c (range (cols g))])
        (if (and (= (at g r c) 1)
                 (or (= r 0) (not (= (at g (- r 1) c) 1)))
                 (<= (+ r k) (rows g))
                 (andmap (lambda (dr) (= (at g (+ r dr) c) 1)) (range k))
                 (or (= (+ r k) (rows g))
                     (not (= (at g (+ r k) c) 1))))
            (set-cell out (+ r (quotient (- k 1) 2)) c 2)
            out)))))"""
    objects = "objects-8" if name == "eight_connectivity" else "objects"
    shape = "#t" if name == "any_shape" else "(= (obj-c1 o) (obj-c2 o))"
    size = "(odd? (obj-size o))" if name == "all_odd_vertical" else "(= (obj-size o) k)"
    # Row-major median agrees with the canonical midpoint on vertical lines and
    # defines a total, concrete hypothesis for horizontal and branched objects.
    return f"""(rule!
  (lambda (g)
    (let ([k {k}])
      (for/fold ([out g])
                ([obj (filter (lambda (o) (and (= (obj-color o) 1) {shape} {size}))
                              ({objects} g 0))])
        (let* ([ordered (sort-by (obj-cells obj)
                                (lambda (p) (+ (* (first p) (cols g)) (second p))))]
               [p (nth ordered (quotient (- (obj-size obj) 1) 2))])
          (set-cell out (first p) (second p) 2))))))"""
