"""Parametric three-panel agreement family for ARC task 083ba0fc4534.

The private episode setting chooses whether a nonzero color survives when it is
supported by at least two aligned panels (the exact canonical rule) or only when
all three panels agree.  Inputs are sampled independently of the setting.
"""
from __future__ import annotations

import copy
import functools
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root


TASK_ID = "083ba0fc4534"
FAMILY_VERSION = "1.0.0"
DIVIDER_COLOR = 5
BACKGROUND_COLOR = 0
ALLOWED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
AGREEMENTS = ("majority", "unanimous")
DEMO_LIMITS = (2, 6)
QUERY_COUNT = 4

# Input width is 3 * panel_width + 2.  Thus 29, not 30, is the largest
# lawful width under the canonical equal-panel grammar; height can reach 30.
DEMO_PROFILES = ((4, 4), (5, 5), (7, 6), (9, 7), (12, 8), (16, 9))
QUERY_PROFILES = ((5, 4), (12, 6), (21, 8), (30, 9))


@functools.lru_cache(maxsize=1)
def canonical_program() -> str:
    """Read the unique exact canonical Racket authority from this source tree."""
    root = find_root(__file__)
    programs: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise ValueError("canonical task row has no nonempty program_solution")
                programs.add(program)
    if len(programs) != 1:
        raise ValueError(f"expected one exact canonical program, found {len(programs)}")
    return next(iter(programs))


UNANIMOUS_PROGRAM = """(rule!
  (let* ((divs (filter (lambda (c)
                         (all? (lambda (r) (= (at g r c) 5)) (range 0 (rows g))))
                       (range 0 (cols g))))
         (d1 (first divs))
         (d2 (second divs)))
    (grid-from-fn (rows g) d1
      (lambda (r c)
        (let ((a (at g r c))
              (b (at g r (+ d1 1 c)))
              (x (at g r (+ d2 1 c))))
          (cond [(and (not (= a 0)) (= a b) (= a x)) a]
                [else 0]))))))"""


EXACTLY_TWO_PROGRAM = """(rule!
  (let* ((divs (filter (lambda (c)
                         (all? (lambda (r) (= (at g r c) 5)) (range 0 (rows g))))
                       (range 0 (cols g))))
         (d1 (first divs))
         (d2 (second divs)))
    (grid-from-fn (rows g) d1
      (lambda (r c)
        (let ((a (at g r c))
              (b (at g r (+ d1 1 c)))
              (x (at g r (+ d2 1 c))))
          (cond [(and (not (= a 0)) (= a b) (not (= a x))) a]
                [(and (not (= a 0)) (= a x) (not (= a b))) a]
                [(and (not (= b 0)) (= b x) (not (= b a))) b]
                [else 0]))))))"""


OCCUPANCY_PROGRAM = """(rule!
  (let* ((divs (filter (lambda (c)
                         (all? (lambda (r) (= (at g r c) 5)) (range 0 (rows g))))
                       (range 0 (cols g))))
         (d1 (first divs))
         (d2 (second divs)))
    (grid-from-fn (rows g) d1
      (lambda (r c)
        (let ((a (at g r c))
              (b (at g r (+ d1 1 c)))
              (x (at g r (+ d2 1 c))))
          (if (>= (+ (if (= a 0) 0 1)
                     (if (= b 0) 0 1)
                     (if (= x 0) 0 1))
                  2)
              (cond [(not (= a 0)) a]
                    [(not (= b 0)) b]
                    [else x])
              0))))))"""


def fixed_divider_program(agreement: str, *, d1: int = 4, d2: int = 9) -> str:
    """Racket rival that skips divider discovery and reuses a fixed intermediate."""
    _validate_agreement(agreement)
    if type(d1) is not int or type(d2) is not int or not 1 <= d1 < d2:
        raise ValueError("fixed divider columns must be ordered positive integers")
    if agreement == "majority":
        body = """(cond [(and (not (= a 0)) (or (= a b) (= a x))) a]
                [(and (not (= b 0)) (= b x)) b]
                [else 0])"""
    else:
        body = """(cond [(and (not (= a 0)) (= a b) (= a x)) a]
                [else 0])"""
    return f"""(rule!
  (let* ((d1 {d1})
         (d2 {d2}))
    (grid-from-fn (rows g) d1
      (lambda (r c)
        (let ((a (at g r c))
              (b (at g r (+ d1 1 c)))
              (x (at g r (+ d2 1 c))))
          {body})))))"""


