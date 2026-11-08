"""Native midpoint-collapse family for 2fc4ca4ea6c4.

``midpoints`` is the exact selected canonical rule. ``connect_aligned`` first
collapses every horizontal same-color run to its midpoint, then connects pairs
of equal-colored midpoint cells that align in a column across empty space.
Inputs are independent of the private setting.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
MODES = ("midpoints", "connect_aligned")
DEFAULT = {"completion_mode": "midpoints"}


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"completion_mode"}
            or type(settings["completion_mode"]) is not str
            or settings["completion_mode"] not in MODES):
        raise ValueError("settings must contain only a supported completion_mode")
    return settings["completion_mode"]


def program(settings) -> str:
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "midpoints" else "connect_aligned.rkt"
    return (HERE / name).read_text()


def _validate_grid(grid) -> tuple[int, int]:
    if (type(grid) is not list or not 3 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 3 <= len(grid[0]) <= 30):
        raise ValueError("expected a rectangular 3..30 grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid cells must be exact ARC integer colors")
    return len(grid), width


def stage_a(grid):
    """Return the canonical input-dependent grid of horizontal run midpoints."""
    height, width = _validate_grid(grid)
    out = [[0] * width for _ in range(height)]
    for row in range(height):
        column = 0
        while column < width:
            value = grid[row][column]
            if value == 0:
                column += 1
                continue
            start = column
            while column < width and grid[row][column] == value:
                column += 1
            end = column - 1
            out[row][(start + end) // 2] = value
    return out


def stage_b(midpoints):
    """Connect exactly two same-color aligned midpoint cells through zeroes."""
    height, width = _validate_grid(midpoints)
    source = [list(row) for row in midpoints]
    out = [list(row) for row in midpoints]
    for column in range(width):
        colors = []
        for row in range(height):
            value = source[row][column]
            if value and value not in colors:
                colors.append(value)
        for color in colors:
            hits = [row for row in range(height) if source[row][column] == color]
            if len(hits) != 2:
                continue
            first, last = hits
            if all(source[row][column] == 0 for row in range(first + 1, last)):
                for row in range(first, last + 1):
                    out[row][column] = color
    return out


def solve(grid, completion_mode="midpoints"):
    if type(completion_mode) is not str or completion_mode not in MODES:
        raise ValueError("unknown completion mode")
    midpoint_grid = stage_a(grid)
    return midpoint_grid if completion_mode == "midpoints" else stage_b(midpoint_grid)


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"2fc4ca4ea6c4-parametric-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _put_run(grid, row: int, center: int, length: int, color: int) -> None:
    if length < 1 or length % 2 == 0:
        raise ValueError("run length must be positive and odd")
    start = center - length // 2
    end = center + length // 2
    if not (0 <= row < len(grid) and 0 <= start <= end < len(grid[0])):
        raise ValueError("run does not fit")
    if any(grid[row][column] != 0 for column in range(start, end + 1)):
        raise ValueError("run placement collision")
    if start > 0 and grid[row][start - 1] != 0:
        raise ValueError("run lacks left separator")
    if end + 1 < len(grid[0]) and grid[row][end + 1] != 0:
        raise ValueError("run lacks right separator")
    for column in range(start, end + 1):
        grid[row][column] = color


def _odd_at_most(value: int) -> int:
    value = max(1, value)
    return value if value % 2 else value - 1


def _profile(seed: int, split: str, index: int):
    demo_sizes = ((9, 13), (12, 16), (14, 18), (18, 22), (22, 26), (24, 28))
    query_sizes = ((10, 14), (18, 24), (30, 30), (26, 29))
    height, width = (demo_sizes if split == "train" else query_sizes)[index]
    rng = _rng(seed, split, index)
    grid = [[0] * width for _ in range(height)]

    pair_count = 2 if height < 14 else 3 if height < 20 else 4 if height < 27 else 6
    row_points = [round(i * (height - 1) / (2 * pair_count - 1))
                  for i in range(2 * pair_count)]
    row_pairs = [(row_points[i], row_points[-1 - i]) for i in range(pair_count)]
    colors = list(range(1, 10))
    rng.shuffle(colors)

    max_length = _odd_at_most(min(11, width))
    fractions = (0.12, 0.88, 0.50, 0.28, 0.72, 0.42)
    main_centers = []
    for pair_index, (top, bottom) in enumerate(row_pairs):
        if pair_index == 0:
            boundary_length = min(7, max_length)
            center = boundary_length // 2
            choices = [boundary_length]
        elif pair_index == 1:
            boundary_length = min(7, max_length)
            center = width - 1 - boundary_length // 2
            choices = [boundary_length]
        else:
            center = round(fractions[pair_index] * (width - 1))
            room = 2 * min(center, width - 1 - center) + 1
            choices = [value for value in (3, 5, 7, 9, 11)
                       if value <= min(max_length, room)]
        main_centers.append(center)
        length_top = rng.choice(choices)
        length_bottom = rng.choice(choices)
        color = colors[pair_index]
        _put_run(grid, top, center, length_top, color)
        _put_run(grid, bottom, center, length_bottom, color)

    used_rows = {row for pair in row_pairs for row in pair}
    free_rows = [row for row in range(height) if row not in used_rows]
    if len(free_rows) < 3:
        raise ValueError("profile lacks rows for connector guard examples")
    guard_rows = (free_rows[0], free_rows[len(free_rows) // 2], free_rows[-1])
    branch_columns = [column for column in range(1, width - 1)
                      if column not in set(main_centers)]
    branch_column = min(branch_columns, key=lambda column: (abs(column - width // 2), column))
    branch_color = colors[pair_count]

    if index % 2 == 0:
        # Exactly two equal-colored endpoints exist, but a different midpoint
        # blocks their column.  This teaches the clear-path guard.
        _put_run(grid, guard_rows[0], branch_column, 1, branch_color)
        _put_run(grid, guard_rows[2], branch_column, 1, branch_color)
        _put_run(grid, guard_rows[1], branch_column, 1, colors[pair_count + 1])
    else:
        # Three equal-colored aligned midpoints must remain unconnected.  This
        # teaches that the connector requires exactly two endpoints.
        for row in guard_rows:
            _put_run(grid, row, branch_column, 1, branch_color)

    if rng.randrange(2):
        grid.reverse()
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    return grid


def generate(seed, settings, demos, queries):
    mode = _mode(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    banks = {
        "train": [_profile(seed, "train", index) for index in range(6)],
        "test": [_profile(seed, "test", index) for index in range(4)],
    }
    result = {}
    for split, count in (("train", demos), ("test", queries)):
        result[split] = [
            {"input": copy.deepcopy(grid), "output": solve(grid, mode)}
            for grid in banks[split][:count]
        ]
    return {**result, "program_solution": program(settings), "seed": seed,
            "settings": copy.deepcopy(settings)}


def public_turn(episode, query_index):
    _integer(query_index, 0, 3, "query_index")
    if (type(episode) is not dict or type(episode.get("train")) is not list
            or type(episode.get("test")) is not list
            or query_index >= len(episode["test"])):
        raise ValueError("episode does not contain the requested query")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
