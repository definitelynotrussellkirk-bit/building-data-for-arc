"""Native row-only / row-then-column parametric family for 569aa05e004d.

The canonical ``rows_only`` setting is byte-for-byte the selected ARC rule: on
fresh zero, fill the horizontal interval for every row/color occurring exactly
twice.  The alternate ``rows_then_columns`` setting performs that exact pass,
then consumes the resulting grid and fills every column/color interval occurring
exactly twice in the intermediate.  The second pass therefore cannot be chosen
from the raw input alone.

Inputs are deterministic and independent of the hidden setting.  The first two
teaching scenes include multi-pair rows, erased controls, exact-three column
controls, and a raw-input decoy whose apparent vertical pair becomes a triple in
the Stage-A intermediate.  Four fixed query profiles include thin/tall cases,
boundaries, dense controls, and a substantive 30x30 scene.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

TASK_ID = "569aa05e004d"
PARAMETER = "closure_axis"
PARAMETERS = {PARAMETER: ["rows_only", "rows_then_columns"]}
DEFAULT = {PARAMETER: "rows_only"}
SETTINGS = tuple({PARAMETER: value} for value in PARAMETERS[PARAMETER])
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERIES = 4
MAX_SEED = 2**63 - 1

HERE = Path(__file__).resolve().parent
_CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8").rstrip("\n")
_ROWS_THEN_COLUMNS = (HERE / "rows_then_columns.rkt").read_text(encoding="utf-8").rstrip("\n")
_PROGRAMS = {
    "rows_only": _CANONICAL,
    "rows_then_columns": _ROWS_THEN_COLUMNS,
}


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _strict_int(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in PARAMETERS[PARAMETER]:
        raise ValueError(f"{PARAMETER} must be one of {PARAMETERS[PARAMETER]!r}")
    return {PARAMETER: value}


def _grid(grid: object) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be a nonempty 1..30 by 1..30 list")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colours")
    return grid


def program(settings: object) -> str:
    return _PROGRAMS[_settings(settings)[PARAMETER]]


def _ordered_colors(grid: list[list[int]]) -> list[int]:
    colors: list[int] = []
    seen: set[int] = set()
    for row in grid:
        for value in row:
            if value and value not in seen:
                seen.add(value)
                colors.append(value)
    return colors


def _row_positions(row: list[int]) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {}
    for column, color in enumerate(row):
        if color:
            result.setdefault(color, []).append(column)
    return result


def stage_rows(grid: list[list[int]]) -> list[list[int]]:
    """Canonical fresh-zero row-local exact-pair fill."""
    _grid(grid)
    output = [[0 for _ in row] for row in grid]
    colors = _ordered_colors(grid)
    for row_index, row in enumerate(grid):
        positions = _row_positions(row)
        for color in colors:
            columns = positions.get(color, [])
            if len(columns) == 2:
                for column in range(columns[0], columns[1] + 1):
                    output[row_index][column] = color
    return output


def _column_relations(grid: list[list[int]]) -> list[tuple[int, int, list[int]]]:
    colors = _ordered_colors(grid)
    height, width = len(grid), len(grid[0])
    relations: list[tuple[int, int, list[int]]] = []
    for column in range(width):
        for color in colors:
            rows = [row for row in range(height) if grid[row][column] == color]
            relations.append((column, color, rows))
    return relations


def stage_columns(intermediate: list[list[int]]) -> list[list[int]]:
    """Fill exact-pair column intervals into background, preserving Stage A."""
    _grid(intermediate)
    output = [row[:] for row in intermediate]
    for column, color, rows in _column_relations(intermediate):
        if len(rows) == 2:
            for row in range(rows[0], rows[1] + 1):
                if output[row][column] == 0:
                    output[row][column] = color
    return output


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    chosen = _settings(settings)[PARAMETER]
    first = stage_rows(grid)
    return first if chosen == "rows_only" else stage_columns(first)


def _paint(grid: list[list[int]], row: int, column: int, color: int) -> None:
    if type(row) is not int or type(column) is not int or type(color) is not int:
        raise TypeError("cell coordinates and colours must be exact integers")
    if not 0 <= row < len(grid) or not 0 <= column < len(grid[0]):
        raise ValueError(f"cell {(row, column)} is outside the grid")
    if not 1 <= color <= 9:
        raise ValueError("paint colours must be in 1..9")
    if grid[row][column] not in (0, color):
        raise ValueError(f"cell {(row, column)} has conflicting colours")
    grid[row][column] = color


def _span(value: object, width: int) -> tuple[int, int]:
    if (
        type(value) not in (tuple, list)
        or len(value) != 2
        or any(type(x) is not int for x in value)
    ):
        raise ValueError("span must be an exact two-integer pair")
    left, right = value
    if not 0 <= left < right < width or right - left < 2:
        raise ValueError("span must be an in-bounds visible-gap interval")
    return left, right


def make_control_scene(
    height: int,
    width: int,
    *,
    bridges: Iterable[dict[str, Any]] = (),
    triples: Iterable[dict[str, Any]] = (),
    blockers: Iterable[tuple[int, int, int]] = (),
    row_triples: Iterable[tuple[int, int, tuple[int, int, int]]] = (),
    singletons: Iterable[tuple[int, int, int]] = (),
) -> list[list[int]]:
    """Build an endpoint-only scene with explicit semantic controls."""
    _strict_int("height", height, 1, 30)
    _strict_int("width", width, 1, 30)
    grid = [[0] * width for _ in range(height)]

    for motif in bridges:
        if type(motif) is not dict or set(motif) != {"color", "rows", "spans"}:
            raise ValueError("bridge needs color, rows, and spans")
        color = motif["color"]
        rows = motif["rows"]
        spans = motif["spans"]
        if type(color) is not int or not 1 <= color <= 9:
            raise ValueError("bridge colour must be in 1..9")
        if type(rows) not in (tuple, list) or len(rows) != 2 or any(type(r) is not int for r in rows):
            raise ValueError("bridge rows must contain two exact integers")
        if not 0 <= rows[0] < rows[1] < height:
            raise ValueError("bridge rows must be increasing and in bounds")
        if type(spans) not in (tuple, list) or len(spans) != 2:
            raise ValueError("bridge spans must contain two intervals")
        for row, span in zip(rows, spans):
            left, right = _span(span, width)
            _paint(grid, row, left, color)
            _paint(grid, row, right, color)

    for motif in triples:
        if type(motif) is not dict or set(motif) != {"color", "rows", "spans"}:
            raise ValueError("triple needs color, rows, and spans")
        color = motif["color"]
        rows = motif["rows"]
        spans = motif["spans"]
        if type(color) is not int or not 1 <= color <= 9:
            raise ValueError("triple colour must be in 1..9")
        if type(rows) not in (tuple, list) or len(rows) != 3 or any(type(r) is not int for r in rows):
            raise ValueError("triple rows must contain three exact integers")
        if not 0 <= rows[0] < rows[1] < rows[2] < height:
            raise ValueError("triple rows must be increasing and in bounds")
        if type(spans) not in (tuple, list) or len(spans) != 3:
            raise ValueError("triple spans must contain three intervals")
        for row, span in zip(rows, spans):
            left, right = _span(span, width)
            _paint(grid, row, left, color)
            _paint(grid, row, right, color)

    for row, column, color in blockers:
        _paint(grid, row, column, color)
    for row, color, columns in row_triples:
        if type(columns) not in (tuple, list) or len(columns) != 3 or len(set(columns)) != 3:
            raise ValueError("row triple columns must contain three distinct cells")
        for column in columns:
            _paint(grid, row, column, color)
    for row, column, color in singletons:
        _paint(grid, row, column, color)
    return grid


def _vertical_targets(intermediate: list[list[int]], *, at_least: bool = False,
                      first_two: bool = False) -> list[tuple[int, int, int, int]]:
    targets: list[tuple[int, int, int, int]] = []
    for column, color, rows in _column_relations(intermediate):
        selected: list[int] = []
        if len(rows) == 2:
            selected = rows
        elif at_least and len(rows) >= 2:
            selected = rows[:2] if first_two else [rows[0], rows[-1]]
        if selected:
            targets.append((column, color, selected[0], selected[1]))
    return targets


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    _grid(grid)
    first = stage_rows(grid)
    final = stage_columns(first)
    row_relations = sum(
        len(columns) == 2
        for row in grid
        for columns in _row_positions(row).values()
    )
    exact_columns = [item for item in _column_relations(first) if len(item[2]) == 2]
    triple_columns = [item for item in _column_relations(first) if len(item[2]) == 3]
    erased = sum(
        before != 0 and after == 0
        for in_row, out_row in zip(grid, first)
        for before, after in zip(in_row, out_row)
    )
    changed = sum(
        before != after
        for first_row, final_row in zip(first, final)
        for before, after in zip(first_row, final_row)
    )
    raw_columns = [item for item in _column_relations(grid) if len(item[2]) == 2]
    return {
        "shape": [len(grid), len(grid[0])],
        "row_relations": row_relations,
        "column_relations": len(exact_columns),
        "triple_blocked_columns": len(triple_columns),
        "stage_a_nonzero": sum(value != 0 for row in first for value in row),
        "stage_b_changed_cells": changed,
        "erased_control_cells": erased,
        "raw_column_relations": len(raw_columns),
        "input_nonzero": sum(value != 0 for row in grid for value in row),
        "output_nonzero": sum(value != 0 for row in final for value in row),
    }


def _base_scene(split: str, index: int) -> list[list[int]]:
    if split == "train" and index == 0:
        return make_control_scene(
            13, 17,
            bridges=[{"color": 2, "rows": (1, 5), "spans": ((1, 10), (4, 14))}],
            triples=[{"color": 3, "rows": (7, 9, 11), "spans": ((5, 14), (3, 12), (5, 10))}],
            blockers=[(1, 6, 8)],
            row_triples=[(12, 4, (0, 8, 16))],
            singletons=[(0, 2, 5), (0, 15, 6)],
        )
    if split == "train" and index == 1:
        return make_control_scene(
            13, 17,
            bridges=[
                {"color": 2, "rows": (0, 4), "spans": ((0, 7), (2, 9))},
                {"color": 3, "rows": (0, 6), "spans": ((11, 16), (9, 14))},
                {"color": 4, "rows": (9, 12), "spans": ((0, 4), (10, 16))},
            ],
            blockers=[(6, 12, 8)],
            row_triples=[(8, 5, (0, 8, 16))],
            singletons=[(2, 15, 6)],
        )
    if split == "train" and index == 2:
        return make_control_scene(
            15, 19,
            bridges=[
                {"color": 2, "rows": (1, 6), "spans": ((0, 7), (2, 10))},
                {"color": 3, "rows": (1, 8), "spans": ((12, 18), (10, 16))},
            ],
            triples=[{"color": 4, "rows": (10, 12, 14), "spans": ((4, 13), (2, 11), (4, 9))}],
            blockers=[(1, 4, 8)],
            row_triples=[(9, 5, (1, 9, 17))],
            singletons=[(0, 18, 9)],
        )
    if split == "train" and index == 3:
        return make_control_scene(
            17, 13,
            bridges=[
                {"color": 2, "rows": (0, 6), "spans": ((0, 8), (3, 12))},
                {"color": 4, "rows": (9, 15), "spans": ((0, 3), (6, 12))},
            ],
            triples=[{"color": 3, "rows": (8, 12, 16), "spans": ((4, 12), (2, 10), (4, 8))}],
            blockers=[(0, 5, 8)],
            row_triples=[(7, 5, (0, 6, 12))],
        )
    if split == "train" and index == 4:
        return make_control_scene(
            24, 24,
            bridges=[
                {"color": 2, "rows": (0, 6), "spans": ((0, 12), (4, 18))},
                {"color": 3, "rows": (8, 14), "spans": ((5, 23), (0, 17))},
                {"color": 5, "rows": (17, 22), "spans": ((0, 6), (2, 7))},
            ],
            triples=[{"color": 4, "rows": (16, 19, 23), "spans": ((8, 23), (4, 20), (8, 16))}],
            blockers=[(8, 11, 8), (17, 3, 9)],
            row_triples=[(7, 6, (0, 12, 23))],
        )
    if split == "train" and index == 5:
        return make_control_scene(
            29, 27,
            bridges=[
                {"color": 2, "rows": (0, 7), "spans": ((0, 13), (4, 18))},
                {"color": 3, "rows": (9, 16), "spans": ((8, 26), (3, 20))},
                {"color": 5, "rows": (18, 25), "spans": ((0, 10), (5, 15))},
            ],
            triples=[{"color": 4, "rows": (19, 23, 28), "spans": ((17, 26), (14, 24), (17, 21))}],
            blockers=[(0, 6, 8), (9, 14, 9)],
            row_triples=[(8, 6, (0, 13, 26))],
        )
    if split == "test" and index == 0:
        return make_control_scene(
            9, 21,
            bridges=[{"color": 2, "rows": (0, 4), "spans": ((0, 12), (5, 20))}],
            triples=[{"color": 3, "rows": (5, 6, 8), "spans": ((6, 20), (3, 17), (6, 12))}],
            blockers=[(0, 7, 8)],
            singletons=[(2, 20, 6)],
        )
    if split == "test" and index == 1:
        return make_control_scene(
            21, 9,
            bridges=[{"color": 2, "rows": (0, 9), "spans": ((0, 6), (2, 8))}],
            triples=[{"color": 3, "rows": (11, 15, 20), "spans": ((3, 8), (1, 7), (3, 5))}],
            blockers=[(0, 4, 8)],
            row_triples=[(10, 5, (0, 4, 8))],
        )
    if split == "test" and index == 2:
        return make_control_scene(
            24, 26,
            bridges=[
                {"color": 2, "rows": (0, 6), "spans": ((0, 13), (5, 19))},
                {"color": 3, "rows": (8, 15), "spans": ((10, 25), (4, 20))},
                {"color": 5, "rows": (17, 23), "spans": ((0, 9), (3, 14))},
            ],
            triples=[{"color": 4, "rows": (16, 19, 22), "spans": ((16, 25), (13, 23), (16, 20))}],
            blockers=[(8, 14, 8), (17, 6, 9)],
            row_triples=[(7, 6, (0, 12, 25))],
        )
    if split == "test" and index == 3:
        return make_control_scene(
            30, 30,
            bridges=[
                {"color": 2, "rows": (0, 5), "spans": ((0, 13), (4, 17))},
                {"color": 3, "rows": (7, 13), "spans": ((12, 29), (8, 23))},
                {"color": 4, "rows": (15, 21), "spans": ((0, 11), (4, 15))},
            ],
            triples=[
                {"color": 5, "rows": (15, 18, 21), "spans": ((18, 29), (16, 27), (18, 23))},
                {"color": 6, "rows": (23, 26, 29), "spans": ((10, 29), (6, 24), (10, 18))},
            ],
            blockers=[(0, 7, 8), (7, 18, 9)],
            row_triples=[(6, 7, (0, 14, 29))],
            singletons=[(14, 29, 8), (22, 0, 9)],
        )
    raise ValueError(f"unsupported scene profile: {split} {index}")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|row-column-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _variant_scene(seed: int, split: str, index: int) -> list[list[int]]:
    grid = _base_scene(split, index)
    rng = _rng(seed, split, index)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    mapping = {source: palette[source - 1] for source in range(1, 10)}
    grid = [[mapping.get(value, value) for value in row] for row in grid]
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    if rng.randrange(2):
        grid = list(reversed(grid))
    return grid


def _assert_no_competing_vertical_overwrite(grid: list[list[int]]) -> None:
    first = stage_rows(grid)
    owners: dict[tuple[int, int], set[int]] = {}
    for column, color, top, bottom in _vertical_targets(first):
        for row in range(top, bottom + 1):
            owners.setdefault((row, column), set()).add(color)
    conflicts = {cell: colors for cell, colors in owners.items() if len(colors) > 1}
    if conflicts:
        raise AssertionError(f"scene has competing vertical writes: {conflicts}")


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    limit = MAX_DEMOS if split == "train" else QUERIES
    _strict_int("scene index", index, 0, limit - 1)
    grid = _variant_scene(seed, split, index)
    _assert_no_competing_vertical_overwrite(grid)
    analysis = analyze_scene(grid)
    if analysis["stage_b_changed_cells"] <= 0:
        raise AssertionError("every scene must expose the closure parameter")
    return grid


def _row_total_exactly_two(grid: list[list[int]]) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        entries = [(column, color) for column, color in enumerate(row) if color]
        if len(entries) == 2 and entries[0][1] == entries[1][1]:
            left, color = entries[0]
            right = entries[1][0]
            for column in range(left, right + 1):
                output[row_index][column] = color
    return output


def _rows_at_least_two(grid: list[list[int]]) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        for color, columns in _row_positions(row).items():
            if len(columns) >= 2:
                for column in range(columns[0], columns[-1] + 1):
                    output[row_index][column] = color
    return output


def _preserve_nonqualifying_rows(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        for color, columns in _row_positions(row).items():
            if len(columns) == 2:
                for column in range(columns[0], columns[1] + 1):
                    output[row_index][column] = color
    return output


def _first_pair_per_row(grid: list[list[int]]) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        candidates = sorted(
            (columns[0], columns[1], color)
            for color, columns in _row_positions(row).items()
            if len(columns) == 2
        )
        if candidates:
            left, right, color = candidates[0]
            for column in range(left, right + 1):
                output[row_index][column] = color
    return output


def _global_exactly_two(grid: list[list[int]]) -> list[list[int]]:
    totals: dict[int, int] = {}
    for row in grid:
        for value in row:
            if value:
                totals[value] = totals.get(value, 0) + 1
    output = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        for color, columns in _row_positions(row).items():
            if len(columns) == 2 and totals.get(color) == 2:
                for column in range(columns[0], columns[1] + 1):
                    output[row_index][column] = color
    return output


def _columns_on_raw(grid: list[list[int]]) -> list[list[int]]:
    return stage_columns(grid)


def _columns_at_least_two(grid: list[list[int]]) -> list[list[int]]:
    first = stage_rows(grid)
    output = [row[:] for row in first]
    for column, color, top, bottom in _vertical_targets(first, at_least=True):
        for row in range(top, bottom + 1):
            if output[row][column] == 0:
                output[row][column] = color
    return output


def _columns_first_two(grid: list[list[int]]) -> list[list[int]]:
    first = stage_rows(grid)
    output = [row[:] for row in first]
    for column, color, top, bottom in _vertical_targets(first, at_least=True, first_two=True):
        for row in range(top, bottom + 1):
            if output[row][column] == 0:
                output[row][column] = color
    return output


def _partial_rows_then_columns(grid: list[list[int]]) -> list[list[int]]:
    return stage_columns(_first_pair_per_row(grid))


def _preserve_then_columns(grid: list[list[int]]) -> list[list[int]]:
    return stage_columns(_preserve_nonqualifying_rows(grid))


_SHORTCUTS: dict[str, dict[str, Callable[[list[list[int]]], list[list[int]]]]] = {
    "rows_only": {
        "row_total_exactly_two": _row_total_exactly_two,
        "row_at_least_two": _rows_at_least_two,
        "preserve_nonqualifying": _preserve_nonqualifying_rows,
        "first_pair_per_row": _first_pair_per_row,
        "global_exactly_two": _global_exactly_two,
    },
    "rows_then_columns": {
        "rows_only_partial": stage_rows,
        "columns_on_raw": _columns_on_raw,
        "column_at_least_two": _columns_at_least_two,
        "column_first_two": _columns_first_two,
        "partial_rows_then_columns": _partial_rows_then_columns,
        "preserve_then_columns": _preserve_then_columns,
    },
}


def certify(episode: object) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    chosen = _settings(episode.get("settings"))
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not MIN_DEMOS <= len(train) <= MAX_DEMOS:
        raise ValueError("train count is outside 2..6")
    if type(test) is not list or len(test) != QUERIES:
        raise ValueError("test count must equal four")

    normalized: list[tuple[str, int, dict[str, Any]]] = []
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError(f"{split} pair {index} needs input and output")
            _grid(pair["input"])
            _grid(pair["output"])
            normalized.append((split, index, pair))
    keys = [digest(pair["input"]) for _split, _index, pair in normalized]
    if len(keys) != len(set(keys)):
        raise ValueError("all demonstration and query inputs must be distinct")
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program_solution must equal program(settings) exactly")

    for split, index, pair in normalized:
        expected = transform(pair["input"], chosen)
        if pair["output"] != expected:
            label = "query label" if split == "test" else "demonstration label"
            raise ValueError(f"{label} disagrees with fixed setting at index {index}")

    survivors = [
        setting for setting in SETTINGS
        if all(transform(pair["input"], setting) == pair["output"] for pair in train)
    ]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not uniquely identify setting: {survivors}")

    shortcut_disagreements: dict[str, list[int]] = {}
    shortcut_survivors: list[str] = []
    for name, shortcut in _SHORTCUTS[chosen[PARAMETER]].items():
        disagreements = [
            index for index, pair in enumerate(train)
            if shortcut(pair["input"]) != pair["output"]
        ]
        shortcut_disagreements[name] = disagreements
        if not disagreements:
            shortcut_survivors.append(name)
    if shortcut_survivors:
        raise ValueError(f"declared wrong shortcuts survive demonstrations: {shortcut_survivors}")

    return {
        "status": "pass",
        "survivors": survivors,
        "shortcut_disagreements": shortcut_disagreements,
        "shortcut_survivors": shortcut_survivors,
        "train_analysis": [analyze_scene(pair["input"]) for pair in train],
        "queries": [
            {
                "input_sha256": digest(pair["input"]),
                "output_sha256": digest(pair["output"]),
                "analysis": analyze_scene(pair["input"]),
            }
            for pair in test
        ],
    }


def generate(
    seed: int,
    settings: dict[str, str],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, QUERIES, QUERIES)
    chosen = _settings(settings)
    train = []
    for index in range(demos):
        grid = _scene(seed, "train", index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for index in range(queries):
        grid = _scene(seed, "test", index)
        test.append({"input": grid, "output": transform(grid, chosen)})
    episode: dict[str, Any] = {
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": program(chosen),
    }
    episode["certificate"] = certify(episode)
    return episode


def crossed_controls() -> dict[str, list[dict[str, Any]]]:
    small = make_control_scene(
        13, 17,
        bridges=[{"color": 2, "rows": (1, 5), "spans": ((1, 10), (4, 14))}],
        triples=[{"color": 3, "rows": (7, 9, 11), "spans": ((5, 14), (3, 12), (5, 10))}],
        blockers=[(1, 6, 8)],
    )
    larger = make_control_scene(
        13, 17,
        bridges=[
            {"color": 2, "rows": (1, 5), "spans": ((1, 10), (4, 14))},
            {"color": 4, "rows": (7, 11), "spans": ((0, 6), (2, 9))},
        ],
        blockers=[(1, 6, 8)],
    )
    nuisance_a = make_control_scene(
        13, 17,
        bridges=[{"color": 2, "rows": (1, 5), "spans": ((1, 10), (4, 14))}],
        blockers=[(1, 6, 8)],
        row_triples=[(12, 3, (0, 8, 16))],
    )
    nuisance_b = make_control_scene(
        13, 17,
        bridges=[{"color": 2, "rows": (1, 5), "spans": ((1, 10), (4, 14))}],
        blockers=[(1, 7, 9)],
        row_triples=[(12, 4, (1, 8, 15))],
    )
    varying = []
    for grid in (small, larger):
        varying.append({"input": grid, "analysis": analyze_scene(grid)})
    nuisance = []
    for grid in (nuisance_a, nuisance_b):
        first = stage_rows(grid)
        nuisance.append({
            "input": grid,
            "intermediate": first,
            "output": stage_columns(first),
            "analysis": analyze_scene(grid),
        })
    return {
        "different_intermediate_same_profile": varying,
        "same_intermediate_different_raw_nuisance": nuisance,
    }
