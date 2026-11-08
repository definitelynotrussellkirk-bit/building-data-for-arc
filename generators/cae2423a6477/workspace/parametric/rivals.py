"""Independent finite semantic probes for selected-barrier enclosure.

This module imports neither the production generator nor the prototype.  The
Python oracle, executable Racket rules, and authored controls are review tools.
The finite bank is a falsification aid, never a completeness claim.  In the
admitted 0/3 grammar, some named mechanisms can be behaviorally equivalent;
``signature_groups`` reports observed equivalence instead of counting names as
independent evidence.  In particular, bbox-only and eight-neighbor exterior
completion are retained as two interpretable controls of the same likely class.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
import hashlib
import json

MODES = ("border", "enclosed")
FOUR = ((-1, 0), (0, -1), (0, 1), (1, 0))
EIGHT = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if (r, c) != (0, 0))

CORE = (
    "identity", "opposite_completion", "all_green", "any_hole", "closed_loop",
    "rectangular_hole", "large_bbox", "size_at_least_8", "perimeter_size_only",
    "border_subset", "border_complete", "solid_rectangles", "allow_thin_frames",
    "minimum_4x4", "square_only", "wide_only", "tall_only", "largest_only",
    "smallest_only", "first_only", "last_only", "empty_interiors", "outermost_only",
    "innermost_only", "avoid_boundary", "eight_neighbor_objects", "red_frames",
    "erase_frames",
)
COMPLETION = (
    "bbox_interiors", "eight_neighbor_exterior", "all_green_walls",
    "green_only_walls", "overwrite_green", "largest_pocket", "smallest_pocket",
    "rectangular_pockets", "fill_outside", "top_boundary_only", "corner_seed_only",
    "one_layer_only",
)


def _validated(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
            type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("expected a nonempty 1..30 rectangular grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(value) is not int or value not in (0, 3) for value in row)
           for row in grid):
        raise ValueError("input cells must be exact integers 0 or 3")
    return tuple(tuple(row) for row in grid)


def _mode(mode):
    if type(mode) is not str or mode not in MODES:
        raise ValueError("completion mode must be border or enclosed")
    return mode


def _components(cells, directions=FOUR):
    unseen = set(cells)
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        piece = {start}
        todo = [start]
        while todo:
            r, c = todo.pop()
            for dr, dc in directions:
                point = r + dr, c + dc
                if point in unseen:
                    unseen.remove(point)
                    piece.add(point)
                    todo.append(point)
        result.append(frozenset(piece))
    return tuple(result)


def _box(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _rectangle(box):
    r1, c1, r2, c2 = box
    return {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}


def _border(box):
    r1, c1, r2, c2 = box
    return {p for p in _rectangle(box) if p[0] in (r1, r2) or p[1] in (c1, c2)}


def _inside(point, box):
    r1, c1, r2, c2 = box
    return r1 < point[0] < r2 and c1 < point[1] < c2


def _contains(outer, inner):
    return outer[0] < inner[0] and outer[1] < inner[1] and outer[2] > inner[2] and outer[3] > inner[3]


def _features(cells):
    box = _box(cells)
    r1, c1, r2, c2 = box
    height, width = r2 - r1 + 1, c2 - c1 + 1
    perimeter = _border(box)
    holes = tuple(piece for piece in _components(_rectangle(box) - cells)
                  if all(r1 < r < r2 and c1 < c < c2 for r, c in piece))
    return {
        "cells": cells, "box": box, "height": height, "width": width,
        "area": height * width, "size": len(cells), "border": perimeter,
        "exact": height >= 3 and width >= 3 and cells == perimeter,
        "holes": holes,
        "loop": bool(holes) and all(sum((r + dr, c + dc) in cells for dr, dc in FOUR) == 2
                                     for r, c in cells),
        "rectangular_hole": any(set(piece) == _rectangle(_box(piece)) for piece in holes),
    }


@lru_cache(maxsize=384)
def _analysis(key, connectivity=4):
    green = {(r, c) for r, row in enumerate(key) for c, value in enumerate(row) if value == 3}
    return tuple(_features(piece) for piece in _components(green, FOUR if connectivity == 4 else EIGHT))


def _select(key, name):
    features = _analysis(key, 8 if name == "eight_neighbor_objects" else 4)
    frames = tuple(item for item in features if item["exact"])
    height, width = len(key), len(key[0])
    if name == "all_green":
        return features
    predicates = {
        "any_hole": lambda f: bool(f["holes"]),
        "closed_loop": lambda f: f["loop"],
        "rectangular_hole": lambda f: f["rectangular_hole"],
        "large_bbox": lambda f: f["height"] >= 3 and f["width"] >= 3,
        "size_at_least_8": lambda f: f["size"] >= 8,
        "perimeter_size_only": lambda f: f["height"] >= 3 and f["width"] >= 3 and
            f["size"] == 2 * (f["height"] + f["width"]) - 4,
        "border_subset": lambda f: f["height"] >= 3 and f["width"] >= 3 and f["cells"] <= f["border"],
        "border_complete": lambda f: f["height"] >= 3 and f["width"] >= 3 and f["border"] <= f["cells"],
        "solid_rectangles": lambda f: f["height"] >= 3 and f["width"] >= 3 and f["size"] == f["area"],
        "allow_thin_frames": lambda f: f["cells"] == f["border"],
        "minimum_4x4": lambda f: f["exact"] and min(f["height"], f["width"]) >= 4,
        "square_only": lambda f: f["exact"] and f["height"] == f["width"],
        "wide_only": lambda f: f["exact"] and f["width"] >= f["height"],
        "tall_only": lambda f: f["exact"] and f["height"] >= f["width"],
        "empty_interiors": lambda f: f["exact"] and not any(
            key[r][c] == 3 and _inside((r, c), f["box"])
            for r, c in _rectangle(f["box"])),
        "outermost_only": lambda f: f["exact"] and not any(
            _contains(other["box"], f["box"]) for other in frames),
        "innermost_only": lambda f: f["exact"] and not any(
            _contains(f["box"], other["box"]) for other in frames),
        "avoid_boundary": lambda f: f["exact"] and f["box"][0] > 0 and f["box"][1] > 0 and
            f["box"][2] < height - 1 and f["box"][3] < width - 1,
    }
    if name in predicates:
        return tuple(item for item in features if predicates[name](item))
    if name in ("largest_only", "smallest_only") and frames:
        extreme = (max if name == "largest_only" else min)(f["area"] for f in frames)
        return tuple(f for f in frames if f["area"] == extreme)
    if name == "first_only":
        return frames[:1]
    if name == "last_only":
        return frames[-1:]
    return frames


def _pockets(stage, name=None):
    height, width = len(stage), len(stage[0])
    wall_values = {3, 7} if name == "all_green_walls" else ({3} if name == "green_only_walls" else {7})
    passable = {(r, c) for r in range(height) for c in range(width) if stage[r][c] not in wall_values}
    pieces = _components(passable, EIGHT if name == "eight_neighbor_exterior" else FOUR)

    def outside(piece):
        if name == "corner_seed_only":
            return (0, 0) in piece
        if name == "top_boundary_only":
            return any(r == 0 for r, c in piece)
        return any(r in (0, height - 1) or c in (0, width - 1) for r, c in piece)

    holes = tuple(piece for piece in pieces if outside(piece) == (name == "fill_outside"))
    if name in ("largest_pocket", "smallest_pocket") and holes:
        extreme = (max if name == "largest_pocket" else min)(len(piece) for piece in holes)
        holes = tuple(piece for piece in holes if len(piece) == extreme)
    if name == "rectangular_pockets":
        holes = tuple(piece for piece in holes if set(piece) == _rectangle(_box(piece)))
    return holes


def _predict(grid, mode, name=None):
    key = _validated(grid)
    _mode(mode)
    if name == "identity":
        return [list(row) for row in key]
    if name == "opposite_completion":
        mode = "enclosed" if mode == "border" else "border"
    selected = _select(key, name)
    output = [list(row) for row in key]
    frame_color = 2 if name == "red_frames" else (0 if name == "erase_frames" else 7)
    for item in selected:
        for r, c in item["cells"]:
            output[r][c] = frame_color
    if mode == "border":
        return output
    if name == "bbox_interiors":
        candidates = {point for item in selected for point in _rectangle(item["box"])
                      if _inside(point, item["box"])}
    else:
        candidates = set().union(*_pockets(output, name))
    # Evaluate every mask against the completed first-stage canvas, never an
    # incrementally filled canvas.  Detached green contents stay passable.
    to_paint = {(r, c) for r, c in candidates if output[r][c] == 0 or
                (name == "overwrite_green" and output[r][c] == 3)}
    if name == "one_layer_only":
        to_paint = {(r, c) for r, c in to_paint if any(
            0 <= r + dr < len(output) and 0 <= c + dc < len(output[0]) and
            output[r + dr][c + dc] == 7 for dr, dc in FOUR)}
    for r, c in to_paint:
        output[r][c] = 2
    return output


def intended(grid, mode):
    """Independent total rule over rectangular 1..30 exact-integer 0/3 grids."""
    return _predict(grid, mode)


def bank(mode):
    """Return named, total, deterministic rivals; query labels are never used."""
    _mode(mode)
    names = CORE + (COMPLETION if mode == "enclosed" else ())
    return {name: (lambda grid, name=name: _predict(grid, mode, name)) for name in names}


def feature_summary(grid, mode="enclosed"):
    key = _validated(grid)
    frames = _select(key, None)
    stage = intended(grid, "border")
    output = intended(grid, mode)
    fill = {(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value == 2}
    collective = {point for point in fill if not any(_inside(point, item["box"]) for item in frames)}
    h, w = len(grid), len(grid[0])
    features = _analysis(key)
    return {"height": h, "width": w, "green_cells": sum(row.count(3) for row in grid),
            "components": len(features), "selected_frames": len(frames),
            "nonframes": sum(not item["exact"] for item in features),
            "hollow_nonframes": sum(bool(item["holes"]) and not item["exact"] for item in features),
            "orange_cells": sum(row.count(7) for row in stage), "red_cells": len(fill),
            "collective_fill_cells": len(collective),
            "enclosed_green_cells": sum(stage[r][c] == 3 for piece in _pockets(stage) for r, c in piece),
            "selected_boxes": [list(item["box"]) for item in frames],
            "quadrant_nonzero": [sum(grid[r][c] != 0 for r in range(ra, rb) for c in range(ca, cb))
                                 for ra, rb, ca, cb in ((0, h//2, 0, w//2), (0, h//2, w//2, w),
                                                        (h//2, h, 0, w//2), (h//2, h, w//2, w))]}


def signature_groups(mode, grids):
    """Observed signature classes; equality here is not a global proof."""
    groups = {}
    items = list(grids)
    for name, predict in bank(mode).items():
        signature = hashlib.sha256(json.dumps([predict(grid) for grid in items],
                                              separators=(",", ":")).encode()).hexdigest()
        groups.setdefault(signature, []).append(name)
    return sorted(groups.values(), key=lambda names: names[0])


def _frame(r, c, height, width):
    return _border((r, c, r + height - 1, c + width - 1))


def _shift(cells, dr, dc):
    return {(r + dr, c + dc) for r, c in cells}


def _canvas(height, width, shapes):
    out = [[0] * width for _ in range(height)]
    for cells in shapes:
        for r, c in cells:
            out[r][c] = 3
    return out


def fixtures():
    """Authored controls independent of generated demonstrations and queries."""
    stepped = ({(0, c) for c in range(4)} | {(1, c) for c in range(3, 7)} |
               {(r, 6) for r in range(1, 6)} | {(5, c) for c in range(7)} |
               {(r, 0) for r in range(6)})
    cage = [_frame(r, c, 3, 3) for r, c in ((0, 3), (3, 0), (3, 6), (6, 3))]
    spoof = (_frame(0, 0, 5, 5) - {(0, 2)}) | {(1, 1)}
    dense = [_frame(r, c, 5, 5) for r in range(0, 30, 6) for c in range(0, 30, 6)
             if not (r < 12 and c < 12) and (r, c) not in ((18, 18), (24, 24))]
    dense += cage + [_rectangle((18, 18, 22, 22)), _rectangle((24, 24, 28, 28))]
    return {
        "blank": [[0]], "singleton": [[3]],
        "thin_axes": _canvas(15, 20, [_frame(0, 0, 1, 8), _frame(3, 0, 8, 1),
                                      _frame(0, 12, 2, 4), _frame(4, 5, 4, 2), _frame(11, 12, 2, 2)]),
        "mixed_rectangles": _canvas(15, 18, [_frame(1, 1, 3, 3), _frame(1, 7, 3, 6),
                                             _frame(6, 1, 7, 3), _frame(6, 8, 6, 7)]),
        "open_border": _canvas(9, 16, [(_frame(1, 1, 6, 7) - {(1, 4)}), _frame(3, 11, 3, 4)]),
        "irregular_loop": _canvas(10, 16, [_shift(stepped, 1, 1), _frame(2, 11, 4, 3)]),
        "outward_nub": _canvas(11, 18, [_frame(3, 1, 5, 6) | {(2, 3)}, _frame(1, 11, 6, 4)]),
        "inward_nub": _canvas(11, 18, [_frame(2, 1, 6, 7) | {(3, 4)}, _frame(1, 12, 4, 4)]),
        "filled_block": _canvas(12, 18, [_rectangle((1, 1, 6, 6)), _frame(2, 10, 7, 5)]),
        "perimeter_spoof": _canvas(9, 17, [_shift(spoof, 2, 1), _frame(2, 10, 5, 5)]),
        "nested_with_contents": _canvas(17, 17, [_frame(0, 0, 17, 17), _frame(4, 4, 9, 9),
                                                  {(7, 7), (7, 8), (8, 7)}]),
        "joint_cage": _canvas(9, 9, cage),
        "diagonal_contact": _canvas(10, 12, [_frame(1, 1, 3, 3), _frame(4, 4, 4, 5)]),
        "top_seed_trap": _canvas(10, 13, [_frame(3, 0, 3, 13)]),
        "boundary_and_interior": _canvas(13, 17, [_frame(0, 0, 5, 6), _frame(6, 9, 5, 6)]),
        "dense_30": _canvas(30, 30, dense),
    }


_RACKET_COMMON = r"""
  (define (border-cells obj)
    (filter (lambda (p)
      (or (= (first p) (obj-r1 obj)) (= (first p) (obj-r2 obj))
          (= (second p) (obj-c1 obj)) (= (second p) (obj-c2 obj))))
      (positions-in-rect (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj))))
  (define (large? obj) (and (>= (obj-h obj) 3) (>= (obj-w obj) 3)))
  (define (exact? obj)
    (and (large? obj)
         (= (obj-size obj) (- (* 2 (+ (obj-h obj) (obj-w obj))) 4))
         (all? (lambda (p) (member p (border-cells obj))) (obj-cells obj))))
  (define (inside? p obj)
    (and (< (obj-r1 obj) (first p) (obj-r2 obj))
         (< (obj-c1 obj) (second p) (obj-c2 obj))))
  (define (contains? outer inner)
    (and (< (obj-r1 outer) (obj-r1 inner)) (< (obj-c1 outer) (obj-c1 inner))
         (> (obj-r2 outer) (obj-r2 inner)) (> (obj-c2 outer) (obj-c2 inner))))
  (define (touches? obj height width)
    (or (= (obj-r1 obj) 0) (= (obj-c1 obj) 0)
        (= (obj-r2 obj) (- height 1)) (= (obj-c2 obj) (- width 1))))
  (define (area obj) (* (obj-h obj) (obj-w obj)))
  (define (neighbors p)
    (list (list (- (first p) 1) (second p)) (list (+ (first p) 1) (second p))
          (list (first p) (- (second p) 1)) (list (first p) (+ (second p) 1))))
  (define (holes obj)
    (define mask (grid-from-fn (obj-h obj) (obj-w obj)
      (lambda (r c) (if (member (list (+ r (obj-r1 obj)) (+ c (obj-c1 obj)))
                                (obj-cells obj)) 0 1))))
    (filter (lambda (part) (not (touches? part (rows mask) (cols mask)))) (objects mask 0)))
  (define (loop? obj)
    (and (not (null? (holes obj)))
      (all? (lambda (p) (= 2 (length (filter (lambda (q) (member q (obj-cells obj)))
                                            (neighbors p))))) (obj-cells obj))))
