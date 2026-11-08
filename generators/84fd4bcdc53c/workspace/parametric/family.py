"""Matched-input horizontal-first/vertical-first route family for 84fd4bcdc53c."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import normalize_grid, public_challenge_bytes


HOME = Path(__file__).resolve().parent
TASK_ID = "84fd4bcdc53c"
MODES = ("horizontal_then_vertical", "vertical_then_horizontal")
SETTINGS = tuple({"bend_order": mode} for mode in MODES)
RIVALS = (
    "points_only",
    "first_pair_only",
    "first_hub",
    "last_hub",
    "column_major",
    "both_bends",
    "alternate_bends",
    "overwrite_later",
    "descending_colors",
)
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
VERTICAL_PROGRAM = (HOME / "vertical_then_horizontal.rkt").read_text(encoding="utf-8")

# Six demonstrations and four queries. Each group is one color's row-major
# endpoint sequence before seed-controlled flips. Every color has 3-4 markers
# on distinct rows and columns. The last query is a boundary-spanning 30x30
# multi-color route field.
_PROFILES = (
    (10, 12, (((1, 1), (4, 9), (8, 3)),)),
    (12, 14, (
        ((1, 10), (5, 2), (10, 8)),
        ((2, 1), (7, 12), (11, 5)),
    )),
    (14, 16, (
        ((1, 2), (4, 13), (9, 5), (12, 14)),
        ((2, 14), (6, 3), (11, 10)),
    )),
    (16, 18, (
        ((1, 15), (5, 2), (10, 13), (14, 6)),
        ((2, 1), (7, 16), (12, 4), (15, 11)),
    )),
    (18, 22, (
        ((1, 2), (6, 19), (12, 5), (16, 17)),
        ((2, 20), (8, 3), (15, 11)),
        ((0, 10), (9, 1), (17, 14)),
    )),
    (22, 24, (
        ((1, 1), (7, 21), (14, 4), (20, 18)),
        ((2, 22), (9, 3), (16, 20), (21, 7)),
        ((0, 12), (8, 0), (15, 23), (19, 10)),
    )),
    (12, 15, (
        ((0, 2), (5, 13), (11, 4)),
        ((1, 14), (7, 1), (10, 9)),
    )),
    (18, 20, (
        ((1, 1), (6, 18), (12, 4), (17, 15)),
        ((0, 11), (8, 2), (16, 19)),
        ((2, 19), (10, 0), (15, 8)),
    )),
    (24, 28, (
        ((0, 2), (8, 25), (15, 5), (23, 22)),
        ((2, 27), (10, 1), (18, 24), (22, 8)),
        ((1, 14), (12, 0), (20, 27)),
    )),
    (30, 30, (
        ((0, 1), (7, 27), (15, 4), (28, 24)),
        ((1, 28), (9, 2), (20, 26), (29, 5)),
        ((0, 15), (10, 0), (18, 29), (27, 12)),
        ((3, 0), (12, 23), (21, 7), (29, 28)),
    )),
)
_PALETTE = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def mode_from_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"bend_order"}:
        raise ValueError("settings must contain exactly bend_order")
    mode = settings["bend_order"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("bend_order must be horizontal_then_vertical or vertical_then_horizontal")
    return mode


def program(settings: Any) -> str:
    return CANONICAL_PROGRAM if mode_from_settings(settings) == "horizontal_then_vertical" else VERTICAL_PROGRAM


def _step_range(a: int, b: int) -> list[int]:
    step = 1 if a <= b else -1
    return list(range(a, b + step, step))


def _dedupe(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    seen: set[tuple[int, int]] = set()
    result = []
    for point in points:
        if point not in seen:
            seen.add(point)
            result.append(point)
    return result


def _segment(first: tuple[int, int], second: tuple[int, int], mode: str) -> list[tuple[int, int]]:
    r1, c1 = first
    r2, c2 = second
    if mode == "horizontal_then_vertical":
        horizontal = [(r1, col) for col in _step_range(c1, c2)[1:]]
        vertical = [(row, c2) for row in _step_range(r1, r2)[1:]]
        return [first, *horizontal, *vertical]
    if mode == "vertical_then_horizontal":
        vertical = [(row, c1) for row in _step_range(r1, r2)[1:]]
        horizontal = [(r2, col) for col in _step_range(c1, c2)[1:]]
        return [first, *vertical, *horizontal]
    if mode == "both_bends":
        return _dedupe(
            _segment(first, second, "horizontal_then_vertical")
            + _segment(first, second, "vertical_then_horizontal")
        )
    raise ValueError(f"unknown bend mode {mode!r}")


def _trace(points: list[tuple[int, int]], mode: str) -> list[tuple[int, int]]:
    if not points:
        return []
    out = [points[0]]
    for index, (first, second) in enumerate(zip(points, points[1:])):
        segment_mode = mode
        if mode.startswith("alternate:"):
            selected = mode.split(":", 1)[1]
            other = MODES[1] if selected == MODES[0] else MODES[0]
            segment_mode = selected if index % 2 == 0 else other
        out.extend(_segment(first, second, segment_mode)[1:])
    return _dedupe(out)


def endpoint_groups(grid: Any) -> dict[int, list[tuple[int, int]]]:
    normalized = normalize_grid(grid)
    groups: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(normalized):
        for col, value in enumerate(values):
            if value:
                groups.setdefault(value, []).append((row, col))
    if not groups:
        raise ValueError("family inputs need endpoint colors")
    for color, points in groups.items():
        if not 3 <= len(points) <= 4:
            raise ValueError(f"color {color} needs 3..4 endpoints")
        if len({row for row, _ in points}) != len(points) or len({col for _, col in points}) != len(points):
            raise ValueError(f"color {color} endpoints must use distinct rows and columns")
    return groups


def _traces_for_policy(grid: Any, selected_mode: str, policy: str | None = None) -> dict[int, list[tuple[int, int]]]:
    groups = endpoint_groups(grid)
    traces: dict[int, list[tuple[int, int]]] = {}
    for color, row_major in groups.items():
        points = list(row_major)
        if policy == "column_major":
            points.sort(key=lambda point: (point[1], point[0]))
        if policy == "points_only":
            trace = points
        elif policy == "first_pair_only":
            trace = _trace(points[:2], selected_mode)
        elif policy == "first_hub":
            trace = _dedupe(sum((_segment(points[0], point, selected_mode) for point in points[1:]), []))
        elif policy == "last_hub":
            trace = _dedupe(sum((_segment(point, points[-1], selected_mode) for point in points[:-1]), []))
        elif policy == "both_bends":
            trace = _trace(points, "both_bends")
        elif policy == "alternate_bends":
            trace = _trace(points, f"alternate:{selected_mode}")
        else:
            trace = _trace(points, selected_mode)
        traces[color] = trace
    return traces


def _render(
    grid: Any,
    traces: dict[int, list[tuple[int, int]]],
    *,
    overwrite: bool = False,
    descending: bool = False,
) -> list[list[int]]:
    normalized = normalize_grid(grid)
    output = [[0 for _ in row] for row in normalized]
    colors = sorted(traces, reverse=descending)
    for color in colors:
        for row, col in traces[color]:
            if overwrite or output[row][col] == 0:
                output[row][col] = color
    return output


def _solve_policy(grid: Any, selected_mode: str, policy: str | None = None) -> tuple[list[list[int]], dict[str, Any]]:
    if selected_mode not in MODES:
        raise ValueError("selected_mode must be a declared bend order")
    traces = _traces_for_policy(grid, selected_mode, policy)
    output = _render(
        grid,
        traces,
        overwrite=policy == "overwrite_later",
        descending=policy == "descending_colors",
    )
    intermediate = {
        "bend_order": selected_mode,
        "trace_policy": policy or "chain",
        "traces": {
            str(color): [[row, col] for row, col in points]
            for color, points in sorted(traces.items())
        },
        "trace_lengths": {str(color): len(points) for color, points in sorted(traces.items())},
        "color_render_order": sorted(traces, reverse=policy == "descending_colors"),
        "collision_policy": "overwrite" if policy == "overwrite_later" else "first_color_wins",
    }
    return output, intermediate


def solve(grid: Any, mode: str) -> list[list[int]]:
    return _solve_policy(grid, mode)[0]


def dependency_intermediate(grid: Any, mode: str) -> dict[str, Any]:
    return _solve_policy(grid, mode)[1]


def rival_outputs(grid: Any, selected_mode: str) -> dict[str, list[list[int]]]:
    return {name: _solve_policy(grid, selected_mode, name)[0] for name in RIVALS}


def _rng(seed: int, index: int, salt: str) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}|v1|{seed}|{index}|{salt}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _transform_point(row: int, col: int, height: int, width: int, code: int) -> tuple[int, int]:
    if code == 0:
        return row, col
    if code == 1:
        return row, width - 1 - col
    if code == 2:
        return height - 1 - row, col
    if code == 3:
        return height - 1 - row, width - 1 - col
    raise ValueError(code)


def _scene(seed: int, index: int) -> list[list[int]]:
    height, width, groups = _PROFILES[index]
    colors = list(_PALETTE)
    _rng(seed, index, "colors").shuffle(colors)
    selected_colors = colors[: len(groups)]
    transform = _rng(seed, index, "transform").randrange(4)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    for color, points in zip(selected_colors, groups, strict=True):
        transformed = [_transform_point(row, col, height, width, transform) for row, col in points]
        if len({row for row, _ in transformed}) != len(transformed) or len({col for _, col in transformed}) != len(transformed):
            raise AssertionError("transform broke endpoint uniqueness")
        for point in transformed:
            if point in occupied:
                raise AssertionError("endpoint collision")
            occupied.add(point)
            grid[point[0]][point[1]] = color
    endpoint_groups(grid)
    return grid


@lru_cache(maxsize=128)
def _episode_inputs_cached(seed: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    return tuple(tuple(tuple(row) for row in _scene(seed, index)) for index in range(len(_PROFILES)))


def episode_inputs(seed: Any) -> dict[str, list[list[list[int]]]]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    grids = [[list(row) for row in frozen] for frozen in _episode_inputs_cached(seed)]
    return {"train": grids[:6], "test": grids[6:]}


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    mode = mode_from_settings(settings)
    inputs = episode_inputs(seed)
    train = [{"input": deepcopy(grid), "output": solve(grid, mode)} for grid in inputs["train"][:demos]]
    test = [{"input": deepcopy(grid), "output": solve(grid, mode)} for grid in inputs["test"][:queries]]
    return {"train": train, "test": test, "program_solution": program(settings)}


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    query_index = _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    visible = {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
    return json.loads(public_challenge_bytes(visible))


def execute_racket(source: str, grid: list[list[int]], bridge: Any) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))
