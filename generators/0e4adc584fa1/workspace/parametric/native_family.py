"""Object-selected control variants for ARC task 0e4adc584fa1.

The canonical setting keeps the selected Racket source byte-for-byte: remove
all isolated 1..4 controls, crop the remaining object, and rotate by the last
control in row-major order.  The alternate setting first measures the object's
bounding box, selects the isolated control with minimum Manhattan distance to
that box, and then uses the selected control code for the same crop/rotation.

The input plan is independent of the private setting.  A six-demo/four-query
plan is generated once and sliced, so counts are prefix stable and a one-query
first turn is byte-identical to the first turn of a four-query lesson.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import random
from pathlib import Path
from typing import Iterable, Sequence


TASK_ID = "0e4adc584fa1"
HOME = Path(__file__).resolve().parent
SETTINGS = (
    {"control_selector": "last_isolated"},
    {"control_selector": "nearest_object"},
)
DEFAULT = {"control_selector": "last_isolated"}

# canvas height, canvas width, object bbox height, object bbox width
_DEMO_PROFILES = (
    (10, 12, 5, 7),
    (12, 14, 7, 8),
    (16, 18, 9, 11),
    (20, 22, 12, 14),
    (24, 26, 15, 18),
    (28, 30, 19, 22),
)
_QUERY_PROFILES = (
    (13, 15, 7, 9),
    (18, 20, 10, 12),
    (25, 27, 16, 19),
    (30, 30, 22, 22),
)
_NEAR_CODES = (2, 3, 1, 4, 2, 4, 3, 1, 2, 3)
_LAST_CODES = (4, 1, 3, 2, 3, 2, 1, 4, 1, 4)
_FIRST_CODES = (1, 4, 2, 3, 1, 3, 4, 2, 4, 2)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

_NEAREST_PROGRAM = r"""(rule! (let ((dummy 0))
  (define dirs4 (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
  (define (e11b-transform-code grid code)
    (cond ((= code 1) grid)
          ((= code 2) (rotate-cw grid))
          ((= code 3) (rotate-180 grid))
          ((= code 4) (rotate-ccw grid))
          ((= code 5) (flip-lr grid))
          ((= code 6) (flip-ud grid))
          (else grid)))
  (define (distance-to-bbox p bb)
    (+ (cond ((< (first p) (first bb)) (- (first bb) (first p)))
             ((> (first p) (third bb)) (- (first p) (third bb)))
             (else 0))
       (cond ((< (second p) (second bb)) (- (second bb) (second p)))
             ((> (second p) (fourth bb)) (- (second p) (fourth bb)))
             (else 0))))
  (let* ((isolated
           (filter
             (lambda (p)
               (let ((v (at g (first p) (second p))))
                 (and (member? v (list 1 2 3 4))
                      (= (length
                           (filter
                             (lambda (d)
                               (let ((rr (+ (first p) (first d)))
                                     (cc (+ (second p) (second d))))
                                 (and (in-bounds? rr cc (rows g) (cols g))
                                      (not (= (at g rr cc) 0)))))
                             dirs4))
                         0))))
             (grid-positions g)))
         (cells
           (filter
             (lambda (p)
               (and (not (= (at g (first p) (second p)) 0))
                    (not (member? p isolated))))
             (grid-positions g))))
    (if (or (empty? isolated) (empty? cells))
        (list (list 0))
        (let* ((bb (bbox-of-cells cells))
               (selected
                 (for/fold ((best (first isolated)))
                           ((p (in-list (rest isolated))))
                   (if (< (distance-to-bbox p bb)
                          (distance-to-bbox best bb))
                       p
                       best)))
               (control (at g (first selected) (second selected))))
          (e11b-transform-code
            (subgrid g (first bb) (second bb) (third bb) (fourth bb))
            control))))))"""


def _selector(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"control_selector"}:
        raise ValueError("settings must contain exactly control_selector")
    value = settings["control_selector"]
    if type(value) is not str:
        raise TypeError("control_selector must be a string")
    if value not in ("last_isolated", "nearest_object"):
        raise ValueError("control_selector must be last_isolated|nearest_object")
    return value


def setting_name(settings: object) -> str:
    return _selector(settings)


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def program(settings: object) -> str:
    selector = _selector(settings)
    if selector == "last_isolated":
        return (HOME / "canonical.rkt").read_text(encoding="utf-8")
    return _NEAREST_PROGRAM


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid dimensions must be in 1..30")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with literal colors 0..9")
    return deepcopy(value)


def _isolated_controls(grid: Sequence[Sequence[int]]) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    result: list[tuple[int, int]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] not in (1, 2, 3, 4):
                continue
            if all(
                not (0 <= row + dr < height and 0 <= col + dc < width)
                or grid[row + dr][col + dc] == 0
                for dr, dc in _DIR4
            ):
                result.append((row, col))
    return result


def _object_cells(
    grid: Sequence[Sequence[int]], controls: Iterable[tuple[int, int]]
) -> list[tuple[int, int]]:
    control_set = set(controls)
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) not in control_set
    ]


def _bbox(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _col in cells),
        min(col for _row, col in cells),
        max(row for row, _col in cells),
        max(col for _row, col in cells),
    )


def _distance_to_bbox(
    point: tuple[int, int], box: tuple[int, int, int, int]
) -> int:
    row, col = point
    top, left, bottom, right = box
    dr = top - row if row < top else row - bottom if row > bottom else 0
    dc = left - col if col < left else col - right if col > right else 0
    return dr + dc


def _select_control(grid: Sequence[Sequence[int]], selector: str) -> tuple[int, int]:
    controls = _isolated_controls(grid)
    cells = _object_cells(grid, controls)
    if not controls or not cells:
        raise ValueError("scene requires controls and an object")
    if selector == "last_isolated":
        return controls[-1]
    box = _bbox(cells)
    return min(controls, key=lambda p: (_distance_to_bbox(p, box), controls.index(p)))


def _rotate(grid: list[list[int]], code: int) -> list[list[int]]:
    result = deepcopy(grid)
    turns = {1: 0, 2: 1, 3: 2, 4: 3}.get(code, 0)
    for _ in range(turns):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _reference_with_selector(grid: object, selector: str) -> list[list[int]]:
    source = _grid(grid)
    controls = _isolated_controls(source)
    cells = _object_cells(source, controls)
    if not controls or not cells:
        return [[0]]
    point = _select_control(source, selector)
    code = source[point[0]][point[1]]
    top, left, bottom, right = _bbox(cells)
    crop = [row[left : right + 1] for row in source[top : bottom + 1]]
    return _rotate(crop, code)


def reference(grid: object, settings: object) -> list[list[int]]:
    return _reference_with_selector(grid, _selector(settings))


def _stable_rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|object-control-v1|{seed}|{role}|{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _snake_cells(height: int, width: int) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for row in range(height):
        if row % 2 == 0:
            cells.update((row, col) for col in range(width))
        else:
            connector = width - 1 if (row // 2) % 2 == 0 else 0
            cells.add((row, connector))
    # Break accidental geometric regularity while preserving connectivity.
    if height >= 5 and width >= 5:
        cells.update({(1, width - 2), (3, 1), (height - 2, width // 2)})
    return cells


def _scene(
    seed: int,
    role: str,
    index: int,
    profile: tuple[int, int, int, int],
    ordinal: int,
) -> list[list[int]]:
    height, width, obj_h, obj_w = profile
    rng = _stable_rng(seed, role, index)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError("profile exceeds ARC bounds")
    if height - obj_h < 4 or width - obj_w < 4:
        raise ValueError("profile needs a two-cell control margin")
    top = (height - obj_h) // 2
    left = (width - obj_w) // 2
    cells = _snake_cells(obj_h, obj_w)
    if rng.random() < 0.5:
        cells = {(obj_h - 1 - row, col) for row, col in cells}
    if rng.random() < 0.5:
        cells = {(row, obj_w - 1 - col) for row, col in cells}
    grid = [[0] * width for _ in range(height)]
    palette = (5, 6, 7, 8, 9)
    salt = rng.randrange(len(palette))
    for row, col in sorted(cells):
        value = palette[(row * 3 + col * 5 + salt + (row * col) % 3) % len(palette)]
        grid[top + row][left + col] = value

    side = ordinal % 4
    near = (
        (top - 2, left + obj_w // 3),
        (top + obj_h // 2, left - 2),
        (top + obj_h + 1, left + (2 * obj_w) // 3),
        (top + obj_h // 3, left + obj_w + 1),
    )[side]
    first = (0, 0)
    last = (height - 1, width - 1)
    if len({near, first, last}) != 3:
        raise RuntimeError("control positions collided")
    codes = (
        _NEAR_CODES[ordinal % len(_NEAR_CODES)],
        _FIRST_CODES[ordinal % len(_FIRST_CODES)],
        _LAST_CODES[ordinal % len(_LAST_CODES)],
    )
    if len(set(codes)) != 3:
        raise RuntimeError("teaching controls must use distinct codes")
    for point, code in zip((near, first, last), codes):
        row, col = point
        if grid[row][col] != 0:
            raise RuntimeError("control overlaps object")
        if any(
            0 <= row + dr < height
            and 0 <= col + dc < width
            and grid[row + dr][col + dc] != 0
            for dr, dc in _DIR4
        ):
            raise RuntimeError("control is not isolated")
        grid[row][col] = code
    summary = scene_summary(grid)
    if not summary["nearest_unique"] or summary["nearest_code"] == summary["last_code"]:
        raise RuntimeError("scene does not distinguish selectors")
    return grid


def _plan(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [
        _scene(seed, "demo", index, profile, index)
        for index, profile in enumerate(_DEMO_PROFILES)
    ]
    queries = [
        _scene(seed, "query", index, profile, len(_DEMO_PROFILES) + index)
        for index, profile in enumerate(_QUERY_PROFILES)
    ]
    return demos, queries


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    _selector(settings)
    demo_inputs, query_inputs = _plan(seed)
    return {
        "train": [
            {"input": deepcopy(grid), "output": reference(grid, settings)}
            for grid in demo_inputs[:demos]
        ],
        "test": [
            {"input": deepcopy(grid), "output": reference(grid, settings)}
            for grid in query_inputs[:queries]
        ],
        "program_solution": program(settings),
        "sampling": {
            "schema": "0e4adc584fa1-object-control-sampling-v1",
            "matched_inputs_across_settings": True,
            "prefix_stable_counts": True,
            "full_demo_count": 6,
            "full_query_count": 4,
        },
    }


def public_turn(episode: object, query_index: int = 0) -> dict:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    query_index = _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def scene_summary(grid: object) -> dict:
    source = _grid(grid)
    controls = _isolated_controls(source)
    cells = _object_cells(source, controls)
    box = _bbox(cells)
    distances = [_distance_to_bbox(point, box) for point in controls]
    nearest_distance = min(distances)
    nearest = controls[distances.index(nearest_distance)]
    return {
        "shape": [len(source), len(source[0])],
        "isolated_controls": len(controls),
        "object_cells": len(cells),
        "object_bbox_height": box[2] - box[0] + 1,
        "object_bbox_width": box[3] - box[1] + 1,
        "nearest_unique": distances.count(nearest_distance) == 1,
        "nearest_position": list(nearest),
        "nearest_code": source[nearest[0]][nearest[1]],
        "last_position": list(controls[-1]),
        "last_code": source[controls[-1][0]][controls[-1][1]],
    }


def _selector_reference(grid: object, name: str) -> list[list[int]]:
    source = _grid(grid)
    controls = _isolated_controls(source)
    cells = _object_cells(source, controls)
    box = _bbox(cells)
    if name in ("last_isolated", "nearest_object"):
        return _reference_with_selector(source, name)
    if name == "first_isolated":
        point = controls[0]
    elif name == "smallest_code":
        point = min(controls, key=lambda p: (source[p[0]][p[1]], controls.index(p)))
    elif name == "largest_code":
        point = max(controls, key=lambda p: (source[p[0]][p[1]], -controls.index(p)))
    elif name.startswith("fixed_code_"):
        code = int(name.rsplit("_", 1)[1])
        top, left, bottom, right = box
        crop = [row[left : right + 1] for row in source[top : bottom + 1]]
        return _rotate(crop, code)
    else:
        raise KeyError(name)
    top, left, bottom, right = box
    crop = [row[left : right + 1] for row in source[top : bottom + 1]]
    return _rotate(crop, source[point[0]][point[1]])


_RIVAL_NAMES = (
    "last_isolated",
    "nearest_object",
    "first_isolated",
    "smallest_code",
    "largest_code",
    "fixed_code_1",
    "fixed_code_2",
    "fixed_code_3",
    "fixed_code_4",
)


def teaching_survivors(demos: object, settings: object) -> tuple[str, ...]:
    _selector(settings)
    if type(demos) is not list or len(demos) < 2:
        raise ValueError("at least two demonstrations are required")
    survivors = []
    for name in _RIVAL_NAMES:
        if all(_selector_reference(pair["input"], name) == pair["output"] for pair in demos):
            survivors.append(name)
    return tuple(survivors)
