"""Native parametric adapter for exact yellow-bar target length.

The canonical/default setting targets length three exactly.  The alternate
setting targets length four while preserving monochrome 4-connectivity,
straightness, independent cap availability, cap color 8, and all distractors.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "d48317a7c7c8"
ALLOWED_TARGET_LENGTHS = (3, 4)
DEFAULT_SETTINGS = {"target_length": 3}
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

_DEMO_SIZES = ((12, 12), (14, 16), (16, 14), (18, 18), (20, 22), (22, 20))
_QUERY_SIZES = ((13, 17), (17, 13), (24, 24), (30, 30))


def _validate_count(name: str, value: int, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an integer in [{lo},{hi}]")
    return value


def _settings(settings: dict[str, Any] | None) -> dict[str, int]:
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        raise TypeError("settings must be a dictionary")
    unknown = sorted(set(settings) - {"target_length"})
    if unknown:
        raise ValueError(f"unknown setting(s): {', '.join(unknown)}")
    value = settings.get("target_length", DEFAULT_SETTINGS["target_length"])
    if type(value) is not int or value not in ALLOWED_TARGET_LENGTHS:
        raise ValueError(f"target_length must be one of {ALLOWED_TARGET_LENGTHS}")
    return {"target_length": value}


@lru_cache(maxsize=1)
def _canonical_program() -> str:
    rows = []
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}")
    return str(rows[0]["program_solution"])


def program(settings: dict[str, Any] | None = None) -> str:
    selected = _settings(settings)
    length = selected["target_length"]
    canonical = _canonical_program()
    if length == 3:
        return canonical

    replacements = (
        ("(= (obj-size o) 3)", f"(= (obj-size o) {length})", 1),
        ("(= (- hi lo) 2)", f"(= (- hi lo) {length - 1})", 2),
        ("(= (length cs) 3)", f"(= (length cs) {length})", 1),
        ("(= (length rs) 3)", f"(= (length rs) {length})", 1),
    )
    rendered = canonical
    for old, new, expected in replacements:
        if rendered.count(old) != expected:
            raise ValueError(f"canonical source occurrence drift for {old!r}")
        rendered = rendered.replace(old, new)
    return rendered


def _neighbors(cell: tuple[int, int]):
    row, col = cell
    yield row - 1, col
    yield row + 1, col
    yield row, col - 1
    yield row, col + 1


def _yellow_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 4
    }
    result = []
    while remaining:
        start = min(remaining)
        stack = [start]
        component = {start}
        remaining.remove(start)
        while stack:
            cell = stack.pop()
            for neighbor in _neighbors(cell):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _ends(cells: set[tuple[int, int]], length: int) -> tuple[tuple[int, int], ...]:
    rows = sorted({row for row, _ in cells})
    cols = sorted({col for _, col in cells})
    if len(cells) != length:
        return ()
    if len(rows) == 1 and len(cols) == length and cols[-1] - cols[0] == length - 1:
        return ((rows[0], cols[0] - 1), (rows[0], cols[-1] + 1))
    if len(cols) == 1 and len(rows) == length and rows[-1] - rows[0] == length - 1:
        return ((rows[0] - 1, cols[0]), (rows[-1] + 1, cols[0]))
    return ()


def apply_python(grid: list[list[int]], target_length: int) -> list[list[int]]:
    _settings({"target_length": target_length})
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
        or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid)
        or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)
    ):
        raise ValueError("grid must be a nonempty rectangular ARC integer grid")
    height, width = len(grid), len(grid[0])
    output = deepcopy(grid)
    for cells in _yellow_components(grid):
        for row, col in _ends(cells, target_length):
            if 0 <= row < height and 0 <= col < width and grid[row][col] == 0:
                output[row][col] = 8
    return output


def _put(grid: list[list[int]], cells: list[tuple[int, int]], color: int) -> None:
    for row, col in cells:
        if grid[row][col] != 0:
            raise ValueError(f"scene collision at {(row, col)}")
        grid[row][col] = color


def _can_place_yellow(
    grid: list[list[int]], cells: list[tuple[int, int]], caps: list[tuple[int, int]]
) -> bool:
    height, width = len(grid), len(grid[0])
    selected = set(cells)
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells + caps):
        return False
    if any(grid[row][col] != 0 for row, col in cells + caps):
        return False
    for cell in cells:
        for row, col in _neighbors(cell):
            if (row, col) not in selected and 0 <= row < height and 0 <= col < width:
                if grid[row][col] == 4:
                    return False
    return True


def _try_extra_bar(
    grid: list[list[int]], *, row: int, col: int, length: int, horizontal: bool
) -> bool:
    if horizontal:
        cells = [(row, col + offset) for offset in range(length)]
        caps = [(row, col - 1), (row, col + length)]
    else:
        cells = [(row + offset, col) for offset in range(length)]
        caps = [(row - 1, col), (row + length, col)]
    if not _can_place_yellow(grid, cells, caps):
        return False
    _put(grid, cells, 4)
    return True


def _scene(seed: int, ordinal: int, height: int, width: int) -> list[list[int]]:
    rng = random.Random((seed << 17) ^ (ordinal * 0x9E3779B1) ^ 0xD48317A7)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    # Two actionable examples of each supported length.  One length-three bar
    # has an occupied cap, keeping the independent-endpoint branch visible.
    _put(grid, [(2, col) for col in range(2, 5)], 4)
    grid[2][1] = 6
    _put(grid, [(row, width - 3) for row in range(2, 6)], 4)
    _put(grid, [(height - 3, col) for col in range(2, 6)], 4)
    _put(grid, [(height - 5, col) for col in range(width - 6, width - 3)], 4)

    # Canonical distractors: wrong color straight three and a bent yellow three.
    wrong = rng.choice((1, 2, 3, 5, 6, 7, 9))
    mid = width // 2
    _put(grid, [(1, mid - 1), (1, mid), (1, mid + 1)], wrong)
    bend_row = height // 2
    _put(grid, [(bend_row, 2), (bend_row + 1, 2), (bend_row + 1, 3)], 4)

    # Larger canvases carry multiple actionable bars across the interior, so the
    # 30x30 stress is not a padded small puzzle.  Both settings act repeatedly.
    target_each = 0 if min(height, width) < 20 else (3 if min(height, width) < 24 else 5)
    added = {3: 0, 4: 0}
    candidates = [
        (row, col, horizontal)
        for row in range(4, height - 5, 3)
        for col in range(7, width - 6, 5)
        for horizontal in (True, False)
    ]
    rng.shuffle(candidates)
    for length in (3, 4):
        for row, col, horizontal in candidates:
            if added[length] >= target_each:
                break
            if _try_extra_bar(
                grid, row=row, col=col, length=length, horizontal=horizontal
            ):
                added[length] += 1
        if added[length] < target_each:
            raise RuntimeError(f"could not place {target_each} extra length-{length} bars")

    protected = set()
    for cells in _yellow_components(grid):
        for cap in _ends(cells, len(cells)):
            if 0 <= cap[0] < height and 0 <= cap[1] < width:
                protected.add(cap)
    extra_colors = (1, 2, 3, 5, 6, 7, 9)
    for _ in range(max(3, (height * width) // 80)):
        for _attempt in range(200):
            cell = (rng.randrange(height), rng.randrange(width))
            if cell not in protected and grid[cell[0]][cell[1]] == 0:
                grid[cell[0]][cell[1]] = rng.choice(extra_colors)
                break

    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    if rng.randrange(2):
        grid = list(reversed(grid))
    return grid


def _episode_inputs(seed: int, demos: int, queries: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    train = [
        _scene(seed, index, *_DEMO_SIZES[index])
        for index in range(demos)
    ]
    test = [
        _scene(seed, 100 + index, *_QUERY_SIZES[index])
        for index in range(queries)
    ]
    all_inputs = train + test
    serialized = {json.dumps(grid, separators=(",", ":")) for grid in all_inputs}
    if len(serialized) != len(all_inputs):
        raise RuntimeError("episode input sampler produced a duplicate")
    return train, test


def generate(
    seed: int,
    settings: dict[str, Any] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    demos = _validate_count("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _validate_count("queries", queries, MIN_QUERIES, MAX_QUERIES)
    selected = _settings(settings)
    target_length = selected["target_length"]
    train_inputs, test_inputs = _episode_inputs(seed, demos, queries)

    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {"input": grid, "output": apply_python(grid, target_length)}

    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program(selected),
    }
