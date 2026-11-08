"""Native D4 equality-matrix family with optional largest-block selection."""
from __future__ import annotations

from collections import Counter, deque
import hashlib
from math import ceil
from pathlib import Path
import random
from typing import Any, Callable, Iterable, Sequence

TASK_ID = "397767b9f88c"
DEFAULT = {"finish": "all_matches"}
SETTINGS = (
    {"finish": "all_matches"},
    {"finish": "largest_equivalence_blocks"},
)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_AXIS_TRANSFORMS = (0, 1, 2, 3, 4, 6)


def _setting(settings: Any = None) -> str:
    if settings is None:
        return "all_matches"
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    value = settings["finish"]
    if type(value) is not str or value not in {
        "all_matches", "largest_equivalence_blocks"
    }:
        raise ValueError("finish must be all_matches or largest_equivalence_blocks")
    return value


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not grid or len(grid) > 30
            or type(grid[0]) is not list or not grid[0] or len(grid[0]) > 30):
        raise ValueError("grid must be a rectangular 1..30 list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid must contain exact integer ARC colors")
    return [row[:] for row in grid]


def _norm(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dihedral(cells: Sequence[tuple[int, int]], transform: int) -> tuple[tuple[int, int], ...]:
    out: list[tuple[int, int]] = []
    for r, c in cells:
        if transform == 0:
            point = (r, c)
        elif transform == 1:
            point = (c, -r)
        elif transform == 2:
            point = (-r, -c)
        elif transform == 3:
            point = (-c, r)
        elif transform == 4:
            point = (r, -c)
        elif transform == 5:
            point = (-c, -r)
        elif transform == 6:
            point = (-r, c)
        elif transform == 7:
            point = (c, r)
        else:
            raise ValueError("dihedral transform must be 0..7")
        out.append(point)
    return _norm(out)


def _d4_key(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_dihedral(cells, transform) for transform in range(8))


def _rotation_key(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_dihedral(cells, transform) for transform in range(4))


def _axis_match(left: Sequence[tuple[int, int]], right: Sequence[tuple[int, int]]) -> bool:
    target = _norm(right)
    return any(_dihedral(left, transform) == target for transform in _AXIS_TRANSFORMS)


def _components(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    parts: list[dict[str, Any]] = []
    for r0 in range(height):
        for c0 in range(width):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    rr, cc = r + dr, c + dc
                    if (0 <= rr < height and 0 <= cc < width
                            and grid[rr][cc] != 0 and (rr, cc) not in seen):
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)
            shape = _norm(cells)
            parts.append({
                "cells": tuple(sorted(cells)),
                "shape": shape,
                "d4_key": _d4_key(shape),
                "rotation_key": _rotation_key(shape),
                "size": len(cells),
                "bbox": (bottom - top + 1, right - left + 1),
                "bbox_unordered": tuple(sorted((bottom - top + 1, right - left + 1))),
                "top_left": (top, left),
            })
    parts.sort(key=lambda part: part["top_left"])
    return parts


def equality_matrix(grid: Any) -> list[list[int]]:
    parts = _components(_grid(grid))
    if not parts:
        raise ValueError("input must contain at least one nonzero object")
    return [[2 if left["d4_key"] == right["d4_key"] else 0 for right in parts]
            for left in parts]


def _matrix_components(matrix: Sequence[Sequence[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(matrix), len(matrix[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if matrix[r][c] != 0}
    result: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells = [start]
        for r, c in cells:
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    cells.append(point)
        result.append(sorted(cells))
    return result


def _largest_blocks(matrix: Sequence[Sequence[int]]) -> list[list[int]]:
    parts = _matrix_components(matrix)
    largest = max((len(part) for part in parts), default=0)
    output = [[0] * len(matrix[0]) for _ in matrix]
    for part in parts:
        if len(part) == largest:
            for r, c in part:
                output[r][c] = 8
    return output


def transform(grid: Any, settings: Any = None) -> list[list[int]]:
    finish = _setting(settings)
    matrix = equality_matrix(grid)
    return _largest_blocks(matrix) if finish == "largest_equivalence_blocks" else matrix


def wrong_order_transform(grid: Any) -> list[list[int]]:
    """Counterfactual: select largest input objects before computing the matrix."""
    parts = _components(_grid(grid))
    largest = max(part["size"] for part in parts)
    return [[8 if (left["size"] == largest and right["size"] == largest
                   and left["d4_key"] == right["d4_key"]) else 0
             for right in parts] for left in parts]


def program(settings: Any = None) -> str:
    finish = _setting(settings)
    canonical = Path(__file__).with_name("canonical.rkt").read_text()
    if finish == "all_matches":
        return canonical
    stripped = canonical.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("canonical rule must be one rule! expression")
    body = stripped[len("(rule!"):-1].strip()
    return """(rule!
  (let* ((matrix %s)
         (parts (objects matrix 0))
         (largest (if (null? parts) 0 (apply max (map obj-size parts)))))
    (for/fold ((out (grid-from-fn (rows matrix) (cols matrix) (lambda (r c) 0))))
              ((obj (in-list parts)))
      (if (= (obj-size obj) largest)
          (paint-cells out (obj-cells obj) 8)
          out))))""" % body


def wrong_order_program() -> str:
    return """(rule!
  (let* ((mask (grid-from-fn (rows g) (cols g)
                 (lambda (r c) (if (= (at g r c) 0) 0 1))))
         (objs (sort (objects mask 0)
                     (lambda (a b)
                       (if (= (obj-r1 a) (obj-r1 b))
                           (< (obj-c1 a) (obj-c1 b))
                           (< (obj-r1 a) (obj-r1 b))))))
         (n (length objs))
         (largest (apply max (map obj-size objs))))
    (grid-from-fn n n
      (lambda (r c)
        (let ((left (nth objs r)) (right (nth objs c)))
          (if (and (= (obj-size left) largest)
                   (= (obj-size right) largest)
                   (match-transform (obj-cells left) (obj-cells right)))
              8 0))))))"""


# Small teaching shapes. A and B have the same area and unordered bbox but are
# distinct D4 classes. C is a larger distractor for the wrong-order witness.
_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "A": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "B": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "C": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 0), (3, 0)),
    "D": ((0, 0), (0, 1), (0, 2)),
    "E": ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
    # Five distinct area-eight shapes make the 30x30 case contain 80 cells.
    "G": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (2, 1), (3, 1)),
    "H": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2), (2, 1), (3, 1)),
    "I": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 2), (3, 2)),
    "J": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (3, 0)),
    "K": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (2, 1), (3, 1)),
}
if len({_d4_key(shape) for shape in _SHAPES.values()}) != len(_SHAPES):
    raise RuntimeError("shape bank contains duplicate D4 classes")


