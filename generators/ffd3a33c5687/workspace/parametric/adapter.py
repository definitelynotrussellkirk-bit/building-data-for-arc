"""Native parametric adapter for ARC task ffd3a33c5687.

The exact canonical default always gives the left member of a mirror orbit
priority.  The alternate first reads a unique center guide row to infer an
input-dependent left/right priority, then uses that intermediate when resolving
all occupied mirror conflicts.  Inputs are shared across settings and the final
query is a substantive 30x30 boundary case.
"""
from __future__ import annotations

from copy import deepcopy
import json
import random


_TASK_ID = "ffd3a33c5687"
_CANONICAL_PROGRAM = """(rule! (lambda (grid)
  (define height (rows grid))
  (define width (cols grid))
  (define (mirror-col col) (- (- width 1) col))
  (define (pair-color left-val right-val)
    (if (!= left-val 0) left-val
        (if (!= right-val 0) right-val 0)))
  (define (repaired-color row col)
    (let* ((other-col (mirror-col col))
           (left-col (min col other-col))
           (right-col (max col other-col))
           (left-val (cell-at grid row left-col))
           (right-val (cell-at grid row right-col)))
      (pair-color left-val right-val)))
  (grid-from-fn height width
    (lambda (row col) (repaired-color row col)))))"""
_GUIDE_PROGRAM = """(rule! (lambda (grid)
  (define height (rows grid))
  (define width (cols grid))
  (define center-left (quotient (- width 1) 2))
  (define center-right (quotient width 2))
  (define (mirror-col col) (- (- width 1) col))
  (define guide-row
    (let loop ((row 0))
      (if (= row height)
          0
          (if (and (= (cell-at grid row center-left) 8)
                   (= (cell-at grid row center-right) 8))
              row
              (loop (+ row 1))))))
  (define guide-left
    (let loop ((col 0))
      (if (= col center-left)
          #f
          (if (!= (cell-at grid guide-row col) 0)
              #t
              (loop (+ col 1))))))
  (define (pair-color left-val right-val)
    (if guide-left
        (if (!= left-val 0) left-val
            (if (!= right-val 0) right-val 0))
        (if (!= right-val 0) right-val
            (if (!= left-val 0) left-val 0))))
  (define (repaired-color row col)
    (let* ((other-col (mirror-col col))
           (left-col (min col other-col))
           (right-col (max col other-col))
           (left-val (cell-at grid row left-col))
           (right-val (cell-at grid row right-col)))
      (pair-color left-val right-val)))
  (grid-from-fn height width
    (lambda (row col) (repaired-color row col)))))"""
_PROGRAMS = {
    "left_priority": _CANONICAL_PROGRAM,
    "guide_priority": _GUIDE_PROGRAM,
}

