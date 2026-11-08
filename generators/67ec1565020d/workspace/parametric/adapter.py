"""Native parametric adapter for ``67ec1565020d``.

``canonical`` is the exact selected source rule. ``wide_region_relay`` first
applies that aspect classifier to controller-side components, counts the
connected color-2 regions in the resulting intermediate, and uses that count to
select one of three payload components for the same aspect recoloring.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "67ec1565020d"
HERE = Path(__file__).resolve().parent
MODES = ("canonical", "wide_region_relay")
HYPOTHESES = MODES + (
    "raw_wide_count",
    "first_payload",
    "second_payload",
    "third_payload",
    "controller_only",
    "all_payload",
    "no_stage",
    "identity",
)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# height, width, post-stage wide-region count
DEMO_PROFILES = (
    (12, 16, 1),
    (14, 18, 2),
    (16, 20, 3),
    (18, 22, 1),
    (20, 24, 2),
    (22, 26, 3),
)
QUERY_PROFILES = (
    (13, 17, 2),
    (19, 23, 1),
    (24, 28, 3),
    (30, 30, 1),
)


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(value: object, *, allow_hypothesis: bool = False) -> str:
    options = HYPOTHESES if allow_hypothesis else MODES
    if type(value) is not str or value not in options:
        raise ValueError(f"mode must be one of {options!r}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"mode"}:
        raise ValueError("settings must contain exactly the mode key")
    return {"mode": _mode(value["mode"])}


def _copy(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def validate_grid(value: object) -> list[list[int]]:
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
    return value


@lru_cache(maxsize=1)
def canonical_program() -> str:
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def relay_program() -> str:
    return (HERE / "wide_region_relay.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    selected = _settings(settings)["mode"]
    return canonical_program() if selected == "canonical" else relay_program()


def _object(color: int, cells: Iterable[tuple[int, int]]) -> dict[str, object]:
    ordered = sorted(cells)
    rows = [r for r, _ in ordered]
    columns = [c for _, c in ordered]
    r1, c1, r2, c2 = min(rows), min(columns), max(rows), max(columns)
    return {
        "color": color,
        "cells": ordered,
        "size": len(ordered),
        "r1": r1,
        "c1": c1,
        "r2": r2,
        "c2": c2,
        "height": r2 - r1 + 1,
        "width": c2 - c1 + 1,
    }


def components(value: object) -> list[dict[str, object]]:
    grid = validate_grid(value)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, object]] = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            color = grid[row][column]
            queue = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.pop(0)
                cells.append((r, c))
                for dr, dc in CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(_object(color, cells))
    return result


def orientation(obj: dict[str, object]) -> str:
    height, width = int(obj["height"]), int(obj["width"])
    return "tall" if height > width else "wide" if width > height else "square"


def aspect_color(obj: dict[str, object]) -> int:
    return {"wide": 2, "tall": 3, "square": 4}[orientation(obj)]


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> None:
    for row, column in cells:
        grid[row][column] = color


def canonical_transform(value: object) -> list[list[int]]:
    source = validate_grid(value)
    out = [[0] * len(source[0]) for _ in source]
    for obj in components(source):
        _paint(out, obj["cells"], aspect_color(obj))
    return out


def _scene_parts(value: object) -> tuple[list[list[int]], dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    source = validate_grid(value)
    height = len(source)
    objects = components(source)
    dividers = [obj for obj in objects if obj["height"] == height and obj["width"] == 1]
    if len(dividers) != 1:
        raise ValueError("relay grammar needs exactly one full-height one-column divider")
    divider = dividers[0]
    split = int(divider["c1"])
    controller = [obj for obj in objects if int(obj["c2"]) < split]
    payload = [obj for obj in objects if int(obj["c1"]) > split]
    if len(controller) < 3 or len(payload) != 3:
        raise ValueError("relay grammar needs controller objects and exactly three payload objects")
    if any(int(obj["c1"]) <= split <= int(obj["c2"]) for obj in controller + payload):
        raise ValueError("objects may not cross the divider")
    return source, divider, controller, payload


def _controller_stage(value: object) -> tuple[list[list[int]], int, list[dict[str, object]], list[dict[str, object]]]:
    source, divider, controller, payload = _scene_parts(value)
    stage = _copy(source)
    for obj in controller:
        _paint(stage, obj["cells"], aspect_color(obj))
    split = int(divider["c1"])
    wide_regions = [
        obj
        for obj in components(stage)
        if obj["color"] == 2 and int(obj["c2"]) < split
    ]
    if not 1 <= len(wide_regions) <= len(payload):
        raise ValueError("post-stage wide-region count must select a payload")
    return stage, len(wide_regions), controller, payload


def _select_and_recolor(
    base: list[list[int]], payload: list[dict[str, object]], index: int
) -> list[list[int]]:
    if not 1 <= index <= len(payload):
        raise ValueError("payload index is outside the available candidates")
    out = _copy(base)
    target = payload[index - 1]
    _paint(out, target["cells"], aspect_color(target))
    return out


def transform(value: object, mode: str) -> list[list[int]]:
    selected = _mode(mode, allow_hypothesis=True)
    source = validate_grid(value)
    if selected == "canonical":
        return canonical_transform(source)
    if selected == "identity":
        return _copy(source)

    stage, actual_count, controller, payload = _controller_stage(source)
    raw_count = sum(orientation(obj) == "wide" for obj in controller)
    if selected == "wide_region_relay":
        return _select_and_recolor(stage, payload, actual_count)
    if selected == "raw_wide_count":
        return _select_and_recolor(stage, payload, raw_count)
    if selected == "first_payload":
        return _select_and_recolor(stage, payload, 1)
    if selected == "second_payload":
        return _select_and_recolor(stage, payload, 2)
    if selected == "third_payload":
        return _select_and_recolor(stage, payload, 3)
    if selected == "controller_only":
        return stage
    if selected == "all_payload":
        out = _copy(stage)
        for obj in payload:
            _paint(out, obj["cells"], aspect_color(obj))
        return out
    if selected == "no_stage":
        return _select_and_recolor(source, payload, actual_count)
    raise AssertionError(selected)


def explain_dependency(value: object) -> dict[str, object]:
    source = validate_grid(value)
    stage, count, controller, payload = _controller_stage(source)
    raw_count = sum(orientation(obj) == "wide" for obj in controller)
    return {
        "step_a": "canonically recolor every controller component by bounding-box aspect",
        "intermediate": "connected color-2 region count in the controller after recoloring",
        "step_b": "select that numbered payload object and recolor it by its own aspect",
        "wide_objects_before": raw_count,
        "wide_regions_after": count,
        "selected_payload_index": count,
        "counterfactual_payload_index": raw_count,
        "stage": stage,
        "output": _select_and_recolor(stage, payload, count),
        "counterfactual_output": _select_and_recolor(stage, payload, raw_count),
    }


def _rng(seed: int, split: str, index: int, attempt: int = 0) -> random.Random:
    raw = f"67ec1565020d-parametric-v1:{seed}:{split}:{index}:{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _shape_rect(height: int, width: int) -> set[tuple[int, int]]:
    return {(r, c) for r in range(height) for c in range(width)}


def _shape_frame(size: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(size)
        for c in range(size)
        if r in (0, size - 1) or c in (0, size - 1)
    }


def _shape_l(size: int) -> set[tuple[int, int]]:
    return {(r, 0) for r in range(size)} | {(0, c) for c in range(size)}


def _translated(cells: Iterable[tuple[int, int]], top: int, left: int) -> set[tuple[int, int]]:
    return {(top + r, left + c) for r, c in cells}


def _paint_new(grid: list[list[int]], cells: set[tuple[int, int]], color: int) -> None:
    height, width = len(grid), len(grid[0])
    if not cells or any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
        raise ValueError("generated object lies outside the grid")
    if any(grid[r][c] != 0 for r, c in cells):
        raise ValueError("generated objects overlap")
    _paint(grid, cells, color)


def _vertical_bands(height: int) -> list[tuple[int, int]]:
    # Leave one blank separator row between three bands. On the 30-row case the
    # top and bottom bands touch the outer boundaries deliberately.
    usable = height - 2
    base, extra = divmod(usable, 3)
    sizes = [base + int(i < extra) for i in range(3)]
    result = []
    top = 0
    for size in sizes:
        result.append((top, size))
        top += size + 1
    return result


def scene(height: int, width: int, region_count: int, rng: random.Random) -> list[list[int]]:
    _integer(height, "height", 12, 30)
    _integer(width, "width", 16, 30)
    _integer(region_count, "region_count", 1, 3)
    divider = width // 2
    if divider < 8 or width - divider - 1 < 7:
        raise ValueError("scene needs controller and payload room")
    grid = [[0] * width for _ in range(height)]
    for row in range(height):
        grid[row][divider] = 5

    colors = [1, 6, 7, 8, 9]
    rng.shuffle(colors)
    wide_colors = colors[:3]
    tall_color, square_color = colors[3:]

    bar_height = 2 if height >= 18 and divider >= 11 else 1
    bar_width = max(bar_height + 1, min(4, (divider - 2) // 3))
    partitions = {1: (3,), 2: (2, 1), 3: (1, 1, 1)}[region_count]
    color_index = 0
    for group_index, count in enumerate(partitions):
        total_width = count * bar_width
        max_left = divider - 1 - total_width
        left = 1 + (rng.randrange(max_left) if max_left > 0 else 0)
        top = group_index * (bar_height + 2)
        for item in range(count):
            cells = _shape_rect(bar_height, bar_width)
            if bar_height > 1 and bar_width > 2 and (item + group_index) % 2:
                cells.remove((bar_height - 1, bar_width - 1))
            _paint_new(
                grid,
                _translated(cells, top, left + item * bar_width),
                wide_colors[color_index],
            )
            color_index += 1

    tall_height = min(9, max(4, height // 3))
    tall_width = min(3, max(1, tall_height // 3), divider // 4)
    if tall_width >= tall_height:
        tall_width = tall_height - 1
    square_size = min(7, max(2, min(height // 4, (divider - 3) // 2)))
    lower_top = height - max(tall_height, square_size)
    tall_cells = _shape_rect(tall_height, tall_width)
    if tall_width > 1 and tall_height > 4:
        tall_cells.remove((1, tall_width - 1))
    _paint_new(grid, _translated(tall_cells, lower_top, 0), tall_color)
    square_cells = _shape_frame(square_size) if square_size >= 4 else _shape_l(square_size)
    _paint_new(
        grid,
        _translated(square_cells, height - square_size, divider - square_size - 1),
        square_color,
    )

    payload_colors = wide_colors[:]
    rng.shuffle(payload_colors)
    payload_left = divider + 2
    payload_width = width - payload_left
    bands = _vertical_bands(height)

    top, band_height = bands[0]
    wide_h = max(1, min(4, band_height // 2))
    wide_w = min(payload_width, max(wide_h + 1, payload_width - (0 if width == 30 else 1)))
    wide_left = width - wide_w if width == 30 else payload_left + rng.randrange(payload_width - wide_w + 1)
    wide_cells = _shape_rect(wide_h, wide_w)
    if wide_h > 1 and wide_w > 4:
        wide_cells.remove((wide_h - 1, 1))
    _paint_new(grid, _translated(wide_cells, top, wide_left), payload_colors[0])

    top, band_height = bands[1]
    tall_h = band_height
    tall_w = max(1, min(4, tall_h - 1, payload_width // 3))
    tall_left = payload_left + rng.randrange(payload_width - tall_w + 1)
    payload_tall = _shape_rect(tall_h, tall_w)
    if tall_w > 1 and tall_h > 4:
        payload_tall.remove((tall_h - 2, tall_w - 1))
    _paint_new(grid, _translated(payload_tall, top, tall_left), payload_colors[1])

    top, band_height = bands[2]
    square = min(8, band_height, payload_width)
    square = max(2, square)
    square_top = height - square if height == 30 else top + rng.randrange(band_height - square + 1)
    square_left = width - square if width == 30 else payload_left + rng.randrange(payload_width - square + 1)
    payload_square = _shape_frame(square) if square >= 4 else _shape_l(square)
    _paint_new(grid, _translated(payload_square, square_top, square_left), payload_colors[2])

    explanation = explain_dependency(grid)
    if explanation["wide_objects_before"] != 3 or explanation["wide_regions_after"] != region_count:
        raise AssertionError("constructed relay intermediate differs from requested count")
    return grid


def _input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    height, width, region_count = profiles[index]
    return scene(height, width, region_count, _rng(seed, split, index))


def generate(seed: int, settings: object, demos: int = 3, queries: int = 4) -> dict[str, object]:
    selected = _settings(settings)
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result: dict[str, object] = {}
    seen: set[tuple[tuple[int, ...], ...]] = set()
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            source = _input(seed, split, index)
            signature = tuple(tuple(row) for row in source)
            if signature in seen:
                raise ValueError("generated episode contains duplicate inputs")
            seen.add(signature)
            pairs.append({"input": source, "output": transform(source, selected["mode"])})
        result[split] = pairs
    return {
        **result,
        "program_solution": program(selected),
        "seed": seed,
        "settings": deepcopy(selected),
    }


def certificate(train: object, query_inputs: object) -> dict[str, object]:
    if type(train) is not list or type(query_inputs) is not list:
        raise ValueError("train and query_inputs must be lists")
    normalized_train = []
    for pair in train:
        if type(pair) is not dict or set(pair) < {"input", "output"}:
            raise ValueError("training pairs need input and output")
        normalized_train.append((validate_grid(pair["input"]), validate_grid(pair["output"])))
    normalized_queries = [validate_grid(value) for value in query_inputs]
    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(transform(source, hypothesis) == output for source, output in normalized_train)
    ]
    disagreements = []
    for left_index, left in enumerate(survivors):
        for right in survivors[left_index + 1 :]:
            changed = [
                index
                for index, source in enumerate(normalized_queries)
                if transform(source, left) != transform(source, right)
            ]
            if changed:
                disagreements.append({"left": left, "right": right, "query_indices": changed})
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demonstrations": len(normalized_train),
        "queries": len(normalized_queries),
        "query_disagreements": disagreements,
        "universal_identifiability": False,
    }


def public_turn(episode: object, query_index: int) -> dict[str, object]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer(query_index, "query_index", 0, len(episode["test"]) - 1)
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