# (height, width, ordered class names). Equal names are contiguous so the
# canonical matrix exposes one 4-connected square block per equivalence class.
_SCENES = (
    (15, 18, ("A", "A", "A", "B", "B", "C")),
    (16, 20, ("A", "A", "B", "B", "C")),
    (18, 22, ("A", "A", "A", "A", "B", "C")),
    (20, 24, ("A", "A", "B", "B", "B", "C", "C")),
    (22, 26, ("A", "A", "A", "B", "B", "B", "C")),
    (24, 28, ("A", "A", "A", "A", "B", "B", "C", "D")),
    (12, 18, ("A", "A", "B", "C")),
    (18, 24, ("A", "A", "A", "B", "B", "B", "C", "C")),
    (26, 28, ("A", "A", "A", "A", "B", "B", "C", "C", "D")),
    (30, 30, ("G", "G", "G", "G", "G", "H", "H", "I", "J", "K")),
)


def _starts(span: int, count: int) -> list[int]:
    if count == 1:
        return [0]
    return [round(index * (span - 4) / (count - 1)) for index in range(count)]


def _anchors(height: int, width: int, count: int) -> list[tuple[int, int]]:
    columns = ceil(count / 2)
    rows = 1 if count <= columns else 2
    result = [(r, c) for r in _starts(height, rows) for c in _starts(width, columns)]
    return result[:count]


