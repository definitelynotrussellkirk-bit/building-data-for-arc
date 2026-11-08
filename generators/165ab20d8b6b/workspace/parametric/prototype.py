"""Native neighborhood family for 165ab20d8b6b.

The canonical setting erases each nonzero four-connected same-color component
and paints its zero-valued cardinal shell.  The nearby setting keeps component
extraction and color ownership fixed, but derives the shell from all eight
neighbor directions.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable, Sequence

TASK_ID = "165ab20d8b6b"
NEIGHBORHOODS = ("cardinal", "moore")
DEFAULT_NEIGHBORHOOD = "cardinal"
SETTINGS = tuple({"neighborhood": value} for value in NEIGHBORHOODS)
CANONICAL_PATH = Path(__file__).resolve().with_name("canonical.rkt")
CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))
DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
MOORE = CARDINAL + DIAGONAL
_CARDINAL_SITE = "cardinal-deltas"
_MOORE_EXPR = "(list (list -1 -1) (list -1 0) (list -1 1) (list 0 -1) (list 0 1) (list 1 -1) (list 1 0) (list 1 1))"


def _ring(side: int) -> frozenset[tuple[int, int]]:
    return frozenset(
        (r, c)
        for r in range(side)
        for c in range(side)
        if r in (0, side - 1) or c in (0, side - 1)
    )


def _rect(height: int, width: int) -> frozenset[tuple[int, int]]:
    return frozenset((r, c) for r in range(height) for c in range(width))


def _c_shape(height: int, width: int) -> frozenset[tuple[int, int]]:
    return frozenset(
        {(r, 0) for r in range(height)}
        | {(0, c) for c in range(width)}
        | {(height - 1, c) for c in range(width)}
    )


def _l_shape(height: int, width: int) -> frozenset[tuple[int, int]]:
    return frozenset({(r, 0) for r in range(height)} | {(height - 1, c) for c in range(width)})


def _t_shape(bar: int, stem: int) -> frozenset[tuple[int, int]]:
    middle = bar // 2
    return frozenset({(0, c) for c in range(bar)} | {(r, middle) for r in range(1, stem + 1)})


def _plus(radius: int) -> frozenset[tuple[int, int]]:
    center = radius
    return frozenset(
        {(center, c) for c in range(2 * radius + 1)}
        | {(r, center) for r in range(2 * radius + 1)}
    )


def _snake(size: int, width: int) -> frozenset[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    row = 0
    while len(cells) < size:
        columns = range(width) if row % 2 == 0 else range(width - 1, -1, -1)
        for column in columns:
            cells.append((row, column))
            if len(cells) == size:
                break
        row += 1
    return frozenset(cells)


# Every scene includes a ring so the internal-shell branch is visibly taught.
DEMO_SPECS: tuple[tuple[tuple[int, int], tuple[frozenset[tuple[int, int]], ...]], ...] = (
    ((12, 15), (_ring(3), _t_shape(5, 3), _l_shape(5, 4))),
    ((14, 16), (_ring(4), _c_shape(5, 5), _snake(9, 4), _rect(2, 3))),
    ((16, 18), (_ring(3), _plus(2), _snake(12, 5), _l_shape(6, 4))),
    ((18, 20), (_ring(4), _c_shape(6, 5), _t_shape(7, 5), _rect(3, 4))),
    ((20, 22), (_ring(5), _snake(16, 5), _plus(3), _l_shape(7, 5), _rect(3, 3))),
    ((22, 24), (_ring(4), _snake(20, 6), _c_shape(7, 6), _rect(3, 5), _plus(3))),
)
QUERY_SPECS: tuple[tuple[tuple[int, int], tuple[frozenset[tuple[int, int]], ...]], ...] = (
    ((12, 15), (_ring(3), _c_shape(5, 4), _snake(8, 4))),
    ((18, 20), (_ring(4), _plus(3), _snake(15, 5), _l_shape(6, 5))),
    ((24, 27), (_ring(5), _c_shape(7, 6), _snake(20, 6), _t_shape(7, 6), _rect(4, 4))),
    ((30, 30), (_ring(6), _rect(5, 6), _c_shape(7, 6), _snake(25, 6), _plus(4), _l_shape(8, 7))),
)


def _plain_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a plain Python int in [{low}, {high}]")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"neighborhood"}:
        raise ValueError("settings must contain exactly neighborhood")
    neighborhood = value["neighborhood"]
    if type(neighborhood) is not str or neighborhood not in NEIGHBORHOODS:
        raise ValueError(f"neighborhood must be one of {NEIGHBORHOODS}")
    return {"neighborhood": neighborhood}


def program(settings: Any) -> str:
    neighborhood = _settings(settings)["neighborhood"]
    source = CANONICAL_PATH.read_text(encoding="utf-8")
    if neighborhood == DEFAULT_NEIGHBORHOOD:
        return source
    if source.count(_CARDINAL_SITE) != 1:
        raise ValueError("canonical neighborhood site changed")
    changed = source.replace(_CARDINAL_SITE, _MOORE_EXPR, 1)
    if changed == source:
        raise ValueError("alternate neighborhood did not change the program")
    return changed


def _normalize_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or len(grid) > 30
        or len(grid[0]) > 30
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row)
    ):
        raise ValueError("grid must be a rectangular 1..30 ARC grid")
    return deepcopy(grid)


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    objects: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, column = stack.pop()
            for dr, dc in CARDINAL:
                point = (row + dr, column + dc)
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        objects.append({"color": color, "cells": frozenset(cells), "first": min(cells)})
    objects.sort(key=lambda obj: obj["first"])
    return objects


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    return (
        min(r for r, _ in points),
        min(c for _, c in points),
        max(r for r, _ in points),
        max(c for _, c in points),
    )


def _shell_cells(
    grid: list[list[int]], cells: Iterable[tuple[int, int]], deltas: Sequence[tuple[int, int]]
) -> frozenset[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    return frozenset(
        (row + dr, column + dc)
        for row, column in cells
        for dr, dc in deltas
        if 0 <= row + dr < height
        and 0 <= column + dc < width
        and grid[row + dr][column + dc] == 0
    )


def _exterior_zeros(grid: list[list[int]]) -> frozenset[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    starts = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 0 and (r in (0, height - 1) or c in (0, width - 1))
    }
    seen = set(starts)
    queue = deque(starts)
    while queue:
        row, column = queue.popleft()
        for dr, dc in CARDINAL:
            point = (row + dr, column + dc)
            if (
                0 <= point[0] < height
                and 0 <= point[1] < width
                and grid[point[0]][point[1]] == 0
                and point not in seen
            ):
                seen.add(point)
                queue.append(point)
    return frozenset(seen)


def _apply(
    grid: Any,
    deltas: Sequence[tuple[int, int]],
    *,
    keep_source: bool = False,
    exterior_only: bool = False,
    bbox_source: bool = False,
    fixed_color: int | None = None,
    merge_colors: bool = False,
) -> list[list[int]]:
    normalized = _normalize_grid(grid)
    height, width = len(normalized), len(normalized[0])
    output = deepcopy(normalized) if keep_source else [[0 for _ in range(width)] for _ in range(height)]
    objects = _objects(normalized)
    if merge_colors and objects:
        objects = [{"color": objects[0]["color"], "cells": frozenset().union(*(o["cells"] for o in objects)), "first": objects[0]["first"]}]
    exterior = _exterior_zeros(normalized) if exterior_only else None
    for obj in objects:
        cells = obj["cells"]
        if bbox_source:
            r0, c0, r1, c1 = _bbox(cells)
            cells = frozenset((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))
        shell = _shell_cells(normalized, cells, deltas)
        if exterior is not None:
            shell = shell & exterior
        color = fixed_color if fixed_color is not None else obj["color"]
        for row, column in shell:
            output[row][column] = color
    return output


def solve(grid: Any, settings: Any) -> list[list[int]]:
    neighborhood = _settings(settings)["neighborhood"]
    return _apply(grid, CARDINAL if neighborhood == "cardinal" else MOORE)


def has_enclosed_shell_cell(grid: Any) -> bool:
    normalized = _normalize_grid(grid)
    exterior = _exterior_zeros(normalized)
    for obj in _objects(normalized):
        if any(cell not in exterior for cell in _shell_cells(normalized, obj["cells"], CARDINAL)):
            return True
    return False


def _rng(seed: int, role: str, index: int, attempt: int = 0) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|neighborhood-v1|{seed}|{role}|{index}|{attempt}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    points = tuple(cells)
    row0 = min(r for r, _ in points)
    column0 = min(c for _, c in points)
    return frozenset((r - row0, c - column0) for r, c in points)


def _transform_shape(cells: frozenset[tuple[int, int]], transform: int) -> frozenset[tuple[int, int]]:
    points = list(cells)
    if transform >= 4:
        points = [(r, -c) for r, c in points]
    for _ in range(transform % 4):
        points = [(c, -r) for r, c in points]
    return _normalize_shape(points)


def _dimensions(shape: frozenset[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _footprint(cells: frozenset[tuple[int, int]], height: int, width: int) -> frozenset[tuple[int, int]]:
    return frozenset(
        (r + dr, c + dc)
        for r, c in cells
        for dr, dc in ((0, 0),) + MOORE
        if 0 <= r + dr < height and 0 <= c + dc < width
    )


def _origins(
    shape: frozenset[tuple[int, int]],
    height: int,
    width: int,
    boundary: str | None,
    rng: random.Random,
) -> list[tuple[int, int]]:
    shape_height, shape_width = _dimensions(shape)
    if shape_height > height or shape_width > width:
        return []
    values = [
        (row, column)
        for row in range(height - shape_height + 1)
        for column in range(width - shape_width + 1)
        if boundary is None
        or (boundary == "top" and row == 0)
        or (boundary == "bottom" and row + shape_height == height)
        or (boundary == "left" and column == 0)
        or (boundary == "right" and column + shape_width == width)
    ]
    rng.shuffle(values)
    return values


def _place_shapes(
    shapes: list[frozenset[tuple[int, int]]],
    height: int,
    width: int,
    rng: random.Random,
    stress_boundaries: bool,
) -> list[frozenset[tuple[int, int]]]:
    boundaries: dict[int, str] = {}
    if stress_boundaries:
        boundaries = {0: "top", 1: "right", 2: "bottom", 3: "left"}
    candidates = [
        _origins(shape, height, width, boundaries.get(index), rng)
        for index, shape in enumerate(shapes)
    ]
    if any(not rows for rows in candidates):
        raise RuntimeError("no legal placement candidates")
    order = sorted(range(len(shapes)), key=lambda index: len(candidates[index]))
    placed: list[frozenset[tuple[int, int]] | None] = [None] * len(shapes)

    def search(position: int, used_footprint: frozenset[tuple[int, int]]) -> bool:
        if position == len(order):
            return True
        index = order[position]
        shape = shapes[index]
        for row0, column0 in candidates[index]:
            cells = frozenset((row0 + r, column0 + c) for r, c in shape)
            footprint = _footprint(cells, height, width)
            if footprint & used_footprint:
                continue
            placed[index] = cells
            if search(position + 1, used_footprint | footprint):
                return True
            placed[index] = None
        return False

    if not search(0, frozenset()):
        raise RuntimeError("could not place shapes with disjoint Moore shells")
    return [cells for cells in placed if cells is not None]


def _scene(seed: int, role: str, index: int, attempt: int = 0) -> list[list[int]]:
    specs = DEMO_SPECS if role == "demo" else QUERY_SPECS
    (height, width), bases = specs[index]
    rng = _rng(seed, role, index, attempt)
    shapes = [_transform_shape(base, rng.randrange(8)) for base in bases]
    cells_by_object = _place_shapes(
        shapes,
        height,
        width,
        rng,
        stress_boundaries=(role == "query" and index == 3),
    )
    colors = rng.sample(range(1, 10), len(cells_by_object))
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in zip(colors, cells_by_object, strict=True):
        for row, column in cells:
            grid[row][column] = color
    if len(_objects(grid)) != len(cells_by_object):
        raise RuntimeError("constructed object count changed")
    if not has_enclosed_shell_cell(grid):
        raise RuntimeError("scene lost its enclosed-shell witness")
    if solve(grid, SETTINGS[0]) == solve(grid, SETTINGS[1]):
        raise RuntimeError("neighborhood settings did not separate")
    return grid


def _rule(
    deltas: Sequence[tuple[int, int]],
    **kwargs: Any,
) -> Callable[[list[list[int]]], list[list[int]]]:
    return lambda grid: _apply(grid, deltas, **kwargs)


def candidate_rules() -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    return {
        "cardinal": _rule(CARDINAL),
        "moore": _rule(MOORE),
        "diagonal_only": _rule(DIAGONAL),
        "cardinal_keep_source": _rule(CARDINAL, keep_source=True),
        "moore_keep_source": _rule(MOORE, keep_source=True),
        "cardinal_exterior_only": _rule(CARDINAL, exterior_only=True),
        "moore_exterior_only": _rule(MOORE, exterior_only=True),
        "cardinal_bbox": _rule(CARDINAL, bbox_source=True),
        "moore_bbox": _rule(MOORE, bbox_source=True),
        "cardinal_fixed_color": _rule(CARDINAL, fixed_color=8),
        "moore_fixed_color": _rule(MOORE, fixed_color=8),
        "color_blind_cardinal": _rule(CARDINAL, merge_colors=True),
    }


def _teaching_pair_identifies_both(grids: tuple[list[list[int]], list[list[int]]]) -> bool:
    rules = candidate_rules()
    for setting in SETTINGS:
        intended = setting["neighborhood"]
        outputs = [solve(grid, setting) for grid in grids]
        for name, rule in rules.items():
            if name == intended:
                continue
            try:
                if all(rule(grid) == output for grid, output in zip(grids, outputs, strict=True)):
                    return False
            except (ValueError, RuntimeError):
                continue
    return True


@lru_cache(maxsize=None)
def _teaching_inputs(seed: int) -> tuple[list[list[int]], list[list[int]]]:
    for attempt in range(128):
        grids = (_scene(seed, "demo", 0, attempt), _scene(seed, "demo", 1, attempt))
        if _teaching_pair_identifies_both(grids):
            return grids
    raise RuntimeError("could not construct an identifying two-demonstration lesson")


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _plain_int("seed", seed, 0, 2**63 - 1)
    settings = _settings(settings)
    demos = _plain_int("demos", demos, 2, 6)
    queries = _plain_int("queries", queries, 1, 4)
    teaching = _teaching_inputs(seed)
    train_inputs = [deepcopy(grid) for grid in teaching]
    train_inputs.extend(_scene(seed, "demo", index) for index in range(2, demos))
    test_inputs = [_scene(seed, "query", index) for index in range(queries)]
    serialized = {
        json.dumps(grid, sort_keys=True, separators=(",", ":"))
        for grid in train_inputs + test_inputs
    }
    if len(serialized) != demos + queries:
        raise RuntimeError("episode contains duplicate inputs")

    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {"input": deepcopy(grid), "output": solve(grid, settings)}

    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program(settings),
    }


def fit_settings(demonstrations: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        dict(setting)
        for setting in SETTINGS
        if all(solve(pair["input"], setting) == pair["output"] for pair in demonstrations)
    ]


def self_review(episode: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    selected = next((setting for setting in SETTINGS if program(setting) == episode.get("program_solution")), None)
    if selected is None:
        raise ValueError("episode program is not a declared setting")
    survivors: list[str] = []
    harmful: list[str] = []
    mismatches: dict[str, list[int]] = {}
    errors: dict[str, str] = {}
    for name, rule in candidate_rules().items():
        try:
            fits = all(rule(pair["input"]) == pair["output"] for pair in episode["train"])
        except (ValueError, RuntimeError) as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"
            continue
        if fits:
            survivors.append(name)
            try:
                differing = [
                    index
                    for index, pair in enumerate(episode["test"])
                    if rule(pair["input"]) != pair["output"]
                ]
            except (ValueError, RuntimeError) as exc:
                errors[name] = f"query {type(exc).__name__}: {exc}"
                differing = list(range(len(episode["test"])))
            mismatches[name] = differing
            if differing:
                harmful.append(name)
    intended = selected["neighborhood"]
    return {
        "schema": "165ab20d8b6b-native-self-review-v1",
        "selected": dict(selected),
        "tested_candidates": sorted(candidate_rules()),
        "survivors": survivors,
        "intended_survivors": [name for name in survivors if name == intended],
        "harmful_survivors": harmful,
        "query_mismatch_indices": mismatches,
        "candidate_errors": errors,
        "limits": "Finite declared candidates only; not a universal uniqueness proof.",
    }


def public_challenge(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    query_index = _plain_int("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
