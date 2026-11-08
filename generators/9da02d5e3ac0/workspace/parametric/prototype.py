"""Native row-fill / vertical-bridge family for ARC task 9da02d5e3ac0.

The default setting is the exact canonical per-row color-5 completion.  The
alternate first performs that same completion, then uses the completed grid as
an input-dependent intermediate: in each column, if all signal cells
(nonzero, non-5) share one color and there are at least two of them, zero cells
strictly between the first and last signal are bridged with that color.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "9da02d5e3ac0"
PARAMETER = "finish_rule"
FINISH_RULES = ("row_fill_only", "row_fill_then_vertical_bridge")

_DEMO_SHAPES = ((8, 10), (10, 12), (12, 14), (14, 16), (18, 20), (22, 24))
_QUERY_SHAPES = ((9, 13), (16, 18), (24, 26), (30, 30))
_SIGNAL_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer, not bool or a coercion")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _setting(settings: dict[str, str]) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER}
        or type(settings[PARAMETER]) is not str
        or settings[PARAMETER] not in FINISH_RULES
    ):
        raise ValueError(
            "settings must be exactly {'finish_rule': "
            "'row_fill_only'|'row_fill_then_vertical_bridge'}"
        )
    return settings[PARAMETER]


def program(settings: dict[str, str]) -> str:
    finish = _setting(settings)
    filename = "canonical.rkt" if finish == "row_fill_only" else "vertical_bridge.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = json.dumps(
        [TASK_ID, "row-fill-vertical-bridge-v1", seed, split, index],
        separators=(",", ":"),
    ).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _shape(split: str, index: int) -> tuple[int, int]:
    shapes = _DEMO_SHAPES if split == "train" else _QUERY_SHAPES
    _integer("index", index, 0, len(shapes) - 1)
    return shapes[index]


def _first_non5(row: list[int]) -> int | None:
    return next((value for value in row if value != 5), None)


def row_fill(grid: list[list[int]]) -> list[list[int]]:
    result = []
    for row in grid:
        key = _first_non5(row)
        result.append([key if value == 5 and key is not None else value for value in row])
    return result


def _signal_rows(grid: list[list[int]], column: int) -> list[int]:
    return [
        row
        for row in range(len(grid))
        if grid[row][column] not in (0, 5)
    ]


def vertical_bridge(completed: list[list[int]]) -> list[list[int]]:
    result = deepcopy(completed)
    height, width = len(completed), len(completed[0])
    for column in range(width):
        rows = _signal_rows(completed, column)
        colors = {completed[row][column] for row in rows}
        if len(rows) < 2 or len(colors) != 1:
            continue
        color = next(iter(colors))
        for row in range(rows[0] + 1, rows[-1]):
            if completed[row][column] == 0:
                result[row][column] = color
    return result


def claimed_output(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    finish = _setting(settings)
    completed = row_fill(grid)
    return completed if finish == "row_fill_only" else vertical_bridge(completed)


def _first_free(candidates: range, forbidden: set[int]) -> int:
    for value in candidates:
        if value not in forbidden:
            return value
    raise AssertionError("profile has no free teaching row")


def _build_input(seed: int, split: str, index: int) -> list[list[int]]:
    height, width = _shape(split, index)
    rng = _rng(seed, split, index)
    colors = rng.sample(_SIGNAL_COLORS, 3)
    a, b, c = colors
    grid = [[0 for _ in range(width)] for _ in range(height)]

    # Six anchor rows define three input-derived vertical bridges.  Their cells
    # are 5 in the input, so the bridge endpoints do not exist as colored
    # signals until the canonical row-fill stage has run.
    anchor_colors = {
        0: a,
        1: b,
        2: c,
        height - 4: c,
        height - 3: a,
        height - 2: b,
    }
    reserved_columns = {width - 1, width - 2, width - 3, width - 4, width - 5}
    zero_row = _first_free(range(3, height - 1), set(anchor_colors))
    deep_row = 2

    row_keys: dict[int, int] = {}
    for row in range(height - 1):
        key = anchor_colors.get(row, colors[(row + index) % len(colors)])
        row_keys[row] = key
        if row == zero_row:
            # First non-5 is literal zero.  Keep an explicit color-5 cell before
            # the later colored signals so every minimum lesson refutes the
            # tempting "first nonzero" replacement for the canonical row key.
            grid[row][0] = 0
            grid[row][1] = 5
            key_column = 0
        else:
            key_column = 2 if row == deep_row else ((row + index) % 2)
            for column in range(key_column):
                grid[row][column] = 5
            grid[row][key_column] = key

        # Substantive horizontal color-5 material.  Reserved bridge columns are
        # cleared below so only the intended endpoints influence stage B.
        for column in range(max(key_column + 2, 3), width):
            if column in reserved_columns:
                continue
            if (column + 2 * row + index + rng.randrange(3)) % 4 in (0, 1):
                grid[row][column] = 5

        # Preserve a later, different signal in every ordinary row.  This makes
        # last-non-5 and whole-row shortcuts visibly wrong.
        candidates = [
            column
            for column in range(max(key_column + 2, 3), width - 5)
            if column not in reserved_columns
        ]
        if candidates:
            column = candidates[(row + index) % len(candidates)]
            distractor = next(value for value in colors if value != key)
            grid[row][column] = distractor

    # Keep the canonical all-5 branch and make the largest case touch bottom.
    grid[-1] = [5] * width

    # Clear the five controlled columns before installing their witnesses.
    for row in range(height - 1):
        for column in reserved_columns:
            grid[row][column] = 0

    # Three derived bridges: endpoints are uncolored 5s until row completion.
    for row in (0, height - 3):
        grid[row][width - 1] = 5  # color a
    for row in (1, height - 2):
        grid[row][width - 3] = 5  # color b
    for row in (2, height - 4):
        grid[row][width - 5] = 5  # color c

    # One raw-visible bridge and one mixed-color non-bridge teach both the
    # dependency on stage A and the unique-color guard in stage B.
    grid[0][width - 4] = a
    grid[height - 3][width - 4] = a
    grid[1][width - 2] = 5        # becomes b
    grid[height - 3][width - 2] = 5  # becomes a, therefore must not bridge

    # A same-color horizontal gap is a deliberate orientation distractor.
    grid[zero_row][2] = a
    grid[zero_row][3] = 0
    grid[zero_row][4] = a

    return grid


def _changed_cells(before: list[list[int]], after: list[list[int]]) -> list[list[int]]:
    return [
        [row, column]
        for row in range(len(before))
        for column in range(len(before[0]))
        if before[row][column] != after[row][column]
    ]


def analyze_input(grid: list[list[int]]) -> dict:
    completed = row_fill(grid)
    raw_bridged = vertical_bridge(grid)
    completed_bridged = vertical_bridge(completed)
    mixed = []
    for column in range(len(grid[0])):
        rows = _signal_rows(completed, column)
        colors = {completed[row][column] for row in rows}
        if len(rows) >= 2 and len(colors) >= 2:
            mixed.append(column)

    horizontal = []
    for row_index, row in enumerate(completed):
        for color in sorted(set(row) - {0, 5}):
            columns = [column for column, value in enumerate(row) if value == color]
            if len(columns) >= 2 and any(row[column] == 0 for column in range(columns[0] + 1, columns[-1])):
                horizontal.append({"row": row_index, "color": color,
                                   "first": columns[0], "last": columns[-1]})
    return {
        "shape": [len(grid), len(grid[0])],
        "row_keys": [_first_non5(row) for row in grid],
        "raw_bridge_cells": _changed_cells(grid, raw_bridged),
        "completed_bridge_cells": _changed_cells(completed, completed_bridged),
        "mixed_signal_columns": mixed,
        "horizontal_same_color_gaps": horizontal,
    }


def generate(seed: int, settings: dict[str, str], demos: int, queries: int) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    finish = _setting(settings)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)

    chosen = {PARAMETER: finish}
    train = []
    test = []
    for split, count in (("train", demos), ("test", queries)):
        destination = train if split == "train" else test
        for index in range(count):
            grid = _build_input(seed, split, index)
            destination.append({"input": grid, "output": claimed_output(grid, chosen)})
    return {
        "train": train,
        "test": test,
        "program_solution": program(chosen),
        "settings": chosen,
        "seed": seed,
    }


def public_turn(episode: dict, query_index: int) -> dict:
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    test = episode.get("test") if isinstance(episode, dict) else None
    train = episode.get("train") if isinstance(episode, dict) else None
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train/test lists")
    if not 0 <= query_index < len(test):
        raise ValueError("query_index is outside the stored query prefix")
    return {
        "train": deepcopy(train),
        "test": [{"input": deepcopy(test[query_index]["input"])}],
    }


def public_turn_bytes(episode: dict, query_index: int) -> bytes:
    public = public_turn(episode, query_index)
    return (json.dumps(public, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode("utf-8")


def public_turn_id(episode: dict, query_index: int) -> str:
    return hashlib.sha256(public_turn_bytes(episode, query_index)).hexdigest()
