"""Constructive native family for all-object and anchor-indexed left slides."""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "96d4a788da47"
VERSION = "native-anchor-indexed-v1"
POLICIES = ("all_objects_left", "anchor_indexed_payload")
_HERE = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HERE / "canonical.rkt").read_text(encoding="utf-8")
ANCHOR_PROGRAM = (_HERE / "anchor-indexed.rkt").read_text(encoding="utf-8").rstrip("\n")
WRONG_ANCHOR_PROGRAM = (_HERE / "wrong-anchor.rkt").read_text(encoding="utf-8").rstrip("\n")

_DEMO_DIMS = ((12, 14), (13, 15), (14, 16), (15, 17), (16, 18), (17, 19))
_QUERY_DIMS = ((18, 22), (22, 24), (26, 28), (30, 30))
_DEMO_SELECTORS = (1, 2, 3, 1, 2, 3)
_QUERY_SELECTORS = (2, 3, 1, 2)
_PAYLOAD_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_RANKS = ("top", "middle", "bottom")


def validate_settings(settings: Any) -> dict[str, str]:
    if not isinstance(settings, dict):
        raise TypeError("settings must be a dictionary naming slide_policy")
    if set(settings) != {"slide_policy"}:
        raise ValueError("settings must name exactly slide_policy")
    value = settings["slide_policy"]
    if type(value) is not str or value not in POLICIES:
        raise ValueError(f"slide_policy must be one of {POLICIES}")
    return {"slide_policy": value}


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: Any) -> str:
    policy = validate_settings(settings)["slide_policy"]
    return CANONICAL_PROGRAM if policy == "all_objects_left" else ANCHOR_PROGRAM


def _rng(seed: int, split: str, index: int, stream: str) -> random.Random:
    material = f"{TASK_ID}|{VERSION}|{seed}|{split}|{index}|{stream}".encode("utf-8")
    number = int.from_bytes(hashlib.sha256(material).digest()[:16], "big")
    return random.Random(number)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list rectangle")
    width = len(grid[0])
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid cells must be exact integer ARC colors 0..9")
    return len(grid), width


