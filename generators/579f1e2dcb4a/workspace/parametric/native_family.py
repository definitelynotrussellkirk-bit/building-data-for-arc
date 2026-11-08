"""Pack original component crops in spatial or input-selected-color order.

The exact canonical source owns segmentation, raw crops and ordinary packing.
Python labels are claims independently replayed by native qualification/audit.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
POLICIES = ("spatial", "anchor_color_ascending", "anchor_color_descending")
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
_TAIL = "(let* ((comps (sort (e5b-nz-components g)"
if CANONICAL.count(_TAIL) != 1:
    raise ValueError("selected canonical helper/body boundary changed")
_PREFIX = CANONICAL.split(_TAIL)[0]
_DIR4_SOURCE = "(define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))"
_DIR8_SOURCE = "(define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1) (list -1 -1) (list -1 1) (list 1 -1) (list 1 1)))"
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"pack_order"}:
        raise ValueError("settings must contain only pack_order")
    policy = settings["pack_order"]
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("unknown pack_order")
    return policy


def _analyze(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or any(type(row) is not list for row in grid)
            or not 1 <= len(grid[0]) <= 30
            or any(len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
        raise ValueError("expected a rectangular literal-integer ARC grid at most 30x30")
    height, width = len(grid), len(grid[0])
    seen, components = set(), []
    for row in range(height):
        for col in range(width):
            if not grid[row][col] or (row, col) in seen:
                continue
            pending, cells = deque([(row, col)]), []
            seen.add((row, col))
            while pending:
                r, c = pending.popleft()
                cells.append((r, c))
                for dr, dc in DIRECTIONS:
                    nxt = (r + dr, c + dc)
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and grid[nxt[0]][nxt[1]] != 0 and nxt not in seen):
                        seen.add(nxt)
                        pending.append(nxt)
            top, left = min(r for r, _ in cells), min(c for _, c in cells)
            bottom, right = max(r for r, _ in cells), max(c for _, c in cells)
            # Raw subgrid is intentional: foreign component cells in the box
            # are retained by the selected canonical source.
            crop = [values[left:right + 1] for values in grid[top:bottom + 1]]
            components.append({"cells": tuple(sorted(cells)), "size": len(cells),
                               "top": top, "left": left, "height": bottom - top + 1,
                               "width": right - left + 1, "crop": crop,
                               "colors": Counter(grid[r][c] for r, c in cells)})
    if not 2 <= len(components) <= 6:
        raise ValueError("the shared grammar requires two through six nonzero 4-components")
    output_width = sum(c["width"] for c in components) + len(components) - 1
    if output_width > 30:
        raise ValueError("packed output width exceeds 30")
    largest = max(c["size"] for c in components)
    anchors = [c for c in components if c["size"] == largest]
    if len(anchors) != 1:
        raise ValueError("the largest occupied-area component must be unique")
    anchor = anchors[0]
    frequency = max(anchor["colors"].values())
    modes = [color for color, count in anchor["colors"].items() if count == frequency]
    if len(modes) != 1:
        raise ValueError("the largest component must have a unique modal nonzero color")
    return components, anchor, modes[0]


def apply_claim(grid, settings):
    policy = _settings(settings)
    components, _, key = _analyze(grid)
    if policy == "spatial":
        ordered = sorted(components, key=lambda c: (c["left"], c["top"]))
    else:
        direction = -1 if policy == "anchor_color_descending" else 1
        ordered = sorted(components, key=lambda c: (direction * c["colors"][key], c["left"], c["top"]))
    height = max(c["height"] for c in ordered)
    width = sum(c["width"] for c in ordered) + len(ordered) - 1
    output = [[0] * width for _ in range(height)]
    left = 0
    for component in ordered:
        for row, values in enumerate(component["crop"]):
            output[row][left:left + component["width"]] = values[:]
        left += component["width"] + 1
    return output


# All comparisons use integer cross-products. The protected bridge's / is
# integer division, so it must not be used to implement the density rival.
# Racket bbox-of-cells returns inclusive endpoints (r1,c1,r2,c2), unlike
# the explicit height/width fields in our Python component descriptions.
_HELPERS = r"""
 (define (spatial-key cells)
   (let ((b (bbox-of-cells cells))) (list (second b) (first b))))
 (define (spatial< a b) (e8b-list< (spatial-key a) (spatial-key b)))
 (define (values-of cells) (map (lambda (p) (at g (first p) (second p))) cells))
 (define (count-color cells color)
   (length (filter (lambda (p) (= (at g (first p) (second p)) color)) cells)))
 (define (mode-color cells)
   (argmax (lambda (color) (count-color cells color)) (range 1 10)))
 (define (bbox-area cells)
   (* (bbox-height cells) (bbox-width cells)))
 (define (bbox-height cells)
   (let ((b (bbox-of-cells cells))) (+ 1 (- (third b) (first b)))))
 (define (bbox-width cells)
   (let ((b (bbox-of-cells cells))) (+ 1 (- (fourth b) (second b)))))
 (define (perimeter cells)
   (apply + (map (lambda (p)
     (length (filter (lambda (d)
       (not (member? (list (+ (first p) (first d)) (+ (second p) (second d))) cells)))
       (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1))))) cells)))
 (define (box-cells cells)
   (let ((b (bbox-of-cells cells)))
     (filter (lambda (p) (not (= (at g (first p) (second p)) 0)))
       (for*/list ((r (in-range (first b) (+ 1 (third b))))
                   (c (in-range (second b) (+ 1 (fourth b))))) (list r c)))))
 (define (masked-crop cells)
   (let ((b (bbox-of-cells cells)))
     (for/fold ((out (empty-grid (bbox-height cells) (bbox-width cells) 0))) ((p (in-list cells)))
       (set-cell out (- (first p) (first b)) (- (second p) (second b))
         (at g (first p) (second p))))))
 (define (solid-crop cells)
   (let ((b (bbox-of-cells cells)))
     (empty-grid (bbox-height cells) (bbox-width cells) (apply min (values-of cells)))))
 (define (pack-variant crops gap bottom)
   (let* ((h (apply max (map rows crops)))
          (w (+ (apply + (map cols crops)) (* gap (- (length crops) 1)))))
     (let loop ((remaining crops) (left 0) (out (empty-grid h w 0)))
       (if (empty? remaining) out
         (let ((p (first remaining)))
           (loop (rest remaining) (+ left (cols p) gap)
             (e8b-paste out p (if bottom (- h (rows p)) 0) left)))))))
