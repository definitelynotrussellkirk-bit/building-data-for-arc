"""Upward projection with an optional equal-endpoint top-edge relay.

The default program is the exact canonical rule.  The alternate performs that
same projection first, then uses the newly derived top-edge endpoints: every
color appearing exactly twice on the completed top row bridges its two
endpoints along that row.  Inputs never contain top-row seeds, so the second
operation genuinely consumes Stage A's intermediate rather than raw input.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "138ffc14ac65"
VERSION = "equal-top-bridge-v1"
HERE = Path(__file__).resolve().parent
PARAMETER = "finish_rule"
MODES = ("up_only", "equal_top_bridge")
SETTINGS = tuple({PARAMETER: mode} for mode in MODES)

# height, width, number of equal-color pairs, singleton colors
DEMO_PROFILES = (
    (10, 12, 2, 1),
    (12, 15, 2, 2),
    (14, 18, 3, 1),
    (18, 20, 3, 2),
    (22, 24, 4, 1),
    (26, 27, 4, 1),
)
QUERY_PROFILES = (
    (13, 16, 2, 2),
    (18, 21, 3, 1),
    (24, 27, 4, 1),
    (30, 30, 4, 1),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {PARAMETER}:
        raise ValueError("settings must name exactly finish_rule")
    mode = value[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"finish_rule must be one of {MODES}")
    return {PARAMETER: mode}


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return deepcopy(value)


def program(settings: Any) -> str:
    mode = _setting(settings)[PARAMETER]
    filename = "canonical.rkt" if mode == "up_only" else "equal_top_bridge.rkt"
    return (HERE / filename).read_bytes().decode("utf-8")


def project_up(grid: Any) -> list[list[int]]:
    original = _grid(grid)
    h, w = len(original), len(original[0])
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            value = original[r][c]
            if value:
                for rr in range(r + 1):
                    out[rr][c] = value
    return out


def _pair_intervals(stage_a: list[list[int]]) -> list[tuple[int, int, int]]:
    top = stage_a[0]
    intervals: list[tuple[int, int, int]] = []
    for color in range(1, 10):
        hits = [c for c, value in enumerate(top) if value == color]
        if len(hits) == 2:
            intervals.append((color, hits[0], hits[1]))
    return intervals


def bridge_equal_endpoints(stage_a: Any) -> list[list[int]]:
    data = _grid(stage_a)
    out = deepcopy(data)
    for color, left, right in _pair_intervals(data):
        for c in range(left, right + 1):
            out[0][c] = color
    return out


def transform(grid: Any, settings: Any) -> list[list[int]]:
    mode = _setting(settings)[PARAMETER]
    stage_a = project_up(grid)
    return stage_a if mode == "up_only" else bridge_equal_endpoints(stage_a)


def _rng(seed: int, split: str, index: int, purpose: str) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}:{purpose}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _profile(split: str, index: int) -> tuple[int, int, int, int]:
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    if not 0 <= index < len(profiles):
        raise ValueError("profile index outside available bank")
    return profiles[index]


def _bands(length: int, count: int) -> list[tuple[int, int]]:
    return [(length * i // count, length * (i + 1) // count - 1) for i in range(count)]


def _columns(width: int, pair_count: int, singleton_count: int, rng: random.Random) -> tuple[list[tuple[int, int]], list[int]]:
    intervals: list[tuple[int, int]] = []
    occupied_ranges: list[range] = []
    for start, stop in _bands(width, pair_count):
        if stop - start + 1 < 5:
            raise AssertionError("pair band too narrow")
        left_jitter = rng.randrange(2)
        right_jitter = rng.randrange(2)
        left = start + 1 + left_jitter
        right = stop - 1 - right_jitter
        if right - left < 4:
            left, right = start + 1, stop - 1
        intervals.append((left, right))
        occupied_ranges.append(range(left, right + 1))
    candidates = [
        c
        for c in range(width)
        if all(c not in span for span in occupied_ranges)
        and all(c not in endpoint for endpoint in intervals)
    ]
    if len(candidates) < singleton_count:
        raise AssertionError("not enough singleton columns outside relay intervals")
    rng.shuffle(candidates)
    return intervals, sorted(candidates[:singleton_count])


def _draw_scene(seed: int, split: str, index: int) -> list[list[int]]:
    h, w, pair_count, singleton_count = _profile(split, index)
    rng = _rng(seed, split, index, "scene")
    intervals, singleton_columns = _columns(w, pair_count, singleton_count, rng)
    colors = list(range(1, 10))
    rng.shuffle(colors)
    pair_colors = colors[:pair_count]
    singleton_colors = colors[pair_count : pair_count + singleton_count]
    grid = [[0] * w for _ in range(h)]
    endpoint_columns: list[tuple[int, int]] = []
    for color, (left, right) in zip(pair_colors, intervals):
        grid[rng.randint(2, h - 2)][left] = color
        grid[rng.randint(2, h - 2)][right] = color
        endpoint_columns.append((left, right))
    for color, column in zip(singleton_colors, singleton_columns):
        grid[rng.randint(1, h - 2)][column] = color

    info = analyze(grid)
    if len(info["pair_intervals"]) != pair_count:
        raise AssertionError("authored equal-color pairs were not recovered")
    if len(info["bridge_cells"]) < 2 * pair_count:
        raise AssertionError("relay is not substantive")
    return grid


def analyze(grid: Any) -> dict[str, Any]:
    original = _grid(grid)
    stage_a = project_up(original)
    relayed = bridge_equal_endpoints(stage_a)
    intervals = _pair_intervals(stage_a)
    return {
        "shape": [len(original), len(original[0])],
        "seeds": [
            [r, c, value]
            for r, row in enumerate(original)
            for c, value in enumerate(row)
            if value != 0
        ],
        "top_endpoints": [[c, value] for c, value in enumerate(stage_a[0]) if value != 0],
        "pair_intervals": [[color, left, right] for color, left, right in intervals],
        "bridge_cells": [
            [0, c]
            for c in range(len(stage_a[0]))
            if stage_a[0][c] != relayed[0][c]
        ],
    }


def _pair(grid: list[list[int]], settings: dict[str, str]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": transform(grid, settings)}


def fit_settings(demos: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    pairs = list(demos)
    survivors: list[dict[str, str]] = []
    for candidate in SETTINGS:
        try:
            if pairs and all(
                type(pair) is dict and pair.get("output") == transform(pair.get("input"), candidate)
                for pair in pairs
            ):
                survivors.append(dict(candidate))
        except (TypeError, ValueError):
            continue
    return survivors


def _only_intervals(stage_a: list[list[int]], intervals: list[tuple[int, int, int]]) -> list[list[int]]:
    out = deepcopy(stage_a)
    for color, left, right in intervals:
        for c in range(left, right + 1):
            out[0][c] = color
    return out


def simple_rival_outputs(pairs: Iterable[dict[str, Any]]) -> dict[str, list[list[list[int]]]]:
    material = list(pairs)
    results: dict[str, list[list[list[int]]]] = {
        "bridge_first_pair_only": [],
        "bridge_widest_pair_only": [],
        "bridge_adjacent_endpoints": [],
        "bridge_at_seed_rows": [],
        "bridge_everything": [],
    }
    for pair in material:
        original = _grid(pair["input"])
        stage_a = project_up(original)
        intervals = _pair_intervals(stage_a)
        results["bridge_first_pair_only"].append(_only_intervals(stage_a, intervals[:1]))
        widest = [max(intervals, key=lambda item: (item[2] - item[1], -item[0]))]
        results["bridge_widest_pair_only"].append(_only_intervals(stage_a, widest))

        adjacent = deepcopy(stage_a)
        endpoints = [c for c, value in enumerate(stage_a[0]) if value]
        for left, right in zip(endpoints, endpoints[1:]):
            color = stage_a[0][left]
            for c in range(left, right + 1):
                adjacent[0][c] = color
        results["bridge_adjacent_endpoints"].append(adjacent)

        seed_rows = deepcopy(stage_a)
        for color in range(1, 10):
            points = [(r, c) for r, row in enumerate(original) for c, value in enumerate(row) if value == color]
            if len(points) == 2:
                row = min(points[0][0], points[1][0])
                left, right = sorted((points[0][1], points[1][1]))
                for c in range(left, right + 1):
                    seed_rows[row][c] = color
        results["bridge_at_seed_rows"].append(seed_rows)

        everything = deepcopy(stage_a)
        nonzero = [c for c, value in enumerate(stage_a[0]) if value]
        color = stage_a[0][nonzero[0]]
        for c in range(nonzero[0], nonzero[-1] + 1):
            everything[0][c] = color
        results["bridge_everything"].append(everything)
    return results


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    chosen = _setting(settings)
    train = [_pair(_draw_scene(seed, "train", index), chosen) for index in range(demos)]
    test = [_pair(_draw_scene(seed, "test", index), chosen) for index in range(queries)]
    if fit_settings(train) != [chosen]:
        raise RuntimeError("demonstrations do not uniquely identify finish_rule")
    serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("episode contains duplicate inputs")
    return {"train": train, "test": test, "program_solution": program(chosen)}