"""

_SELECTION_RACKET = {
    "all_green": "#t",
    "any_hole": "(not (null? (holes obj)))",
    "closed_loop": "(loop? obj)",
    "rectangular_hole": "(any? (lambda (part) (= (obj-size part) (area part))) (holes obj))",
    "large_bbox": "(large? obj)",
    "size_at_least_8": "(>= (obj-size obj) 8)",
    "perimeter_size_only": "(and (large? obj) (= (obj-size obj) (- (* 2 (+ (obj-h obj) (obj-w obj))) 4)))",
    "border_subset": "(and (large? obj) (all? (lambda (p) (member p (border-cells obj))) (obj-cells obj)))",
    "border_complete": "(and (large? obj) (all? (lambda (p) (member p (obj-cells obj))) (border-cells obj)))",
    "solid_rectangles": "(and (large? obj) (= (obj-size obj) (area obj)))",
    "allow_thin_frames": "(and (= (obj-size obj) (length (border-cells obj))) (all? (lambda (p) (member p (border-cells obj))) (obj-cells obj)))",
    "minimum_4x4": "(and (exact? obj) (>= (obj-h obj) 4) (>= (obj-w obj) 4))",
    "square_only": "(and (exact? obj) (= (obj-h obj) (obj-w obj)))",
    "wide_only": "(and (exact? obj) (>= (obj-w obj) (obj-h obj)))",
    "tall_only": "(and (exact? obj) (>= (obj-h obj) (obj-w obj)))",
    "largest_only": "(and (exact? obj) (all? (lambda (other) (>= (area obj) (area other))) frames))",
    "smallest_only": "(and (exact? obj) (all? (lambda (other) (<= (area obj) (area other))) frames))",
    "first_only": "(and (not (null? frames)) (equal? obj (first frames)))",
    "last_only": "(and (not (null? frames)) (equal? obj (last frames)))",
    "empty_interiors": "(and (exact? obj) (not (any? (lambda (p) (inside? p obj)) (find-color g 3))))",
    "outermost_only": "(and (exact? obj) (not (any? (lambda (other) (contains? other obj)) frames)))",
    "innermost_only": "(and (exact? obj) (not (any? (lambda (other) (contains? obj other)) frames)))",
    "avoid_boundary": "(and (exact? obj) (not (touches? obj (rows g) (cols g))))",
}


def racket(mode, name=None):
    """An executable independent rule for the intended semantics or one rival."""
    _mode(mode)
    if name is not None and name not in bank(mode):
        raise ValueError("undeclared rival for mode")
    if name == "identity":
        return "(rule! (let () g))"
    if name == "opposite_completion":
        mode = "enclosed" if mode == "border" else "border"
    object_function = "objects-8" if name == "eight_neighbor_objects" else "objects"
    selector = _SELECTION_RACKET.get(name, "(exact? obj)")
    color = 2 if name == "red_frames" else (0 if name == "erase_frames" else 7)
    text = "(rule! (let ()\n" + _RACKET_COMMON
    text += f"  (define objs (filter (lambda (obj) (= (obj-color obj) 3)) ({object_function} g 0)))\n"
    text += "  (define frames (filter exact? objs))\n"
    text += f"  (define selected (filter (lambda (obj) {selector}) objs))\n"
    text += f"  (define staged (for/fold ((out g)) ((obj (in-list selected))) (paint-cells out (obj-cells obj) {color})))\n"
    if mode == "border":
        return text + "  staged))"
    if name == "bbox_interiors":
        text += "  (define candidates (apply append (map (lambda (obj) (filter (lambda (p) (inside? p obj)) (positions-in-rect (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj)))) selected)))\n"
    else:
        wall = "(or (= v 3) (= v 7))" if name == "all_green_walls" else ("(= v 3)" if name == "green_only_walls" else "(= v 7)")
        component_function = "objects-8" if name == "eight_neighbor_exterior" else "objects"
        exterior = "(touches? part (rows g) (cols g))"
        if name == "top_boundary_only":
            exterior = "(= (obj-r1 part) 0)"
        elif name == "corner_seed_only":
            exterior = "(member '(0 0) (obj-cells part))"
        wanted = exterior if name == "fill_outside" else f"(not {exterior})"
        text += f"  (define mask (grid-from-fn (rows g) (cols g) (lambda (r c) (let ((v (at staged r c))) (if {wall} 0 1)))))\n"
        text += f"  (define pockets (filter (lambda (part) {wanted}) ({component_function} mask 0)))\n"
        if name in ("largest_pocket", "smallest_pocket"):
            relation = ">=" if name == "largest_pocket" else "<="
            chosen = f"(filter (lambda (part) (all? (lambda (other) ({relation} (obj-size part) (obj-size other))) pockets)) pockets)"
        elif name == "rectangular_pockets":
            chosen = "(filter (lambda (part) (= (obj-size part) (area part))) pockets)"
        else:
            chosen = "pockets"
        text += f"  (define candidates (apply append (map obj-cells {chosen})))\n"
    paintable = "(= (at staged (first p) (second p)) 0)"
    if name == "overwrite_green":
        paintable = "(member (at staged (first p) (second p)) '(0 3))"
    if name == "one_layer_only":
        paintable = f"(and {paintable} (any? (lambda (q) (= (safe-at staged (first q) (second q) 0) 7)) (neighbors p)))"
    text += f"  (paint-cells staged (filter (lambda (p) {paintable}) candidates) 2)))"
    return text