def objects_by_color(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = _validate_grid(grid)
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    objects: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        cells = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen and grid[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        objects.append(
            {
                "color": color,
                "cells": tuple(sorted(cells)),
                "bbox": (
                    min(row for row, _ in cells),
                    min(col for _, col in cells),
                    max(row for row, _ in cells),
                    max(col for _, col in cells),
                ),
            }
        )
    colors = [obj["color"] for obj in objects]
    if len(colors) != len(set(colors)):
        raise ValueError("each nonzero color must form exactly one connected object")
    return objects


def _payloads(grid: list[list[int]]) -> list[dict[str, Any]]:
    payloads = [obj for obj in objects_by_color(grid) if obj["color"] != 8]
    payloads.sort(key=lambda obj: obj["bbox"][0])
    if len(payloads) != 3:
        raise ValueError("input must contain exactly three non-anchor payloads")
    if len({obj["bbox"][0] for obj in payloads}) != 3:
        raise ValueError("payload top rows must be distinct")
    return payloads


def anchor_selector(grid: list[list[int]]) -> dict[str, Any]:
    anchors = [obj for obj in objects_by_color(grid) if obj["color"] == 8]
    if len(anchors) != 1:
        raise ValueError("input must contain exactly one connected color-8 anchor")
    size = len(anchors[0]["cells"])
    if size not in (1, 2, 3):
        raise ValueError("anchor size must be exactly 1, 2, or 3")
    _payloads(grid)
    return {
        "anchor_color": 8,
        "anchor_size": size,
        "payload_index": size - 1,
        "payload_rank": _RANKS[size - 1],
    }


def _paint_shifted(grid: list[list[int]], objects: list[dict[str, Any]]) -> list[list[int]]:
    height, width = _validate_grid(grid)
    out = [[0 for _ in range(width)] for _ in range(height)]
    for obj in objects:
        col0 = obj["bbox"][1]
        for row, col in obj["cells"]:
            target_col = col - col0
            if out[row][target_col] != 0:
                raise ValueError("translated objects overlap")
            out[row][target_col] = obj["color"]
    return out


def apply_policy(grid: list[list[int]], slide_policy: str) -> list[list[int]]:
    validate_settings({"slide_policy": slide_policy})
    objects = objects_by_color(grid)
    if slide_policy == "all_objects_left":
        return _paint_shifted(grid, objects)
    selector = anchor_selector(grid)
    return _paint_shifted(grid, [_payloads(grid)[selector["payload_index"]]])


def apply_wrong_intermediate(grid: list[list[int]]) -> list[list[int]]:
    selector = anchor_selector(grid)
    wrong_index = (selector["payload_index"] + 1) % 3
    return _paint_shifted(grid, [_payloads(grid)[wrong_index]])


def counterfactual_program() -> str:
    return WRONG_ANCHOR_PROGRAM


def _anchor_cells(selector: int, col0: int) -> tuple[tuple[int, int], ...]:
    if selector == 1:
        return ((0, col0),)
    if selector == 2:
        return ((0, col0), (0, col0 + 1))
    return ((0, col0), (1, col0), (1, col0 + 1))


def _snake_shape(width: int, size: int, reflected: bool) -> tuple[tuple[int, int], ...]:
    if not width + 1 <= size <= 2 * width:
        raise ValueError("snake size must fill one row and part of the second")
    cells = [(0, col) for col in range(width)]
    extra = size - width
    cells.extend((1, col) for col in range(extra))
    if reflected:
        cells = [(row, width - 1 - col) for row, col in cells]
    return tuple(sorted(cells))


def _dense_shape(height: int, width: int, phase: int) -> tuple[tuple[int, int], ...]:
    cells = []
    for row in range(height):
        row_width = width - ((row + phase) % 3)
        cells.extend((row, col) for col in range(row_width))
    return tuple(cells)


def _place(
    grid: list[list[int]],
    cells: tuple[tuple[int, int], ...],
    row0: int,
    col0: int,
    color: int,
) -> None:
    height, width = len(grid), len(grid[0])
    for dr, dc in cells:
        row, col = row0 + dr, col0 + dc
        if not (0 <= row < height and 0 <= col < width):
            raise RuntimeError("constructive object escaped the grid")
        if grid[row][col] != 0:
            raise RuntimeError("constructive objects overlapped")
        grid[row][col] = color


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    if split == "demo":
        height, width = _DEMO_DIMS[index]
        selector = _DEMO_SELECTORS[index]
    elif split == "query":
        height, width = _QUERY_DIMS[index]
        selector = _QUERY_SELECTORS[index]
    else:
        raise ValueError("split must be demo or query")
    stress = split == "query" and index == 3
    grid = [[0 for _ in range(width)] for _ in range(height)]

    anchor_col = width - 4
    _place(grid, _anchor_cells(selector, anchor_col), 0, 0, 8)

    colors = list(_PAYLOAD_COLORS)
    _rng(seed, split, index, "colors").shuffle(colors)
    colors = colors[:3]

    if stress:
        specs = (
            (4, 4, _dense_shape(6, 17, 0)),
            (12, 9, _dense_shape(6, 20, 1)),
            (21, 1, _dense_shape(9, 29, 0)),
        )
    else:
        if index % 2 == 0:
            sizes = (9, 5, 7)
            widths = (5, 4, 4)
        else:
            sizes = (7, 4, 9)
            widths = (4, 3, 5)
        row_starts = (3, 6, height - 2)
        specs_list = []
        for payload_index, (row0, shape_width, size) in enumerate(
            zip(row_starts, widths, sizes, strict=True)
        ):
            shape = _snake_shape(
                shape_width,
                size,
                reflected=bool(_rng(seed, split, index, f"reflect-{payload_index}").randrange(2)),
            )
            max_col0 = width - shape_width
            col0 = _rng(seed, split, index, f"column-{payload_index}").randint(1, max_col0)
            specs_list.append((row0, col0, shape))
        specs = tuple(specs_list)

    for color, (row0, col0, shape) in zip(colors, specs, strict=True):
        _place(grid, shape, row0, col0, color)

    objects = objects_by_color(grid)
    if len(objects) != 4 or len({obj["color"] for obj in objects}) != 4:
        raise RuntimeError("expected one anchor and three distinct payload objects")
    if any(obj["bbox"][1] < 1 for obj in objects):
        raise RuntimeError("every input object must begin right of column zero")
    facts = anchor_selector(grid)
    if facts["anchor_size"] != selector:
        raise RuntimeError("anchor construction changed the selector")
    return grid


def _pair(seed: int, split: str, index: int, policy: str) -> dict[str, list[list[int]]]:
    grid = _sample_input(seed, split, index)
    return {"input": grid, "output": apply_policy(grid, policy)}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    policy = validate_settings(settings)["slide_policy"]
    return {
        "train": [_pair(seed, "demo", index, policy) for index in range(demos)],
        "test": [_pair(seed, "query", index, policy) for index in range(queries)],
        "program_solution": program({"slide_policy": policy}),
    }


def causal_case(episode: dict[str, Any]) -> dict[str, Any]:
    for split in ("train", "test"):
        for index, pair in enumerate(episode.get(split, [])):
            facts = anchor_selector(pair["input"])
            wrong = apply_wrong_intermediate(pair["input"])
            if wrong != pair["output"]:
                return {
                    "split": split,
                    "pair_index": index,
                    "input": pair["input"],
                    "output": pair["output"],
                    "intermediate_value": facts,
                    "counterfactual_output": wrong,
                }
    raise ValueError("episode contains no distinguishing anchor-indexed case")
