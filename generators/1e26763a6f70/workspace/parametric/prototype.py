"""Matched-input midpoint-selection episodes for 1e26763a6f70.

The canonical setting marks every eligible midpoint.  The alternate setting
first derives every eligible pair and its input-dependent span, then marks only
pairs attaining the maximum span.  Python outputs are deterministic claims;
native qualification independently executes every label through protected
Racket.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "1e26763a6f70"
HERE = Path(__file__).resolve().parent
SETTING_NAMES = ("all_pairs", "longest_pairs")
CANDIDATE_NAMES = (
    "all_pairs",
    "longest_pairs",
    "shortest_pairs",
    "first_pair",
    "last_pair",
    "horizontal_only",
    "vertical_only",
    "span_four",
    "longest_first_only",
    "longest_last_only",
)

# Coordinates are (row, col) endpoints in the unreflected profile.  Every
# eligible pair has an even positive span and a distinct empty midpoint.
_PROFILES: dict[str, tuple[dict[str, Any], ...]] = {
    "demo": (
        {"shape": (8, 10), "eligible": (((1, 1), (1, 3)), ((1, 7), (5, 7)), ((6, 1), (6, 7))),
         "invalid": (((2, 2), (4, 4)),), "noise": 1},
        {"shape": (10, 12), "eligible": (((1, 1), (1, 9)), ((1, 10), (9, 10)), ((5, 1), (5, 5)), ((5, 7), (7, 7))),
         "invalid": (((2, 2), (2, 5)),), "noise": 1},
        {"shape": (12, 15), "eligible": (((1, 0), (1, 2)), ((1, 13), (5, 13)), ((10, 2), (10, 8)), ((2, 10), (10, 10))),
         "invalid": (((3, 3), (4, 4)),), "noise": 2},
        {"shape": (15, 18), "eligible": (((1, 1), (1, 11)), ((2, 16), (12, 16)), ((7, 1), (7, 7)), ((4, 9), (8, 9)), ((12, 2), (12, 4))),
         "invalid": (((2, 3), (5, 3)),), "noise": 2},
        {"shape": (18, 21), "eligible": (((1, 1), (1, 13)), ((2, 19), (14, 19)), ((6, 2), (6, 10)), ((3, 15), (9, 15)), ((15, 3), (15, 7)), ((10, 12), (12, 12))),
         "invalid": (((4, 4), (7, 7)),), "noise": 2},
        {"shape": (21, 24), "eligible": (((1, 0), (1, 14)), ((2, 22), (16, 22)), ((7, 2), (7, 12)), ((3, 17), (11, 17)), ((18, 3), (18, 9)), ((10, 14), (14, 14)), ((15, 1), (15, 3))),
         "invalid": (((4, 5), (4, 10)),), "noise": 2},
    ),
    "query": (
        {"shape": (12, 15), "eligible": (((0, 1), (0, 11)), ((1, 14), (9, 14)), ((6, 1), (6, 7)), ((3, 10), (7, 10)), ((10, 2), (10, 4))),
         "invalid": (((2, 2), (5, 5)),), "noise": 2},
        {"shape": (18, 20), "eligible": (((1, 0), (1, 12)), ((2, 18), (14, 18)), ((7, 2), (7, 12)), ((3, 15), (11, 15)), ((15, 1), (15, 7)), ((10, 9), (14, 9))),
         "invalid": (((4, 3), (4, 8)),), "noise": 2},
        {"shape": (24, 27), "eligible": (((0, 1), (0, 15)), ((2, 26), (16, 26)), ((7, 2), (7, 14)), ((3, 20), (13, 20)), ((20, 3), (20, 11)), ((11, 16), (17, 16)), ((18, 1), (18, 5))),
         "invalid": (((4, 4), (9, 9)),), "noise": 3},
        {"shape": (30, 30), "eligible": (((0, 1), (0, 17)), ((1, 29), (17, 29)), ((7, 0), (7, 12)), ((2, 23), (12, 23)), ((25, 2), (25, 10)), ((18, 19), (24, 19)), ((15, 1), (15, 5)), ((20, 27), (22, 27))),
         "invalid": (), "noise": 3},
    ),
}


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"pair_selection"}:
        raise ValueError("settings must contain exactly pair_selection")
    value = settings["pair_selection"]
    if type(value) is not str or value not in SETTING_NAMES:
        raise ValueError(f"pair_selection must be one of {SETTING_NAMES}")
    return value


def program_for(selection: str) -> str:
    if selection == "all_pairs":
        path = HERE / "canonical.rkt"
    elif selection == "longest_pairs":
        path = HERE / "longest_pairs.rkt"
    elif selection == "shortest_pairs":
        path = HERE / "shortest_pairs.rkt"
    else:
        raise ValueError("selection has no declared Racket program")
    return path.read_text()


def program(settings: dict[str, Any]) -> str:
    return program_for(_setting(settings))


def _validate_grid(grid: Any) -> tuple[list[list[int]], int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    clean: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid cells must be exact integer colors 0..9")
        clean.append(list(row))
    return clean, len(clean), width


def analyze(grid: Any) -> dict[str, Any]:
    values, height, width = _validate_grid(grid)
    colors: list[int] = []
    cells_by_color: dict[int, list[tuple[int, int]]] = {}
    for row in range(height):
        for col in range(width):
            color = values[row][col]
            if color == 0:
                continue
            if color not in cells_by_color:
                colors.append(color)
                cells_by_color[color] = []
            cells_by_color[color].append((row, col))

    eligible: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    for rank, color in enumerate(colors):
        cells = cells_by_color[color]
        if len(cells) != 2:
            ignored.append({"color": color, "reason": "count", "count": len(cells)})
            continue
        (r1, c1), (r2, c2) = cells
        record: dict[str, Any] | None = None
        if r1 == r2 and (c1 + c2) % 2 == 0:
            midpoint = (r1, (c1 + c2) // 2)
            if values[midpoint[0]][midpoint[1]] == 0:
                record = {"color": color, "cells": [list(cells[0]), list(cells[1])],
                          "midpoint": list(midpoint), "orientation": "horizontal",
                          "span": abs(c2 - c1), "reading_rank": rank}
        elif c1 == c2 and (r1 + r2) % 2 == 0:
            midpoint = ((r1 + r2) // 2, c1)
            if values[midpoint[0]][midpoint[1]] == 0:
                record = {"color": color, "cells": [list(cells[0]), list(cells[1])],
                          "midpoint": list(midpoint), "orientation": "vertical",
                          "span": abs(r2 - r1), "reading_rank": rank}
        if record is None:
            ignored.append({"color": color, "reason": "geometry_or_midpoint", "count": 2})
        else:
            eligible.append(record)
    return {"height": height, "width": width, "colors_reading": colors,
            "eligible_pairs": eligible, "ignored_colors": ignored}


def selected_pairs(analysis: dict[str, Any], selection: str) -> list[dict[str, Any]]:
    pairs = list(analysis["eligible_pairs"])
    if selection == "all_pairs":
        return pairs
    if not pairs:
        return []
    if selection == "longest_pairs":
        target = max(pair["span"] for pair in pairs)
        return [pair for pair in pairs if pair["span"] == target]
    if selection == "shortest_pairs":
        target = min(pair["span"] for pair in pairs)
        return [pair for pair in pairs if pair["span"] == target]
    if selection == "first_pair":
        return pairs[:1]
    if selection == "last_pair":
        return pairs[-1:]
    if selection == "horizontal_only":
        return [pair for pair in pairs if pair["orientation"] == "horizontal"]
    if selection == "vertical_only":
        return [pair for pair in pairs if pair["orientation"] == "vertical"]
    if selection == "span_four":
        return [pair for pair in pairs if pair["span"] == 4]
    if selection == "longest_first_only":
        longest = selected_pairs(analysis, "longest_pairs")
        return longest[:1]
    if selection == "longest_last_only":
        longest = selected_pairs(analysis, "longest_pairs")
        return longest[-1:]
    raise ValueError(f"unknown selection {selection!r}")


def solve(grid: Any, selection: str) -> list[list[int]]:
    values, _, _ = _validate_grid(grid)
    analysis = analyze(values)
    output = copy.deepcopy(values)
    for pair in selected_pairs(analysis, selection):
        row, col = pair["midpoint"]
        output[row][col] = pair["color"]
    return output


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = json.dumps([TASK_ID, "parametric-v1", seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _mirror(point: tuple[int, int], height: int, width: int, vertical: bool, horizontal: bool) -> tuple[int, int]:
    row, col = point
    if vertical:
        row = height - 1 - row
    if horizontal:
        col = width - 1 - col
    return row, col


def _noise_cells(height: int, width: int, level: int, phase: int) -> list[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    if level == 1:
        candidates = [(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1),
                      (height // 2, width // 2), (height // 2, max(0, width // 2 - 2))]
        cells.update(candidates)
    elif level == 2:
        for row in range(height):
            for col in range(width):
                boundary = row in (0, height - 1) or col in (0, width - 1)
                diagonal = (row - col - phase) % 7 == 0
                if (boundary and (row + col + phase) % 3 == 0) or diagonal:
                    cells.add((row, col))
    elif level == 3:
        for row in range(height):
            for col in range(width):
                boundary = row in (0, height - 1) or col in (0, width - 1)
                stripe = ((row + phase) % 5 == 0 and col % 2 == 0) or ((col + phase) % 7 == 0 and row % 3 == 0)
                if boundary or stripe:
                    cells.add((row, col))
    else:
        raise ValueError("unknown noise level")
    return sorted(cells)


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in _PROFILES:
        raise ValueError("split must be demo or query")
    profile = _PROFILES[split][_integer(index, 0, len(_PROFILES[split]) - 1, "index")]
    height, width = profile["shape"]
    rng = _rng(seed, split, index)
    horizontal = bool(rng.getrandbits(1))
    vertical = bool(rng.getrandbits(1))
    palette = list(range(1, 10))
    rng.shuffle(palette)

    eligible = [
        (_mirror(a, height, width, vertical, horizontal), _mirror(b, height, width, vertical, horizontal))
        for a, b in profile["eligible"]
    ]
    invalid = [
        (_mirror(a, height, width, vertical, horizontal), _mirror(b, height, width, vertical, horizontal))
        for a, b in profile["invalid"]
    ]
    needed = len(eligible) + len(invalid) + 1
    if needed > len(palette):
        raise ValueError("profile requires more colors than ARC permits")
    grid = [[0] * width for _ in range(height)]
    critical: set[tuple[int, int]] = set()
    for color, (a, b) in zip(palette, eligible + invalid, strict=False):
        if a == b or a in critical or b in critical:
            raise ValueError("profile pair collision")
        grid[a[0]][a[1]] = color
        grid[b[0]][b[1]] = color
        critical.update((a, b))
        if a[0] == b[0] and (a[1] + b[1]) % 2 == 0:
            critical.add((a[0], (a[1] + b[1]) // 2))
        elif a[1] == b[1] and (a[0] + b[0]) % 2 == 0:
            critical.add(((a[0] + b[0]) // 2, a[1]))

    noise_color = palette[len(eligible) + len(invalid)]
    noise = [_mirror(cell, height, width, vertical, horizontal)
             for cell in _noise_cells(height, width, profile["noise"], index + seed % 11)]
    for row, col in noise:
        if (row, col) not in critical and grid[row][col] == 0:
            grid[row][col] = noise_color
    if sum(value == noise_color for row in grid for value in row) < 3:
        for row in range(height):
            for col in range(width):
                if (row, col) not in critical and grid[row][col] == 0:
                    grid[row][col] = noise_color
                    if sum(value == noise_color for values in grid for value in values) >= 3:
                        break
            else:
                continue
            break

    report = analyze(grid)
    if len(report["eligible_pairs"]) != len(eligible):
        raise ValueError("constructed profile changed eligible pair count")
    if len({tuple(pair["midpoint"]) for pair in report["eligible_pairs"]}) != len(eligible):
        raise ValueError("constructed profile shares eligible midpoints")
    if solve(grid, "all_pairs") == solve(grid, "longest_pairs"):
        raise ValueError("profile does not distinguish declared settings")
    return grid


def teaching_survivors(train: list[dict[str, Any]]) -> list[str]:
    survivors: list[str] = []
    for candidate in CANDIDATE_NAMES:
        if all(solve(pair["input"], candidate) == pair["output"] for pair in train):
            survivors.append(candidate)
    return survivors


def generate_episode(seed: int, selection: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if selection not in SETTING_NAMES:
        raise ValueError(f"selection must be one of {SETTING_NAMES}")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train_inputs = [sample_input(seed, "demo", index) for index in range(demos)]
    test_inputs = [sample_input(seed, "query", index) for index in range(queries)]
    inputs = train_inputs + test_inputs
    keys = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    if len(keys) != len(set(keys)):
        raise ValueError("episode inputs must be distinct")
    train = [{"input": grid, "output": solve(grid, selection)} for grid in train_inputs]
    test = [{"input": grid, "output": solve(grid, selection)} for grid in test_inputs]
    if teaching_survivors(train) != [selection]:
        raise ValueError("visible demonstrations do not uniquely identify intended finite rule")
    return {"train": train, "test": test, "program_solution": program_for(selection),
            "sampling": {"draws": demos + queries, "duplicate_rejections": 0}}


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    return generate_episode(seed, _setting(settings), demos=demos, queries=queries)
