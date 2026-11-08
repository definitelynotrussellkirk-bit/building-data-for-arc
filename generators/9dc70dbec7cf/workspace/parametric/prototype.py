"""Matched-input family for ordered elbow routing and overlap counting.

``horizontal_then_vertical`` is the byte-identical canonical rule.  The
alternate routes each row-major endpoint pair vertically first.  In both
settings A computes an input-dependent ordered path for every pair (including
canonical bend multiplicity), and B consumes those paths by counting cell
coverage and mapping counts to colors 3, 6, and 9.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "9dc70dbec7cf"
PARAMETER = "elbow_order"
MODES = ("horizontal_then_vertical", "vertical_then_horizontal")
_DIR = Path(__file__).resolve().parent
_PROGRAMS = {
    "horizontal_then_vertical": (_DIR / "canonical.rkt").read_text(encoding="utf-8"),
    "vertical_then_horizontal": (_DIR / "vertical_then_horizontal.rkt").read_text(encoding="utf-8"),
}
_DEMO_DIMS = ((13, 15), (15, 18), (18, 20), (21, 24), (26, 28), (30, 30))
_QUERY_DIMS = ((14, 17), (20, 23), (26, 29), (30, 30))
_COLORS = (1, 2, 4, 5, 7, 8)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must name exactly elbow_order")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"elbow_order must be one of {MODES}")
    return mode


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAMS[_mode(settings)]


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        raise ValueError("grid must fit within 30x30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _pairs(grid: list[list[int]]) -> list[tuple[int, tuple[int, int], tuple[int, int]]]:
    _validate_grid(grid)
    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    bad = {color: len(cells) for color, cells in positions.items() if len(cells) != 2}
    if bad:
        raise ValueError(f"every nonzero color must appear exactly twice: {bad}")
    if not 1 <= len(positions) <= 9:
        raise ValueError("input must contain at least one endpoint pair")
    return [(color, *sorted(cells)) for color, cells in sorted(positions.items())]


def _inclusive(a: int, b: int) -> list[int]:
    step = 1 if b >= a else -1
    return list(range(a, b + step, step))


def _path(start: tuple[int, int], end: tuple[int, int], mode: str) -> list[tuple[int, int]]:
    r0, c0 = start
    r1, c1 = end
    if mode == "horizontal_then_vertical":
        return ([(r0, c) for c in _inclusive(c0, c1)]
                + [(r, c1) for r in _inclusive(r0, r1)])
    if mode == "vertical_then_horizontal":
        return ([(r, c0) for r in _inclusive(r0, r1)]
                + [(r1, c) for c in _inclusive(c0, c1)])
    raise ValueError(f"unsupported mode: {mode}")


def _render(height: int, width: int, paths: list[list[tuple[int, int]]]) -> list[list[int]]:
    coverage = Counter(cell for path in paths for cell in path)
    output = [[0] * width for _ in range(height)]
    for (r, c), count in coverage.items():
        output[r][c] = 9 if count >= 3 else 6 if count == 2 else 3
    return output


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _mode(settings)
    pairs = _pairs(grid)
    return _render(len(grid), len(grid[0]), [_path(start, end, mode) for _, start, end in pairs])


def intermediate(grid: list[list[int]], settings: dict[str, Any]) -> dict[str, Any]:
    mode = _mode(settings)
    paths = []
    coverage: Counter[tuple[int, int]] = Counter()
    for color, start, end in _pairs(grid):
        cells = _path(start, end, mode)
        bend = (start[0], end[1]) if mode == "horizontal_then_vertical" else (end[0], start[1])
        coverage.update(cells)
        paths.append({
            "color": color,
            "start": list(start),
            "end": list(end),
            "bend": list(bend),
            "bend_multiplicity": cells.count(bend),
            "cells": [list(cell) for cell in cells],
        })
    histogram = Counter(coverage.values())
    return {
        "mode": mode,
        "paths": paths,
        "coverage_histogram": {str(count): frequency for count, frequency in sorted(histogram.items())},
    }


def output_from_intermediate(grid: list[list[int]], value: dict[str, Any]) -> list[list[int]]:
    _validate_grid(grid)
    if type(value) is not dict or type(value.get("paths")) is not list:
        raise ValueError("intermediate must contain paths")
    paths: list[list[tuple[int, int]]] = []
    for row in value["paths"]:
        if type(row) is not dict or type(row.get("cells")) is not list:
            raise ValueError("each intermediate path must contain cells")
        paths.append([tuple(cell) for cell in row["cells"]])
    return _render(len(grid), len(grid[0]), paths)


def validate_input(grid: Any) -> list[str]:
    try:
        pairs = _pairs(grid)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    if not 2 <= len(pairs) <= 6:
        errors.append(f"parametric grammar requires 2..6 endpoint pairs, found {len(pairs)}")
    for color, start, end in pairs:
        if start[0] == end[0] or start[1] == end[1]:
            errors.append(f"color {color} must require a genuine elbow")
    try:
        if solve(grid, {PARAMETER: MODES[0]}) == solve(grid, {PARAMETER: MODES[1]}):
            errors.append("declared route orders must change the output")
    except ValueError as exc:  # pragma: no cover
        errors.append(str(exc))
    return errors


def _rng(seed: int, split: str, index: int, attempt: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|route-v1|{seed}|{split}|{index}|{attempt}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _candidate_scene(seed: int, split: str, index: int, attempt: int) -> list[list[int]]:
    dims = _DEMO_DIMS if split == "train" else _QUERY_DIMS
    height, width = dims[index]
    rng = _rng(seed, split, index, attempt)
    pair_count = min(6, 3 + ((index + (0 if split == "train" else 1)) % 4))
    if height == 30 and width == 30:
        pair_count = 6
    colors = list(_COLORS[:pair_count])
    rng.shuffle(colors)
    grid = [[0] * width for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    upper_max = max(1, height // 3)
    lower_min = min(height - 2, max(upper_max + 2, (2 * height) // 3))
    min_span = max(3, width // 3)
    for color in colors:
        for _ in range(200):
            start = (rng.randint(0, upper_max), rng.randint(0, width - 1))
            end = (rng.randint(lower_min, height - 1), rng.randint(0, width - 1))
            if start in occupied or end in occupied or start[1] == end[1]:
                continue
            if abs(start[1] - end[1]) < min_span:
                continue
            occupied.update((start, end))
            grid[start[0]][start[1]] = color
            grid[end[0]][end[1]] = color
            break
        else:
            raise AssertionError("failed to place a separated endpoint pair")
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    return grid


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    dims = _DEMO_DIMS if split == "train" else _QUERY_DIMS
    if not 0 <= index < len(dims):
        raise ValueError(f"unsupported {split} index {index}")
    for attempt in range(256):
        grid = _candidate_scene(seed, split, index, attempt)
        if validate_input(grid):
            continue
        h_output = solve(grid, {PARAMETER: MODES[0]})
        v_output = solve(grid, {PARAMETER: MODES[1]})
        if h_output == v_output:
            continue
        if not any(value == 6 for row in h_output for value in row):
            continue
        if len(grid) == 30 and sum(value != 0 for row in v_output for value in row) < 100:
            continue
        return grid
    raise RuntimeError(f"failed to construct a lawful distinguishing {split} scene {index}")


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    mode = _mode(settings)
    train: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    seen: set[bytes] = set()
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = _scene(seed, split, index)
            key = json.dumps(grid, separators=(",", ":")).encode()
            if key in seen:
                raise AssertionError("deterministic schedule emitted a duplicate input")
            seen.add(key)
            target.append({"input": grid, "output": solve(grid, {PARAMETER: mode})})
    return {"train": train, "test": test, "program_solution": program({PARAMETER: mode})}


def public_view(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def _custom_solve(grid: list[list[int]], builder: Callable[[tuple[int, int], tuple[int, int]], list[tuple[int, int]]], *, mapper: Callable[[int], int] | None = None) -> list[list[int]]:
    paths = [builder(start, end) for _, start, end in _pairs(grid)]
    if mapper is None:
        return _render(len(grid), len(grid[0]), paths)
    coverage = Counter(cell for path in paths for cell in path)
    out = [[0] * len(grid[0]) for _ in grid]
    for (r, c), count in coverage.items():
        out[r][c] = mapper(count)
    return out


def _both_elbows(grid):
    return _custom_solve(grid, lambda a, b: _path(a, b, MODES[0]) + _path(a, b, MODES[1]))


def _endpoints_only(grid):
    return _custom_solve(grid, lambda a, b: [a, b])


def _horizontal_only(grid):
    return _custom_solve(grid, lambda a, b: [(a[0], c) for c in _inclusive(a[1], b[1])])


def _vertical_only(grid):
    return _custom_solve(grid, lambda a, b: [(r, b[1]) for r in _inclusive(a[0], b[0])])


def _binary_coverage(grid):
    return _custom_solve(grid, lambda a, b: _path(a, b, MODES[0]), mapper=lambda count: 3)


def _swapped_overlap_palette(grid):
    return _custom_solve(
        grid,
        lambda a, b: _path(a, b, MODES[0]),
        mapper=lambda count: 6 if count >= 3 else 9 if count == 2 else 3,
    )


def _column_order_horizontal(grid):
    paths = []
    for _, start, end in _pairs(grid):
        left, right = sorted((start, end), key=lambda cell: (cell[1], cell[0]))
        paths.append(_path(left, right, MODES[0]))
    return _render(len(grid), len(grid[0]), paths)


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    MODES[0]: lambda grid: solve(grid, {PARAMETER: MODES[0]}),
    MODES[1]: lambda grid: solve(grid, {PARAMETER: MODES[1]}),
    "both_elbows": _both_elbows,
    "endpoints_only": _endpoints_only,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "binary_coverage": _binary_coverage,
    "swapped_overlap_palette": _swapped_overlap_palette,
    "column_order_horizontal": _column_order_horizontal,
}


def audit_episode(seed: int, mode: str, *, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    episode = generate(seed, {PARAMETER: mode}, demos, queries)
    survivors: list[str] = []
    harmful: list[str] = []
    for name, rival in RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in episode["train"]):
            survivors.append(name)
            if any(rival(pair["input"]) != pair["output"] for pair in episode["test"]):
                harmful.append(name)
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {PARAMETER: mode},
        "fit_uses": "demonstrations_only",
        "rivals": sorted(RIVALS),
        "survivors": survivors,
        "harmful_survivors": harmful,
        "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
        "intermediate": intermediate(episode["test"][0]["input"], {PARAMETER: mode}),
    }
