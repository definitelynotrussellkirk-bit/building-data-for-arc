"""Native two-setting parametric family for separated-panel NOR.

The canonical setting keeps every aligned 00 result.  The alternative first
builds that same NOR mask, then keeps the mask only on rows attaining the
maximum number of positive cells.  Inputs are sampled independently of the
private setting so paired qualification jobs receive identical grids.
"""
from __future__ import annotations

import hashlib
import random
from typing import Any


TASK_ID = "a3fcfe29ef7e"
ROW_POLICIES = ("all", "densest")
DEMO_HEIGHTS = (4, 5, 6, 7, 8, 9)
QUERY_HEIGHTS = (12, 18, 24, 30)
COUNT_PROFILES = ((3, 2, 1), (2, 1, 1), (2, 2, 1), (3, 3, 1))
PALETTE = (1, 2, 4, 5, 6, 7, 8, 9)

CANONICAL_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let ((w 3))
             (build-grid h
                         w
                         (r c)
                         (if (and (zero? (at g r c)) (zero? (at g r (+ c 4)))) 3 0))))))"""

DENSEST_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (mask (build-grid h
                                  3
                                  (r c)
                                  (if (and (zero? (at g r c))
                                           (zero? (at g r (+ c 4))))
                                      3
                                      0)))
                (row-counts
                 (map (lambda (r)
                        (count-if (lambda (c) (= (at mask r c) 3))
                                  (range 0 3)))
                      (range 0 h)))
                (best (max-list row-counts)))
           (build-grid h
                       3
                       (r c)
                       (if (and (= (list-ref row-counts r) best)
                                (= (at mask r c) 3))
                           3
                           0)))))"""


def settings(row_policy: Any) -> dict[str, str]:
    if type(row_policy) is not str or row_policy not in ROW_POLICIES:
        raise ValueError("row_policy must be all or densest")
    return {"row_policy": row_policy}


def materialize_program(*, row_policy: str = "all") -> str:
    normalized = settings(row_policy)
    return CANONICAL_PROGRAM if normalized["row_policy"] == "all" else DENSEST_PROGRAM


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if any(type(row) is not list or len(row) != 7 for row in grid):
        raise ValueError("grid must be rectangular with width 7")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid colors must be exact integers in 0..9")
    return grid


def analyze(grid: Any) -> dict[str, Any]:
    checked = _grid(grid)
    mask = [
        [3 if row[c] == 0 and row[c + 4] == 0 else 0 for c in range(3)]
        for row in checked
    ]
    row_counts = [sum(value == 3 for value in row) for row in mask]
    return {
        "mask": mask,
        "row_counts": row_counts,
        "max_count": max(row_counts),
    }


def transform(grid: Any, *, row_policy: str = "all") -> list[list[int]]:
    normalized = settings(row_policy)
    analysis = analyze(grid)
    if normalized["row_policy"] == "all":
        return analysis["mask"]
    best = analysis["max_count"]
    return [
        [value if analysis["row_counts"][r] == best else 0 for value in row]
        for r, row in enumerate(analysis["mask"])
    ]


def _rng(seed: int, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def sample_input(seed: int, *, index: int, height: int) -> list[list[int]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0, 10_000)
    _integer(height, "height", 4, 30)
    rng = _rng(seed, index)

    palette = list(PALETTE)
    rng.shuffle(palette)
    left_color = palette[0]
    if index % 2:
        right_color = left_color
        separator = palette[1]
    else:
        right_color = palette[1]
        separator = palette[2]

    # Rotate four teaching profiles so the global maximum is sometimes two,
    # sometimes three, and sometimes tied.  This prevents the intended global
    # comparison from collapsing to "keep exactly-three rows" or a first-winner
    # tie break.  The chosen private setting never affects these inputs.
    counts = COUNT_PROFILES[index % len(COUNT_PROFILES)]
    rows = list(range(height))
    rng.shuffle(rows)
    zero_cells: set[tuple[int, int]] = set()
    for row, count in zip(rows, counts):
        columns = range(3) if count == 3 else rng.sample(range(3), count)
        zero_cells.update((row, column) for column in columns)

    negative_cells = [
        (r, c)
        for r in range(height)
        for c in range(3)
        if (r, c) not in zero_cells
    ]
    states = ("10", "01", "11")
    phase = rng.randrange(len(states))

    grid = [[0 for _ in range(7)] for _ in range(height)]
    for row in grid:
        row[3] = separator
    for position, (r, c) in enumerate(negative_cells):
        state = states[(position + phase) % len(states)]
        if state[0] == "1":
            grid[r][c] = left_color
        if state[1] == "1":
            grid[r][c + 4] = right_color
    return grid


def sample_episode(
    seed: int,
    *,
    row_policy: str = "all",
    n_demo: int = 3,
    n_query: int = 4,
) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(n_demo, "n_demo", 2, 6)
    _integer(n_query, "n_query", 1, 4)
    normalized = settings(row_policy)

    demo_inputs = [
        sample_input(seed, index=i, height=DEMO_HEIGHTS[i])
        for i in range(n_demo)
    ]
    query_inputs = [
        sample_input(seed, index=100 + i, height=QUERY_HEIGHTS[i])
        for i in range(n_query)
    ]

    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {
            "input": grid,
            "output": transform(grid, **normalized),
        }

    return {
        "train": [pair(grid) for grid in demo_inputs],
        "test": [pair(grid) for grid in query_inputs],
        "program_solution": materialize_program(**normalized),
    }
