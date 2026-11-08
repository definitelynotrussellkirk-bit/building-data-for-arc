"""Native scan-order family with a causal run-length encoding stage."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "a2b78ff2c2e0"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"mode": ["scan_only", "scan_then_rle"]}
DEFAULT = {"mode": "scan_only"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}

_CANONICAL_STRIPPED = CANONICAL.strip()
if not (_CANONICAL_STRIPPED.startswith("(rule!") and _CANONICAL_STRIPPED.endswith(")")):
    raise ValueError("canonical.rkt must contain one rule! expression")
_CANONICAL_BODY = _CANONICAL_STRIPPED[len("(rule!"):-1].strip()

ALTERNATIVE = f"""(rule!
  (let* ((serialized {_CANONICAL_BODY})
         (xs (first serialized)))
    (if (empty? xs)
        (list (list 0) (list 0))
        (let loop ((remaining (rest xs))
                   (current (first xs))
                   (run-length 1)
                   (colors (list))
                   (lengths (list)))
          (if (empty? remaining)
              (list (reverse (cons current colors))
                    (reverse (cons run-length lengths)))
              (let ((next (first remaining)))
                (if (= next current)
                    (loop (rest remaining) current (+ run-length 1) colors lengths)
                    (loop (rest remaining) next 1
                          (cons current colors)
                          (cons run-length lengths)))))))))"""

REVERSED_INTERMEDIATE_PROGRAM = f"""(rule!
  (let* ((serialized {_CANONICAL_BODY})
         (xs (reverse (first serialized))))
    (if (empty? xs)
        (list (list 0) (list 0))
        (let loop ((remaining (rest xs))
                   (current (first xs))
                   (run-length 1)
                   (colors (list))
                   (lengths (list)))
          (if (empty? remaining)
              (list (reverse (cons current colors))
                    (reverse (cons run-length lengths)))
              (let ((next (first remaining)))
                (if (= next current)
                    (loop (rest remaining) current (+ run-length 1) colors lengths)
                    (loop (rest remaining) next 1
                          (cons current colors)
                          (cons run-length lengths)))))))))"""


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in PARAMETERS["mode"]:
        raise ValueError("mode must be scan_only or scan_then_rle")
    return mode


def validate_grid(grid: Any) -> None:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty lists")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid axes must be 1..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be exact integer colors 0..9")


def program(settings: Any) -> str:
    return CANONICAL if _mode(settings) == "scan_only" else ALTERNATIVE


def scan_only(grid: list[list[int]]) -> list[list[int]]:
    validate_grid(grid)
    return [[value for row in grid for value in row if value != 0]]


def rle_row(sequence: list[int]) -> list[list[int]]:
    if type(sequence) is not list or not sequence:
        raise ValueError("sequence must be a nonempty list")
    if any(type(v) is not int or not 1 <= v <= 9 for v in sequence):
        raise ValueError("sequence values must be nonzero ARC colors")
    colors: list[int] = []
    lengths: list[int] = []
    current = sequence[0]
    count = 1
    for value in sequence[1:]:
        if value == current:
            count += 1
        else:
            if count > 9:
                raise ValueError("run length exceeds ARC color range")
            colors.append(current)
            lengths.append(count)
            current = value
            count = 1
    if count > 9:
        raise ValueError("run length exceeds ARC color range")
    colors.append(current)
    lengths.append(count)
    return [colors, lengths]


def scan_then_rle(grid: list[list[int]]) -> list[list[int]]:
    return rle_row(scan_only(grid)[0])


def _rng(seed: int, stream: str) -> random.Random:
    _integer(seed, 0, 2**63 - 1, "seed")
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _run_sequence(lengths: list[int], rng: random.Random) -> list[int]:
    if any(type(n) is not int or not 1 <= n <= 9 for n in lengths):
        raise ValueError("run lengths must be exact integers in 1..9")
    if len(lengths) < 3:
        raise ValueError("teaching sequences need at least three runs")
    # Repeat the first color after a different run. This makes run boundaries,
    # rather than a global color histogram, observable in every pair.
    base = rng.sample(range(1, 10), len(lengths) - 1)
    colors = [base[0], base[1], base[0], *base[2:]]
    return [color for color, length in zip(colors, lengths) for _ in range(length)]


def _positions(h: int, w: int, count: int, rng: random.Random, *, boundary: bool = False) -> list[tuple[int, int]]:
    forced: list[tuple[int, int]] = []
    if boundary:
        forced = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    candidates = [(r, c) for r in range(0, h, 2) for c in range(0, w, 2)]
    candidates += [(r, w - 1) for r in range(2, h - 2, 2) if (r, w - 1) not in candidates]
    candidates += [(h - 1, c) for c in range(2, w - 2, 2) if (h - 1, c) not in candidates]
    rng.shuffle(candidates)
    selected = list(forced)
    for pos in candidates:
        if len(selected) >= count:
            break
        if pos in selected:
            continue
        if all(max(abs(pos[0] - r), abs(pos[1] - c)) >= 2 for r, c in selected):
            selected.append(pos)
    if len(selected) != count:
        raise ValueError("could not scatter the requested nonadjacent marks")
    return sorted(selected)


def _scene(h: int, w: int, lengths: list[int], rng: random.Random, *, boundary: bool = False) -> list[list[int]]:
    sequence = _run_sequence(lengths, rng)
    positions = _positions(h, w, len(sequence), rng, boundary=boundary)
    grid = [[0] * w for _ in range(h)]
    for (r, c), value in zip(positions, sequence):
        grid[r][c] = value
    return grid


def input_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    train_specs = [
        (5, 7, [2, 3, 1]),
        (6, 8, [1, 2, 2, 2]),
        (8, 9, [3, 1, 4]),
        (10, 12, [2, 1, 3, 2, 1]),
        (14, 16, [4, 2, 3, 2]),
        (18, 20, [1, 3, 2, 4, 2]),
    ]
    test_specs = [
        (7, 11, [2, 2, 1, 3]),
        (12, 15, [3, 3, 2, 4]),
        (22, 24, [5, 2, 4, 3, 2]),
        (30, 30, [5, 4, 3, 6, 6]),
    ]
    train = [
        _scene(h, w, lengths, _rng(seed, f"train:{i}"))
        for i, (h, w, lengths) in enumerate(train_specs)
    ]
    test = [
        _scene(h, w, lengths, _rng(seed, f"test:{i}"), boundary=(i == 3))
        for i, (h, w, lengths) in enumerate(test_specs)
    ]
    keys = [tuple(map(tuple, grid)) for grid in train + test]
    if len(keys) != len(set(keys)):
        raise ValueError("constructed inputs must be distinct")
    return train, test


def generate(seed: int, settings: Any = None, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"mode": _rng(seed, "settings").choice(PARAMETERS["mode"])}
    mode = _mode(settings)
    train, test = input_bank(seed)
    solve = scan_only if mode == "scan_only" else scan_then_rle

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": solve(grid)}

    return {
        "train": [pair(grid) for grid in train[:demos]],
        "test": [pair(grid) for grid in test[:queries]],
        "program_solution": program(settings),
    }
