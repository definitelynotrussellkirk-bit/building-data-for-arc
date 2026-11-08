"""Matched-input canonical border and border-to-clockwise-corner relay family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "5ee8de1860a7"
VERSION = "2.0.0"
BORDER_ONLY = {"finish_rule": "border_only"}
CLOCKWISE_SEGMENT = {"finish_rule": "clockwise_segment"}
SETTINGS = (BORDER_ONLY, CLOCKWISE_SEGMENT)
_HOME = Path(__file__).resolve().parent
_PROGRAMS = {
    "border_only": _HOME / "canonical.rkt",
    "clockwise_segment": _HOME / "clockwise_segment.rkt",
}
_COUNTERFACTUAL = _HOME / "skip_border.rkt"
_DIRECTIONS = ("up", "right", "down", "left")
_DIRECTION_VECTORS = {
    "up": (-1, 0),
    "right": (0, 1),
    "down": (1, 0),
    "left": (0, -1),
}
_DIRECTION_COLORS = {
    "up": (1, 5, 9),
    "right": (2, 6),
    "down": (3, 7),
    "left": (4,),
}
_DEMO_SPECS = (
    (5, 7, "up", 3),
    (8, 9, "right", 3),
    (11, 13, "down", 4),
    (14, 12, "left", 4),
    (18, 20, "up", 6),
    (24, 17, "right", 7),
)
_QUERY_SPECS = (
    (7, 13, "down", 4),
    (14, 22, "left", 5),
    (21, 16, "up", 6),
    (30, 30, "right", 15),
)


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _mode(settings: Any) -> str:
    if (type(settings) is not dict or set(settings) != {"finish_rule"}
            or type(settings["finish_rule"]) is not str
            or settings["finish_rule"] not in _PROGRAMS):
        raise ValueError("settings must contain only finish_rule=border_only|clockwise_segment")
    return settings["finish_rule"]


def program(settings: Any) -> str:
    return _PROGRAMS[_mode(settings)].read_text(encoding="utf-8")


def _mix_seed(seed: int, role: str, index: int, attempt: int) -> int:
    payload = f"{TASK_ID}|{seed}|{role}|{index}|{attempt}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _validate_grid(grid: Any) -> tuple[list[list[int]], int, int, int, int, int]:
    if (type(grid) is not list or not 3 <= len(grid) <= 30 or not grid
            or type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(value) is not int or not 0 <= value <= 9 for value in row)
                   for row in grid)):
        raise ValueError("expected a rectangular exact-integer grid within 3..30 by 3..30")
    nonzero = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if len(nonzero) != 1:
        raise ValueError("input must contain exactly one nonzero marker")
    row, column, color = nonzero[0]
    if not (0 < row < len(grid) - 1 and 0 < column < len(grid[0]) - 1):
        raise ValueError("the sole marker must be strictly interior")
    return deepcopy(grid), len(grid), len(grid[0]), row, column, color


def _direction(color: int) -> str:
    # Color 8 is retained for totality on the canonical source domain.  The
    # generated family still excludes it because painting an 8 segment on an
    # 8 border would not distinguish the alternate setting.
    if color == 8:
        return "left"
    for direction, colors in _DIRECTION_COLORS.items():
        if color in colors:
            return direction
    raise ValueError(f"unsupported marker color {color}")


def _border(grid: list[list[int]]) -> list[list[int]]:
    _, height, width, _, _, color = _validate_grid(grid)
    return [
        [color if row in (0, height - 1) or column in (0, width - 1) else 0
         for column in range(width)]
        for row in range(height)
    ]


def route_intermediate(grid: list[list[int]], direction: str | None = None) -> dict[str, Any]:
    clean, height, width, marker_row, marker_column, color = _validate_grid(grid)
    direction = _direction(color) if direction is None else direction
    if direction not in _DIRECTIONS:
        raise ValueError(f"direction must be one of {_DIRECTIONS}")
    dr, dc = _DIRECTION_VECTORS[direction]
    bordered = _border(clean)
    row, column = marker_row + dr, marker_column + dc
    while bordered[row][column] == 0:
        row += dr
        column += dc
    if row == 0:
        side = "top"
        cells = [(0, c) for c in range(column, width)]
    elif column == width - 1:
        side = "right"
        cells = [(r, width - 1) for r in range(row, height)]
    elif row == height - 1:
        side = "bottom"
        cells = [(height - 1, c) for c in range(column, -1, -1)]
    else:
        side = "left"
        cells = [(r, 0) for r in range(row, -1, -1)]
    return {
        "marker": [marker_row, marker_column],
        "direction": direction,
        "hit": [row, column],
        "hit_side": side,
        "next_clockwise_corner": list(cells[-1]),
        "segment_length": len(cells),
        "segment_cells": [list(cell) for cell in cells],
        "bordered_grid": bordered,
    }


def clockwise_output(grid: list[list[int]], direction: str | None = None) -> list[list[int]]:
    intermediate = route_intermediate(grid, direction)
    out = deepcopy(intermediate["bordered_grid"])
    for row, column in intermediate["segment_cells"]:
        out[row][column] = 8
    return out


def solve(grid: list[list[int]], settings: Any) -> list[list[int]]:
    return _border(grid) if _mode(settings) == "border_only" else clockwise_output(grid)


def _counterclockwise_output(grid: list[list[int]]) -> list[list[int]]:
    intermediate = route_intermediate(grid)
    bordered = deepcopy(intermediate["bordered_grid"])
    row, column = intermediate["hit"]
    height, width = len(grid), len(grid[0])
    if row == 0:
        cells = [(0, c) for c in range(column, -1, -1)]
    elif column == width - 1:
        cells = [(r, width - 1) for r in range(row, -1, -1)]
    elif row == height - 1:
        cells = [(height - 1, c) for c in range(column, width)]
    else:
        cells = [(r, 0) for r in range(row, height)]
    for r, c in cells:
        bordered[r][c] = 8
    return bordered


def _whole_hit_side(grid: list[list[int]]) -> list[list[int]]:
    intermediate = route_intermediate(grid)
    out = deepcopy(intermediate["bordered_grid"])
    side = intermediate["hit_side"]
    height, width = len(grid), len(grid[0])
    cells = {
        "top": [(0, c) for c in range(width)],
        "right": [(r, width - 1) for r in range(height)],
        "bottom": [(height - 1, c) for c in range(width)],
        "left": [(r, 0) for r in range(height)],
    }[side]
    for row, column in cells:
        out[row][column] = 8
    return out


def _thick_border(grid: list[list[int]]) -> list[list[int]]:
    _, height, width, _, _, color = _validate_grid(grid)
    return [
        [color if min(row, column, height - 1 - row, width - 1 - column) < 2 else 0
         for column in range(width)]
        for row in range(height)
    ]


def _rivals(grid: list[list[int]], mode: str) -> dict[str, list[list[int]]]:
    if mode == "border_only":
        return {
            "clockwise_segment": clockwise_output(grid),
            "thick_border": _thick_border(grid),
        }
    return {
        "border_only": _border(grid),
        "counterclockwise_segment": _counterclockwise_output(grid),
        "fixed_up": clockwise_output(grid, "up"),
        "fixed_right": clockwise_output(grid, "right"),
        "fixed_down": clockwise_output(grid, "down"),
        "fixed_left": clockwise_output(grid, "left"),
        "whole_hit_side": _whole_hit_side(grid),
    }


def lesson_report(episode: dict[str, Any], settings: Any) -> dict[str, Any]:
    mode = _mode(settings)
    train = episode["train"]
    test = episode["test"]
    setting_survivors = [
        candidate["finish_rule"]
        for candidate in SETTINGS
        if all(solve(pair["input"], candidate) == pair["output"] for pair in train)
    ]
    names = sorted(_rivals(train[0]["input"], mode))
    survivors = set(names)
    rejected_at: dict[str, int] = {}
    for index, pair in enumerate(train):
        for name, output in _rivals(pair["input"], mode).items():
            if output != pair["output"]:
                survivors.discard(name)
                rejected_at.setdefault(name, index)
    query_disagreements = {
        name: any(_rivals(pair["input"], mode)[name] != pair["output"] for pair in test)
        for name in names
    }
    harmful = sorted(name for name in survivors if query_disagreements[name])
    return {
        "setting_survivors": setting_survivors,
        "harmful_shortcut_survivors": harmful,
        "rejected_at_demo": rejected_at,
        "query_disagreements": query_disagreements,
    }


def _marker_position(rng: random.Random, height: int, width: int, direction: str, minimum: int) -> tuple[int, int]:
    if direction == "up":
        columns = list(range(1, width - minimum + 1))
        if not columns:
            raise ValueError("grid cannot provide requested clockwise segment")
        return rng.randrange(1, height - 1), rng.choice(columns)
    if direction == "right":
        rows = list(range(1, height - minimum + 1))
        if not rows:
            raise ValueError("grid cannot provide requested clockwise segment")
        return rng.choice(rows), rng.randrange(1, width - 1)
    if direction == "down":
        columns = list(range(minimum - 1, width - 1))
        if not columns:
            raise ValueError("grid cannot provide requested clockwise segment")
        return rng.randrange(1, height - 1), rng.choice(columns)
    rows = list(range(minimum - 1, height - 1))
    if not rows:
        raise ValueError("grid cannot provide requested clockwise segment")
    return rng.choice(rows), rng.randrange(1, width - 1)


def _scene(seed: int, role: str, index: int, spec: tuple[int, int, str, int], attempt: int) -> list[list[int]]:
    height, width, direction, minimum = spec
    rng = random.Random(_mix_seed(seed, role, index, attempt))
    row, column = _marker_position(rng, height, width, direction, minimum)
    color = rng.choice(_DIRECTION_COLORS[direction])
    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[row][column] = color
    intermediate = route_intermediate(grid)
    if intermediate["direction"] != direction or intermediate["segment_length"] < minimum:
        raise AssertionError("constructed route does not satisfy its specification")
    return grid


def _candidate_bank(seed: int, attempt: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [_scene(seed, "demo", index, spec, attempt) for index, spec in enumerate(_DEMO_SPECS)]
    queries = [_scene(seed, "query", index, spec, attempt) for index, spec in enumerate(_QUERY_SPECS)]
    return demos, queries


def select_inputs(seed: Any) -> dict[str, list[dict[str, list[list[int]]]]]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    for attempt in range(128):
        demos, queries = _candidate_bank(seed, attempt)
        if len({repr(grid) for grid in demos + queries}) != len(demos) + len(queries):
            continue
        acceptable = True
        for settings in SETTINGS:
            episode = {
                "train": [{"input": grid, "output": solve(grid, settings)} for grid in demos[:2]],
                "test": [{"input": grid, "output": solve(grid, settings)} for grid in queries],
            }
            report = lesson_report(episode, settings)
            if (report["setting_survivors"] != [settings["finish_rule"]]
                    or report["harmful_shortcut_survivors"]):
                acceptable = False
                break
        if acceptable:
            return {
                "train": [{"input": deepcopy(grid)} for grid in demos],
                "test": [{"input": deepcopy(grid)} for grid in queries],
            }
    raise RuntimeError("failed to construct a two-demo distinguishing matched-input bank")


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    mode = _mode(settings)
    selected = select_inputs(seed)
    train_inputs = [pair["input"] for pair in selected["train"][:demos]]
    test_inputs = [pair["input"] for pair in selected["test"][:queries]]
    chosen = {"finish_rule": mode}
    return {
        "train": [{"input": deepcopy(grid), "output": solve(grid, chosen)} for grid in train_inputs],
        "test": [{"input": deepcopy(grid), "output": solve(grid, chosen)} for grid in test_inputs],
        "program_solution": program(chosen),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    query_index = _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def causal_case(grid: list[list[int]]) -> dict[str, Any]:
    intermediate = route_intermediate(grid)
    output = clockwise_output(grid)
    return {
        "input": deepcopy(grid),
        "settings": deepcopy(CLOCKWISE_SEGMENT),
        "intermediate_value": {
            key: deepcopy(value)
            for key, value in intermediate.items()
            if key not in {"bordered_grid", "segment_cells"}
        },
        "program": program(CLOCKWISE_SEGMENT),
        "output": output,
        "counterfactual_program": _COUNTERFACTUAL.read_text(encoding="utf-8"),
        "counterfactual_output": deepcopy(grid),
        "ablation": "skip_a",
        "step_a": "Replace the interior marker with a one-cell border in the marker color.",
        "intermediate": "The first newly created border cell hit by the marker's color-keyed cardinal ray, including which side and coordinate it occupies.",
        "step_b": "Starting at that hit, traverse clockwise along the created border to the next corner and recolor that segment color 8.",
        "why_b_depends_on_a": "The raw input has no border cell for the ray to hit; step A creates the input-dependent endpoint that anchors step B's segment.",
    }
