"""Native two-setting adapter for folded pair selection."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

_HOME = Path(__file__).resolve().parent
_TASK_HOME = _HOME.parents[1]
_SOURCE = _TASK_HOME / "generator.py"
_NAME = "_arc_0c4c1974cbf2_production_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load production generator: {_SOURCE}")
_PRODUCTION = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PRODUCTION
_SPEC.loader.exec_module(_PRODUCTION)

SETTINGS = ({"pair_mode": "overlap"}, {"pair_mode": "exclusive"})
DEFAULT = SETTINGS[0]
_PROGRAMS = {
    "overlap": (_HOME / "canonical.rkt").read_text(),
    "exclusive": (_HOME / "exclusive.rkt").read_text(),
}
_COLORS = (1, 3, 4, 5, 6, 7, 9)


def _setting(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"pair_mode"}:
        raise ValueError("settings must contain exactly pair_mode")
    value = settings["pair_mode"]
    if type(value) is not str or value not in _PROGRAMS:
        raise ValueError("pair_mode must be overlap or exclusive")
    return {"pair_mode": value}


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _mix(seed: int, stream: str, index: int) -> int:
    payload = f"0c4c1974cbf2:{seed}:{stream}:{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & ((1 << 63) - 1)


def _validate_grid(grid: Any) -> tuple[list[list[int]], int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and at most 30x30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be exact ARC integers 0..9")
    bars = [col for col in range(width) if all(row[col] == 8 for row in grid)]
    if len(bars) != 1:
        raise ValueError("grid must contain exactly one full-height color-8 bar")
    bar = bars[0]
    if bar * 2 + 1 != width:
        raise ValueError("fold bar must be centered in an odd-width grid")
    return deepcopy(grid), bar


def program(settings: dict[str, Any]) -> str:
    return _PROGRAMS[_setting(settings)["pair_mode"]]


def dependency_intermediate(grid: Any, settings: dict[str, Any]) -> dict[str, Any]:
    normalized, bar = _validate_grid(grid)
    mode = _setting(settings)["pair_mode"]
    selected: list[list[int]] = []
    for row in range(len(normalized)):
        for col in range(bar):
            mirror = 2 * bar - col
            left = normalized[row][col] != 0
            right = normalized[row][mirror] != 0
            keep = left and right if mode == "overlap" else left != right
            if keep:
                selected.append([row, col, mirror])
    return {"pair_mode": mode, "bar_col": bar, "selected_pairs": selected}


def solve_from_intermediate(grid: Any, intermediate: dict[str, Any]) -> list[list[int]]:
    normalized, bar = _validate_grid(grid)
    if type(intermediate) is not dict or intermediate.get("bar_col") != bar:
        raise ValueError("intermediate does not belong to this grid")
    selected = intermediate.get("selected_pairs")
    if type(selected) is not list:
        raise ValueError("intermediate selected_pairs must be a list")
    output = [[0 for _ in row] for row in normalized]
    for item in selected:
        if type(item) is not list or len(item) != 3 or any(type(value) is not int for value in item):
            raise ValueError("invalid selected pair")
        row, col, mirror = item
        if not (0 <= row < len(output) and 0 <= col < bar < mirror < len(output[0])
                and mirror == 2 * bar - col):
            raise ValueError("selected pair is out of bounds")
        output[row][mirror] = 2
    return output


def solve(grid: Any, settings: dict[str, Any]) -> list[list[int]]:
    return solve_from_intermediate(grid, dependency_intermediate(grid, settings))


def _stress_grid(seed: int, index: int, height: int, half: int) -> list[list[int]]:
    salt = _mix(seed, "stress", index)
    width = 2 * half + 1
    grid = [[0] * width for _ in range(height)]
    for row in range(height):
        grid[row][half] = 8
    for row in range(height):
        for col in range(half):
            left_code = (7 * row + 11 * col + salt) % 10
            right_code = (13 * row + 5 * col + salt // 17) % 10
            mirror = 2 * half - col
            if left_code < 5:
                grid[row][col] = _COLORS[(row + 2 * col + salt) % len(_COLORS)]
            if right_code < 5:
                grid[row][mirror] = _COLORS[(3 * row + col + salt // 7) % len(_COLORS)]
    grid[0][0] = 1
    grid[0][2 * half] = 3
    if half > 1:
        grid[0][1] = 4
        grid[0][2 * half - 1] = 0
    grid[-1][half - 1] = 0
    grid[-1][half + 1] = 5
    return grid


def _input_banks(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demo_profiles = (2, 3, 4, 0, 1, 2)
    demos = [
        _PRODUCTION.generate(_mix(seed, "demo", index), profile, difficulty="hard")
        for index, profile in enumerate(demo_profiles)
    ]
    queries = [
        _PRODUCTION.generate(_mix(seed, "query", 0), 3, difficulty="hard"),
        _PRODUCTION.generate(_mix(seed, "query", 1), 4, difficulty="hard"),
        _stress_grid(seed, 2, 17, 10),
        _stress_grid(seed, 3, 30, 14),
    ]
    return demos, queries


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    selected = _setting(settings)
    demo_inputs, query_inputs = _input_banks(seed)

    def pairs(inputs: list[list[list[int]]]) -> list[dict[str, list[list[int]]]]:
        return [{"input": deepcopy(grid), "output": solve(grid, selected)} for grid in inputs]

    episode = {
        "settings": deepcopy(selected),
        "train": pairs(demo_inputs[:demos]),
        "test": pairs(query_inputs[:queries]),
        "program_solution": program(selected),
    }
    visible = [repr(pair["input"]) for pair in episode["train"] + episode["test"]]
    if len(visible) != len(set(visible)):
        raise AssertionError("generated inputs must be distinct")
    return episode
