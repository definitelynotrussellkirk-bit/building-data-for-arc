"""Native parametric episode generator for ARC task 75ff4423494a.

``copy_policy=all_anchors`` is the exact canonical rule.  The nearby
``signal_ranked_anchor`` rule counts the cells of the unique color-1 signal,
uses that count as a one-based rank among external cyan anchors, and copies the
discovered prototype only at its original origin and that ranked anchor.
Inputs are independent of the private setting and include a 30x30 stress case.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any

TASK_ID = "75ff4423494a"
PARAMETER_NAME = "copy_policy"
MODES = ("all_anchors", "signal_ranked_anchor")
DEFAULT_SETTINGS = {PARAMETER_NAME: "all_anchors"}

_HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
SIGNAL_RANKED_PROGRAM = (_HOME / "signal_ranked.rkt").read_text(encoding="utf-8")

_DEMO_SIZES = ((11, 13), (13, 15), (16, 18), (18, 20), (21, 23), (24, 26))
_QUERY_SIZES = ((15, 17), (20, 22), (25, 27), (30, 30))
_DEMO_RANKS = (2, 4, 3, 1, 5, 2)
_QUERY_RANKS = (3, 1, 4, 2)
_PAIRS = ((2, 3), (4, 5), (6, 7), (2, 6), (3, 7), (4, 6))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_TEMPLATE = ((0, 0, 8), (0, 1, 0), (1, -1, 0), (1, 0, 0), (1, 1, 0), (2, 0, 1))


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
    return CANONICAL_PROGRAM if mode == "all_anchors" else SIGNAL_RANKED_PROGRAM


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    result: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells: list[tuple[int, int]] = []
        while stack:
            cell = stack.pop()
            cells.append(cell)
            for dr, dc in _CARDINAL:
                neighbor = (cell[0] + dr, cell[1] + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        result.append(cells)
    return result


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    _grid(grid)
    components = _components(grid)
    candidates = [
        cells
        for cells in components
        if len(cells) > 1 and any(grid[r][c] == 8 for r, c in cells)
    ]
    if not candidates:
        raise ValueError("grid needs one multi-cell nonzero prototype containing cyan")
    proto = sorted(
        candidates,
        key=lambda cells: (
            -len(cells),
            min(r for r, _ in cells),
            min(c for _, c in cells),
        ),
    )[0]
    top = min(r for r, _ in proto)
    left = min(c for _, c in proto)
    bottom = max(r for r, _ in proto)
    right = max(c for _, c in proto)
    template = [row[left : right + 1] for row in grid[top : bottom + 1]]
    origin = next(
        (r, c)
        for r, row in enumerate(template)
        for c, value in enumerate(row)
        if value == 8
    )
    abs_origin = (top + origin[0], left + origin[1])
    proto_set = set(proto)
    external = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8 and (r, c) not in proto_set
    ]
    return {
        "components": components,
        "proto": proto_set,
        "template": template,
        "origin": origin,
        "abs_origin": abs_origin,
        "external_anchors": external,
    }


def signal_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    info = analyze(grid)
    signal = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    rank = len(signal)
    external = info["external_anchors"]
    if not 1 <= rank <= len(external):
        raise ValueError("color-1 signal size must rank an external cyan anchor")
    return {
        "signal_cells": [[r, c] for r, c in signal],
        "rank": rank,
        "external_anchors": [[r, c] for r, c in external],
        "selected_anchor": list(external[rank - 1]),
    }


def _overlay(grid: list[list[int]], anchors: list[tuple[int, int]]) -> list[list[int]]:
    info = analyze(grid)
    template = info["template"]
    origin = info["origin"]
    output = [[0 for _ in row] for row in grid]
    for anchor_r, anchor_c in anchors:
        top = anchor_r - origin[0]
        left = anchor_c - origin[1]
        for r, row in enumerate(template):
            for c, value in enumerate(row):
                if value == 0:
                    continue
                rr, cc = top + r, left + c
                if not (0 <= rr < len(output) and 0 <= cc < len(output[0])):
                    continue
                old = output[rr][cc]
                if old == 0:
                    output[rr][cc] = value
                elif old != value:
                    output[rr][cc] = 9
    return output


def apply_ranked(grid: list[list[int]], rank: int) -> list[list[int]]:
    _exact_int(rank, "rank", 1, 32)
    info = analyze(grid)
    external = info["external_anchors"]
    if rank > len(external):
        raise ValueError("rank exceeds external anchor count")
    return _overlay(grid, [info["abs_origin"], external[rank - 1]])


def apply_mode(grid: list[list[int]], mode: str) -> list[list[int]]:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    info = analyze(grid)
    if mode == "all_anchors":
        return _overlay(grid, [info["abs_origin"], *info["external_anchors"]])
    return apply_ranked(grid, signal_intermediate(grid)["rank"])


def _rng(seed: int, namespace: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|{seed}|{namespace}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _cardinally_clear(cells: set[tuple[int, int]], protected: set[tuple[int, int]]) -> bool:
    return all(
        cell not in protected
        and all((cell[0] + dr, cell[1] + dc) not in protected for dr, dc in _CARDINAL)
        for cell in cells
    )


def _anchor_candidates(height: int, width: int) -> list[tuple[int, int]]:
    return [
        (0, 1),
        (0, width - 2),
        (height - 1, 1),
        (height - 1, width - 2),
        (height // 2, 0),
        (height // 2, width - 1),
        (2, width - 2),
        (height - 3, width - 2),
        (2, width // 2),
        (height - 3, width // 2),
        (height // 2, 3),
        (height // 2, width - 4),
    ]


def _place_signal(
    grid: list[list[int]], rank: int, protected: set[tuple[int, int]]
) -> set[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    for row in range(height - 3, 1, -1):
        for col in range(2, width - rank - 1):
            cells = {(row, col + offset) for offset in range(rank)}
            if _cardinally_clear(cells, protected):
                for r, c in cells:
                    grid[r][c] = 1
                return cells
    raise RuntimeError("no isolated signal placement")


def _scene(
    seed: int,
    namespace: str,
    index: int,
    height: int,
    width: int,
    rank: int,
) -> list[list[int]]:
    rng = _rng(seed, namespace, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    payload_a, payload_b = _PAIRS[(seed + index + (0 if namespace == "demo" else 3)) % len(_PAIRS)]
    origin = (3 + (seed + index) % 2, 3 + (seed * 3 + index) % 3)
    protected: set[tuple[int, int]] = set()
    for dr, dc, role in _TEMPLATE:
        r, c = origin[0] + dr, origin[1] + dc
        value = 8 if role == 8 else payload_a if role == 0 else payload_b
        grid[r][c] = value
        protected.add((r, c))

    desired_anchors = 8 if min(height, width) >= 25 else 6 if min(height, width) >= 16 else 5
    anchors: list[tuple[int, int]] = []
    for candidate in _anchor_candidates(height, width):
        if candidate in protected:
            continue
        if any(abs(candidate[0] - r) + abs(candidate[1] - c) <= 1 for r, c in protected):
            continue
        if any(abs(candidate[0] - r) + abs(candidate[1] - c) <= 1 for r, c in anchors):
            continue
        anchors.append(candidate)
        protected.add(candidate)
        grid[candidate[0]][candidate[1]] = 8
        if len(anchors) == desired_anchors:
            break
    if len(anchors) < max(desired_anchors, rank):
        raise RuntimeError("insufficient isolated cyan anchor placements")

    signal = _place_signal(grid, rank, protected)
    occupied = protected | signal
    target = 100 if (height, width) == (30, 30) else max(24, min(70, height * width // 7))
    cells = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(cells)
    palette = (4, 5, 6, 7, 2, 3)
    placed = 0
    for r, c in cells:
        if sum(value != 0 for row in grid for value in row) >= target:
            break
        if grid[r][c] != 0:
            continue
        if any((r + dr, c + dc) in protected for dr, dc in ((0, 0), *_CARDINAL)):
            continue
        grid[r][c] = palette[(placed + seed + index) % len(palette)]
        placed += 1
        occupied.add((r, c))

    info = analyze(grid)
    if info["external_anchors"] != sorted(anchors):
        raise RuntimeError("external anchor inventory drift")
    if signal_intermediate(grid)["rank"] != rank:
        raise RuntimeError("signal rank drift")
    return grid


def _pair(seed: int, namespace: str, index: int, mode: str) -> dict[str, list[list[int]]]:
    if namespace == "demo":
        height, width = _DEMO_SIZES[index]
        rank = _DEMO_RANKS[index]
    else:
        height, width = _QUERY_SIZES[index]
        rank = _QUERY_RANKS[index]
    value = _scene(seed, namespace, index, height, width, rank)
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
