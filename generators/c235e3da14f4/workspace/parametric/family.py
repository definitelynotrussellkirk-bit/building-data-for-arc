"""Matched-input smallest/largest object-crop family for c235e3da14f4.

The canonical setting selects the first smallest same-color 4-connected object
while excluding color 2.  The alternate selects the first largest object.  Both
then crop the *original* grid to the selected object's bounding box, so object
selection is a real input-dependent intermediate consumed by the crop step.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import normalize_grid, public_challenge_bytes


HOME = Path(__file__).resolve().parent
TASK_ID = "c235e3da14f4"
MODES = ("smallest", "largest")
SETTINGS = tuple({"size_rule": mode} for mode in MODES)
RIVALS = (
    "first_scan",
    "last_scan",
    "second_smallest",
    "second_largest",
    "smallest_bbox",
    "largest_bbox",
    "smallest_nonzero",
    "largest_nonzero",
    "zero_object",
)
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
LARGEST_PROGRAM = (HOME / "largest.rkt").read_text(encoding="utf-8")

# Profiles are six demonstrations followed by four independently revealable
# queries.  Each scene has five objects with strictly increasing cell counts.
# The smallest cell-count object has a larger bounding box than the next object;
# the largest-bbox object has fewer cells than the largest object.  Thus bbox
# area is not a substitute for the selected intermediate.
_PROFILES = (
    (18, 22, (("elbow", 4, 4), ("solid", 3, 3), ("frame", 4, 4), ("frame", 6, 7), ("solid", 5, 5))),
    (20, 24, (("elbow", 4, 5), ("solid", 3, 3), ("frame", 4, 5), ("frame", 7, 7), ("solid", 5, 5))),
    (22, 24, (("elbow", 5, 5), ("solid", 2, 5), ("frame", 4, 5), ("frame", 7, 8), ("solid", 5, 6))),
    (24, 26, (("elbow", 5, 6), ("solid", 3, 4), ("frame", 5, 5), ("frame", 8, 8), ("solid", 6, 5))),
    (26, 28, (("elbow", 6, 6), ("solid", 3, 4), ("frame", 5, 6), ("frame", 8, 9), ("solid", 6, 6))),
    (28, 30, (("elbow", 6, 7), ("solid", 3, 5), ("frame", 6, 6), ("frame", 9, 9), ("solid", 6, 6))),
    (20, 25, (("elbow", 4, 6), ("solid", 2, 5), ("frame", 5, 5), ("frame", 7, 8), ("solid", 5, 6))),
    (24, 30, (("elbow", 5, 7), ("solid", 3, 4), ("frame", 5, 6), ("frame", 8, 9), ("solid", 6, 6))),
    (29, 30, (("elbow", 7, 7), ("solid", 3, 5), ("frame", 7, 7), ("frame", 10, 10), ("solid", 7, 6))),
    (30, 30, (("elbow", 8, 8), ("solid", 4, 4), ("frame", 8, 8), ("frame", 12, 12), ("solid", 7, 7))),
)
_ORDER_PATTERNS = (
    (1, 0, 4, 2, 3),
    (4, 2, 0, 3, 1),
    (2, 4, 1, 0, 3),
    (3, 1, 4, 0, 2),
    (1, 3, 0, 4, 2),
    (2, 0, 3, 1, 4),
    (3, 0, 2, 4, 1),
    (1, 4, 2, 0, 3),
    (2, 3, 0, 4, 1),
    (0, 3, 1, 4, 2),
)
_ZERO_RANK = (0, 4, 2, 1, 3, 0, 4, 2, 1, 3)
_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def mode_from_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"size_rule"}:
        raise ValueError("settings must contain exactly size_rule")
    mode = settings["size_rule"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("size_rule must be smallest or largest")
    return mode


def program(settings: Any) -> str:
    return CANONICAL_PROGRAM if mode_from_settings(settings) == "smallest" else LARGEST_PROGRAM


def _shape(kind: str, height: int, width: int) -> set[tuple[int, int]]:
    if kind == "solid":
        return {(row, col) for row in range(height) for col in range(width)}
    if kind == "frame":
        return {
            (row, col)
            for row in range(height)
            for col in range(width)
            if row in (0, height - 1) or col in (0, width - 1)
        }
    if kind == "elbow":
        return {(0, col) for col in range(width)} | {(row, width - 1) for row in range(1, height)}
    raise ValueError(f"unknown shape kind {kind!r}")


def _objects(grid: Any) -> list[dict[str, Any]]:
    normalized = normalize_grid(grid)
    pending = {
        (row, col)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value != 2
    }
    records: list[dict[str, Any]] = []
    while pending:
        start = min(pending)
        color = normalized[start[0]][start[1]]
        pending.remove(start)
        cells = {start}
        todo = [start]
        while todo:
            row, col = todo.pop()
            for dr, dc in _DIRS4:
                point = row + dr, col + dc
                if point in pending and normalized[point[0]][point[1]] == color:
                    pending.remove(point)
                    cells.add(point)
                    todo.append(point)
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(col for _, col in cells)
        right = max(col for _, col in cells)
        records.append({
            "color": color,
            "cells": cells,
            "size": len(cells),
            "bbox": [top, left, bottom, right],
            "bbox_area": (bottom - top + 1) * (right - left + 1),
            "solid": len(cells) == (bottom - top + 1) * (right - left + 1),
        })
    records.sort(key=lambda item: (item["bbox"][0], item["bbox"][1]))
    if len(records) != 5:
        raise ValueError("family inputs must contain exactly five non-2 objects")
    if len({item["size"] for item in records}) != len(records):
        raise ValueError("family object sizes must be distinct")
    return records


def _select(records: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    by_size = sorted(records, key=lambda item: (item["size"], records.index(item)))
    if policy == "smallest":
        return by_size[0]
    if policy == "largest":
        return by_size[-1]
    if policy == "first_scan":
        return records[0]
    if policy == "last_scan":
        return records[-1]
    if policy == "second_smallest":
        return by_size[1]
    if policy == "second_largest":
        return by_size[-2]
    if policy == "smallest_bbox":
        return min(records, key=lambda item: (item["bbox_area"], records.index(item)))
    if policy == "largest_bbox":
        return max(records, key=lambda item: (item["bbox_area"], -records.index(item)))
    if policy == "smallest_nonzero":
        return min((item for item in records if item["color"] != 0), key=lambda item: item["size"])
    if policy == "largest_nonzero":
        return max((item for item in records if item["color"] != 0), key=lambda item: item["size"])
    if policy == "zero_object":
        return next(item for item in records if item["color"] == 0)
    raise ValueError(f"unknown selection policy {policy!r}")


def _solve_policy(grid: Any, policy: str) -> tuple[list[list[int]], dict[str, Any]]:
    normalized = normalize_grid(grid)
    records = _objects(normalized)
    selected = _select(records, policy)
    top, left, bottom, right = selected["bbox"]
    output = [row[left : right + 1] for row in normalized[top : bottom + 1]]
    ordered = [
        {
            "scan_index": index,
            "color": item["color"],
            "size": item["size"],
            "bbox": list(item["bbox"]),
            "bbox_area": item["bbox_area"],
            "solid": item["solid"],
        }
        for index, item in enumerate(records)
    ]
    selected_index = records.index(selected)
    intermediate = {
        "ordered_objects": ordered,
        "selected_scan_index": selected_index,
        "selected_color": selected["color"],
        "selected_size": selected["size"],
        "selected_bbox": list(selected["bbox"]),
        "selection_policy": policy,
    }
    return output, intermediate


def solve(grid: Any, mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError("mode must be smallest or largest")
    return _solve_policy(grid, mode)[0]


def dependency_intermediate(grid: Any, mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError("mode must be smallest or largest")
    return _solve_policy(grid, mode)[1]


def rival_outputs(grid: Any, selected_mode: str) -> dict[str, list[list[int]]]:
    if selected_mode not in MODES:
        raise ValueError("selected_mode must be smallest or largest")
    return {name: _solve_policy(grid, name)[0] for name in RIVALS}


def _rng(seed: int, index: int, salt: str) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}|v1|{seed}|{index}|{salt}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _packed_positions(
    canvas_height: int,
    canvas_width: int,
    specs: tuple[tuple[str, int, int], ...],
    order: tuple[int, ...],
    seed: int,
    index: int,
) -> dict[int, tuple[int, int]]:
    gap = 2
    placements: dict[int, tuple[int, int]] = {}
    row = col = shelf_height = 0
    packed_width = 0
    for rank in order:
        _, height, width = specs[rank]
        if col and col + width > canvas_width:
            row += shelf_height + gap
            col = 0
            shelf_height = 0
        placements[rank] = (row, col)
        col += width + gap
        shelf_height = max(shelf_height, height)
        packed_width = max(packed_width, col - gap)
    packed_height = row + shelf_height
    if packed_height > canvas_height or packed_width > canvas_width:
        raise AssertionError((canvas_height, canvas_width, packed_height, packed_width, specs, order))
    room_row = canvas_height - packed_height
    room_col = canvas_width - packed_width
    if index == len(_PROFILES) - 1:
        offset_row = 0
        offset_col = room_col
    else:
        rng = _rng(seed, index, "offset")
        offset_row = rng.randrange(room_row + 1)
        offset_col = rng.randrange(room_col + 1)
    return {rank: (top + offset_row, left + offset_col) for rank, (top, left) in placements.items()}


def _transform(grid: list[list[int]], code: int) -> list[list[int]]:
    if code == 0:
        return deepcopy(grid)
    if code == 1:
        return [list(reversed(row)) for row in grid]
    if code == 2:
        return list(reversed(deepcopy(grid)))
    if code == 3:
        return [list(reversed(row)) for row in reversed(grid)]
    raise ValueError(code)


def _scene(seed: int, index: int) -> list[list[int]]:
    canvas_height, canvas_width, specs = _PROFILES[index]
    sizes = [len(_shape(kind, height, width)) for kind, height, width in specs]
    if sizes != sorted(sizes) or len(sizes) != len(set(sizes)):
        raise AssertionError((index, sizes))
    if specs[0][1] * specs[0][2] <= specs[1][1] * specs[1][2]:
        raise AssertionError("smallest object must not have the smallest bbox")
    if specs[-2][1] * specs[-2][2] <= specs[-1][1] * specs[-1][2]:
        raise AssertionError("largest-bbox object must differ from largest-cell object")

    colors: list[int | None] = [None] * 5
    zero_rank = _ZERO_RANK[index]
    colors[zero_rank] = 0
    palette = list(_COLORS)
    _rng(seed, index, "colors").shuffle(palette)
    for rank in range(5):
        if colors[rank] is None:
            colors[rank] = palette.pop()

    placements = _packed_positions(
        canvas_height, canvas_width, specs, _ORDER_PATTERNS[index], seed, index
    )
    grid = [[2 for _ in range(canvas_width)] for _ in range(canvas_height)]
    for rank, (kind, height, width) in enumerate(specs):
        top, left = placements[rank]
        for row, col in _shape(kind, height, width):
            if grid[top + row][left + col] != 2:
                raise AssertionError("objects overlap")
            grid[top + row][left + col] = int(colors[rank])

    code = _rng(seed, index, "transform").randrange(4)
    transformed = _transform(grid, code)
    records = _objects(transformed)
    observed_sizes = sorted(item["size"] for item in records)
    if observed_sizes != sizes:
        raise AssertionError((index, observed_sizes, sizes))
    return transformed


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
    train = [
        {"input": deepcopy(grid), "output": solve(grid, mode)}
        for grid in inputs["train"][:demos]
    ]
    test = [
        {"input": deepcopy(grid), "output": solve(grid, mode)}
        for grid in inputs["test"][:queries]
    ]
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