_DEMO_SPECS = (
    (5, 5),
    (7, 9),
    (9, 11),
    (12, 15),
    (16, 17),
    (24, 25),
)
_QUERY_SPECS = (
    (8, 13),
    (15, 16),
    (21, 29),
    (30, 30),
)
_CONFLICT_PAIRS = (
    (2, 5),
    (6, 3),
    (1, 9),
    (5, 2),
    (4, 6),
    (9, 1),
    (3, 7),
    (7, 4),
)
_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def _integer(name: str, value, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _validate_settings(settings) -> str:
    if not isinstance(settings, dict) or set(settings) != {"conflict_policy"}:
        raise ValueError("settings must contain exactly conflict_policy")
    policy = settings["conflict_policy"]
    if type(policy) is not str or policy not in _PROGRAMS:
        raise ValueError("conflict_policy must be left_priority or guide_priority")
    return policy


def program(settings) -> str:
    """Return exact Racket source for one declared private setting."""
    return _PROGRAMS[_validate_settings(settings)]


def _centers(width: int) -> tuple[int, int]:
    return (width - 1) // 2, width // 2


def _guide_side(grid: list[list[int]]) -> str:
    width = len(grid[0])
    center_left, center_right = _centers(width)
    guide_rows = [
        row_index
        for row_index, row in enumerate(grid)
        if row[center_left] == 8 and row[center_right] == 8
    ]
    if len(guide_rows) != 1:
        raise ValueError("input needs exactly one center-marked guide row")
    guide = grid[guide_rows[0]]
    left = [value for value in guide[:center_left] if value != 0]
    right = [value for value in guide[center_right + 1 :] if value != 0]
    if (len(left), len(right)) == (1, 0):
        return "left"
    if (len(left), len(right)) == (0, 1):
        return "right"
    raise ValueError("guide row needs exactly one off-center one-sided signal")


def _priority_output(grid: list[list[int]], side: str) -> list[list[int]]:
    if side not in {"left", "right"}:
        raise ValueError("side must be left or right")
    output = deepcopy(grid)
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            left, right = row[left_col], row[right_col]
            preferred, fallback = (left, right) if side == "left" else (right, left)
            color = preferred if preferred != 0 else fallback
            output[row_index][left_col] = color
            output[row_index][right_col] = color
    return output


def _guide_output(grid: list[list[int]]) -> list[list[int]]:
    return _priority_output(grid, _guide_side(grid))


def _ordered_slots(height: int, width: int, guide_row: int, rng: random.Random) -> list[tuple[int, int]]:
    all_slots = [
        (row, left_col)
        for row in range(height)
        if row != guide_row
        for left_col in range(width // 2)
    ]
    edge_col = width // 2 - 1
    mandatory = []
    for slot in ((0, 0), (height - 1, 0), (0, edge_col), (height - 1, edge_col)):
        if slot in all_slots and slot not in mandatory:
            mandatory.append(slot)
    remaining = [slot for slot in all_slots if slot not in mandatory]
    rng.shuffle(remaining)
    return mandatory + remaining


def _put_orbit(grid: list[list[int]], slot: tuple[int, int], left: int, right: int) -> None:
    row, left_col = slot
    right_col = len(grid[0]) - 1 - left_col
    if grid[row][left_col] != 0 or grid[row][right_col] != 0:
        raise RuntimeError("orbit placement collision")
    grid[row][left_col] = left
    grid[row][right_col] = right


def _build_input(seed: int, pair_index: int, height: int, width: int) -> list[list[int]]:
    mixed = (seed * 1_000_003 + pair_index * 97_409 + height * 409 + width * 997 + 0xFFD3) % (2**63)
    rng = random.Random(mixed)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    guide_row = 1 + ((seed + pair_index * 5) % (height - 2))
    guide_side = "right" if (seed + pair_index) % 2 == 0 else "left"
    center_left, center_right = _centers(width)
    grid[guide_row][center_left] = 8
    grid[guide_row][center_right] = 8
    signal_left = max(0, center_left - 1)
    signal_right = width - 1 - signal_left
    if guide_side == "left":
        grid[guide_row][signal_left] = 7
    else:
        grid[guide_row][signal_right] = 7

    slots = _ordered_slots(height, width, guide_row, rng)
    n_conflicts = min(16, max(2, height // 2))
    n_singletons = min(10, max(3, width // 4))
    n_pairs = min(8, max(1, height // 4))
    while n_conflicts + n_singletons + n_pairs > len(slots):
        if n_pairs > 1:
            n_pairs -= 1
        elif n_singletons > 3:
            n_singletons -= 1
        else:
            n_conflicts -= 1
    cursor = 0
    pair_offset = (seed + pair_index * 3) % len(_CONFLICT_PAIRS)
    for index in range(n_conflicts):
        left, right = _CONFLICT_PAIRS[(pair_offset + index) % len(_CONFLICT_PAIRS)]
        _put_orbit(grid, slots[cursor], left, right)
        cursor += 1

    opposite = "left" if guide_side == "right" else "right"
    for index in range(n_singletons):
        color = _COLORS[(pair_offset + n_conflicts + index) % len(_COLORS)]
        side = opposite if index < max(3, n_singletons - 2) else ("left" if index % 2 == 0 else "right")
        left, right = (color, 0) if side == "left" else (0, color)
        _put_orbit(grid, slots[cursor], left, right)
        cursor += 1

    for index in range(n_pairs):
        color = _COLORS[(pair_offset + n_conflicts + n_singletons + index) % len(_COLORS)]
        _put_orbit(grid, slots[cursor], color, color)
        cursor += 1

    # Assert the authoring grammar now, rather than letting a malformed guide or
    # accidental duplicate survive until protected execution.
    if _guide_side(grid) != guide_side:
        raise RuntimeError("constructed guide side changed")
    if _priority_output(grid, "left") == grid:
        raise RuntimeError("constructed input is an identity case")
    return grid


def _labeled_pair(grid: list[list[int]], policy: str) -> dict:
    output = _priority_output(grid, "left") if policy == "left_priority" else _guide_output(grid)
    return {"input": deepcopy(grid), "output": output}


def generate(seed, settings, demos, queries):
    """Generate one fixed-setting episode with shared deterministic inputs."""
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    policy = _validate_settings(settings)
    specs = list(_DEMO_SPECS[:demos]) + list(_QUERY_SPECS)
    inputs = [
        _build_input(seed, pair_index, height, width)
        for pair_index, (height, width) in enumerate(specs)
    ]
    fingerprints = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    if len(fingerprints) != len(set(fingerprints)):
        raise RuntimeError("episode inputs must be distinct")
    pairs = [_labeled_pair(grid, policy) for grid in inputs]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(settings),
    }