def _validate_agreement(agreement: Any) -> str:
    if type(agreement) is not str or agreement not in AGREEMENTS:
        raise ValueError(f"agreement must be one of {list(AGREEMENTS)}")
    return agreement


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is forbidden)")
    if not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_counts(demos: Any, queries: Any) -> tuple[int, int]:
    for name, value in (("demos", demos), ("queries", queries)):
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer (bool is forbidden)")
    if not DEMO_LIMITS[0] <= demos <= DEMO_LIMITS[1]:
        raise ValueError(f"demos must be in {DEMO_LIMITS[0]}..{DEMO_LIMITS[1]}")
    if queries != QUERY_COUNT:
        raise ValueError(f"queries must equal {QUERY_COUNT}")
    return demos, queries


def program_for(agreement: str) -> str:
    agreement = _validate_agreement(agreement)
    return canonical_program() if agreement == "majority" else UNANIMOUS_PROGRAM


def _stream_rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}|{FAMILY_VERSION}|{seed}|{split}|{index}".encode()
    digest = hashlib.sha256(material).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _unique_positions(height: int, panel_width: int) -> list[tuple[int, int]]:
    proposed = [
        (0, 0),
        (0, panel_width - 1),
        (height - 1, 0),
        (height - 1, panel_width - 1),
        (height // 2, panel_width // 2),
        (0, panel_width // 2),
        (height - 1, panel_width // 2),
        (height // 2, 0),
        (height // 2, panel_width - 1),
    ]
    seen: set[tuple[int, int]] = set()
    ordered = []
    for position in proposed:
        if position not in seen:
            seen.add(position)
            ordered.append(position)
    return ordered


def _pattern(kind: str, colors: tuple[int, ...], index: int, rng: random.Random) -> tuple[int, int, int]:
    c0 = colors[index % len(colors)]
    c1 = colors[(index + 1) % len(colors)]
    if c1 == c0:
        raise AssertionError("palette colors must be distinct")
    if kind == "abc":
        return (c0, c0, c0)
    if kind == "ab":
        return (c0, c0, 0)
    if kind == "ax":
        return (c0, 0, c0)
    if kind == "bx":
        return (0, c0, c0)
    if kind == "singleton":
        values = [0, 0, 0]
        values[index % 3] = c0
        return tuple(values)
    if kind == "conflict":
        values = [0, 0, 0]
        pairs = ((0, 1), (0, 2), (1, 2))
        first, second = pairs[index % len(pairs)]
        if rng.randrange(2):
            c0, c1 = c1, c0
        values[first] = c0
        values[second] = c1
        return tuple(values)
    raise ValueError(f"unknown pattern kind {kind!r}")


def build_input(seed: int, split: str, index: int, height: int, panel_width: int) -> list[list[int]]:
    """Build one setting-independent, content-bearing three-panel input."""
    seed = _validate_seed(seed)
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")
    if type(height) is not int or type(panel_width) is not int:
        raise TypeError("height and panel_width must be exact integers")
    if not 4 <= height <= 30 or not 4 <= panel_width <= 9:
        raise ValueError("height must be 4..30 and panel_width must be 4..9")

    rng = _stream_rng(seed, split, index)
    palette_size = 3 if height * panel_width < 50 else 4
    colors = tuple(rng.sample(ALLOWED_COLORS, palette_size))
    local_area = height * panel_width
    target_active = min(local_area, max(10, round(local_area * 0.30)))

    required_kinds = [
        "abc",
        "ab",
        "ax",
        "bx",
        "conflict",
        "singleton",
        "singleton",
        "singleton",
        "conflict",
    ]
    boundary_positions = _unique_positions(height, panel_width)
    all_positions = [(row, col) for row in range(height) for col in range(panel_width)]
    remaining = [position for position in all_positions if position not in set(boundary_positions)]
    rng.shuffle(remaining)
    positions = boundary_positions + remaining[: max(0, target_active - len(boundary_positions))]

    filler_cycle = (
        "abc",
        "ab",
        "ax",
        "bx",
        "conflict",
        "singleton",
        "ab",
        "ax",
        "bx",
        "abc",
    )
    kinds = required_kinds + [
        filler_cycle[(offset + rng.randrange(len(filler_cycle))) % len(filler_cycle)]
        for offset in range(max(0, len(positions) - len(required_kinds)))
    ]
    kinds = kinds[: len(positions)]

    width = 3 * panel_width + 2
    d1 = panel_width
    d2 = 2 * panel_width + 1
    grid = [[BACKGROUND_COLOR for _ in range(width)] for _ in range(height)]
    for row in range(height):
        grid[row][d1] = DIVIDER_COLOR
        grid[row][d2] = DIVIDER_COLOR

    for pattern_index, ((row, col), kind) in enumerate(zip(positions, kinds, strict=True)):
        left, middle, right = _pattern(kind, colors, pattern_index, rng)
        grid[row][col] = left
        grid[row][d1 + 1 + col] = middle
        grid[row][d2 + 1 + col] = right
    return grid


def divider_columns(grid: list[list[int]]) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    dividers = [
        col
        for col in range(width)
        if all(type(grid[row][col]) is int and grid[row][col] == DIVIDER_COLOR for row in range(len(grid)))
    ]
    if len(dividers) != 2:
        raise ValueError(f"expected exactly two full-height dividers, found {dividers}")
    d1, d2 = dividers
    panel_width = d1
    if panel_width < 1 or d2 != 2 * panel_width + 1 or width != 3 * panel_width + 2:
        raise ValueError("dividers do not delimit three equal panels")
    if any(
        type(cell) is not int or not 0 <= cell <= 9
        for row in grid
        for cell in row
    ):
        raise ValueError("grid cells must be exact integer ARC colors")
    return d1, d2


def _triples(grid: list[list[int]]):
    d1, d2 = divider_columns(grid)
    for row in range(len(grid)):
        for col in range(d1):
            yield row, col, (
                grid[row][col],
                grid[row][d1 + 1 + col],
                grid[row][d2 + 1 + col],
            )


def solve(grid: list[list[int]], agreement: str) -> list[list[int]]:
    agreement = _validate_agreement(agreement)
    d1, _d2 = divider_columns(grid)
    output = [[0 for _ in range(d1)] for _ in range(len(grid))]
    for row, col, (a, b, x) in _triples(grid):
        if agreement == "majority":
            if a != 0 and (a == b or a == x):
                output[row][col] = a
            elif b != 0 and b == x:
                output[row][col] = b
        elif a != 0 and a == b == x:
            output[row][col] = a
    return output


def _kind(values: tuple[int, int, int]) -> str:
    a, b, x = values
    nonzero = [value for value in values if value != 0]
    if a != 0 and a == b == x:
        return "abc"
    if a != 0 and a == b and x != a:
        return "ab"
    if a != 0 and a == x and b != a:
        return "ax"
    if b != 0 and b == x and a != b:
        return "bx"
    if not nonzero:
        return "empty"
    if len(nonzero) == 1:
        return "singleton"
    return "conflict"


def input_metrics(grid: list[list[int]]) -> dict[str, Any]:
    d1, d2 = divider_columns(grid)
    counts: Counter[str] = Counter()
    active_positions: list[tuple[int, int]] = []
    for row, col, values in _triples(grid):
        kind = _kind(values)
        counts[kind] += 1
        if kind != "empty":
            active_positions.append((row, col))
    sides = []
    if any(row == 0 for row, _ in active_positions):
        sides.append("top")
    if any(row == len(grid) - 1 for row, _ in active_positions):
        sides.append("bottom")
    if any(col == 0 for _, col in active_positions):
        sides.append("left")
    if any(col == d1 - 1 for _, col in active_positions):
        sides.append("right")
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "panel_width": d1,
        "divider_columns": [d1, d2],
        "active_local_positions": len(active_positions),
        "active_boundary_sides": sorted(sides),
        "pattern_counts": dict(sorted(counts.items())),
    }


def generate_episode(seed: int, *, agreement: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _validate_seed(seed)
    agreement = _validate_agreement(agreement)
    demos, queries = _validate_counts(demos, queries)

    train = []
    for index, (height, panel_width) in enumerate(DEMO_PROFILES[:demos]):
        grid = build_input(seed, "demo", index, height, panel_width)
        train.append({"input": grid, "output": solve(grid, agreement)})

    test = []
    for index, (height, panel_width) in enumerate(QUERY_PROFILES[:queries]):
        grid = build_input(seed, "query", index, height, panel_width)
        test.append({"input": grid, "output": solve(grid, agreement)})

    serialized = [
        json.dumps(pair["input"], sort_keys=False, separators=(",", ":"))
        for pair in train + test
    ]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("episode sampler produced duplicate visible inputs")
    return {
        "train": copy.deepcopy(train),
        "test": copy.deepcopy(test),
        "program_solution": program_for(agreement),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    """Project exactly one query without exposing counts, settings, code or answers."""
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("episode/query_index is invalid")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }
