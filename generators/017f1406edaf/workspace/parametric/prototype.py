#!/usr/bin/env python3
"""Native episode generator for the 017f1406edaf blue-count scope family.

The exact canonical/default setting counts blue cells in row 0.  The alternate
setting counts every blue cell in the input.  Both then select the first
nonblue object that does not touch row 0 and whose area equals that input-
derived count, returning a blank grid with only that object painted cyan.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "017f1406edaf"
PARAMETER_NAME = "count_scope"
COUNT_SCOPES = ("row0", "all_blue")
DEFAULT_COUNT_SCOPE = "row0"
PROTOTYPE_VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent
RULE_PATHS = {
    "row0": HERE / "rules" / "count_row0.rkt",
    "all_blue": HERE / "rules" / "count_all_blue.rkt",
}
CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))


@dataclass(frozen=True)
class Component:
    color: int
    cells: tuple[tuple[int, int], ...]

    @property
    def size(self) -> int:
        return len(self.cells)

    @property
    def touches_row0(self) -> bool:
        return any(row == 0 for row, _ in self.cells)

    @property
    def first(self) -> tuple[int, int]:
        return min(self.cells)


def _scope(value: str) -> str:
    if type(value) is not str or value not in COUNT_SCOPES:
        raise ValueError(f"count_scope must be one of {COUNT_SCOPES}, got {value!r}")
    return value


def program_for(count_scope: str) -> str:
    scope = _scope(count_scope)
    path = RULE_PATHS[scope]
    if not path.is_file():
        raise FileNotFoundError(path)
    source = path.read_text(encoding="utf-8")
    if not source.startswith("(rule!"):
        raise ValueError(f"expected one standalone rule! expression: {path}")
    return source


def choose_parameters(seed: int) -> dict[str, str]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return {PARAMETER_NAME: COUNT_SCOPES[seed % len(COUNT_SCOPES)]}


def _validate_grid(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty row list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer colors in 0..9")
    return [row[:] for row in grid]


def components(grid: list[list[int]]) -> list[Component]:
    source = _validate_grid(grid)
    height, width = len(source), len(source[0])
    seen: set[tuple[int, int]] = set()
    result: list[Component] = []
    for row in range(height):
        for col in range(width):
            if source[row][col] == 0 or (row, col) in seen:
                continue
            color = source[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in CARDINAL:
                    nxt = current[0] + dr, current[1] + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and source[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(Component(color, tuple(sorted(cells))))
    return result


def target_count(grid: list[list[int]], count_scope: str) -> int:
    source = _validate_grid(grid)
    scope = _scope(count_scope)
    if scope == "row0":
        return sum(value == 1 for value in source[0])
    return sum(value == 1 for row in source for value in row)


def selected_component(grid: list[list[int]], count_scope: str) -> Component:
    target = target_count(grid, count_scope)
    selected = next(
        (
            component
            for component in components(grid)
            if component.color != 1
            and not component.touches_row0
            and component.size == target
        ),
        None,
    )
    if selected is None:
        raise ValueError(f"no eligible nonblue object has area {target}")
    return selected


def selected_cells(grid: list[list[int]], count_scope: str) -> tuple[tuple[int, int], ...]:
    return selected_component(grid, count_scope).cells


def python_reference(
    grid: list[list[int]], *, count_scope: str
) -> list[list[int]]:
    source = _validate_grid(grid)
    selected = selected_component(source, count_scope)
    output = [[0 for _ in row] for row in source]
    for row, col in selected.cells:
        output[row][col] = 8
    return output


def _seed(seed: int, pair_index: int, label: str) -> int:
    digest = hashlib.sha256(
        f"017f-count-scope:v1:{seed}:{pair_index}:{label}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big")


def _normalize(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    minimum_row = min(row for row, _ in cells)
    minimum_col = min(col for _, col in cells)
    return sorted((row - minimum_row, col - minimum_col) for row, col in cells)


def _shape(area: int, variant: int) -> list[tuple[int, int]]:
    if type(area) is not int or area < 1:
        raise ValueError("shape area must be a positive integer")
    width = 2 if area <= 6 else 3
    cells = [(index // width, index % width) for index in range(area)]
    transform = variant % 8
    transformed: list[tuple[int, int]] = []
    for row, col in cells:
        if transform & 4:
            col = -col
        for _ in range(transform % 4):
            row, col = col, -row
        transformed.append((row, col))
    return _normalize(transformed)


def _place(
    grid: list[list[int]],
    shape: list[tuple[int, int]],
    *,
    top: int,
    left: int,
    color: int,
) -> tuple[tuple[int, int], ...]:
    height, width = len(grid), len(grid[0])
    cells = tuple((top + row, left + col) for row, col in shape)
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
        raise ValueError("shape does not fit its slot")
    if any(grid[row][col] != 0 for row, col in cells):
        raise ValueError("shape overlaps an occupied cell")
    for row, col in cells:
        grid[row][col] = color
    return tuple(sorted(cells))


def _place_in_slot(
    grid: list[list[int]],
    area: int,
    variant: int,
    slot: tuple[int, int, int, int],
    color: int,
) -> tuple[tuple[int, int], ...]:
    shape = _shape(area, variant)
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    row0, col0, slot_h, slot_w = slot
    if shape_h > slot_h or shape_w > slot_w:
        # A 90-degree turn is the only alternate bounding box needed for the
        # compact shapes used here.
        shape = _normalize([(col, -row) for row, col in shape])
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
    if shape_h > slot_h or shape_w > slot_w:
        raise ValueError((area, variant, slot, shape_h, shape_w))
    top = row0 + (slot_h - shape_h) // 2
    left = col0 + (slot_w - shape_w) // 2
    return _place(grid, shape, top=top, left=left, color=color)


def _ordinary_input(seed: int, pair_index: int) -> list[list[int]]:
    rng = random.Random(_seed(seed, pair_index, "ordinary"))
    height = 16 + rng.randrange(5)
    width = 17 + rng.randrange(5)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    row0_target = 2 + rng.randrange(5)
    extra_blue = 1 + rng.randrange(4)
    all_blue_target = row0_target + extra_blue

    # A nonblue component touching row 0 exercises the source rule's exclusion.
    # Alternate its area so both count settings see an occasional tempting decoy.
    row0_decoy_area = row0_target if pair_index % 2 == 0 else all_blue_target
    for row in range(row0_decoy_area):
        grid[row][0] = 4

    marker_columns = sorted(rng.sample(range(3, width), row0_target))
    for col in marker_columns:
        grid[0][col] = 1

    palette = rng.sample([2, 3, 5, 6, 7, 9], 5)
    top_slot = (2, 3, 5, 6)
    bottom_slot = (height - 6, width - 8, 5, 6)
    if pair_index % 2 == 0:
        row_slot, all_slot = top_slot, bottom_slot
    else:
        row_slot, all_slot = bottom_slot, top_slot

    row_cells = _place_in_slot(
        grid, row0_target, pair_index, row_slot, palette[0]
    )
    all_cells = _place_in_slot(
        grid, all_blue_target, pair_index + 3, all_slot, palette[1]
    )

    middle_row = height // 2 - 2
    _place_in_slot(
        grid,
        extra_blue,
        pair_index + 5,
        (middle_row, width // 2 - 2, 4, 5),
        1,
    )

    available_sizes = [
        size for size in (1, 2, 3, 4, 5, 7, 8) if size not in {row0_target, all_blue_target}
    ]
    distractor_sizes = available_sizes[:2]
    _place_in_slot(
        grid,
        distractor_sizes[0],
        pair_index + 1,
        (middle_row, 2, 4, 4),
        palette[2],
    )
    _place_in_slot(
        grid,
        distractor_sizes[1],
        pair_index + 2,
        (middle_row, width - 6, 4, 4),
        palette[3],
    )

    # Verify construction rather than relying on slot intuition.
    if target_count(grid, "row0") != row0_target:
        raise AssertionError("row-0 count construction failed")
    if target_count(grid, "all_blue") != all_blue_target:
        raise AssertionError("all-blue count construction failed")
    if selected_cells(grid, "row0") != row_cells:
        raise AssertionError("row-0 target object construction failed")
    if selected_cells(grid, "all_blue") != all_cells:
        raise AssertionError("all-blue target object construction failed")
    if python_reference(grid, count_scope="row0") == python_reference(
        grid, count_scope="all_blue"
    ):
        raise AssertionError("count settings must disagree")
    return grid


def build_stress_input(seed: int) -> list[list[int]]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    grid = [[0 for _ in range(30)] for _ in range(30)]
    row0_target = 6
    all_blue_target = 10
    for col in (1, 6, 11, 18, 23, 28):
        grid[0][col] = 1
    _place(grid, _shape(4, seed), top=2, left=13, color=1)
    _place(grid, _shape(row0_target, seed + 1), top=2, left=2, color=2)
    _place(grid, _shape(all_blue_target, seed + 2), top=2, left=23, color=3)
    for row in range(row0_target):
        grid[row][16] = 4

    # Substantive canvas-spanning distractors. Their areas avoid 6 and 10.
    bars = (
        (7, 2, 11, 5),
        (10, 8, 12, 6),
        (13, 1, 13, 7),
        (16, 12, 14, 9),
        (19, 3, 15, 5),
        (22, 10, 16, 6),
        (25, 1, 17, 7),
        (28, 9, 18, 9),
    )
    for row, col, length, color in bars:
        for offset in range(length):
            grid[row][col + offset] = color

    if target_count(grid, "row0") != row0_target:
        raise AssertionError("stress row-0 count failed")
    if target_count(grid, "all_blue") != all_blue_target:
        raise AssertionError("stress all-blue count failed")
    if len(selected_cells(grid, "row0")) != row0_target:
        raise AssertionError("stress row-0 target failed")
    if len(selected_cells(grid, "all_blue")) != all_blue_target:
        raise AssertionError("stress all-blue target failed")
    if python_reference(grid, count_scope="row0") == python_reference(
        grid, count_scope="all_blue"
    ):
        raise AssertionError("stress settings must disagree")
    return grid


def build_input(seed: int, pair_index: int) -> list[list[int]]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer (not bool)")
    return _ordinary_input(seed, pair_index)


def build_episode(
    seed: int,
    *,
    count_scope: str | None = None,
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    scope = choose_parameters(seed)[PARAMETER_NAME] if count_scope is None else _scope(count_scope)
    grids = [build_input(seed, index) for index in range(demos + queries)]
    if queries == 4:
        grids[-1] = build_stress_input(seed)
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in grids]
    if len(serialized) != len(set(serialized)):
        raise AssertionError("episode inputs must be distinct")
    pairs = [
        {
            "input": deepcopy(grid),
            "output": python_reference(grid, count_scope=scope),
        }
        for grid in grids
    ]
    return {
        "schema": "arcpuzzles-parametric-count-scope-episode-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter": {PARAMETER_NAME: scope},
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(scope),
    }


def generate_episode(seed: int, count_scope: str, demos: int, queries: int) -> dict[str, Any]:
    episode = build_episode(
        seed, count_scope=count_scope, demos=demos, queries=queries
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "arcpuzzles-parametric-count-scope-public-v1",
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }
