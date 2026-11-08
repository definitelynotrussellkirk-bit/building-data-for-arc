"""Reconstruct same-color corner boxes, rank their areas, then select fills.

Python outputs are claims. Protected Racket execution owns labels; the default
program is the byte-exact canonical source. Generated lessons use disjoint
interior-bearing rectangles, while the API preserves the broader executable
canonical behavior for blank grids, ignored colors, lines, and overlaps.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
POLICIES = ("outline", "largest", "smallest")
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"fill_policy"}:
        raise ValueError("settings must contain only fill_policy")
    policy = settings["fill_policy"]
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("unknown fill_policy")
    return policy


def _analyze(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or any(type(row) is not list for row in grid)
            or not 1 <= len(grid[0]) <= 30
            or any(len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
        raise ValueError("expected a rectangular literal-integer ARC grid at most 30x30")
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    boxes = []
    for color, cells in sorted(positions.items()):
        if len(cells) != 2:
            continue
        r0, r1 = sorted((cells[0][0], cells[1][0]))
        c0, c1 = sorted((cells[0][1], cells[1][1]))
        height, width = r1 - r0 + 1, c1 - c0 + 1
        boxes.append({"color": color, "bbox": [r0, c0, r1, c1],
                      "height": height, "width": width, "area": height * width,
                      "perimeter": 2 * (height + width)})
    return boxes


def _selected(boxes, policy):
    if policy == "outline" or not boxes:
        return set()
    target = (max if policy == "largest" else min)(b["area"] for b in boxes)
    return {b["color"] for b in boxes if b["area"] == target}


def apply_claim(grid, settings):
    policy = _settings(settings)
    boxes = _analyze(grid)
    selected = _selected(boxes, policy)
    output = [[0] * len(grid[0]) for _ in grid]
    # Canonical grid-colors is sorted ascending. Each later color overwrites
    # its own painted cells, without clearing any previously painted interior.
    for box in boxes:
        r0, c0, r1, c1 = box["bbox"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if box["color"] in selected or r in (r0, r1) or c in (c0, c1):
                    output[r][c] = box["color"]
    return output


_PRELUDE = r"""(rule! (lambda (g)
  (let ((h (rows g)) (w (cols g)))
    (define colors
      (filter (lambda (color) (= (length (find-color g color)) 2)) (grid-colors g 0)))
    (define (from-points color pts)
      (list color (apply min (map first pts)) (apply min (map second pts))
                  (apply max (map first pts)) (apply max (map second pts))))
    (define raw-boxes (map (lambda (color) (from-points color (find-color g color))) colors))
    (define (box-height box) (+ 1 (- (list-ref box 3) (list-ref box 1))))
    (define (box-width box) (+ 1 (- (list-ref box 4) (list-ref box 2))))
    (define (rectangle-area box) (* (box-height box) (box-width box)))
    (define (rectangle-perimeter box) (* 2 (+ (box-height box) (box-width box))))
    (define (inside? box r c)
      (and (<= (list-ref box 1) r (list-ref box 3))
           (<= (list-ref box 2) c (list-ref box 4))))
    (define (horizontal? box r) (or (= r (list-ref box 1)) (= r (list-ref box 3))))
    (define (vertical? box c) (or (= c (list-ref box 2)) (= c (list-ref box 4))))
"""


def _rule(policy, *, metric="area", ties="all", grouping="color",
          render="normal", skip_single=False, fixed_color=None,
          absolute_threshold=None, selector="extreme"):
    """Complete executable rules for the policies and finite teaching rivals."""
    if grouping == "global":
        boxes = """(if (empty? raw-boxes) '()
          (list (list (first (first raw-boxes))
            (apply min (map (lambda (b) (list-ref b 1)) raw-boxes))
            (apply min (map (lambda (b) (list-ref b 2)) raw-boxes))
            (apply max (map (lambda (b) (list-ref b 3)) raw-boxes))
            (apply max (map (lambda (b) (list-ref b 4)) raw-boxes)))))"""
    elif grouping == "reading_order":
        boxes = """(let ((pts (for*/list ((r (range 0 h)) (c (range 0 w))
                         #:when (member (at g r c) colors)) (list r c))))
          (map (lambda (i)
            (let ((a (list-ref pts i)) (b (list-ref pts (+ i 1))))
              (from-points (at g (first a) (second a)) (list a b))))
            (range 0 (length pts) 2)))"""
    elif grouping == "first":
        boxes = "(if (empty? raw-boxes) '() (list (first raw-boxes)))"
    elif grouping == "last":
        boxes = "(if (empty? raw-boxes) '() (list (last raw-boxes)))"
    else:
        boxes = "raw-boxes"
    score = {
        "area": "rectangle-area",
        "perimeter": "rectangle-perimeter",
        "height": "box-height",
        "width": "box-width",
        "span_area": "(lambda (box) (* (- (box-height box) 1) (- (box-width box) 1)))",
        "interior_area": "(lambda (box) (* (max 0 (- (box-height box) 2)) (max 0 (- (box-width box) 2))))",
        "diagonal_squared": "(lambda (box) (+ (* (box-height box) (box-height box)) (* (box-width box) (box-width box))))",
        "marker_count": "(lambda (box) 2)",
        "color": "first",
        "top": "(lambda (box) (list-ref box 1))",
        "left": "(lambda (box) (list-ref box 2))",
        "reading_order": "(lambda (box) (+ (* w (list-ref box 1)) (list-ref box 2)))",
    }[metric]
    extreme = "min" if policy == "smallest" else "max"
    selected = "'()" if policy == "outline" else """(filter
      (lambda (i) (= (list-ref scores i) target)) (range 0 (length boxes)))"""
    if policy == "all":
        selected = "(range 0 (length boxes))"
    if absolute_threshold is not None:
        compare = "<=" if policy == "smallest" else ">="
        selected = f"(filter (lambda (i) ({compare} (list-ref scores i) {absolute_threshold})) (range 0 (length boxes)))"
    if selector == "non_opposite":
        compare, opposite = ("<", "max") if policy == "smallest" else (">", "min")
        predicate = f"(or (= (apply min scores) (apply max scores)) ({compare} (list-ref scores i) (apply {opposite} scores)))"
        selected = f"(filter (lambda (i) {predicate}) (range 0 (length boxes)))"
    elif selector == "mean":
        compare = "<=" if policy == "smallest" else ">="
        selected = f"(filter (lambda (i) ({compare} (* (length scores) (list-ref scores i)) (apply + scores))) (range 0 (length boxes)))"
    elif selector == "median":
        compare = "<=" if policy == "smallest" else ">="
        index = "(quotient (- (length scores) 1) 2)" if policy == "smallest" else "(quotient (length scores) 2)"
        selected = f"(filter (lambda (i) ({compare} (list-ref scores i) (list-ref (sort scores <) {index}))) (range 0 (length boxes)))"
    if ties in ("first", "last"):
        selected = f"(let ((ids {selected})) (if (empty? ids) '() (list ({ties} ids))))"
    elif ties == "unique_only":
        selected = f"(let ((ids {selected})) (if (= (length ids) 1) ids '()))"
    if skip_single:
        selected = f"(if (= (length boxes) 1) '() {selected})"
    defs = _PRELUDE + f"""
    (define boxes {boxes})
    (define scores (map {score} boxes))
    (define target (if (empty? scores) 0 (apply {extreme} scores)))
    (define selected {selected})
"""
    edge = "(or (horizontal? box r) (vertical? box c))"
    fill = "(member i selected)"
    paint = f"(or {fill} {edge})"
    if render == "selected_only":
        paint = fill
    elif render == "interior_only":
        paint = f"(if {fill} (not {edge}) {edge})"
    elif render == "horizontal_only":
        paint = "(horizontal? box r)"
    elif render == "vertical_only":
        paint = "(vertical? box c)"
    value = str(fixed_color) if fixed_color is not None else "(first box)"
    return defs + f"""
    (grid-from-fn h w
      (lambda (r c)
        (for/fold ((value 0)) ((i (in-range (length boxes))))
          (let ((box (list-ref boxes i)))
            (if (and (inside? box r c) {paint}) {value} value))))))))"""


def program(settings):
    policy = _settings(settings)
    return CANONICAL if policy == "outline" else _rule(policy)


def rivals(settings):
    """Finite plausible rivals on the disjoint generated lesson grammar.

    Overlap-order alternatives are intentionally absent: that wider API
    behavior is checked by literal regressions, not generated lessons.
    """
    policy = _settings(settings)
    result = {
        "copy_markers": "(rule! (lambda (g) g))",
        "fill_every_rectangle": _rule("all"),
        "one_global_box": _rule(policy, grouping="global"),
        "pair_in_reading_order": _rule(policy, grouping="reading_order"),
        "first_color_rectangle_only": _rule(policy, grouping="first"),
        "last_color_rectangle_only": _rule(policy, grouping="last"),
        "horizontal_edges_only": _rule(policy, render="horizontal_only"),
        "vertical_edges_only": _rule(policy, render="vertical_only"),
        "paint_all_results_color_1": _rule(policy, fixed_color=1),
    }
    if policy != "outline":
        result.update({f"rank_by_{metric}": _rule(policy, metric=metric)
                       for metric in ("perimeter", "height", "width", "span_area",
                                      "interior_area", "diagonal_squared", "marker_count",
                                      "color", "top", "left", "reading_order")})
        result.update({"fill_first_tie_only": _rule(policy, ties="first"),
                       "fill_last_tie_only": _rule(policy, ties="last"),
                       "fill_unique_extreme_only": _rule(policy, ties="unique_only"),
                       "omit_unselected_outlines": _rule(policy, render="selected_only"),
                       "erase_selected_border": _rule(policy, render="interior_only"),
                       "do_not_fill_single_rectangle": _rule(policy, skip_single=True)})
        result.update({f"absolute_area_threshold_{cutoff}":
                       _rule(policy, absolute_threshold=cutoff)
                       for cutoff in (24, 35, 36, 40, 42)})
        result.update({"fill_all_except_opposite_extreme": _rule(policy, selector="non_opposite"),
                       "split_at_mean": _rule(policy, selector="mean"),
                       "split_at_median": _rule(policy, selector="median")})
    return result


def _sampler():
    path = HERE / "sampler.py"
    name = "_f7672a367745_inputs_" + hashlib.sha256(str(path).encode()).hexdigest()
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def generate(seed, settings, demos, queries):
    _settings(settings)
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    if type(demos) is not int or not 3 <= demos <= 6:
        raise ValueError("demos must be a literal integer in 3..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be a literal integer in 1..4")
    banks = _sampler().input_banks(seed)
    episode = {split: [{"input": deepcopy(grid), "output": apply_claim(grid, settings)}
                       for grid in banks[split][:count]]
               for split, count in (("train", demos), ("test", queries))}
    episode["program_solution"] = program(settings)
    return episode


def describe(grid, settings):
    policy = _settings(settings)
    boxes = _analyze(grid)
    output = apply_claim(grid, settings)
    return {"fill_policy": policy, "input_shape": [len(grid), len(grid[0])],
            "output_shape": [len(output), len(output[0])], "boxes": boxes,
            "selected_colors": sorted(_selected(boxes, policy)),
            "occupied_input_cells": sum(v != 0 for row in grid for v in row),
            "occupied_output_cells": sum(v != 0 for row in output for v in row),
            "changed_cells": sum(a != b for row, other in zip(grid, output) for a, b in zip(row, other))}


def public_turn(episode, index):
    if type(index) is not int or not 0 <= index < len(episode["test"]):
        raise ValueError("query index must select exactly one existing query")
    return {"train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])}
                      for p in episode["train"]],
            "test": [{"input": deepcopy(episode["test"][index]["input"])}]}