def _rng(seed: int, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:native-v1:{seed}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _scene(seed: int, index: int) -> list[list[int]]:
    height, width, classes = _SCENES[index]
    grid = [[0] * width for _ in range(height)]
    anchors = _anchors(height, width, len(classes))
    seen: Counter[str] = Counter()
    rng = _rng(seed, index)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    for object_index, (name, (top, left)) in enumerate(zip(classes, anchors)):
        occurrence = seen[name]
        seen[name] += 1
        transform_code = 0 if occurrence == 0 else 5 if occurrence == 1 else (2 * occurrence + object_index) % 8
        cells = _dihedral(_SHAPES[name], transform_code)
        colors = palette[:]
        rng.shuffle(colors)
        for cell_index, (r, c) in enumerate(cells):
            rr, cc = top + r, left + c
            if grid[rr][cc] != 0:
                raise RuntimeError("object slots overlap")
            grid[rr][cc] = colors[(cell_index + object_index) % len(colors)]
    observed = _components(grid)
    if len(observed) != len(classes):
        raise RuntimeError("object slots touch or split")
    expected = [_d4_key(_SHAPES[name]) for name in classes]
    if [part["d4_key"] for part in observed] != expected:
        raise RuntimeError("scene class ordering drifted")
    return grid


def has_diagonal_reflection_witness(grid: Any) -> bool:
    parts = _components(_grid(grid))
    for i, left in enumerate(parts):
        for right in parts[i + 1:]:
            if left["d4_key"] == right["d4_key"] and not _axis_match(left["shape"], right["shape"]):
                return True
    return False


def _inputs(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [_scene(seed, index) for index in range(6)]
    queries = [_scene(seed, index) for index in range(6, 10)]
    random.Random(int.from_bytes(hashlib.sha256(f"{TASK_ID}:query-order:{seed}".encode()).digest()[:16], "big")).shuffle(queries)
    return demos, queries


def _pairwise(grid: Any, predicate: Callable[[dict[str, Any], dict[str, Any]], bool], color: int = 2) -> list[list[int]]:
    parts = _components(_grid(grid))
    return [[color if predicate(left, right) else 0 for right in parts] for left in parts]


def semantic_rivals(settings: Any) -> dict[str, Callable[[Any], list[list[int]]]]:
    finish = _setting(settings)
    if finish == "all_matches":
        return {
            "diagonal_only": lambda grid: [[2 if i == j else 0 for j in range(len(_components(_grid(grid))))]
                                              for i in range(len(_components(_grid(grid))))],
            "all_equivalent": lambda grid: [[2] * len(_components(_grid(grid)))
                                              for _ in _components(_grid(grid))],
            "same_area": lambda grid: _pairwise(grid, lambda a, b: a["size"] == b["size"]),
            "same_bbox": lambda grid: _pairwise(grid, lambda a, b: a["bbox_unordered"] == b["bbox_unordered"]),
            "rotation_only": lambda grid: _pairwise(grid, lambda a, b: a["rotation_key"] == b["rotation_key"]),
            "axis_reflections_only": lambda grid: _pairwise(grid, lambda a, b: _axis_match(a["shape"], b["shape"])),
            "exact_orientation": lambda grid: _pairwise(grid, lambda a, b: a["shape"] == b["shape"]),
        }

    def all_blocks(grid: Any) -> list[list[int]]:
        return [[8 if value else 0 for value in row] for row in equality_matrix(grid)]

    def first_block(grid: Any) -> list[list[int]]:
        matrix = equality_matrix(grid)
        parts = _matrix_components(matrix)
        output = [[0] * len(matrix) for _ in matrix]
        if parts:
            for r, c in parts[0]:
                output[r][c] = 8
        return output

    def first_largest(grid: Any) -> list[list[int]]:
        matrix = equality_matrix(grid)
        parts = _matrix_components(matrix)
        largest = max(map(len, parts))
        output = [[0] * len(matrix) for _ in matrix]
        for part in parts:
            if len(part) == largest:
                for r, c in part:
                    output[r][c] = 8
                break
        return output

    return {
        "recolor_all_matches": all_blocks,
        "keep_first_block": first_block,
        "keep_first_largest_only": first_largest,
        "select_largest_input_objects_first": wrong_order_transform,
    }


def generate(seed: int, settings: Any = None, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    finish = _setting(settings)
    demos = _integer(demos, 3, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    setting = {"finish": finish}
    demo_inputs, query_inputs = _inputs(seed)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        source = [row[:] for row in grid]
        return {"input": source, "output": transform(source, setting)}

    return {
        "settings": setting.copy(),
        "program_solution": program(setting),
        "train": [pair(grid) for grid in demo_inputs[:demos]],
        "test": [pair(grid) for grid in query_inputs[:queries]],
    }
