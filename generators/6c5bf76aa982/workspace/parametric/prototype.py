"""Native parametric episode generator for ARC task 6c5bf76aa982.

``border_policy=exactly_one`` is the exact canonical rule.  The nearby
``signal_target`` setting counts the cells in the unique cyan signal and uses
that count as the target number of distinct canvas borders touched by an orange
component.  The sampler is setting-neutral and includes a substantive 30x30
query with components touching zero, one, two and three borders.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any

TASK_ID = "6c5bf76aa982"
PARAMETER_NAME = "border_policy"
MODES = ("exactly_one", "signal_target")
DEFAULT_SETTINGS = {PARAMETER_NAME: "exactly_one"}

_HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
SIGNAL_TARGET_PROGRAM = (_HOME / "signal_target.rkt").read_text(encoding="utf-8")

_DEMO_SIZES = ((12, 14), (14, 16), (17, 19), (19, 21), (22, 24), (24, 27))
_QUERY_SIZES = ((15, 17), (20, 22), (25, 27), (30, 30))
_DEMO_TARGETS = (2, 3, 2, 3, 2, 3)
_QUERY_TARGETS = (3, 2, 3, 2)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain only {PARAMETER_NAME}")
    mode = settings[PARAMETER_NAME]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"{PARAMETER_NAME} must be one of {MODES}")
    return mode


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be rectangular with dimensions in 1..30")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid cells must be exact ARC integers 0..9")
    return value


def program(settings: Any) -> str:
    mode = _validate_settings(settings)
    return CANONICAL_PROGRAM if mode == "exactly_one" else SIGNAL_TARGET_PROGRAM


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    _grid(grid)
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < len(grid)
                        and 0 <= cc < len(grid[0])
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            found.append({"color": color, "cells": cells})
    return found


def touch_count(cells: list[tuple[int, int]], height: int, width: int) -> int:
    return sum((
        any(r == 0 for r, _ in cells),
        any(r == height - 1 for r, _ in cells),
        any(c == 0 for _, c in cells),
        any(c == width - 1 for _, c in cells),
    ))


def signal_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    _grid(grid)
    signal = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    target = len(signal)
    if target not in (2, 3):
        raise ValueError("cyan signal must contain exactly two or three cells")
    orange = [
        {
            "cells": [[r, c] for r, c in obj["cells"]],
            "touch_count": touch_count(obj["cells"], len(grid), len(grid[0])),
        }
        for obj in components(grid)
        if obj["color"] == 7
    ]
    return {
        "signal_cells": [[r, c] for r, c in signal],
        "target_touch_count": target,
        "orange_components": orange,
    }


def apply_touch_target(grid: list[list[int]], target: int) -> list[list[int]]:
    _exact_int(target, "target", 0, 4)
    output = copy.deepcopy(_grid(grid))
    height, width = len(grid), len(grid[0])
    for obj in components(grid):
        if obj["color"] == 7 and touch_count(obj["cells"], height, width) == target:
            for r, c in obj["cells"]:
                output[r][c] = 3
    return output


def apply_mode(grid: list[list[int]], mode: str) -> list[list[int]]:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if mode == "exactly_one":
        return apply_touch_target(grid, 1)
    return apply_touch_target(grid, signal_intermediate(grid)["target_touch_count"])


def _rng(seed: int, namespace: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|{seed}|{namespace}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _paint(grid: list[list[int]], cells: set[tuple[int, int]], color: int) -> None:
    for r, c in cells:
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            raise RuntimeError("planned cell outside grid")
        if grid[r][c] != 0:
            raise RuntimeError("planned components overlap")
        grid[r][c] = color


def _scene(
    seed: int,
    namespace: str,
    index: int,
    height: int,
    width: int,
    target: int,
) -> list[list[int]]:
    rng = _rng(seed, namespace, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    # Exactly one border: compact top component, separated from row two.
    mid = width // 2
    top_only = {(0, mid - 1), (0, mid), (0, mid + 1)}
    _paint(grid, top_only, 7)

    # Exactly three borders: left + right through row two, then down the right edge to bottom.
    three = {(2, c) for c in range(width)} | {(r, width - 1) for r in range(2, height)}
    _paint(grid, three, 7)

    # Exactly two borders: bottom-left corner L, isolated from the three-border object.
    two = {(height - 1, 0), (height - 2, 0), (height - 1, 1)}
    _paint(grid, two, 7)

    # Zero borders: interior block whose location varies but stays isolated.
    interior_row = max(5, height - 5 - (seed + index) % 2)
    interior_col = 3 + (seed * 5 + index) % max(1, width - 9)
    zero = {
        (interior_row, interior_col),
        (interior_row, interior_col + 1),
        (interior_row + 1, interior_col),
        (interior_row + 1, interior_col + 1),
    }
    _paint(grid, zero, 7)

    # Connected cyan signal; there are no other cyan cells.
    signal_row = 4
    signal_col = 2 + (seed + index) % max(1, width - target - 4)
    signal = {(signal_row, signal_col + offset) for offset in range(target)}
    _paint(grid, signal, 8)

    # Setting-neutral distractors add density and varied non-orange structure.
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    desired = 105 if (height, width) == (30, 30) else max(35, min(82, height * width // 5))
    candidates = [(r, c) for r in range(1, height - 1) for c in range(width)]
    rng.shuffle(candidates)
    palette = (1, 2, 4, 5, 6, 9)
    placed = 0
    for r, c in candidates:
        if sum(value != 0 for row in grid for value in row) >= desired:
            break
        if (r, c) in occupied or grid[r][c] != 0:
            continue
        # Keep a blank moat around the signal so its component/count is obvious.
        if any(abs(r - sr) + abs(c - sc) <= 1 for sr, sc in signal):
            continue
        grid[r][c] = palette[(placed + seed + index) % len(palette)]
        occupied.add((r, c))
        placed += 1

    counts = sorted(
        touch_count(obj["cells"], height, width)
        for obj in components(grid)
        if obj["color"] == 7
    )
    if counts != [0, 1, 2, 3]:
        raise RuntimeError(f"orange touch-count inventory drift: {counts}")
    if signal_intermediate(grid)["target_touch_count"] != target:
        raise RuntimeError("signal target drift")
    return grid


def _pair(seed: int, namespace: str, index: int, mode: str) -> dict[str, list[list[int]]]:
    if namespace == "demo":
        height, width = _DEMO_SIZES[index]
        target = _DEMO_TARGETS[index]
    else:
        height, width = _QUERY_SIZES[index]
        target = _QUERY_TARGETS[index]
    value = _scene(seed, namespace, index, height, width, target)
    return {"input": value, "output": apply_mode(value, mode)}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    mode = _validate_settings(settings)
    demo_count = _exact_int(demos, "demos", 2, 6)
    query_count = _exact_int(queries, "queries", 4, 4)
    train = [_pair(seed, "demo", index, mode) for index in range(demo_count)]
    test = [_pair(seed, "query", index, mode) for index in range(query_count)]
    inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(inputs) != len(set(inputs)):
        raise RuntimeError("episode inputs must be distinct")
    return {"train": train, "test": test, "program_solution": program(settings)}
