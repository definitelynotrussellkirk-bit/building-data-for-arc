"""Native sampling/export boundary around the retained spiral-direction rules.

The original prototype owns both rule strings and the count-to-prefix mirror.
This module adds constructive short lessons, broad lawful geometry and strict
request/public boundaries. Protected Racket independently checks claim labels.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random

TASK_ID = "c1ae510562f9"
VERSION = "native-spiral-v2"
HOME = Path(__file__).resolve().parent
_path = HOME / "spiral_direction.py"
_name = "_retained_spiral_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)
SETTINGS = _legacy.ALLOWED_DIRECTIONS


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"spiral_direction"}
            or type(settings["spiral_direction"]) is not str
            or settings["spiral_direction"] not in SETTINGS):
        raise ValueError("settings must name exactly one declared spiral_direction string")
    return settings["spiral_direction"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in value)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return [row[:] for row in value]


def _analyze(grid):
    g = _grid(grid)
    if any(v not in (0, 5, 8) for row in g for v in row):
        raise ValueError("container grammar uses only black, gray and cyan")
    gray = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 5}
    if not gray:
        raise ValueError("missing gray container")
    top, floor = min(r for r, c in gray), max(r for r, c in gray)
    left, right = min(c for r, c in gray), max(c for r, c in gray)
    if floor <= top or right-left < 2:
        raise ValueError("container needs an interior row and column")
    expected = {(r, c) for r in range(top, floor+1) for c in (left, right)}
    expected |= {(floor, c) for c in range(left, right+1)}
    if gray != expected:
        raise ValueError("gray cells must form exactly one upright U with a floor")
    cyan = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 8}
    if not cyan or any(not (top <= r < floor and left < c < right) for r, c in cyan):
        raise ValueError("at least one cyan cell is required, entirely inside the container")
    interior = [row[left+1:right] for row in g[top:floor]]
    return g, (top, floor, left, right), interior, len(cyan), len(gray)


def program(settings):
    return _legacy.materialize_rule(_setting(settings))


def apply_claim(grid, settings):
    direction = _setting(settings)
    clean, _, _, _, _ = _analyze(grid)
    return _legacy.python_mirror(clean, direction)


def describe(grid, settings):
    direction = _setting(settings)
    clean, bounds, interior, cyan, gray = _analyze(grid)
    counts = [sum(v == 8 for v in row) for row in interior]
    empty = [bounds[0]+i for i, count in enumerate(counts) if count == 0]
    partial = [bounds[0]+i for i, count in enumerate(counts) if 0 < count < len(interior[0])]
    return {"input_shape": [len(clean), len(clean[0])], "output_shape": [3, 3],
            "interior_shape": [len(interior), len(interior[0])], "bounds": list(bounds),
            "empty_row_count": len(empty), "empty_row_indices": empty,
            "partial_row_indices": partial, "row_occupied_counts": counts,
            "cyan_cells": cyan, "gray_cells": gray,
            "output_cyan_count": min(len(empty), 9), "direction": direction}


def make_input(interior, *, top=0, left=0, pad_bottom=1, pad_right=1):
    """Construct a lawful U from an explicit 0/8 interior; useful for replays."""
    if (type(interior) is not list or not interior or type(interior[0]) is not list
            or not interior[0] or any(type(row) is not list or len(row) != len(interior[0])
              or any(type(v) is not int or v not in (0, 8) for v in row) for row in interior)):
        raise ValueError("interior must be a rectangular list of exact 0/8 cells")
    for name, value in (("top", top), ("left", left), ("pad_bottom", pad_bottom), ("pad_right", pad_right)):
        _integer(value, 0, 29, name)
    h, w = len(interior), len(interior[0])
    height, width = top+h+1+pad_bottom, left+w+2+pad_right
    if height > 30 or width > 30:
        raise ValueError("constructed canvas exceeds 30x30")
    g = [[0] * width for _ in range(height)]
    floor, right = top+h, left+w+1
    for r in range(top, floor+1):
        g[r][left] = g[r][right] = 5
    for c in range(left, right+1):
        g[floor][c] = 5
    for r, row in enumerate(interior):
        g[top+r][left+1:right] = row[:]
    _analyze(g)
    return g


def _rng(seed, split, slot):
    encoded = f"{TASK_ID}:{VERSION}:{seed}:{split}:{slot}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(encoded).digest(), "big"))


def _row(width, selected):
    return [8 if c in selected else 0 for c in range(width)]


def _contrast(slot, rng):
    width = rng.randint(2, 8)
    universe = set(range(width))
    if slot == 0:
        # Zero entirely empty rows, despite three zeros in every column.
        # Both singleton edges defeat dropping a strict-interior column.
        interior = [[0] * width for _ in range(6)]
        masks = ({0}, {width-1}, set(rng.sample(range(width), rng.randint(1, width-1))))
        for (first, last), mask in zip(((0,5), (1,4), (2,3)), masks):
            pair = (mask, universe-mask)
            if rng.choice((False, True)):
                pair = pair[::-1]
            interior[first], interior[last] = [_row(width, value) for value in pair]
    else:
        interior = [[0] * width for _ in range(7)]
        # Empty boundary rows reject omitting either endpoint from the crop.
        # A different zero-area/column deficit defeats fixed corrections.
        mask = set(rng.sample(range(width), rng.randint(1, width-1)))
        interior[1], interior[5] = _row(width, mask), _row(width, universe-mask)
    return interior


def _random_interior(height, width, empty, rng, *, dense=False):
    if not 0 <= empty < height:
        raise ValueError("count must leave at least one cyan row")
    empty_rows = set(rng.sample(range(height), empty))
    result = []
    for r in range(height):
        if r in empty_rows:
            result.append([0] * width)
        else:
            minimum = max(1, width//2) if dense else 1
            occupied = rng.randint(minimum, width)
            result.append(_row(width, set(rng.sample(range(width), occupied))))
    return result


def _place(interior, rng, *, teaching=False, full=False):
    if full:
        return make_input(interior, pad_bottom=0, pad_right=0)
    height_room = 29-len(interior)-1
    width_room = 29-len(interior[0])-2
    top = rng.randint(1 if teaching else 0, min(2, height_room))
    bottom = rng.randint(0, min(2, height_room-top))
    left = rng.randint(0, min(3, width_room))
    right = rng.randint(0, min(2, width_room-left))
    return make_input(interior, top=top, left=left, pad_bottom=bottom, pad_right=right)


def _inputs(seed):
    seen, train, test = set(), [], []
    for split, count, result in (("train", 6, train), ("test", 4, test)):
        for slot in range(count):
            rng = _rng(seed, split, slot)
            for _ in range(64):
                full = split == "test" and slot == 3
                if split == "train" and slot < 2:
                    interior = _contrast(slot, rng)
                elif split == "train" and slot == 2:
                    # Teach saturation; small-count-only lessons admit cap-six.
                    empty, occupied, width = rng.randint(9, 12), rng.randint(1, 4), rng.randint(1, 8)
                    interior = [[0]*width for _ in range(empty)] + [[8]*width for _ in range(occupied)]
                elif split == "train":
                    height, width = rng.randint(8, 18), rng.randint(2, 12)
                    interior = _random_interior(height, width, rng.randint(0, min(10, height-1)), rng)
                elif slot == 0:
                    empty = seed % 2
                    interior = _random_interior(rng.randint(empty+1, empty+3), rng.randint(1, 3), empty, rng)
                elif slot == 1:
                    height, width = rng.randint(12, 16), rng.randint(3, 12)
                    empty = 8 if seed % 2 == 0 else rng.randint(9, height-1)
                    interior = _random_interior(height, width, empty, rng)
                elif slot == 2:
                    interior = _random_interior(rng.randint(20, 26), rng.randint(15, 24), rng.randint(2, 7), rng, dense=True)
                else:
                    interior = _random_interior(29, 28, rng.randint(2, 7), rng, dense=True)
                grid = _place(interior, rng, teaching=split == "train" and slot < 3, full=full)
                identity = json.dumps(grid, separators=(",", ":"))
                if identity not in seen:
                    seen.add(identity)
                    result.append(grid)
                    break
            else:
                raise RuntimeError("bounded sampler could not produce distinct inputs")
    return train, test


def generate(seed, settings, demos=3, queries=4):
    _setting(settings)
    _integer(seed, 0, 2**63-1, "seed")
    _integer(demos, 3, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train, test = _inputs(seed)
    def pairs(grids):
        return [{"input": g, "output": apply_claim(g, settings)} for g in grids]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]),
            "program_solution": program(settings)}


def public_turn(episode, index):
    if type(episode) is not dict or type(episode.get("test")) is not list:
        raise ValueError("episode needs query pairs")
    _integer(index, 0, len(episode["test"])-1, "query index")
    if type(episode.get("train")) is not list or not episode["train"]:
        raise ValueError("episode needs demonstrations")
    try:
        return {"train": [{"input": _grid(p["input"]), "output": _grid(p["output"])} for p in episode["train"]],
                "test": [{"input": _grid(episode["test"][index]["input"])}]}
    except (TypeError, KeyError) as error:
        raise ValueError("malformed episode pairs") from error


_EMPTY = "(count-if row-empty? rs)"
_AREA = "(/ (for/sum ((r rs)) (count-if (lambda (c) (zero? (at g r c))) cs)) (length cs))"


def _rival_rule(direction, count, *, order=None):
    positions = _legacy._SPIRALS[direction] if order is None else order
    path = "(list " + " ".join(f"(list {r} {c})" for r, c in positions) + ")"
    return f"""(rule! (lambda (g)
      (let* ((gray (find-color g 5))
             (top (min-of fst gray)) (floor (max-of fst gray))
             (left (min-of snd gray)) (right (max-of snd gray))
             (rs (range top floor)) (cs (range (+ left 1) right))
             (row-empty? (lambda (r) (for/and ((c cs)) (zero? (at g r c)))))
             (n {count}) (path {path}))
        (build-grid 3 3 (r c)
          (let ((idx (find-first (lambda (i) (and (= r (fst (nth path i)))
                                                 (= c (snd (nth path i))))) (range 9))))
            (if (and idx (< idx n)) 8 0))))))"""


def rivals(settings):
    """Finite geometry, aggregation, boundary and output-order hypotheses."""
    direction = _setting(settings)
    opposite = next(value for value in SETTINGS if value != direction)
    counts = {
        "top_headroom": "(let ((occupied (filter (lambda (r) (not (row-empty? r))) rs))) (- (apply min occupied) top))",
        "zero_area_div_width": _AREA,
        "zero_area_minus_1": f"(- {_AREA} 1)",
        "zero_area_minus_2": f"(- {_AREA} 2)",
        "zero_area_minus_3": f"(- {_AREA} 3)",
        "zero_cells": "(for/sum ((r rs)) (count-if (lambda (c) (zero? (at g r c))) cs))",
        "any_zero_in_row": "(count-if (lambda (r) (for/or ((c cs)) (zero? (at g r c)))) rs)",
        "occupied_rows": f"(- (length rs) {_EMPTY})",
        "interior_height": "(length rs)",
        "empty_columns": "(count-if (lambda (c) (for/and ((r rs)) (zero? (at g r c)))) cs)",
        "whole_grid_empty_rows": "(count-if (lambda (values) (andmap zero? values)) g)",
        "omit_first_interior_row": "(count-if row-empty? (range (+ top 1) floor))",
        "omit_last_interior_row": "(count-if row-empty? (range top (- floor 1)))",
        "omit_left_interior_column": "(count-if (lambda (r) (for/and ((c (range (+ left 2) right))) (zero? (at g r c)))) rs)",
        "omit_right_interior_column": "(count-if (lambda (r) (for/and ((c (range (+ left 1) (- right 1)))) (zero? (at g r c)))) rs)",
        "include_exterior_top": "(count-if row-empty? (range (max 0 (- top 1)) floor))",
        "include_gray_walls": "(count-if (lambda (r) (for/and ((c (range left (+ right 1)))) (zero? (at g r c)))) rs)",
        "longest_empty_run": """(first (for/fold ((state (list 0 0))) ((r rs))
           (let ((next (if (row-empty? r) (+ 1 (list-ref state 1)) 0)))
             (list (max (first state) next) next))))""",
        "count_plus_one": f"(+ {_EMPTY} 1)",
        "count_minus_one": f"(- {_EMPTY} 1)",
        "constant_five": "5", "constant_six": "6",
    }
    for limit in range(9):
        counts[f"cap_at_{limit}"] = f"(min {limit} {_EMPTY})"
    for limit in range(1, 10):
        counts[f"floor_at_{limit}"] = f"(max {limit} {_EMPTY})"
    for label, column in (("left", "(+ left 1)"),
                          ("middle", "(+ left 1 (/ (length cs) 2))"),
                          ("right", "(- right 1)")):
        value = f"(count-if (lambda (r) (zero? (at g r {column}))) rs)"
        counts[label + "_column"] = value
        for offset in (1, 2, 3):
            counts[f"{label}_minus_{offset}"] = f"(- {value} {offset})"
    result = {name: _rival_rule(direction, count) for name, count in counts.items()}
    result["opposite_direction"] = program({"spiral_direction": opposite})
    result["row_major"] = _rival_rule(direction, _EMPTY, order=tuple((r, c) for r in range(3) for c in range(3)))
    result["snake_rows"] = _rival_rule(direction, _EMPTY,
        order=((0,0),(0,1),(0,2),(1,2),(1,1),(1,0),(2,0),(2,1),(2,2)))
    return result
