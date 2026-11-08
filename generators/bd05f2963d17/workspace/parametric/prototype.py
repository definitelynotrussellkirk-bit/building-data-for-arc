"""Native rank-direction family for bd05f2963d17.

The default setting is the exact canonical Racket program: rank green
4-connected components by cell count (then bounding-box reading order), select
the second-smallest, and scale it 2x at its bounding-box origin.  The alternate
setting selects the second-largest component from the same derived records.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any, Callable, Iterable

TASK_ID = "bd05f2963d17"
RANK_ORDERS = ("second_smallest", "second_largest")
DEFAULT_RANK_ORDER = "second_smallest"
SETTINGS = tuple({"rank_order": value} for value in RANK_ORDERS)
CANONICAL_PATH = Path(__file__).resolve().with_name("canonical.rkt")
_TARGET_SITE = "(target (second comps))"
_ALTERNATE_TARGET = "(target (list-ref comps (- (length comps) 2)))"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

DEMO_SPECS = (
    ((14, 16), (1, 5, 6, 7, 8)),
    ((15, 17), (2, 4, 6, 9, 11)),
    ((16, 18), (3, 5, 7, 10, 12)),
    ((18, 20), (1, 6, 8, 11, 14)),
    ((20, 22), (2, 7, 9, 13, 16)),
    ((22, 24), (3, 8, 10, 15, 18)),
)
QUERY_SPECS = (
    ((14, 16), (2, 5, 7, 9, 12)),
    ((18, 20), (3, 6, 9, 12, 15)),
    ((24, 27), (4, 7, 11, 15, 19)),
    ((30, 30), (3, 7, 11, 15, 19, 23, 27)),
)


def _plain_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a plain Python int in [{low}, {high}]")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"rank_order"}:
        raise ValueError("settings must contain exactly rank_order")
    rank_order = value["rank_order"]
    if type(rank_order) is not str or rank_order not in RANK_ORDERS:
        raise ValueError(f"rank_order must be one of {RANK_ORDERS}")
    return {"rank_order": rank_order}


def program(settings: Any) -> str:
    rank_order = _settings(settings)["rank_order"]
    source = CANONICAL_PATH.read_text(encoding="utf-8")
    if rank_order == DEFAULT_RANK_ORDER:
        return source
    if source.count(_TARGET_SITE) != 1:
        raise ValueError("canonical target-selection site changed")
    changed = source.replace(_TARGET_SITE, _ALTERNATE_TARGET, 1)
    if changed == source:
        raise ValueError("alternate rank order did not change the program")
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
        or any(type(cell) is not int or cell not in (0, 3) for row in grid for cell in row)
    ):
        raise ValueError("grid must be a rectangular 1..30 ARC grid using only 0 and 3")
    return deepcopy(grid)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    return (
        min(row for row, _ in points),
        min(column for _, column in points),
        max(row for row, _ in points),
        max(column for _, column in points),
    )


def _components(grid: list[list[int]]) -> list[frozenset[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 3
    }
    found: list[frozenset[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, column = stack.pop()
            for dr, dc in CARDINAL:
                point = (row + dr, column + dc)
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        found.append(frozenset(cells))
    return found


def _component_records(grid: list[list[int]]) -> list[dict[str, Any]]:
    records = []
    for cells in _components(grid):
        box = _bbox(cells)
        records.append(
            {
                "cells": cells,
                "size": len(cells),
                "bbox": box,
                "bbox_area": (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
                "first": min(cells),
            }
        )
    records.sort(key=lambda record: (record["size"], record["bbox"][0], record["bbox"][1]))
    if len(records) < 3 or len({record["size"] for record in records}) != len(records):
        raise ValueError("rank family requires at least three components with distinct sizes")
    return records


def _render_record(
    grid: list[list[int]],
    record: dict[str, Any],
    *,
    scale: int = 2,
    anchor: str = "bbox",
    fill_bbox: bool = False,
) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    row0, column0, row1, column1 = record["bbox"]
    source_anchor = (row0, column0) if anchor == "bbox" else record["first"]
    output = [[0 for _ in range(width)] for _ in range(height)]
    if fill_bbox:
        points = {
            (row, column)
            for row in range(row0, row1 + 1)
            for column in range(column0, column1 + 1)
        }
    else:
        points = record["cells"]
    for row, column in points:
        relative_row = row - source_anchor[0]
        relative_column = column - source_anchor[1]
        for dr in range(scale):
            for dc in range(scale):
                target = (
                    source_anchor[0] + scale * relative_row + dr,
                    source_anchor[1] + scale * relative_column + dc,
                )
                if not (0 <= target[0] < height and 0 <= target[1] < width):
                    raise ValueError("selected component does not fit after scaling")
                output[target[0]][target[1]] = 8
    return output


def _select_record(
    grid: list[list[int]],
    rank_order: str,
    *,
    ordering: str = "size",
) -> dict[str, Any]:
    records = _component_records(grid)
    if ordering == "bbox_area":
        records = sorted(records, key=lambda record: (record["bbox_area"], record["bbox"][0], record["bbox"][1]))
    elif ordering == "reading":
        records = sorted(records, key=lambda record: (record["bbox"][0], record["bbox"][1], record["size"]))
    elif ordering != "size":
        raise ValueError(f"unknown ordering {ordering}")
    return records[1] if rank_order == "second_smallest" else records[-2]


def solve(grid: Any, settings: Any) -> list[list[int]]:
    normalized = _normalize_grid(grid)
    rank_order = _settings(settings)["rank_order"]
    return _render_record(normalized, _select_record(normalized, rank_order))


def _rng(seed: int, role: str, index: int, attempt: int = 0) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|rank-direction-v1|{seed}|{role}|{index}|{attempt}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    column0 = min(column for _, column in cells)
    return frozenset((row - row0, column - column0) for row, column in cells)


def _transform_shape(
    cells: frozenset[tuple[int, int]], transform: int
) -> frozenset[tuple[int, int]]:
    points = list(cells)
    if transform >= 4:
        points = [(row, -column) for row, column in points]
    for _ in range(transform % 4):
        points = [(column, -row) for row, column in points]
    return _normalize_shape(points)


def _snake_shape(size: int, variant: int) -> frozenset[tuple[int, int]]:
    width = min(6, max(2, int(math.sqrt(size)) + (variant % 2)))
    cells: list[tuple[int, int]] = []
    row = 0
    while len(cells) < size:
        columns = range(width) if row % 2 == 0 else range(width - 1, -1, -1)
        for column in columns:
            cells.append((row, column))
            if len(cells) == size:
                break
        row += 1
    return _transform_shape(frozenset(cells), variant % 8)


def _corner_empty_shape(size: int, variant: int) -> frozenset[tuple[int, int]]:
    if size < 3:
        return _snake_shape(size, variant)
    width = min(6, max(3, math.ceil(math.sqrt(size + 1))))
    height = max(2, math.ceil((size + 1) / width))
    while height * width - 1 < size:
        height += 1
    cells = {(0, 1), (1, 1), (1, 0)}
    local = random.Random(variant * 1_000_003 + size)
    while len(cells) < size:
        frontier = {
            (row + dr, column + dc)
            for row, column in cells
            for dr, dc in CARDINAL
            if 0 <= row + dr < height
            and 0 <= column + dc < width
            and (row + dr, column + dc) != (0, 0)
            and (row + dr, column + dc) not in cells
        }
        if not frontier:
            raise RuntimeError("corner-empty shape growth exhausted")
        options = sorted(frontier)
        cells.add(options[local.randrange(len(options))])
    shape = _normalize_shape(cells)
    if (0, 0) in shape:
        raise RuntimeError("corner-empty target unexpectedly occupies bbox origin")
    if variant % 2:
        shape = _normalize_shape((column, row) for row, column in shape)
        if (0, 0) in shape:
            raise RuntimeError("transposed target unexpectedly occupies bbox origin")
    return shape


def _shape_dimensions(shape: frozenset[tuple[int, int]]) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(column for _, column in shape) + 1


def _origins(
    shape: frozenset[tuple[int, int]],
    height: int,
    width: int,
    *,
    scaled_fit: bool,
    boundary: str | None,
    rng: random.Random,
) -> list[tuple[int, int]]:
    shape_height, shape_width = _shape_dimensions(shape)
    max_row = height - shape_height
    max_column = width - shape_width
    if scaled_fit:
        max_row = min(max_row, height - 2 * shape_height)
        max_column = min(max_column, width - 2 * shape_width)
    if max_row < 0 or max_column < 0:
        return []
    values = [
        (row, column)
        for row in range(max_row + 1)
        for column in range(max_column + 1)
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
    *,
    rng: random.Random,
    stress_boundaries: bool,
) -> list[frozenset[tuple[int, int]]]:
    count = len(shapes)
    selected_indices = {1, count - 2}
    boundary_by_index: dict[int, str] = {}
    if stress_boundaries:
        boundary_by_index = {0: "top", 2: "left", 3: "right", 4: "bottom"}
    candidates = [
        _origins(
            shape,
            height,
            width,
            scaled_fit=index in selected_indices,
            boundary=boundary_by_index.get(index),
            rng=rng,
        )
        for index, shape in enumerate(shapes)
    ]
    if any(not values for values in candidates):
        raise RuntimeError("scene has no legal placement candidates")
    order = sorted(range(count), key=lambda index: len(candidates[index]))
    placed: list[frozenset[tuple[int, int]] | None] = [None] * count

    def search(position: int, forbidden: frozenset[tuple[int, int]]) -> bool:
        if position == len(order):
            return True
        index = order[position]
        shape = shapes[index]
        for row0, column0 in candidates[index]:
            cells = frozenset((row0 + row, column0 + column) for row, column in shape)
            if cells & forbidden:
                continue
            expanded = set(cells)
            expanded.update(
                (row + dr, column + dc)
                for row, column in cells
                for dr, dc in CARDINAL
                if 0 <= row + dr < height and 0 <= column + dc < width
            )
            placed[index] = cells
            if search(position + 1, forbidden | frozenset(expanded)):
                return True
            placed[index] = None
        return False

    if not search(0, frozenset()):
        raise RuntimeError("could not place rank scene without component contact")
    return [cells for cells in placed if cells is not None]


def _scene(seed: int, role: str, index: int, attempt: int = 0) -> list[list[int]]:
    specs = DEMO_SPECS if role == "demo" else QUERY_SPECS
    shape, sizes = specs[index]
    height, width = shape
    rng = _rng(seed, role, index, attempt)
    count = len(sizes)
    selected_indices = {1, count - 2}
    shapes = [
        (_corner_empty_shape(size, rng.randrange(10_000)) if rank in selected_indices else _snake_shape(size, rng.randrange(8)))
        for rank, size in enumerate(sizes)
    ]
    cells_by_component = _place_shapes(
        shapes,
        height,
        width,
        rng=rng,
        stress_boundaries=(role == "query" and index == 3),
    )
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for cells in cells_by_component:
        for row, column in cells:
            grid[row][column] = 3
    records = _component_records(grid)
    if tuple(record["size"] for record in records) != tuple(sizes):
        raise RuntimeError("constructed component sizes changed")
    for setting in SETTINGS:
        solve(grid, setting)
    if solve(grid, SETTINGS[0]) == solve(grid, SETTINGS[1]):
        raise RuntimeError("rank settings did not separate on constructed scene")
    return grid


def _teaching_pair_identifies_both(grids: tuple[list[list[int]], list[list[int]]]) -> bool:
    rules = candidate_rules()
    for setting in SETTINGS:
        intended = setting["rank_order"]
        outputs = [solve(grid, setting) for grid in grids]
        for name, rule in rules.items():
            if name == intended:
                continue
            try:
                if all(rule(grid) == output for grid, output in zip(grids, outputs, strict=True)):
                    return False
            except (ValueError, RuntimeError):
                # A shortcut that is undefined on a lawful demonstration is refuted.
                continue
    return True


@lru_cache(maxsize=None)
def _teaching_inputs(seed: int) -> tuple[list[list[int]], list[list[int]]]:
    for attempt in range(256):
        grids = (
            _scene(seed, "demo", 0, attempt),
            _scene(seed, "demo", 1, attempt),
        )
        if _teaching_pair_identifies_both(grids):
            return grids
    raise RuntimeError("could not construct a two-demonstration identifying lesson")


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
    survivors = []
    for setting in SETTINGS:
        if all(solve(pair["input"], setting) == pair["output"] for pair in demonstrations):
            survivors.append(dict(setting))
    return survivors


def _rank_rule(
    rank_order: str,
    *,
    ordering: str = "size",
    scale: int = 2,
    anchor: str = "bbox",
    fill_bbox: bool = False,
) -> Callable[[list[list[int]]], list[list[int]]]:
    def apply(grid: list[list[int]]) -> list[list[int]]:
        normalized = _normalize_grid(grid)
        record = _select_record(normalized, rank_order, ordering=ordering)
        return _render_record(
            normalized,
            record,
            scale=scale,
            anchor=anchor,
            fill_bbox=fill_bbox,
        )

    return apply


def _extreme_rule(index: int) -> Callable[[list[list[int]]], list[list[int]]]:
    def apply(grid: list[list[int]]) -> list[list[int]]:
        normalized = _normalize_grid(grid)
        records = _component_records(normalized)
        return _render_record(normalized, records[index])

    return apply


def candidate_rules() -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    return {
        "second_smallest": _rank_rule("second_smallest"),
        "second_largest": _rank_rule("second_largest"),
        "smallest": _extreme_rule(0),
        "largest": _extreme_rule(-1),
        "median": lambda grid: _render_record(_normalize_grid(grid), _component_records(_normalize_grid(grid))[len(_component_records(_normalize_grid(grid))) // 2]),
        "bbox_area_second_smallest": _rank_rule("second_smallest", ordering="bbox_area"),
        "bbox_area_second_largest": _rank_rule("second_largest", ordering="bbox_area"),
        "reading_order_second": _rank_rule("second_smallest", ordering="reading"),
        "second_smallest_scale1": _rank_rule("second_smallest", scale=1),
        "second_largest_scale1": _rank_rule("second_largest", scale=1),
        "second_smallest_first_anchor": _rank_rule("second_smallest", anchor="first"),
        "second_largest_first_anchor": _rank_rule("second_largest", anchor="first"),
        "second_smallest_fill_bbox": _rank_rule("second_smallest", fill_bbox=True),
        "second_largest_fill_bbox": _rank_rule("second_largest", fill_bbox=True),
    }


def self_review(episode: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    selected = next(
        (setting for setting in SETTINGS if program(setting) == episode.get("program_solution")),
        None,
    )
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
    intended = selected["rank_order"]
    return {
        "schema": "bd05f2963d17-native-self-review-v1",
        "selected": dict(selected),
        "tested_candidates": sorted(candidate_rules()),
        "survivors": survivors,
        "intended_survivors": [name for name in survivors if name == intended],
        "harmful_survivors": harmful,
        "query_mismatch_indices": mismatches,
        "candidate_errors": errors,
        "limits": "Finite declared candidates only; invalid rival executions count as refutations, not a uniqueness proof.",
    }


def public_challenge(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    query_index = _plain_int("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