"""


def _rule(policy, *, selector="area", color_mode="own", fixed_color=None,
          count_basis="own", density=False, order=None, reverse_top_tie=False,
          crop_mode="raw", eight=False, gap=1, bottom=False):
    prefix = _PREFIX.replace(_DIR4_SOURCE, _DIR8_SOURCE, 1) if eight else _PREFIX
    anchor_expr = {
        "area": "(argmax length components)",
        "bbox": "(argmax bbox-area components)",
        "perimeter": "(argmax perimeter components)",
        "height": "(argmax bbox-height components)",
        "width": "(argmax bbox-width components)",
        "smallest": "(argmin length components)",
        "first_scan": "(first components)",
        "last_scan": "(last components)",
        "leftmost": "(first (sort components spatial<))",
        "same_color": "(argmax length (map obj-cells (objects g 0)))",
    }[selector]
    color_expr = {
        "own": "(mode-color anchor)",
        "global": "(mode-color (apply append components))",
        "raw_crop": "(mode-color (box-cells anchor))",
        "minority": "(argmin (lambda (c) (count-color anchor c)) (sort (remove-duplicates (values-of anchor)) <))",
        "minimum": "(apply min (values-of anchor))",
        "maximum": "(apply max (values-of anchor))",
    }[color_mode]
    if fixed_color is not None:
        color_expr = str(fixed_color)
    score_cells = "(box-cells cells)" if count_basis == "raw_crop" else "cells"
    tie = "(e8b-list< (list (first (spatial-key a)) (- (second (spatial-key a)))) (list (first (spatial-key b)) (- (second (spatial-key b)))))" if reverse_top_tie else "(spatial< a b)"
    defs = _HELPERS + f"""
 (define components (e5b-nz-components g))
 (define anchor {anchor_expr})
 (define key-color {color_expr})
 (define (score cells) (list (count-color {score_cells} key-color) {"(length cells)" if density else "1"}))
 (define (count< a b)
   (let* ((x (score a)) (y (score b))
          (left (* (first x) (second y))) (right (* (first y) (second x))))
     (if (= left right) {tie} ({">" if policy == "anchor_color_descending" else "<"} left right))))
