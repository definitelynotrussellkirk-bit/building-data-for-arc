"""Opt-in crop/orient/rank/stack family; labels are verified by native Racket.

The canonical program remains an exact resource. The alternate ranks the
number of occupied cells on the TOP edge AFTER clockwise normalization.
Inputs are sampled independently of the private ranking setting. A bounded
two-demo set cover rejects the declared shortcuts for both settings together.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import combinations
import json
from pathlib import Path
import random


RANKINGS = ("perimeter", "normalized_top_edge")
_RIVALS = (
    "other_setting", "source_order", "reverse_source", "bbox_area", "ink",
    "normalized_width", "normalized_height", "source_top_edge",
    "normalized_bottom_edge", "top_span", "ascending", "reverse_ties",
    "counterclockwise", "no_rotation", "color_ascending", "color_descending",
)
_HOME = Path(__file__).resolve().parent
_NEIGHBORS = ((-1, 0), (0, -1), (0, 1), (1, 0))


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _ranking(settings):
    if (type(settings) is not dict or set(settings) != {"ranking"}
            or type(settings["ranking"]) is not str
            or settings["ranking"] not in RANKINGS):
        raise ValueError("settings must name ranking=perimeter|normalized_top_edge")
    return settings["ranking"]


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular 1..30 with exact colors 0..9")


def components(grid):
    """Same-color four-neighbor components in original row-major order."""
    _grid(grid)
    height, width = len(grid), len(grid[0])
    seen, result = set(), []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if not color or (row, col) in seen:
                continue
            pending, cells = [(row, col)], []
            seen.add((row, col))
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for dr, dc in _NEIGHBORS:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
            left, right = min(c for _, c in cells), max(c for _, c in cells)
            result.append({
                "color": color, "cells": sorted(cells), "top": top, "left": left,
                "height": bottom - top + 1, "width": right - left + 1,
                "bbox": [top, left, bottom, right],
                "crop": [line[left:right + 1] for line in grid[top:bottom + 1]],
            })
    if not result:
        raise ValueError("the input grammar requires at least one foreground object")
    return result


def _cw(shape):
    return [list(row) for row in zip(*shape[::-1])]


def _ccw(shape):
    return [list(row) for row in zip(*shape)][::-1]


def rival_names():
    return _RIVALS


def solve(grid, ranking="perimeter", rival=None):
    """Sampler-side claim only; protected Racket is the labeling authority."""
    _ranking({"ranking": ranking})
    if rival is not None and rival not in _RIVALS:
        raise ValueError("undeclared rival")
    selected = RANKINGS[1 - RANKINGS.index(ranking)] if rival == "other_setting" else ranking
    items = []
    for obj in components(grid):
        raw = obj["crop"]
        shape = raw
        if obj["height"] > obj["width"] and rival != "no_rotation":
            shape = _ccw(raw) if rival == "counterclockwise" else _cw(raw)
        score = (2 * (obj["height"] + obj["width"]) if selected == "perimeter"
                 else sum(v != 0 for v in shape[0]))
        if rival == "bbox_area":
            score = obj["height"] * obj["width"]
        elif rival == "ink":
            score = len(obj["cells"])
        elif rival == "normalized_width":
            score = len(shape[0])
        elif rival == "normalized_height":
            score = len(shape)
        elif rival == "source_top_edge":
            score = sum(v != 0 for v in raw[0])
        elif rival == "normalized_bottom_edge":
            score = sum(v != 0 for v in shape[-1])
        elif rival == "top_span":
            positions = [c for c, value in enumerate(shape[0]) if value]
            score = positions[-1] - positions[0] + 1
        top, left = obj["top"], obj["left"]
        key = (-score, top, left)
        if rival == "ascending":
            key = (score, top, left)
        elif rival == "reverse_ties":
            key = (-score, -top, -left)
        elif rival == "source_order":
            key = (top, left)
        elif rival == "reverse_source":
            key = (-top, -left)
        elif rival == "color_ascending":
            key = (obj["color"], top, left)
        elif rival == "color_descending":
            key = (-obj["color"], top, left)
        items.append((key, shape))
    shapes = [shape for _, shape in sorted(items, key=lambda item: item[0])]
    height = sum(len(shape) for shape in shapes) + len(shapes) - 1
    width = max(len(shape[0]) for shape in shapes)
    output = [[0] * width for _ in range(height)]
    top = 0
    for shape in shapes:
        for r, values in enumerate(shape):
            output[top + r][:len(values)] = values
        top += len(shape) + 1
    return output


def _racket_source(ranking, rival=None):
    selected = RANKINGS[1 - RANKINGS.index(ranking)] if rival == "other_setting" else ranking
    normalize = "(if (> (rows raw) (cols raw)) (rotate-cw raw) raw)"
    if rival == "counterclockwise":
        normalize = normalize.replace("rotate-cw", "rotate-ccw")
    elif rival == "no_rotation":
        normalize = "raw"
    score = ("(* 2 (+ (rows sub) (cols sub)))" if selected == "perimeter"
             else "(count-if (lambda (v) (not (= v 0))) (first sub))")
    scores = {
        "bbox_area": "(* (rows sub) (cols sub))",
        "ink": "(obj-size obj)",
        "normalized_width": "(cols sub)",
        "normalized_height": "(rows sub)",
        "source_top_edge": "(count-if (lambda (v) (not (= v 0))) (first raw))",
        "normalized_bottom_edge": "(count-if (lambda (v) (not (= v 0))) (last sub))",
        "top_span": "(let ((xs (filter (lambda (c) (not (= (at sub 0 c) 0))) (range 0 (cols sub))))) (+ 1 (- (apply max xs) (apply min xs))))",
        "color_ascending": "(obj-color obj)",
        "color_descending": "(obj-color obj)",
    }
    score = scores.get(rival, score)
    primary = "<" if rival in ("ascending", "color_ascending") else ">"
    tie = ">" if rival == "reverse_ties" else "<"
    compare = f"""(if (= (first a) (first b))
                     (if (= (second a) (second b))
                         ({tie} (third a) (third b))
                         ({tie} (second a) (second b)))
                     ({primary} (first a) (first b)))"""
    if rival in ("source_order", "reverse_source"):
        direction = "<" if rival == "source_order" else ">"
        compare = f"""(if (= (second a) (second b))
                          ({direction} (third a) (third b))
                          ({direction} (second a) (second b)))"""
    return f"""(rule!
  ;; Crop same-color objects and orient tall crops clockwise.
  ;; Rank by {selected}; ties use original source position.
  ;; Stack the normalized crops left-aligned with one zero row between them.
  ;; Variant/rival: {rival or 'intended'}.
  (lambda (g)
    (let* ((items
            (sort
              (map (lambda (obj)
                     (let* ((raw (subgrid g (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj)))
                            (sub {normalize})
                            (score {score}))
                       (list score (obj-r1 obj) (obj-c1 obj) sub)))
                   (objects g 0))
              (lambda (a b) {compare})))
           (shapes (map fourth items))
           (out-h (+ (apply + (map rows shapes)) (- (length shapes) 1)))
           (out-w (apply max (map cols shapes))))
      (let pack ((remaining shapes) (top 0) (out (empty-grid out-h out-w 0)))
        (if (empty? remaining)
            out
            (let* ((shape (first remaining))
                   (next (for*/fold ((acc out))
                                   ((r (in-range (rows shape))) (c (in-range (cols shape))))
                           (let ((value (at shape r c)))
                             (if (= value 0) acc (set-cell acc (+ top r) c value))))))
              (pack (rest remaining) (+ top (rows shape) 1) next)))))))"""


def program(settings):
    ranking = _ranking(settings)
    if ranking == "perimeter":
        return (_HOME / "canonical.rkt").read_text(encoding="utf-8")
    return _racket_source(ranking)


def rival_program(ranking, rival):
    _ranking({"ranking": ranking})
    if rival not in _RIVALS:
        raise ValueError("undeclared rival")
    if rival == "other_setting":
        return program({"ranking": RANKINGS[1 - RANKINGS.index(ranking)]})
    return _racket_source(ranking, rival)


def _rng(seed, label):
    # This stream intentionally has no parameter settings or requested counts.
    digest = hashlib.sha256(f"ef03216cf2fa-edge-v1:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _shape(rng, short, long):
    """Connected shapes with independently varying edge occupancy and density."""
    mode = rng.randrange(5)
    shape = [[0] * long for _ in range(short)]
    if mode == 0:  # hollow frame, sometimes with a single interior spur
        for r in range(short):
            for c in range(long):
                if r in (0, short - 1) or c in (0, long - 1):
                    shape[r][c] = 1
        if short > 2 and long > 2 and rng.randrange(2):
            shape[1][1] = 1
    elif mode == 1:  # a sparse spanning cross plus connected detail
        spine, bridge = rng.randrange(long), rng.randrange(short)
        for r in range(short):
            shape[r][spine] = 1
        shape[bridge] = [1] * long
        for _ in range(rng.randrange(long + 1)):
            r, c = rng.randrange(short), rng.randrange(long)
            if any(0 <= r + dr < short and 0 <= c + dc < long
                   and shape[r + dr][c + dc] for dr, dc in _NEIGHBORS):
                shape[r][c] = 1
    elif mode == 2:  # asymmetric corner-L, retaining the original shape family
        edge_r, edge_c = rng.choice((0, short - 1)), rng.choice((0, long - 1))
        shape[edge_r] = [1] * long
        for r in range(short):
            shape[r][edge_c] = 1
        if short > 2 and long > 2:
            shape[1][1 if edge_c == 0 else long - 2] = 1
            shape[1][edge_c] = 1
    else:  # combs/dense bridges: split top edge count differs from span
        for r in range(1, short - 1):
            shape[r] = [1] * long
        if short == 2:
            shape[1] = [1] * long
        for r in ([0] if short == 2 else [0, short - 1]):
            count = rng.randint(1, long)
            for c in rng.sample(range(long), count):
                shape[r][c] = 1
    return shape


def _scene(seed, label, height, width, count):
    rng = _rng(seed, label)
    columns = 2 if count <= 4 else 3
    slots = [(r, c) for r in range(2) for c in range(columns)]
    if count < len(slots):
        # Keep both distant corners represented even for the smallest scene.
        middle = slots[1:-1]
        rng.shuffle(middle)
        slots = [slots[0], *middle[:count - 2], slots[-1]]
    rng.shuffle(slots)
    colors = rng.sample(range(1, 10), count)
    tall_indices = set(rng.sample(range(count), max(1, count // 2)))
    grid = [[0] * width for _ in range(height)]
    for index, ((band_r, band_c), color) in enumerate(zip(slots, colors)):
        r0, r1 = band_r * height // 2, (band_r + 1) * height // 2
        c0, c1 = band_c * width // columns, (band_c + 1) * width // columns
        available_h = r1 - r0 - (1 if band_r == 0 else 0)
        available_w = c1 - c0 - (1 if band_c + 1 < columns else 0)
        tall = index in tall_indices
        short = rng.randint(2, min(4, available_w if tall else available_h))
        max_long = available_h if tall else available_w
        if max_long <= short:
            short = max(2, max_long - 1)
        min_long = max(short + 1, (max_long * 2 // 3) if height >= 24 else 3)
        long = rng.randint(min_long, max_long)
        normalized = _shape(rng, short, long)
        source = _ccw(normalized) if tall else normalized
        box_h, box_w = len(source), len(source[0])
        top = rng.randint(r0, r0 + available_h - box_h)
        left = rng.randint(c0, c0 + available_w - box_w)
        # Actual object contact, not just a large blank canvas.
        if (band_r, band_c) == (0, 0):
            top, left = 0, 0
        if (band_r, band_c) == (1, columns - 1):
            top, left = height - box_h, width - box_w
        for r, row in enumerate(source):
            for c, occupied in enumerate(row):
                if occupied:
                    grid[top + r][left + c] = color
    if len(components(grid)) != count:
        raise RuntimeError("internal shape connectivity failure")
    return grid


@lru_cache(maxsize=32)
def _teaching_inputs(seed):
    """Choose a two-demo cover from at most 48 shared candidate scenes.

    Coverage is computed before any query is sampled. Both settings' targets
    share the same cover, so input selection cannot reveal the private choice.
    """
    universe = {(ranking, rival) for ranking in RANKINGS for rival in _RIVALS}
    candidates, coverage = [], []
    for index in range(48):
        shape = (12, 14) if index % 2 == 0 else (16, 16)
        grid = _scene(seed, f"teaching:{index}", *shape, 4)
        covered = set()
        for ranking in RANKINGS:
            wanted = solve(grid, ranking)
            for rival in _RIVALS:
                if solve(grid, ranking, rival) != wanted:
                    covered.add((ranking, rival))
        candidates.append(grid)
        coverage.append(covered)
        for previous in range(index):
            if coverage[previous] | covered == universe:
                return (candidates[previous], grid, {
                    "candidates_examined": index + 1,
                    "selected_candidates": [previous, index],
                    "rival_comparisons_covered": len(universe),
                })
    missing = universe - set().union(*coverage)
    raise RuntimeError(f"bounded two-demo cover failed; missing={sorted(missing)}")


def generate(seed, settings, demos=3, queries=4):
    """Generate a deterministic lesson; native worker executes its claims."""
    _integer(seed, 0, 2**63 - 1, "seed")
    ranking = _ranking(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    first, second, teaching = _teaching_inputs(seed)
    train_inputs = [deepcopy(first), deepcopy(second)]
    for index in range(2, demos):
        train_inputs.append(_scene(seed, f"extra-demo:{index}", 14, 16, 4))
    profiles = ((10, 12, 3), (16, 20, 4), (24, 25, 5), (30, 30, 6))
    test_inputs = [_scene(seed, f"query:{index}", *profiles[index]) for index in range(queries)]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in train_inputs + test_inputs]
    if len(set(serialized)) != len(serialized):
        raise RuntimeError("duplicate demonstration/query input; no short episode emitted")
    pairs = lambda grids: [{"input": grid, "output": solve(grid, ranking)} for grid in grids]
    train, test = pairs(train_inputs), pairs(test_inputs)
    for pair in train + test:
        _grid(pair["output"])
    return {"train": train, "test": test, "program_solution": program(settings),
            "settings": deepcopy(settings), "seed": seed,
            "teaching": deepcopy(teaching),
            "label_status": "python_claims_require_protected_racket_execution"}
