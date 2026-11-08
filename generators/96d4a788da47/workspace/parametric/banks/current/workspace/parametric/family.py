"""Matched-input object-to-edge family for ARC task 96d4a788da47.

The exact canonical setting moves each input object to the left edge.  The
alternative settings move every object to the right edge, or choose the nearer
horizontal edge independently for each object.  The sampler keeps objects in
separate row bands, uses irregular connected shapes, and always contains both a
left-near and a right-near object so all three settings are observable.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "96d4a788da47"
EDGES = ("left", "right", "nearest")
SETTINGS = tuple({"destination_edge": value} for value in EDGES)
DEMO_SIZES = ((12, 14), (13, 16), (15, 18), (18, 20), (21, 24), (24, 27))
QUERY_SIZES = ((30, 30), (24, 30), (30, 24), (27, 29))

# Every shape is connected, tight-normalized, three rows high, irregular, and
# contains at least eight cells.  Three objects therefore make the 30x30 stress
# substantive without turning the task into a texture-copy exercise.
_SHAPES = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 0), (0, 3), (1, 0), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2), (2, 3)),
    ((0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 1), (2, 3)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (1, 3), (2, 2), (2, 3)),
)


def _settings(settings) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"destination_edge"}
        or type(settings["destination_edge"]) is not str
        or settings["destination_edge"] not in EDGES
    ):
        raise ValueError("settings must be exactly destination_edge=left|right|nearest")
    return settings["destination_edge"]


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(grid) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must be a list with 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    rows = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular list-of-lists")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid cells must be exact integer ARC colors 0..9")
        rows.append(list(row))
    return rows


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape cannot be empty")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_size(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    todo = list(seen)
    while todo:
        r, c = todo.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                todo.append(neighbor)
    return seen == cells


def _rng(seed: int, split: str, index: int, label: str) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{split}:{index}:{label}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _objects(grid) -> tuple[dict, ...]:
    rows = _grid(grid)
    height, width = len(rows), len(rows[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if rows[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        color = rows[start[0]][start[1]]
        cells = {start}
        unseen.remove(start)
        todo = [start]
        while todo:
            r, c = todo.pop()
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in unseen and rows[q[0]][q[1]] == color:
                    unseen.remove(q)
                    cells.add(q)
                    todo.append(q)
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        r1 = max(r for r, _ in cells)
        c1 = max(c for _, c in cells)
        result.append({
            "color": color,
            "cells": tuple(sorted(cells)),
            "bbox": (r0, c0, r1, c1),
        })
    return tuple(sorted(result, key=lambda obj: (obj["bbox"], obj["color"])))


def _row_starts(height: int) -> tuple[int, int, int]:
    middle = (height - 3) // 2
    starts = (0, middle, height - 3)
    if not (starts[0] + 3 < starts[1] and starts[1] + 3 < starts[2] + 1):
        raise ValueError("height is too small for three separated row bands")
    return starts


def sample_input(seed: int, split: str, index: int, *, height: int, width: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("demo", "query"):
        raise ValueError("split must be demo or query")
    _integer(index, 0, 63, "index")
    _integer(height, 12, 30, "height")
    _integer(width, 12, 30, "width")

    shape_rng = _rng(seed, split, index, "shapes")
    shape_indices = list(range(len(_SHAPES)))
    shape_rng.shuffle(shape_indices)
    shapes = [_normalize(_SHAPES[i]) for i in shape_indices[:3]]
    starts = _row_starts(height)

    color_rng = _rng(seed, split, index, "colors")
    colors = list(range(1, 10))
    color_rng.shuffle(colors)
    colors = colors[:3]

    # One object is provably nearer the left edge, one nearer the right edge,
    # and one is an input-dependent interior distractor.  All remain one cell
    # away from an edge so the input is never already a setting output.
    widths = [_shape_size(shape)[1] for shape in shapes]
    left_origin = 1
    right_origin = width - widths[1] - 1
    interior_low = 3
    interior_high = width - widths[2] - 3
    if interior_low > interior_high:
        interior_origin = max(2, (width - widths[2]) // 2)
    else:
        interior_origin = _rng(seed, split, index, "interior").randint(interior_low, interior_high)
    origins = (left_origin, right_origin, interior_origin)

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for shape, color, top, left in zip(shapes, colors, starts, origins):
        for dr, dc in shape:
            if grid[top + dr][left + dc] != 0:
                raise RuntimeError("constructive row bands unexpectedly overlap")
            grid[top + dr][left + dc] = color

    facts = analyze(grid)
    if not facts["valid_for_all_settings"] or not facts["setting_outputs_distinct"]:
        raise RuntimeError("constructed scene failed its own parametric grammar")
    return grid


def _shift_for(obj: dict, width: int, mode: str) -> int:
    _, c0, _, c1 = obj["bbox"]
    right_gap = width - 1 - c1
    if mode == "left":
        return -c0
    if mode == "right":
        return right_gap
    if mode == "nearest":
        return -c0 if c0 <= right_gap else right_gap
    raise ValueError(mode)


def solve(grid, settings) -> list[list[int]]:
    mode = _settings(settings)
    rows = _grid(grid)
    height, width = len(rows), len(rows[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for obj in _objects(rows):
        dc = _shift_for(obj, width, mode)
        for r, c in obj["cells"]:
            cc = c + dc
            if not 0 <= cc < width:
                raise ValueError("object translation left the canvas")
            if out[r][cc] != 0:
                raise ValueError("object translations collide")
            out[r][cc] = obj["color"]
    return out


def solve_with_constant_shift(grid, shift: int) -> list[list[int]]:
    _integer(shift, -30, 30, "shift")
    rows = _grid(grid)
    height, width = len(rows), len(rows[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for obj in _objects(rows):
        for r, c in obj["cells"]:
            cc = c + shift
            if 0 <= cc < width:
                if out[r][cc] != 0:
                    raise ValueError("constant-shift objects collide")
                out[r][cc] = obj["color"]
    return out


def analyze(grid) -> dict:
    rows = _grid(grid)
    height, width = len(rows), len(rows[0])
    objects = _objects(rows)
    colors = [obj["color"] for obj in objects]
    row_spans = [(obj["bbox"][0], obj["bbox"][2]) for obj in objects]
    separated = all(a1 < b0 or b1 < a0
                    for i, (a0, a1) in enumerate(row_spans)
                    for b0, b1 in row_spans[i + 1:])
    irregular = sum(
        len(obj["cells"])
        != (obj["bbox"][2] - obj["bbox"][0] + 1)
        * (obj["bbox"][3] - obj["bbox"][1] + 1)
        for obj in objects
    )
    nearest_left = sum(
        obj["bbox"][1] <= width - 1 - obj["bbox"][3]
        for obj in objects
    )
    nearest_right = len(objects) - nearest_left
    valid = (
        len(objects) >= 3
        and len(colors) == len(set(colors))
        and separated
        and irregular >= 2
        and nearest_left >= 1
        and nearest_right >= 1
        and all(obj["bbox"][1] >= 1 and obj["bbox"][3] <= width - 2 for obj in objects)
        and all(_connected(obj["cells"]) for obj in objects)
    )
    outputs = [solve(rows, setting) for setting in SETTINGS] if valid else []
    return {
        "height": height,
        "width": width,
        "object_count": len(objects),
        "irregular_object_count": irregular,
        "nearest_left_count": nearest_left,
        "nearest_right_count": nearest_right,
        "setting_outputs_distinct": len({json.dumps(output) for output in outputs}) == len(SETTINGS),
        "valid_for_all_settings": bool(valid),
    }


def program(settings) -> str:
    mode = _settings(settings)
    name = {"left": "canonical.rkt", "right": "right.rkt", "nearest": "nearest.rkt"}[mode]
    return Path(__file__).resolve().with_name(name).read_text(encoding="utf-8")


def generate(seed, settings, demos=2, queries=4) -> dict:
    _settings(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train_inputs = [
        sample_input(seed, "demo", i, height=h, width=w)
        for i, (h, w) in enumerate(DEMO_SIZES[:demos])
    ]
    query_bank = [
        sample_input(seed, "query", i, height=h, width=w)
        for i, (h, w) in enumerate(QUERY_SIZES)
    ]
    return {
        "train": [{"input": grid, "output": solve(grid, settings)} for grid in train_inputs],
        "test": [{"input": grid, "output": solve(grid, settings)} for grid in query_bank[:queries]],
        "program_solution": program(settings),
    }


def public_turn(episode, query_index=0) -> dict:
    if type(query_index) is not int:
        raise ValueError("query_index must be an exact integer")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("episode needs visible train pairs and the selected query")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }


def _rival_constant_shift_one() -> str:
    return Path(__file__).resolve().with_name("constant_shift_1.rkt").read_text(encoding="utf-8")


def _rival_bbox_fill(mode: str) -> str:
    target = {
        "left": "0",
        "right": "(- (cols g) (+ 1 (- c1 c0)))",
        "nearest": "(if (<= c0 (- (- (cols g) 1) c1)) 0 (- (cols g) (+ 1 (- c1 c0))))",
    }[mode]
    return f"""(rule!
  (let ((dummy 0))
    (for/fold ((out (empty-grid (rows g) (cols g) 0)))
              ((obj (in-list (objects g 0))))
      (let* ((bb (obj-bbox obj))
             (r0 (first bb)) (c0 (second bb))
             (r1 (third bb)) (c1 (fourth bb))
             (tc {target}))
        (paint-cells out
                     (positions-in-rect r0 tc r1 (+ tc (- c1 c0)))
                     (obj-color obj))))))"""


def _rival_global_leftmost(mode: str) -> str:
    # A plausible shortcut: infer one horizontal shift from the first object and
    # apply it to every object, rather than measuring each bounding box.
    target = {
        "left": "(- 0 (second (obj-bbox first-obj)))",
        "right": "(- (- (cols g) 1) (fourth (obj-bbox first-obj)))",
        "nearest": "(let* ((bb (obj-bbox first-obj)) (c0 (second bb)) (c1 (fourth bb)) (rg (- (- (cols g) 1) c1))) (if (<= c0 rg) (- 0 c0) rg))",
    }[mode]
    return f"""(rule!
  (let ((dummy 0))
    (define objs (objects g 0))
    (define first-obj (first objs))
    (define dc {target})
    (for/fold ((out (empty-grid (rows g) (cols g) 0)))
              ((obj (in-list objs)))
      (paint-cells out
                   (map (lambda (p) (list (first p) (+ (second p) dc)))
                        (obj-cells obj))
                   (obj-color obj)))))"""


def rival_programs(settings) -> dict[str, str]:
    mode = _settings(settings)
    result = {
        "constant_shift_one": _rival_constant_shift_one(),
        "filled_bbox": _rival_bbox_fill(mode),
        "single_global_shift": _rival_global_leftmost(mode),
        "preserve_input": "(rule! (let ((dummy 0)) g))",
    }
    for other in SETTINGS:
        other_mode = other["destination_edge"]
        if other_mode != mode:
            result[f"other_setting_{other_mode}"] = program(other)
    return result
