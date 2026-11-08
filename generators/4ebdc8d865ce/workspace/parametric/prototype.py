"""Episode-fixed orthogonal-degree variants for ARC task 4ebdc8d865ce.

The exact canonical rule recolors color-2 cells with zero orthogonal color-2
neighbors.  The alternate rule recolors color-2 cells with exactly one such
neighbor.  Inputs are setting-neutral and deliberately contain singleton,
pair, path, branch, block, boundary, interior, and diagonal-contact cases.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable, Sequence

TASK_ID = "4ebdc8d865ce"
SETTINGS = ({"target_degree": 0}, {"target_degree": 1})
DEFAULT = {"target_degree": 0}
DEMO_PROFILES = ((14, 14), (14, 18), (18, 14), (18, 18), (18, 22), (22, 18))
QUERY_PROFILES = ((14, 22), (22, 22), (26, 30), (30, 30))

_CANONICAL_PATH = Path(__file__).with_name("canonical.rkt")
CANONICAL_PROGRAM = _CANONICAL_PATH.read_text(encoding="utf-8")


def _degree_program(target: int, *, diagonals: bool = False) -> str:
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonals:
        offsets += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    terms = []
    for dr, dc in offsets:
        row = "r" if dr == 0 else f"({'+' if dr > 0 else '-'} r {abs(dr)})"
        col = "c" if dc == 0 else f"({'+' if dc > 0 else '-'} c {abs(dc)})"
        row_guard = "#t" if dr == 0 else (f"(< r (- h {abs(dr)}))" if dr > 0 else f"(>= r {abs(dr)})")
        col_guard = "#t" if dc == 0 else (f"(< c (- w {abs(dc)}))" if dc > 0 else f"(>= c {abs(dc)})")
        guards = [guard for guard in (row_guard, col_guard) if guard != "#t"]
        guard = guards[0] if len(guards) == 1 else f"(and {' '.join(guards)})"
        if not guards:
            guard = "#t"
        terms.append(f"(if (and {guard} (= 2 (at g {row} {col}))) 1 0)")
    return (
        "(rule! (lambda (g)\n"
        "         (let ((h (rows g))\n"
        "               (w (cols g)))\n"
        "           (map-grid g\n"
        "                     (lambda (r c v)\n"
        "                       (if (!= v 2)\n"
        "                           v\n"
        "                           (let ((degree\n"
        f"                                  (+ {' '.join(terms)})))\n"
        f"                             (if (= degree {target}) 1 2))))))))"
    )


DEGREE_ONE_PROGRAM = _degree_program(1)
EIGHT_NEIGHBOR_DEGREE_ZERO_PROGRAM = _degree_program(0, diagonals=True)

# Every motif fits inside a 3x3 tile.  The diagonal pair is deliberately two
# separate 4-connected components, which distinguishes 4- from 8-connectivity.
_MOTIFS: dict[str, tuple[tuple[int, int], ...]] = {
    "diagonal_pair": ((0, 0), (1, 1)),
    "horizontal_domino": ((0, 0), (0, 1)),
    "vertical_domino": ((0, 0), (1, 0)),
    "line3": ((0, 0), (0, 1), (0, 2)),
    "el3": ((0, 0), (1, 0), (1, 1)),
    "tee4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "block4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "plus5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "singleton": ((0, 0),),
    "zigzag4": ((0, 0), (0, 1), (1, 1), (1, 2)),
}


def _integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    return value


def _settings(value: Any) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"target_degree"}:
        raise ValueError("settings must contain exactly target_degree")
    target = value["target_degree"]
    if type(target) is not int:
        raise TypeError("target_degree must be an integer (not bool)")
    if target not in (0, 1):
        raise ValueError("target_degree must be 0 or 1")
    return {"target_degree": target}


def program(settings: Any) -> str:
    target = _settings(settings)["target_degree"]
    return CANONICAL_PROGRAM if target == 0 else DEGREE_ONE_PROGRAM


def _rectangular(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    if not isinstance(grid, Sequence) or isinstance(grid, (str, bytes)) or not grid:
        raise ValueError("grid must be a non-empty rectangular sequence")
    first = grid[0]
    if not isinstance(first, Sequence) or isinstance(first, (str, bytes)) or not first:
        raise ValueError("grid must be a non-empty rectangular sequence")
    width = len(first)
    if any(
        not isinstance(row, Sequence)
        or isinstance(row, (str, bytes))
        or len(row) != width
        for row in grid
    ):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or value not in (0, 2) for row in grid for value in row):
        raise ValueError("cells must be integers from {0, 2}")
    return len(grid), width


def degree_map(grid: Sequence[Sequence[int]], *, diagonals: bool = False) -> list[list[int]]:
    height, width = _rectangular(grid)
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonals:
        offsets += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    result = [[-1] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2:
                continue
            result[row][col] = sum(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] == 2
                for dr, dc in offsets
            )
    return result


def _paint_by_map(
    grid: Sequence[Sequence[int]],
    values: Sequence[Sequence[int]],
    predicate: Callable[[int, int, int], bool],
) -> list[list[int]]:
    height, width = _rectangular(grid)
    if len(values) != height or any(len(row) != width for row in values):
        raise ValueError("intermediate map shape must match grid")
    output = deepcopy([list(row) for row in grid])
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 2 and predicate(int(values[row][col]), row, col):
                output[row][col] = 1
    return output


def transform(grid: Sequence[Sequence[int]], settings: Any) -> list[list[int]]:
    target = _settings(settings)["target_degree"]
    values = degree_map(grid)
    return _paint_by_map(grid, values, lambda degree, _row, _col: degree == target)


def _normalize(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(shape)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _orientations(shape: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    current = tuple(shape)
    values = set()
    for _ in range(4):
        values.add(_normalize(current))
        values.add(_normalize((row, -col) for row, col in current))
        current = tuple((col, -row) for row, col in current)
    bounded = [value for value in values if max(r for r, _ in value) < 3 and max(c for _, c in value) < 3]
    return tuple(sorted(bounded))


def _place(grid: list[list[int]], origin: tuple[int, int], shape: Iterable[tuple[int, int]]) -> None:
    row0, col0 = origin
    cells = [(row0 + dr, col0 + dc) for dr, dc in shape]
    height, width = len(grid), len(grid[0])
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
        raise RuntimeError("motif escaped its scene")
    if any(grid[row][col] != 0 for row, col in cells):
        raise RuntimeError("motifs overlap")
    for row, col in cells:
        grid[row][col] = 2


def _flip(grid: list[list[int]], *, rows: bool, cols: bool) -> list[list[int]]:
    result = [list(row) for row in grid]
    if rows:
        result.reverse()
    if cols:
        result = [list(reversed(row)) for row in result]
    return result


def _scene(seed: int, role: str, index: int, shape: tuple[int, int]) -> list[list[int]]:
    height, width = shape
    if height < 14 or width < 14 or height > 30 or width > 30:
        raise ValueError("degree scenes require dimensions in [14, 30]")
    rng = random.Random(f"{TASK_ID}:degree-family-v1:{seed}:{role}:{index}")
    grid = [[0] * width for _ in range(height)]
    row_origins = list(range(0, height - 2, 4))
    col_origins = list(range(0, width - 2, 4))
    origins = [(row, col) for row in row_origins for col in col_origins]
    required = [(0, 0), (0, 4), (4, 0)]
    if not all(origin in origins for origin in required):
        raise RuntimeError("scene has insufficient motif tiles")

    # Fixed edge cases: diagonal singletons, horizontal pair, vertical pair.
    _place(grid, (0, 0), _MOTIFS["diagonal_pair"])
    _place(grid, (0, 4), _MOTIFS["horizontal_domino"])
    _place(grid, (4, 0), _MOTIFS["vertical_domino"])

    remaining = [origin for origin in origins if origin not in required]
    rng.shuffle(remaining)
    mandatory = ["line3", "el3", "tee4", "block4", "plus5", "singleton"]
    extras = ["line3", "el3", "tee4", "block4", "plus5", "singleton", "zigzag4", "diagonal_pair"]
    names = mandatory + [rng.choice(extras) for _ in range(max(0, len(remaining) - len(mandatory)))]
    for origin, name in zip(remaining, names):
        choices = _orientations(_MOTIFS[name])
        _place(grid, origin, rng.choice(choices))

    # A three-cell empty margin after the last tile lets these touch the opposite
    # boundaries without accidentally joining the tiled components.
    _place(grid, (height - 1, 0), _MOTIFS["horizontal_domino"])
    _place(grid, (0, width - 1), _MOTIFS["vertical_domino"])
    _place(grid, (height - 1, width - 1), _MOTIFS["singleton"])

    grid = _flip(grid, rows=rng.random() < 0.5, cols=rng.random() < 0.5)
    if not any(value == 2 for row in grid for value in row):
        raise RuntimeError("empty scene")
    return grid


def _components(grid: Sequence[Sequence[int]]) -> list[set[tuple[int, int]]]:
    height, width = _rectangular(grid)
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 2}
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _candidate_transform(grid: Sequence[Sequence[int]], name: str) -> list[list[int]]:
    orth = degree_map(grid)
    height, width = _rectangular(grid)
    if name.startswith("target_degree_"):
        target = int(name.rsplit("_", 1)[1])
        return _paint_by_map(grid, orth, lambda degree, _r, _c: degree == target)
    if name == "degree_at_most_one":
        return _paint_by_map(grid, orth, lambda degree, _r, _c: degree <= 1)
    if name == "degree_two":
        return _paint_by_map(grid, orth, lambda degree, _r, _c: degree == 2)
    if name == "all_foreground":
        return _paint_by_map(grid, orth, lambda _degree, _r, _c: True)
    if name.startswith("horizontal_degree_"):
        target = int(name.rsplit("_", 1)[1])
        horizontal = [[-1] * width for _ in range(height)]
        for r in range(height):
            for c in range(width):
                if grid[r][c] == 2:
                    horizontal[r][c] = sum(
                        0 <= c + dc < width and grid[r][c + dc] == 2 for dc in (-1, 1)
                    )
        return _paint_by_map(grid, horizontal, lambda degree, _r, _c: degree == target)
    if name.startswith("vertical_degree_"):
        target = int(name.rsplit("_", 1)[1])
        vertical = [[-1] * width for _ in range(height)]
        for r in range(height):
            for c in range(width):
                if grid[r][c] == 2:
                    vertical[r][c] = sum(
                        0 <= r + dr < height and grid[r + dr][c] == 2 for dr in (-1, 1)
                    )
        return _paint_by_map(grid, vertical, lambda degree, _r, _c: degree == target)
    if name.startswith("eight_neighbor_degree_"):
        target = int(name.rsplit("_", 1)[1])
        eight = degree_map(grid, diagonals=True)
        return _paint_by_map(grid, eight, lambda degree, _r, _c: degree == target)
    if name == "component_size_two":
        selected = set().union(*(cells for cells in _components(grid) if len(cells) == 2))
        return _paint_by_map(grid, orth, lambda _degree, r, c: (r, c) in selected)
    if name.startswith("boundary_degree_"):
        target = int(name.rsplit("_", 1)[1])
        return _paint_by_map(
            grid,
            orth,
            lambda degree, r, c: degree == target and (r in (0, height - 1) or c in (0, width - 1)),
        )
    if name.startswith("interior_degree_"):
        target = int(name.rsplit("_", 1)[1])
        return _paint_by_map(
            grid,
            orth,
            lambda degree, r, c: degree == target and not (r in (0, height - 1) or c in (0, width - 1)),
        )
    raise KeyError(name)


CANDIDATE_NAMES = (
    "target_degree_0",
    "target_degree_1",
    "degree_at_most_one",
    "degree_two",
    "all_foreground",
    "horizontal_degree_0",
    "horizontal_degree_1",
    "vertical_degree_0",
    "vertical_degree_1",
    "eight_neighbor_degree_0",
    "eight_neighbor_degree_1",
    "component_size_two",
    "boundary_degree_0",
    "boundary_degree_1",
    "interior_degree_0",
    "interior_degree_1",
)


def fit_candidates(demos: Iterable[dict[str, Any]]) -> list[str]:
    pairs = list(demos)
    survivors = []
    for name in CANDIDATE_NAMES:
        try:
            if all(
                isinstance(pair, dict)
                and pair.get("output") == _candidate_transform(pair.get("input"), name)
                for pair in pairs
            ):
                survivors.append(name)
        except (KeyError, TypeError, ValueError):
            continue
    return survivors


def _pair(grid: list[list[int]], settings: dict[str, int]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": transform(grid, settings)}


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    chosen = _settings(settings)
    train = [
        _pair(_scene(seed, "demo", index, DEMO_PROFILES[index]), chosen)
        for index in range(demos)
    ]
    test = [
        _pair(_scene(seed, "query", index, QUERY_PROFILES[index]), chosen)
        for index in range(queries)
    ]
    expected = [f"target_degree_{chosen['target_degree']}"]
    if fit_candidates(train[:2]) != expected:
        raise RuntimeError(
            f"first two demonstrations do not identify {expected[0]}: {fit_candidates(train[:2])}"
        )
    serial = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(serial) != len(set(serial)):
        raise RuntimeError("episode contains duplicate inputs")
    return {
        "train": train,
        "test": test,
        "settings": chosen,
        "seed": seed,
        "program_solution": program(chosen),
        "certificate": {
            "candidate_names": list(CANDIDATE_NAMES),
            "survivors_after_two_demos": fit_candidates(train[:2]),
            "sequential_dependency": {
                "A": "count each color-2 cell's orthogonal color-2 neighbors",
                "intermediate": "per-cell orthogonal degree map",
                "B": "recolor exactly the cells whose degree equals the episode target_degree",
            },
        },
    }


def causal_witness() -> dict[str, Any]:
    grid = [
        [0, 0, 0, 0, 0, 0],
        [0, 2, 0, 2, 2, 0],
        [0, 0, 2, 0, 0, 0],
        [2, 2, 0, 0, 2, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    correct_map = degree_map(grid)
    wrong_map = degree_map(grid, diagonals=True)
    correct = _paint_by_map(grid, correct_map, lambda degree, _r, _c: degree == 0)
    wrong = _paint_by_map(grid, wrong_map, lambda degree, _r, _c: degree == 0)
    difference = sum(
        a != b for row_a, row_b in zip(correct, wrong) for a, b in zip(row_a, row_b)
    )
    return {
        "setting": {"target_degree": 0},
        "input": grid,
        "A": "orthogonal degree count",
        "intermediate": "correct_degree_map",
        "B": "recolor cells whose derived degree is zero",
        "correct_degree_map": correct_map,
        "wrong_intermediate": "eight-neighbor degree count",
        "wrong_eight_neighbor_degree_map": wrong_map,
        "correct_program": program({"target_degree": 0}),
        "wrong_program": EIGHT_NEIGHBOR_DEGREE_ZERO_PROGRAM,
        "correct_output": correct,
        "wrong_output": wrong,
        "difference_cells": difference,
    }
