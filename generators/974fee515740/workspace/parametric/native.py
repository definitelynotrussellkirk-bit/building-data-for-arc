"""Native composition-order family for ARC task 974fee515740.

The default is the exact canonical rule: rotate blue, then combine it with
red.  The alternative combines the unrotated masks first, then rotates the
combined intermediate.  The same input controls operation and rotation in
both settings; only the order of the two stages changes.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

HOME = Path(__file__).resolve().parent
SETTINGS = ("rotate_then_combine", "combine_then_rotate")
RIVAL_NAMES = (
    "rotate_then_combine",
    "combine_then_rotate",
    "no_rotation_then_combine",
    "counterclockwise_blue_then_combine",
    "rotate_red_then_combine",
    "fixed_rotation_2_then_combine",
    "fixed_rotation_3_then_combine",
    "fixed_rotation_4_then_combine",
    "always_union_after_blue_rotation",
    "always_intersection_after_blue_rotation",
    "always_xor_after_blue_rotation",
    "reverse_subtraction_after_blue_rotation",
)

CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
ALTERNATE_PROGRAM = """(rule!
  (let ((dummy 0))
    (define (same-pos? a b)
      (and (= (fst a) (fst b)) (= (snd a) (snd b))))
    (define (has-cell? p cells)
      (any? (lambda (q) (same-pos? p q)) cells))
    (define (rotate-by cells code)
      (cond
        [(= code 2) (normalize-cells (rotate-cells-cw cells))]
        [(= code 3) (normalize-cells (rotate-cells-cw (rotate-cells-cw cells)))]
        [(= code 4) (normalize-cells (rotate-cells-cw (rotate-cells-cw (rotate-cells-cw cells))))]
        [else (normalize-cells cells)]))
    (define (render cells)
      (if (empty? cells)
          (list (list 0))
          (let* ((norm (normalize-cells cells))
                 (bb (bbox-of-cells norm))
                 (out-h (+ 1 (third bb)))
                 (out-w (+ 1 (fourth bb))))
            (grid-from-fn out-h out-w
              (lambda (r c) (if (has-cell? (list r c) norm) 8 0))))))
    (let* ((nz (filter (lambda (v) (not (= v 0))) (row-at g 0)))
           (op-raw (if (empty? nz) 6 (first nz)))
           (rot-raw (if (> (length nz) 1) (second nz) 1))
           (op (if (member? op-raw (list 3 4 6 7)) op-raw 6))
           (rot-code (if (member? rot-raw (list 1 2 3 4)) rot-raw 1))
           (red-obj (first (filter (lambda (obj) (= (obj-color obj) 2)) (objects g 0))))
           (blue-obj (first (filter (lambda (obj) (= (obj-color obj) 1)) (objects g 0))))
           (red (normalize-cells (obj-cells red-obj)))
           (blue (normalize-cells (obj-cells blue-obj)))
           (combined
             (cond
               [(= op 3) (append red (filter (lambda (p) (not (has-cell? p red))) blue))]
               [(= op 4) (filter (lambda (p) (has-cell? p blue)) red)]
               [(= op 6)
                (append
                  (filter (lambda (p) (not (has-cell? p blue))) red)
                  (filter (lambda (p) (not (has-cell? p red))) blue))]
               [else (filter (lambda (p) (not (has-cell? p blue))) red)]))
           (result (rotate-by combined rot-code)))
      (render result))))"""

# (height, width, op, rotation, red mask, blue mask)
_PROFILES = (
    (12, 14, 7, 2,
     ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2), (2, 2)),
     ((0, 0), (1, 0), (1, 1), (2, 1), (2, 3), (3, 1), (3, 2), (3, 3))),
    (13, 15, 4, 4,
     ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 2), (2, 3), (3, 3)),
     ((0, 2), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (3, 2))),
    (14, 16, 3, 3,
     ((0, 0), (0, 1), (0, 2), (0, 3), (1, 2), (2, 2), (2, 3), (3, 2)),
     ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (3, 0), (3, 1))),
    (15, 17, 6, 2,
     ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0)),
     ((0, 1), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 3), (3, 1))),
    (16, 18, 7, 4,
     ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1), (2, 2), (2, 3), (3, 3)),
     ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 2), (3, 2), (3, 3))),
    (17, 19, 3, 2,
     ((0, 0), (0, 1), (1, 1), (2, 1), (3, 0), (3, 1), (3, 2), (3, 3)),
     ((0, 0), (0, 1), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2))),
    (18, 20, 4, 3,
     ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 3), (3, 3)),
     ((0, 1), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1))),
    (20, 22, 6, 4,
     ((0, 1), (1, 1), (1, 3), (2, 1), (2, 2), (2, 3), (3, 0), (3, 1)),
     ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2), (3, 0), (3, 1))),
    (24, 26, 7, 3,
     ((0, 2), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1)),
     ((0, 0), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (3, 2))),
    (30, 30, 3, 2,
     ((0, 0), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
     ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 3))),
)


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"composition_order"}:
        raise ValueError("settings must contain exactly composition_order")
    value = settings["composition_order"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"composition_order must be one of {SETTINGS}")
    return value


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    return CANONICAL_PROGRAM if _setting(settings) == "rotate_then_combine" else ALTERNATE_PROGRAM


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not 3 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must have 3..30 rows")
    width = len(grid[0])
    if not 3 <= width <= 30:
        raise ValueError("grid must have 3..30 columns")
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(grid), width


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _first_component(grid: list[list[int]], color: int) -> tuple[tuple[int, int], ...]:
    height, width = len(grid), len(grid[0])
    start = next(((row, col) for row in range(height) for col in range(width)
                  if grid[row][col] == color), None)
    if start is None:
        raise ValueError(f"missing color-{color} source")
    found = {start}
    pending = [start]
    while pending:
        row, col = pending.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            other = row + dr, col + dc
            if (0 <= other[0] < height and 0 <= other[1] < width
                    and grid[other[0]][other[1]] == color and other not in found):
                found.add(other)
                pending.append(other)
    return tuple(sorted(found))


def _rotate_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((col, -row) for row, col in cells)


def _rotate_by(cells: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    result = _normalize(cells)
    for _ in range(code - 1):
        result = _rotate_cw(result)
    return result


def _combine(red: Iterable[tuple[int, int]], blue: Iterable[tuple[int, int]], op: int,
             *, reverse_subtraction: bool = False) -> tuple[tuple[int, int], ...]:
    red_set, blue_set = set(red), set(blue)
    if op == 3:
        result = red_set | blue_set
    elif op == 4:
        result = red_set & blue_set
    elif op == 6:
        result = red_set ^ blue_set
    elif reverse_subtraction:
        result = blue_set - red_set
    else:
        result = red_set - blue_set
    return tuple(sorted(result))


def _render(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    norm = _normalize(cells)
    if not norm:
        return [[0]]
    height = 1 + max(row for row, _ in norm)
    width = 1 + max(col for _, col in norm)
    occupied = set(norm)
    return [[8 if (row, col) in occupied else 0 for col in range(width)]
            for row in range(height)]


def analyze(grid: Any) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    nonzero = [(col, value) for col, value in enumerate(grid[0]) if value != 0]
    op_raw = nonzero[0][1] if nonzero else 6
    rot_raw = nonzero[1][1] if len(nonzero) > 1 else 1
    op = op_raw if op_raw in (3, 4, 6, 7) else 6
    rot = rot_raw if rot_raw in (1, 2, 3, 4) else 1
    red_cells = _first_component(grid, 2)
    blue_cells = _first_component(grid, 1)
    red = _normalize(red_cells)
    blue = _normalize(blue_cells)
    rotated_blue = _rotate_by(blue, rot)
    canonical_result = _combine(red, rotated_blue, op)
    unrotated_combined = _combine(red, blue, op)
    alternate_result = _rotate_by(unrotated_combined, rot)
    return {
        "height": height,
        "width": width,
        "op_code": op,
        "rotation_code": rot,
        "red_mask": [list(cell) for cell in red],
        "blue_mask": [list(cell) for cell in blue],
        "rotated_blue_mask": [list(cell) for cell in rotated_blue],
        "rotate_then_combine_intermediate": [list(cell) for cell in rotated_blue],
        "combine_then_rotate_intermediate": [list(cell) for cell in unrotated_combined],
        "rotate_then_combine_output": _render(canonical_result),
        "combine_then_rotate_output": _render(alternate_result),
    }


def transform(grid: Any, composition_order: str) -> list[list[int]]:
    if type(composition_order) is not str or composition_order not in SETTINGS:
        raise ValueError(f"composition_order must be one of {SETTINGS}")
    facts = analyze(grid)
    return deepcopy(facts[f"{composition_order}_output"])


def rival_output(grid: Any, name: str) -> list[list[int]]:
    facts = analyze(grid)
    red = tuple(map(tuple, facts["red_mask"]))
    blue = tuple(map(tuple, facts["blue_mask"]))
    op = facts["op_code"]
    rot = facts["rotation_code"]
    if name in SETTINGS:
        return transform(grid, name)
    if name == "no_rotation_then_combine":
        return _render(_combine(red, blue, op))
    if name == "counterclockwise_blue_then_combine":
        inverse = {1: 1, 2: 4, 3: 3, 4: 2}[rot]
        return _render(_combine(red, _rotate_by(blue, inverse), op))
    if name == "rotate_red_then_combine":
        return _render(_combine(_rotate_by(red, rot), blue, op))
    if name.startswith("fixed_rotation_"):
        fixed = int(name.split("_")[2])
        return _render(_combine(red, _rotate_by(blue, fixed), op))
    if name == "always_union_after_blue_rotation":
        return _render(_combine(red, _rotate_by(blue, rot), 3))
    if name == "always_intersection_after_blue_rotation":
        return _render(_combine(red, _rotate_by(blue, rot), 4))
    if name == "always_xor_after_blue_rotation":
        return _render(_combine(red, _rotate_by(blue, rot), 6))
    if name == "reverse_subtraction_after_blue_rotation":
        return _render(_combine(red, _rotate_by(blue, rot), op,
                                reverse_subtraction=(op == 7)))
    raise ValueError(f"unknown rival: {name}")


def _rng(seed: int, stream: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"composition-order-v1:{seed}:{stream}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _paint(grid: list[list[int]], shape: Iterable[tuple[int, int]],
           top: int, left: int, color: int) -> None:
    for row, col in shape:
        if grid[top + row][left + col] != 0:
            raise ValueError("scene placement overlap")
        grid[top + row][left + col] = color


def _add_decoys(grid: list[list[int]], rng: random.Random, count: int) -> None:
    height, width = len(grid), len(grid[0])
    quadrants = (
        (range(2, max(3, height // 2)), range(0, max(1, width // 2))),
        (range(2, max(3, height // 2)), range(width // 2, width)),
        (range(height // 2, height), range(0, max(1, width // 2))),
        (range(height // 2, height), range(width // 2, width)),
    )
    candidates: list[tuple[int, int]] = []
    for rows, cols in quadrants:
        available = [(row, col) for row in rows for col in cols if grid[row][col] == 0]
        rng.shuffle(available)
        candidates.extend(available[: max(1, count // 4)])
    remaining = [(row, col) for row in range(2, height) for col in range(width)
                 if grid[row][col] == 0 and (row, col) not in candidates]
    rng.shuffle(remaining)
    candidates.extend(remaining)
    colors = (5, 8, 9)
    for index, (row, col) in enumerate(candidates[:count]):
        grid[row][col] = colors[index % len(colors)]


def _scene(seed: int, profile_index: int) -> list[list[int]]:
    height, width, op, rot, red, blue = _PROFILES[profile_index]
    rng = _rng(seed, "scene", profile_index)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[0][0] = op
    if rot == 2:
        # The color-2 rotation control is the top-left cell of the red source.
        red_left = 2 + rng.randrange(max(1, min(3, width - 7)))
        _paint(grid, red, 0, red_left, 2)
        blue_h = 1 + max(row for row, _ in blue)
        blue_w = 1 + max(col for _, col in blue)
        blue_top = height - blue_h - 2 - rng.randrange(max(1, min(3, height - blue_h - 3)))
        blue_left = width - blue_w - 1 - rng.randrange(max(1, min(3, width - blue_w - 1)))
        _paint(grid, blue, blue_top, blue_left, 1)
    else:
        grid[0][2] = rot
        red_h = 1 + max(row for row, _ in red)
        red_w = 1 + max(col for _, col in red)
        blue_h = 1 + max(row for row, _ in blue)
        blue_w = 1 + max(col for _, col in blue)
        red_top = 3 + rng.randrange(max(1, min(3, height - red_h - 4)))
        red_left = 1 + rng.randrange(max(1, min(3, width // 2 - red_w)))
        blue_top = height - blue_h - 2 - rng.randrange(max(1, min(3, height - blue_h - 3)))
        blue_left = width - blue_w - 1 - rng.randrange(max(1, min(3, width - blue_w - 1)))
        _paint(grid, red, red_top, red_left, 2)
        _paint(grid, blue, blue_top, blue_left, 1)
    _add_decoys(grid, rng, 40 if profile_index == 9 else 12 + profile_index)
    facts = analyze(grid)
    if facts["rotate_then_combine_output"] == facts["combine_then_rotate_output"]:
        raise AssertionError("profile does not distinguish composition order")
    if not facts["red_mask"] or not facts["blue_mask"]:
        raise AssertionError("profile lost a source object")
    return grid


def _full_inputs(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [_scene(seed, index) for index in range(6)]
    queries = [_scene(seed, index) for index in range(6, 10)]
    order = list(range(3))
    _rng(seed, "query-order", 0).shuffle(order)
    queries = [queries[index] for index in order] + [queries[3]]
    return demos, queries


def generate(seed: Any, settings: Any, demos: Any = 2, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**31 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    order = _setting(settings)
    demo_inputs, query_inputs = _full_inputs(seed)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": transform(grid, order)}

    return {
        "train": [pair(grid) for grid in demo_inputs[:demos]],
        "test": [pair(grid) for grid in query_inputs[:queries]],
        "program_solution": program({"composition_order": order}),
    }