"""
    if order in ("anchor_first", "anchor_last"):
        remaining = "(sort (filter (lambda (c) (not (equal? c anchor))) components) spatial<)"
        ordered = f"(cons anchor {remaining})" if order == "anchor_first" else f"(append {remaining} (list anchor))"
    else:
        keys = {
            "top_first": "(list (second (spatial-key cells)) (first (spatial-key cells)))",
            "right_to_left": "(list (- (first (spatial-key cells))) (second (spatial-key cells)))",
            "reverse_top": "(list (first (spatial-key cells)) (- (second (spatial-key cells))))",
            "color": "(append (list (apply min (values-of cells))) (spatial-key cells))",
            "area_ascending": "(append (list (length cells)) (spatial-key cells))",
            "area_descending": "(append (list (- (length cells))) (spatial-key cells))",
        }
        if order is not None:
            defs += f"(define (order-key cells) {keys[order]})\n"
            comparator = "(lambda (a b) (e8b-list< (order-key a) (order-key b)))"
        else:
            comparator = "spatial<" if policy == "spatial" else "count<"
        ordered = f"(sort components {comparator})"
    crop = {"raw": "(lambda (cells) (e5b-crop-cells g cells))",
            "masked": "masked-crop", "solid": "solid-crop"}[crop_mode]
    expression = f"(pack-variant (map {crop} {ordered}) {gap} {'#t' if bottom else '#f'})"
    return prefix + defs + expression + "))"


def program(settings):
    policy = _settings(settings)
    return CANONICAL if policy == "spatial" else _rule(policy)


def rivals(settings):
    """Additional finite rivals; audit.py separately includes other settings."""
    policy = _settings(settings)
    result = {"order_" + name: _rule("spatial", order=name) for name in
              ("top_first", "right_to_left", "reverse_top", "color", "area_ascending", "area_descending")}
    result.update({"eight_connected": _rule(policy, eight=True),
                   "masked_crops": _rule(policy, crop_mode="masked"),
                   "solid_crops": _rule(policy, crop_mode="solid"),
                   "bottom_alignment": _rule(policy, bottom=True),
                   "no_gap": _rule(policy, gap=0)})
    if policy != "spatial":
        result.update({"anchor_" + name: _rule(policy, selector=name) for name in
                       ("bbox", "perimeter", "height", "width", "smallest", "first_scan",
                        "last_scan", "leftmost", "same_color")})
        result.update({"color_" + name: _rule(policy, color_mode=name) for name in
                       ("global", "raw_crop", "minority", "minimum", "maximum")})
        result.update({f"fixed_color_{color}": _rule(policy, fixed_color=color) for color in range(1, 10)})
        result.update({"raw_crop_counts": _rule(policy, count_basis="raw_crop"),
                       "color_fraction": _rule(policy, density=True),
                       "reverse_top_tie": _rule(policy, reverse_top_tie=True),
                       "anchor_first": _rule(policy, order="anchor_first"),
                       "anchor_last": _rule(policy, order="anchor_last")})
    return result


def _sampler():
    path = HERE / "sampler.py"
    name = "_579f1e2dcb4a_inputs_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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
    components, anchor, key = _analyze(grid)
    output = apply_claim(grid, settings)
    return {"pack_order": policy, "input_shape": [len(grid), len(grid[0])],
            "output_shape": [len(output), len(output[0])],
            "components": [{"top": c["top"], "left": c["left"], "height": c["height"],
                            "width": c["width"], "size": c["size"],
                            "key_color_count": c["colors"][key],
                            "raw_crop_key_count": sum(v == key for row in c["crop"] for v in row),
                            "foreign_crop_cells": sum(v != 0 for row in c["crop"] for v in row) - c["size"]}
                           for c in components],
            "anchor_scan_index": components.index(anchor), "key_color": key,
            "anchor_histogram": dict(anchor["colors"]),
            "occupied_input_cells": sum(v != 0 for row in grid for v in row),
            "occupied_output_cells": sum(v != 0 for row in output for v in row)}


def public_turn(episode, index):
    if type(index) is not int or not 0 <= index < len(episode["test"]):
        raise ValueError("query index must select exactly one existing query")
    return {"train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])}
                      for p in episode["train"]],
            "test": [{"input": deepcopy(episode["test"][index]["input"])}]}
