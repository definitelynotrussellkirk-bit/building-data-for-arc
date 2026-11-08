"""Episode-fixed exact-count variants for c83b29b14c16.

The canonical setting connects aligned colors occurring exactly twice.  The
alternate setting applies the same alignment-and-fill reasoning to colors
occurring exactly three times.  Inputs are setting-neutral and include both
counts plus non-collinear controls, so labels—not input distributions—identify
the rule.
"""
from __future__ import annotations

from copy import deepcopy
import random
from typing import Any, Iterable, Sequence

TASK_ID = "c83b29b14c16"
SETTINGS = ({"required_count": 2}, {"required_count": 3})
DEFAULT = {"required_count": 2}
DEMO_PROFILES = ((9, 9), (10, 12), (12, 10), (14, 14), (16, 18), (20, 16))
QUERY_PROFILES = ((13, 17), (18, 18), (24, 20), (30, 30), (21, 27), (27, 21), (26, 30), (30, 26))

CANONICAL_PROGRAM = """(rule!
  (let ((colors (filter (lambda (v) (not (= v 0))) (grid-colors g))))
    (for/fold ([out g]) ([color (in-list colors)])
      (let ((pts (find-color g color)))
        (if (= (length pts) 2)
            (let ((a (first pts)) (b (second pts)))
              (cond [(= (first a) (first b))
                     (paint-cells out (map (lambda (c) (list (first a) c))
                                           (range (min (second a) (second b)) (+ (max (second a) (second b)) 1))) color)]
                    [(= (second a) (second b))
                     (paint-cells out (map (lambda (r) (list r (second a)))
                                           (range (min (first a) (first b)) (+ (max (first a) (first b)) 1))) color)]
                    [else out]))
            out)))))"""

COUNT_THREE_PROGRAM = """(rule!
  (let ((colors (filter (lambda (v) (not (= v 0))) (grid-colors g))))
    (for/fold ([out g]) ([color (in-list colors)])
      (let ((pts (find-color g color)))
        (if (= (length pts) 3)
            (let ((a (first pts)) (b (second pts)) (c (third pts)))
              (cond [(and (= (first a) (first b)) (= (first b) (first c)))
                     (paint-cells out
                                  (map (lambda (col) (list (first a) col))
                                       (range (min (second a) (second b) (second c))
                                              (+ (max (second a) (second b) (second c)) 1)))
                                  color)]
                    [(and (= (second a) (second b)) (= (second b) (second c)))
                     (paint-cells out
                                  (map (lambda (row) (list row (second a)))
                                       (range (min (first a) (first b) (first c))
                                              (+ (max (first a) (first b) (first c)) 1)))
                                  color)]
                    [else out]))
            out)))))"""


def _integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    return value


def _settings(value: Any) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"required_count"}:
        raise ValueError("settings must contain exactly required_count")
    count = value["required_count"]
    if type(count) is not int:
        raise TypeError("required_count must be an integer (not bool)")
    if count not in (2, 3):
        raise ValueError("required_count must be 2 or 3")
    return {"required_count": count}


def program(settings: Any) -> str:
    chosen = _settings(settings)
    return CANONICAL_PROGRAM if chosen["required_count"] == 2 else COUNT_THREE_PROGRAM


def _positions(grid: Sequence[Sequence[int]]) -> dict[int, list[tuple[int, int]]]:
    positions: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                positions.setdefault(int(value), []).append((row, col))
    return positions


def transform(grid: Sequence[Sequence[int]], settings: Any) -> list[list[int]]:
    count = _settings(settings)["required_count"]
    out = [list(map(int, row)) for row in grid]
    for color, cells in _positions(grid).items():
        if len(cells) != count:
            continue
        rows = {row for row, _ in cells}
        cols = {col for _, col in cells}
        if len(rows) == 1:
            row = cells[0][0]
            for col in range(min(col for _, col in cells), max(col for _, col in cells) + 1):
                out[row][col] = color
        elif len(cols) == 1:
            col = cells[0][1]
            for row in range(min(row for row, _ in cells), max(row for row, _ in cells) + 1):
                out[row][col] = color
    return out


def _scene(seed: int, role: str, index: int, shape: tuple[int, int]) -> list[list[int]]:
    height, width = shape
    if height < 9 or width < 9:
        raise ValueError("count-mode scenes require dimensions at least 9x9")
    rng = random.Random(f"{TASK_ID}:{seed}:{role}:{index}")
    colors = list(range(1, 9))
    rng.shuffle(colors)
    grid = [[0] * width for _ in range(height)]

    groups: list[tuple[tuple[int, int], ...]] = [
        ((0, 0), (0, max(2, width // 4))),
        ((0, width - 1), (max(3, height // 4), width - 1)),
        ((height - 1, 0), (height - 1, max(2, width // 4)), (height - 1, width // 2)),
        ((height // 2, width - 1), (3 * height // 4, width - 1), (height - 1, width - 1)),
        ((height // 3, 1), (height // 3, max(3, width // 2 - 1))),
        ((1, width // 2), (max(3, height // 4), width // 2), (max(5, height // 2 - 1), width // 2)),
        ((height // 2, width // 3), (min(height - 2, height // 2 + 2), min(width - 2, width // 3 + 3))),
        ((height // 3 + 1, 2 * width // 3), (height // 3 + 2, 2 * width // 3 + 1), (height // 3 + 3, 2 * width // 3 + 1)),
    ]
    occupied: set[tuple[int, int]] = set()
    for color, group in zip(colors, groups):
        if len(set(group)) != len(group) or any(cell in occupied for cell in group):
            raise RuntimeError(f"invalid constructive group for {shape}: {group}")
        for row, col in group:
            if not (0 <= row < height and 0 <= col < width):
                raise RuntimeError(f"group escaped {shape}: {(row, col)}")
            grid[row][col] = color
            occupied.add((row, col))
    return grid


def _pair(grid: list[list[int]], settings: dict[str, int]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": transform(grid, settings)}


def fit_settings(demos: Iterable[dict[str, Any]]) -> list[dict[str, int]]:
    pairs = list(demos)
    survivors: list[dict[str, int]] = []
    for candidate in SETTINGS:
        if all(
            isinstance(pair, dict)
            and pair.get("output") == transform(pair.get("input"), candidate)
            for pair in pairs
        ):
            survivors.append(dict(candidate))
    return survivors


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 8, "queries")
    chosen = _settings(settings)

    train = [
        _pair(_scene(seed, "demo", index, DEMO_PROFILES[index]), chosen)
        for index in range(demos)
    ]
    test = [
        _pair(_scene(seed, "query", index, QUERY_PROFILES[index]), chosen)
        for index in range(queries)
    ]
    if fit_settings(train) != [chosen]:
        raise RuntimeError("demonstrations do not uniquely identify required_count")
    serial = [repr(pair["input"]) for pair in train + test]
    if len(serial) != len(set(serial)):
        raise RuntimeError("episode contains duplicate inputs")
    return {
        "train": train,
        "test": test,
        "settings": chosen,
        "seed": seed,
        "program_solution": program(chosen),
        "certificate": {
            "finite_rivals": [dict(setting) for setting in SETTINGS],
            "survivors": fit_settings(train),
            "racket_checked": False,
        },
    }
