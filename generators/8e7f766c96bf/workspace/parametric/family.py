"""Matched-input fixed/anchor-dimension frame family for 8e7f766c96bf."""
from __future__ import annotations

from collections import Counter
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
TASK_ID = "8e7f766c96bf"
MODES = ("fixed_4x4", "anchor_dimensions")
SETTINGS = tuple({"frame_rule": mode} for mode in MODES)
RIVALS = (
    "all_frames",
    "anchor_only",
    "second_dimensions",
    "smallest_dimensions",
    "largest_dimensions",
    "height_only",
    "width_only",
    "most_frequent_dimensions",
    "fixed_3x3",
    "fixed_5x5",
)
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
ANCHOR_PROGRAM = (HOME / "anchor_dimensions.rkt").read_text(encoding="utf-8")

# Six demonstrations followed by four independently revealable queries.
# The first two demonstrations alone refute the finite rival inventory.
_PROFILES = (
    (22, 28, ((3, 5), (4, 4), (3, 5), (3, 3), (3, 3), (3, 3), (4, 5), (5, 5), (6, 6))),
    (24, 28, ((5, 3), (4, 5), (5, 3), (4, 4), (5, 5), (5, 5), (5, 5), (3, 3), (6, 6))),
    (20, 26, ((4, 6), (3, 3), (4, 6), (4, 4), (4, 5), (5, 6), (3, 3), (6, 6))),
    (26, 22, ((6, 4), (3, 5), (6, 4), (4, 4), (6, 5), (5, 4), (3, 3), (6, 6))),
    (21, 29, ((3, 6), (4, 5), (3, 6), (4, 4), (3, 4), (5, 6), (3, 3), (6, 6), (5, 5))),
    (29, 22, ((6, 3), (5, 4), (6, 3), (4, 4), (6, 5), (4, 3), (3, 3), (6, 6), (5, 5))),
    (24, 30, ((5, 5), (4, 6), (5, 5), (4, 4), (5, 3), (3, 5), (3, 3), (6, 6), (4, 6))),
    (30, 24, ((3, 4), (5, 5), (3, 4), (4, 4), (3, 6), (6, 4), (3, 3), (6, 6), (5, 5))),
    (27, 30, ((5, 6), (3, 4), (5, 6), (4, 4), (5, 3), (3, 6), (3, 3), (6, 6), (4, 5), (5, 5))),
    (30, 30, ((6, 5), (4, 6), (6, 5), (4, 4), (6, 3), (3, 5), (3, 3), (6, 6), (5, 5), (4, 5), (5, 4), (3, 6))),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def mode_from_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"frame_rule"}:
        raise ValueError("settings must contain only frame_rule")
    mode = settings["frame_rule"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("frame_rule must be fixed_4x4 or anchor_dimensions")
    return mode


def program(settings: Any) -> str:
    return CANONICAL_PROGRAM if mode_from_settings(settings) == "fixed_4x4" else ANCHOR_PROGRAM


def _rng(seed: int, index: int) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{index}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    components: list[set[tuple[int, int]]] = []
    while pending:
        start = min(pending)
        pending.remove(start)
        cells = {start}
        todo = [start]
        while todo:
            row, col = todo.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in pending:
                    pending.remove(point)
                    cells.add(point)
                    todo.append(point)
        components.append(cells)
    return components


def _frame_records(grid: list[list[int]]) -> list[dict[str, Any]]:
    normalized = normalize_grid(grid)
    if any(value not in (0, 1) for row in normalized for value in row):
        raise ValueError("family inputs may contain only 0 and 1")
    records = []
    for cells in _components(normalized):
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(col for _, col in cells)
        right = max(col for _, col in cells)
        height, width = bottom - top + 1, right - left + 1
        if height < 3 or width < 3:
            raise ValueError("every blue component must be a hollow frame")
        border = {
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
            if row in (top, bottom) or col in (left, right)
        }
        if cells != border:
            raise ValueError("every blue component must be a complete hollow frame")
        records.append({
            "top": top,
            "left": left,
            "bottom": bottom,
            "right": right,
            "height": height,
            "width": width,
            "dimensions": [height, width],
            "interior": [
                [row, col]
                for row in range(top + 1, bottom)
                for col in range(left + 1, right)
            ],
        })
    records.sort(key=lambda item: (item["top"], item["left"]))
    if len(records) < 2:
        raise ValueError("family inputs require at least two frames")
    return records


def _dimension_key(frame: dict[str, Any]) -> tuple[int, int]:
    return frame["height"], frame["width"]


def _selection(frames: list[dict[str, Any]], policy: str) -> tuple[list[int], Callable[[dict[str, Any], int], bool]]:
    anchor_h, anchor_w = _dimension_key(frames[0])
    if policy == "fixed_4x4":
        selected = (4, 4)
        predicate = lambda frame, index: _dimension_key(frame) == selected
    elif policy == "anchor_dimensions":
        selected = (anchor_h, anchor_w)
        predicate = lambda frame, index: _dimension_key(frame) == selected
    elif policy == "all_frames":
        selected = (-1, -1)
        predicate = lambda frame, index: True
    elif policy == "anchor_only":
        selected = (anchor_h, anchor_w)
        predicate = lambda frame, index: index == 0
    elif policy == "second_dimensions":
        selected = _dimension_key(frames[1])
        predicate = lambda frame, index: _dimension_key(frame) == selected
    elif policy == "smallest_dimensions":
        selected = min((_dimension_key(frame) for frame in frames), key=lambda dim: (dim[0] * dim[1], dim))
        predicate = lambda frame, index: _dimension_key(frame) == selected
    elif policy == "largest_dimensions":
        selected = max((_dimension_key(frame) for frame in frames), key=lambda dim: (dim[0] * dim[1], dim))
        predicate = lambda frame, index: _dimension_key(frame) == selected
    elif policy == "height_only":
        selected = (anchor_h, -1)
        predicate = lambda frame, index: frame["height"] == anchor_h
    elif policy == "width_only":
        selected = (-1, anchor_w)
        predicate = lambda frame, index: frame["width"] == anchor_w
    elif policy == "most_frequent_dimensions":
        counts = Counter(_dimension_key(frame) for frame in frames)
        selected = min(counts, key=lambda dim: (-counts[dim], dim))
        predicate = lambda frame, index: _dimension_key(frame) == selected
    elif policy == "fixed_3x3":
        selected = (3, 3)
        predicate = lambda frame, index: _dimension_key(frame) == selected
    elif policy == "fixed_5x5":
        selected = (5, 5)
        predicate = lambda frame, index: _dimension_key(frame) == selected
    else:
        raise ValueError(f"unknown frame policy: {policy}")
    return list(selected), predicate


def _solve_policy(grid: list[list[int]], policy: str) -> tuple[list[list[int]], dict[str, Any]]:
    frames = _frame_records(grid)
    selected_dimensions, predicate = _selection(frames, policy)
    selected_indices = [index for index, frame in enumerate(frames) if predicate(frame, index)]
    output = deepcopy(normalize_grid(grid))
    for index in selected_indices:
        for row, col in frames[index]["interior"]:
            output[row][col] = 2
    intermediate = {
        "ordered_frames": [
            {
                "index": index,
                "top_left": [frame["top"], frame["left"]],
                "dimensions": list(_dimension_key(frame)),
                "interior_cells": len(frame["interior"]),
            }
            for index, frame in enumerate(frames)
        ],
        "selected_dimensions": selected_dimensions,
        "selected_indices": selected_indices,
        "matched_frame_count": len(selected_indices),
    }
    return output, intermediate


def solve(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError("mode must be fixed_4x4 or anchor_dimensions")
    return _solve_policy(grid, mode)[0]


def dependency_intermediate(grid: list[list[int]], mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError("mode must be fixed_4x4 or anchor_dimensions")
    return _solve_policy(grid, mode)[1]


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {name: _solve_policy(grid, name)[0] for name in RIVALS}


def _draw_frame(grid: list[list[int]], top: int, left: int, height: int, width: int) -> None:
    for row in range(top, top + height):
        for col in range(left, left + width):
            if row in (top, top + height - 1) or col in (left, left + width - 1):
                if grid[row][col] != 0:
                    raise AssertionError("frame overlap")
                grid[row][col] = 1


def _pack_positions(height: int, width: int, dimensions: tuple[tuple[int, int], ...], rng: random.Random, *, boundary_last: bool) -> list[tuple[int, int, int, int]]:
    regular = dimensions[:-1] if boundary_last else dimensions
    positions: list[tuple[int, int, int, int]] = []
    row = 0
    col = 0
    shelf_height = 0
    for frame_height, frame_width in regular:
        if col and col + frame_width > width:
            row += shelf_height + rng.randint(1, 2)
            col = 0
            shelf_height = 0
        if row + frame_height > height:
            raise AssertionError("profile does not fit its canvas")
        positions.append((row, col, frame_height, frame_width))
        shelf_height = max(shelf_height, frame_height)
        col += frame_width + rng.randint(1, 2)
    if boundary_last:
        frame_height, frame_width = dimensions[-1]
        candidate = (height - frame_height, width - frame_width, frame_height, frame_width)
        top, left, h, w = candidate
        for other_top, other_left, other_h, other_w in positions:
            separated = (
                top + h <= other_top
                or other_top + other_h <= top
                or left + w <= other_left
                or other_left + other_w <= left
            )
            if not separated:
                raise AssertionError("boundary frame overlaps regular packing")
        positions.append(candidate)
    return positions


def _scene(seed: int, index: int) -> list[list[int]]:
    height, width, dimensions = _PROFILES[index]
    rng = _rng(seed, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    positions = _pack_positions(height, width, dimensions, rng, boundary_last=index == 9)
    for top, left, frame_height, frame_width in positions:
        _draw_frame(grid, top, left, frame_height, frame_width)
    frames = _frame_records(grid)
    observed_dimensions = [tuple(frame["dimensions"]) for frame in frames]
    if observed_dimensions != list(dimensions):
        raise AssertionError((index, observed_dimensions, dimensions))
    anchor_dimensions = dimensions[0]
    if sum(dim == anchor_dimensions for dim in dimensions) < 2 or (4, 4) not in dimensions:
        raise AssertionError("each scene must contain repeated anchor dimensions and a 4x4 frame")
    return grid


@lru_cache(maxsize=128)
def _episode_inputs_cached(seed: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    return tuple(tuple(tuple(row) for row in _scene(seed, index)) for index in range(len(_PROFILES)))


def episode_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    grids = [[list(row) for row in frozen] for frozen in _episode_inputs_cached(seed)]
    return {"train": grids[:6], "test": grids[6:]}


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    mode = mode_from_settings(settings)
    inputs = episode_inputs(seed)
    train = [{"input": deepcopy(grid), "output": solve(grid, mode)} for grid in inputs["train"][:demos]]
    test = [{"input": deepcopy(grid), "output": solve(grid, mode)} for grid in inputs["test"][:queries]]
    return {"train": train, "test": test, "program_solution": program(settings)}


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    visible = {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
    return json.loads(public_challenge_bytes(visible))


def execute_racket(source: str, grid: list[list[int]], bridge: Any) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))
