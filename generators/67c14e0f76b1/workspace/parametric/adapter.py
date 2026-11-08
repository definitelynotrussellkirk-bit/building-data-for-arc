"""Native parametric adapter for 67c14e0f76b1.

``mark_only`` is the exact canonical local gap-marking rule.  The
``largest_marked`` setting first performs that rule, then finds the unique
largest four-connected component made from newly marked color-2 cells and
recolors that component to 8.  All settings share the exact same inputs.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
from itertools import permutations
from pathlib import Path
import random
from typing import Any, Iterable

_HOME = Path(__file__).resolve().parent
_PROGRAMS = {
    "mark_only": _HOME / "canonical.rkt",
    "largest_marked": _HOME / "largest_marked.rkt",
}
_DEMO_SPECS = (
    (10, 15, "compact"),
    (11, 17, "offset"),
    (12, 19, "wide"),
    (14, 21, "mixed"),
    (16, 23, "dense"),
    (18, 25, "boundary"),
)
_QUERY_SPECS = (
    (12, 18, "transfer"),
    (16, 22, "boundary"),
    (22, 26, "dense"),
    (30, 30, "stress"),
)
_PERMUTATIONS = tuple(permutations((0, 1, 2)))
# The first three demonstrations place the largest marked stack at right,
# middle, then left.  That prefix refutes the row-major-first shortcut for
# every seed while later examples retain the remaining permutations.
_DEMO_PERMUTATION_INDICES = (0, 1, 4, 2, 3, 5)
Grid = list[list[int]]
Cell = tuple[int, int]


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _postprocess(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {"postprocess"}:
        raise ValueError("settings must contain exactly postprocess")
    value = settings["postprocess"]
    if type(value) is not str or value not in _PROGRAMS:
        raise ValueError("postprocess must be mark_only or largest_marked")
    return value


def program(settings: Any) -> str:
    return _PROGRAMS[_postprocess(settings)].read_text(encoding="utf-8")


def _grid(grid: Any) -> Grid:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty rectangular list")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid exceeds ARC bounds")
    output: Grid = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError("grid must be rectangular")
        copied: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("grid values must be integers in 0..9")
            copied.append(value)
        output.append(copied)
    return output


def target_cells(grid: Any) -> list[Cell]:
    source = _grid(grid)
    height, width = len(source), len(source[0])
    return [
        (r, c)
        for r in range(height)
        for c in range(1, width - 1)
        if source[r][c] == 0
        and source[r][c - 1] == 1
        and source[r][c + 1] == 1
    ]


def intermediate(grid: Any) -> Grid:
    source = _grid(grid)
    output = deepcopy(source)
    targets = target_cells(source)
    if not targets:
        raise ValueError("input must contain at least one immediate horizontal gap")
    for r, c in targets:
        output[r][c] = 2
    return output


def _components_of_color(grid: Grid, color: int) -> list[list[Cell]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == color
    }
    result: list[list[Cell]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells: list[Cell] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if cell in remaining:
                    remaining.remove(cell)
                    queue.append(cell)
        result.append(sorted(cells))
    return sorted(result, key=lambda cells: cells[0])


def marked_components(stage: Any) -> list[list[Cell]]:
    return _components_of_color(_grid(stage), 2)


def predict(grid: Any, postprocess: str) -> Grid:
    if postprocess not in _PROGRAMS:
        raise ValueError("unknown postprocess")
    stage = intermediate(grid)
    if postprocess == "mark_only":
        return stage
    components = marked_components(stage)
    if not components:
        raise ValueError("intermediate has no marked component")
    largest = max(len(cells) for cells in components)
    winners = [cells for cells in components if len(cells) == largest]
    if len(winners) != 1:
        raise ValueError("marked components must have a unique largest component")
    output = deepcopy(stage)
    for r, c in winners[0]:
        output[r][c] = 8
    return output


def wrong_order_predict(grid: Any) -> Grid:
    """Counterfactual: select/recolor the largest raw blue component first."""
    source = _grid(grid)
    components = _components_of_color(source, 1)
    if not components:
        raise ValueError("input has no blue component")
    # Mirror pick-max's first-maximum behavior deterministically.
    largest = max(len(cells) for cells in components)
    selected = next(cells for cells in components if len(cells) == largest)
    wrong_input = deepcopy(source)
    for r, c in selected:
        wrong_input[r][c] = 8
    return intermediate(wrong_input)


def _mix_seed(seed: int, role: str, index: int) -> int:
    raw = f"67c14e0f76b1|{seed}|{role}|{index}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _put_target_stack(grid: Grid, center_col: int, start: int, length: int) -> set[Cell]:
    cells: set[Cell] = set()
    for row in range(start, start + length):
        if grid[row][center_col - 1] != 0 or grid[row][center_col + 1] != 0:
            raise RuntimeError("target endpoint collision")
        grid[row][center_col - 1] = 1
        grid[row][center_col + 1] = 1
        cells.add((row, center_col))
    return cells


def _add_controls(grid: Grid, expected: set[Cell], seed: int) -> tuple[Cell, tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    starts = list(range(width - 3))
    columns = list(range(width))
    shift = seed % len(starts)
    starts = starts[shift:] + starts[:shift]
    shift = (seed // 7) % len(columns)
    columns = columns[shift:] + columns[:shift]
    for gap_start in starts:
        for column in columns:
            candidate = deepcopy(grid)
            candidate[height - 1][gap_start : gap_start + 4] = [1, 0, 0, 1]
            if column in (gap_start + 1, gap_start + 2):
                continue
            candidate[height - 3][column] = 1
            candidate[height - 2][column] = 0
            candidate[height - 1][column] = 1
            if set(target_cells(candidate)) != expected:
                continue
            if candidate[height - 1][gap_start : gap_start + 4] != [1, 0, 0, 1]:
                continue
            grid[:] = candidate
            return (height - 2, column), (height - 1, gap_start)
    raise RuntimeError("failed to place nonconfounding horizontal/vertical controls")


def _add_distractors(
    grid: Grid,
    protected: set[Cell],
    rng: random.Random,
    *,
    stress: bool,
) -> None:
    height, width = len(grid), len(grid[0])
    free = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 0 and (r, c) not in protected
    ]
    rng.shuffle(free)
    current = sum(value != 0 for row in grid for value in row)
    goal = 105 if stress else min(height * width // 4, current + max(12, height + width // 2))
    count = max(0, min(len(free), goal - current))
    palette = (3, 4, 5, 6, 7)
    for index, (r, c) in enumerate(free[:count]):
        grid[r][c] = palette[(index + rng.randrange(len(palette))) % len(palette)]


def _build_input(seed: int, role: str, index: int, spec: tuple[int, int, str]) -> Grid:
    height, width, profile = spec
    rng = random.Random(_mix_seed(seed, role, index))
    grid = [[0 for _ in range(width)] for _ in range(height)]
    centers = (1, width // 2, width - 2)
    sizes = (2, max(3, height // 3), height - 3)
    if len(set(sizes)) != 3:
        raise RuntimeError("target stack sizes must be unique")
    permutation_index = (
        _DEMO_PERMUTATION_INDICES[index]
        if role == "demo"
        else (seed + index + 3) % len(_PERMUTATIONS)
    )
    permutation = _PERMUTATIONS[permutation_index]
    lengths = [sizes[rank] for rank in permutation]
    expected: set[Cell] = set()
    for slot, (center, length) in enumerate(zip(centers, lengths)):
        room = height - 3 - length
        # Align demonstration stacks at the top so row-major component order
        # is governed by column, then vary which column receives the largest
        # stack. Queries retain independent vertical offsets.
        start = 0 if role == "demo" or room == 0 else rng.randrange(room + 1)
        expected.update(_put_target_stack(grid, center, start, length))
    vertical_center, wide_start = _add_controls(grid, expected, _mix_seed(seed, role + profile, index))
    protected = set(expected)
    protected.add(vertical_center)
    protected.update({(wide_start[0], wide_start[1] + 1), (wide_start[0], wide_start[1] + 2)})
    _add_distractors(grid, protected, rng, stress=(height, width) == (30, 30))
    actual = set(target_cells(grid))
    if actual != expected:
        raise RuntimeError(f"generated target set changed: expected {sorted(expected)!r}, got {sorted(actual)!r}")
    stage = intermediate(grid)
    components = marked_components(stage)
    component_sizes = sorted(len(cells) for cells in components)
    if component_sizes != sorted(sizes):
        raise RuntimeError(f"marked component sizes differ: {component_sizes!r} vs {sorted(sizes)!r}")
    if profile == "stress" and sum(value != 0 for row in grid for value in row) < 100:
        raise RuntimeError("30x30 stress input is too sparse")
    return grid


def _pair(grid: Grid, postprocess: str) -> dict[str, Grid]:
    return {"input": deepcopy(grid), "output": predict(grid, postprocess)}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    postprocess = _postprocess(settings)
    demo_inputs = [
        _build_input(seed, "demo", index, spec)
        for index, spec in enumerate(_DEMO_SPECS)
    ]
    query_inputs = [
        _build_input(seed, "query", index, spec)
        for index, spec in enumerate(_QUERY_SPECS)
    ]
    selected = demo_inputs[:demos] + query_inputs[:queries]
    if len({repr(grid) for grid in selected}) != len(selected):
        raise RuntimeError("episode inputs must be distinct")
    return {
        "train": [_pair(grid, postprocess) for grid in demo_inputs[:demos]],
        "test": [_pair(grid, postprocess) for grid in query_inputs[:queries]],
        "program_solution": program(settings),
    }
