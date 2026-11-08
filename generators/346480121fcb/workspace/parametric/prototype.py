#!/usr/bin/env python3
"""Episode-fixed selector semantics for 346480121fcb.

The canonical setting interprets the upper-left marker as a color.  The alternate
setting interprets that same exact integer as an object area.  Every generated
input contains one unique candidate of each kind, deliberately different, and
then feeds the selected crop to the unchanged key-coded transform stage.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import public_challenge_id


TASK_ID = "346480121fcb"
PROTOTYPE_VERSION = "1.0.0"
MODES = ("color", "area")
DEFAULT_SETTINGS = {"selection_mode": "color"}
SETTINGS = tuple({"selection_mode": mode} for mode in MODES)
DEMO_DIMS = ((9, 13), (10, 14), (12, 16), (14, 18), (16, 20), (18, 22))
QUERY_DIMS = ((18, 24), (22, 28), (30, 30), (17, 30))
DEMO_OBJECT_COUNTS = (3, 3, 4, 4, 5, 5)
QUERY_OBJECT_COUNTS = (6, 7, 8, 6)

HERE = Path(__file__).resolve().parent
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"selection_mode"}:
        raise ValueError("settings must contain exactly selection_mode")
    mode = value["selection_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"selection_mode must be one of {MODES}, got {mode!r}")
    return {"selection_mode": mode}


def program(settings: Any) -> str:
    chosen = _settings(settings)
    name = "canonical.rkt" if chosen["selection_mode"] == "color" else "select_by_area.rkt"
    source = (HERE / name).read_bytes()
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{name} must be UTF-8") from error
    if not text.strip():
        raise ValueError(f"{name} is empty")
    return text


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 3 <= len(value) <= 30
        or type(value[0]) is not list
        or not 4 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a rectangular ARC grid within 3..30 by 4..30")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return deepcopy(value)


def _output_grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("output grid must be a nonempty ARC grid within 1..30 by 1..30")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("output grid must be rectangular with exact integer colors 0..9")
    return deepcopy(value)


def _objects(source: list[list[int]]) -> list[dict[str, Any]]:
    pending = {
        (row, column)
        for row in range(1, len(source))
        for column in range(len(source[0]))
        if source[row][column] != 0
    }
    objects = []
    while pending:
        start = min(pending)
        pending.remove(start)
        color = source[start[0]][start[1]]
        stack = [start]
        cells = []
        while stack:
            point = stack.pop()
            cells.append(point)
            for dr, dc in _CARDINAL:
                neighbor = (point[0] + dr, point[1] + dc)
                if neighbor in pending and source[neighbor[0]][neighbor[1]] == color:
                    pending.remove(neighbor)
                    stack.append(neighbor)
        cells.sort()
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        objects.append(
            {
                "color": color,
                "size": len(cells),
                "cells": cells,
                "bbox": [min(rows), min(columns), max(rows), max(columns)],
            }
        )
    objects.sort(key=lambda item: item["cells"][0])
    for index, item in enumerate(objects):
        item["index"] = index
    return objects


def _bbox_overlap(first: list[int], second: list[int]) -> bool:
    return not (
        first[2] < second[0]
        or second[2] < first[0]
        or first[3] < second[1]
        or second[3] < first[1]
    )


def analyze_input(value: Any) -> dict[str, Any]:
    source = _grid(value)
    height, width = len(source), len(source[0])
    selector, key = source[0][0], source[0][-1]
    if selector not in (2, 3, 4, 5, 6, 7):
        raise ValueError("selector must be one of colors/areas 2..7")
    if key not in (1, 2, 3, 4, 5):
        raise ValueError("transform key must be one of 1..5")
    if any(source[0][column] != 0 for column in range(1, width - 1)):
        raise ValueError("header interior must be background")
    objects = _objects(source)
    if len(objects) < 3:
        raise ValueError("body needs two candidates and at least one decoy")
    color_matches = [item for item in objects if item["color"] == selector]
    area_matches = [item for item in objects if item["size"] == selector]
    if len(color_matches) != 1:
        raise ValueError(f"need exactly one selector-color object, found {len(color_matches)}")
    if len(area_matches) != 1:
        raise ValueError(f"need exactly one selector-area object, found {len(area_matches)}")
    if color_matches[0]["index"] == area_matches[0]["index"]:
        raise ValueError("color and area candidates must be different objects")
    for index, first in enumerate(objects):
        for second in objects[index + 1 :]:
            if _bbox_overlap(first["bbox"], second["bbox"]):
                raise ValueError("object bounding boxes must not overlap")
    return {
        "height": height,
        "width": width,
        "selector": selector,
        "key": key,
        "objects": deepcopy(objects),
        "color_candidate": deepcopy(color_matches[0]),
        "area_candidate": deepcopy(area_matches[0]),
    }


def _crop(source: list[list[int]], bbox: list[int]) -> list[list[int]]:
    row0, column0, row1, column1 = bbox
    return [row[column0 : column1 + 1] for row in source[row0 : row1 + 1]]


def _crop_to_content(grid: list[list[int]]) -> list[list[int]]:
    points = [(row, column) for row, values in enumerate(grid) for column, value in enumerate(values) if value != 0]
    if not points:
        return [[0]]
    row0 = min(row for row, _ in points)
    row1 = max(row for row, _ in points)
    column0 = min(column for _, column in points)
    column1 = max(column for _, column in points)
    return [row[column0 : column1 + 1] for row in grid[row0 : row1 + 1]]


def _transform(grid: list[list[int]], key: int) -> list[list[int]]:
    if key == 1:
        return deepcopy(grid)
    if key == 2:
        return [list(row) for row in zip(*grid[::-1])]
    if key == 3:
        return [list(reversed(row)) for row in grid]
    if key == 4:
        return [list(row) for row in zip(*grid)]
    if key == 5:
        return [list(reversed(row)) for row in reversed(grid)]
    raise ValueError("transform key must be 1..5")


def selected_intermediate(value: Any, settings: Any) -> dict[str, Any]:
    source = _grid(value)
    profile = analyze_input(source)
    chosen = _settings(settings)
    candidate = profile[f"{chosen['selection_mode']}_candidate"]
    return {"candidate": candidate, "crop": _crop(source, candidate["bbox"])}


def apply_without_transform(value: Any, settings: Any) -> list[list[int]]:
    return _crop_to_content(selected_intermediate(value, settings)["crop"])


def apply_python(value: Any, settings: Any) -> list[list[int]]:
    source = _grid(value)
    profile = analyze_input(source)
    chosen = _settings(settings)
    candidate = profile[f"{chosen['selection_mode']}_candidate"]
    crop = _crop(source, candidate["bbox"])
    return _crop_to_content(_transform(crop, profile["key"]))


def _rng(seed: int, split: str, index: int, purpose: str) -> random.Random:
    payload = f"{TASK_ID}|{PROTOTYPE_VERSION}|{seed}|{split}|{index}|{purpose}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _normalize_shape(cells: set[tuple[int, int]] | list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    row0 = min(row for row, _ in cells)
    column0 = min(column for _, column in cells)
    return tuple(sorted((row - row0, column - column0) for row, column in cells))


def _transform_shape(shape: tuple[tuple[int, int], ...], key: int) -> tuple[tuple[int, int], ...]:
    height = max(row for row, _ in shape) + 1
    width = max(column for _, column in shape) + 1
    if key == 1:
        cells = set(shape)
    elif key == 2:
        cells = {(column, height - 1 - row) for row, column in shape}
    elif key == 3:
        cells = {(row, width - 1 - column) for row, column in shape}
    elif key == 4:
        cells = {(column, row) for row, column in shape}
    elif key == 5:
        cells = {(height - 1 - row, width - 1 - column) for row, column in shape}
    else:
        raise ValueError("key must be 1..5")
    return _normalize_shape(cells)


def _random_blob(
    rng: random.Random,
    size: int,
    key: int,
    *,
    require_distinct_transforms: bool = False,
) -> tuple[tuple[int, int], ...]:
    for _ in range(2048):
        cells = {(0, 0)}
        while len(cells) < size:
            row, column = rng.choice(sorted(cells))
            dr, dc = rng.choice(_CARDINAL)
            cells.add((row + dr, column + dc))
        shape = _normalize_shape(cells)
        height = max(row for row, _ in shape) + 1
        width = max(column for _, column in shape) + 1
        if height > 6 or width > 6:
            continue
        if key != 1 and _transform_shape(shape, key) == shape:
            continue
        if require_distinct_transforms and len({_transform_shape(shape, code) for code in range(1, 6)}) != 5:
            continue
        return shape
    requirement = " with five distinct key transforms" if require_distinct_transforms else ""
    raise RuntimeError(
        f"unable to sample an asymmetric connected blob of size {size} for key {key}{requirement}"
    )


def _key_schedule(seed: int) -> tuple[int, ...]:
    rng = _rng(seed, "episode", 0, "key-schedule")
    nonidentity = [2, 3, 4, 5]
    rng.shuffle(nonidentity)
    return (*nonidentity, 1, nonidentity[0])


def _scene_parameters(seed: int, split: str, index: int, key: int, object_count: int) -> dict[str, Any]:
    rng = _rng(seed, split, index, "scene")
    earlier_color = index % 2 == 0
    larger_color = index % 2 == 0
    if split == "demo" and index == 0:
        selector, area_color = 4, 8
    elif split == "demo" and index == 1:
        selector, area_color = 7, 2
    elif larger_color:
        selector = rng.choice((3, 4, 5, 6))
        higher = [color for color in range(selector + 1, 10)]
        area_color = rng.choice(higher or [color for color in range(1, selector) if color != selector])
    else:
        selector = rng.choice((5, 6, 7))
        lower = [color for color in range(1, selector)]
        area_color = rng.choice(lower)
    color_size = selector + 2 if larger_color else selector - 2
    if not 3 <= color_size <= 9:
        raise AssertionError("constructed color candidate size outside 3..9")
    available_colors = [color for color in range(1, 10) if color not in {selector, area_color}]
    rng.shuffle(available_colors)
    decoy_count = object_count - 2
    if decoy_count > len(available_colors):
        raise ValueError("not enough unique colors for requested objects")
    strict_teaching_shape = split == "demo" and index < 2
    specs = [
        {
            "role": "color",
            "color": selector,
            "size": color_size,
            "shape": _random_blob(
                rng, color_size, key, require_distinct_transforms=strict_teaching_shape
            ),
        },
        {
            "role": "area",
            "color": area_color,
            "size": selector,
            "shape": _random_blob(
                rng, selector, key, require_distinct_transforms=strict_teaching_shape
            ),
        },
    ]
    for decoy_index in range(decoy_count):
        legal_sizes = [size for size in range(3, 9) if size != selector]
        # Deterministic cycling keeps the large query substantive instead of
        # relying on a lucky high-density random draw.
        size = legal_sizes[(index + decoy_index + rng.randrange(len(legal_sizes))) % len(legal_sizes)]
        specs.append(
            {
                "role": f"decoy-{decoy_index}",
                "color": available_colors[decoy_index],
                "size": size,
                "shape": _random_blob(rng, size, key),
            }
        )
    return {
        "selector": selector,
        "key": key,
        "earlier_color": earlier_color,
        "larger_color": larger_color,
        "specs": specs,
    }


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(column for _, column in shape) + 1


def _bbox_for(row0: int, column0: int, shape: tuple[tuple[int, int], ...]) -> list[int]:
    height, width = _shape_dims(shape)
    return [row0, column0, row0 + height - 1, column0 + width - 1]


def _bbox_separated(candidate: list[int], existing: list[list[int]]) -> bool:
    # Keep at least one empty row or column between bounding boxes. This prevents
    # another object from leaking into the canonical crop.
    for bbox in existing:
        if not (
            candidate[2] + 1 < bbox[0]
            or bbox[2] + 1 < candidate[0]
            or candidate[3] + 1 < bbox[1]
            or bbox[3] + 1 < candidate[1]
        ):
            return False
    return True


def _paint(grid: list[list[int]], spec: dict[str, Any], row0: int, column0: int) -> list[int]:
    for dr, dc in spec["shape"]:
        if grid[row0 + dr][column0 + dc] != 0:
            raise AssertionError("constructive placement overlap")
        grid[row0 + dr][column0 + dc] = spec["color"]
    return _bbox_for(row0, column0, spec["shape"])


def _construct_input(
    seed: int,
    split: str,
    index: int,
    dims: tuple[int, int],
    object_count: int,
    key: int,
) -> list[list[int]]:
    height, width = dims
    params = _scene_parameters(seed, split, index, key, object_count)
    specs = params["specs"]
    by_role = {spec["role"]: spec for spec in specs}
    first_role, second_role = ("color", "area") if params["earlier_color"] else ("area", "color")
    first, second = by_role[first_role], by_role[second_role]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[0][0] = params["selector"]
    grid[0][-1] = key
    bboxes: list[list[int]] = []

    first_height, first_width = _shape_dims(first["shape"])
    second_height, second_width = _shape_dims(second["shape"])
    anchors = [
        (first, 1, 0),
        (second, height - second_height, width - second_width),
    ]
    # The exact 30x30 query deliberately spans all four body boundaries.
    decoys = [spec for spec in specs if spec["role"].startswith("decoy-")]
    if split == "query" and dims == (30, 30) and len(decoys) >= 2:
        top_right = decoys.pop(0)
        bottom_left = decoys.pop(0)
        tr_height, tr_width = _shape_dims(top_right["shape"])
        bl_height, _ = _shape_dims(bottom_left["shape"])
        anchors.extend(
            [
                (top_right, 1, width - tr_width),
                (bottom_left, height - bl_height, 0),
            ]
        )
    for spec, row0, column0 in anchors:
        bbox = _bbox_for(row0, column0, spec["shape"])
        if not _bbox_separated(bbox, bboxes):
            raise RuntimeError("fixed anchor boxes collided")
        bboxes.append(_paint(grid, spec, row0, column0))

    rng = _rng(seed, split, index, "placement")
    for spec in decoys:
        shape_height, shape_width = _shape_dims(spec["shape"])
        for _ in range(2048):
            row0 = rng.randint(1, height - shape_height)
            column0 = rng.randint(0, width - shape_width)
            bbox = _bbox_for(row0, column0, spec["shape"])
            if _bbox_separated(bbox, bboxes):
                bboxes.append(_paint(grid, spec, row0, column0))
                break
        else:
            raise RuntimeError("unable to place all separated objects")

    profile = analyze_input(grid)
    if len(profile["objects"]) != object_count:
        raise AssertionError("constructed object count changed under parsing")
    return grid


def _pair(seed: int, split: str, index: int, dims: tuple[int, int], count: int, key: int, settings: dict[str, str]) -> dict[str, Any]:
    source = _construct_input(seed, split, index, dims, count, key)
    return {"input": source, "output": apply_python(source, settings)}


def generate_episode(seed: Any, settings: Any, *, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, len(DEMO_DIMS), "demos")
    queries = _integer(queries, 1, len(QUERY_DIMS), "queries")
    chosen = _settings(settings)
    keys = _key_schedule(seed)

    train = [
        _pair(seed, "demo", index, DEMO_DIMS[index], DEMO_OBJECT_COUNTS[index], keys[index], chosen)
        for index in range(demos)
    ]
    # Query construction has its own streams and uses only transform keys already
    # exhibited by the minimum two demonstrations. Therefore changing demo count
    # never changes query inputs or labels.
    test = [
        _pair(seed, "query", index, QUERY_DIMS[index], QUERY_OBJECT_COUNTS[index], keys[index % 2], chosen)
        for index in range(queries)
    ]
    episode = {
        "schema": "346480121fcb-selector-mode-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "settings": deepcopy(chosen),
        "program": program(chosen),
        "train": train,
        "test": test,
    }
    errors = episode_errors(episode)
    if errors:
        raise AssertionError("constructed invalid episode: " + "; ".join(errors))
    return episode


def teaching_survivors(episode: Any) -> list[dict[str, str]]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a train list")
    survivors = []
    for settings in SETTINGS:
        try:
            fits = all(
                type(pair) is dict
                and "input" in pair
                and "output" in pair
                and apply_python(pair["input"], settings) == pair["output"]
                for pair in episode["train"]
            )
        except ValueError:
            fits = False
        if fits:
            survivors.append(deepcopy(settings))
    return survivors


def episode_errors(episode: Any) -> list[str]:
    if type(episode) is not dict:
        return ["episode must be a dictionary"]
    errors: list[str] = []
    try:
        chosen = _settings(episode.get("settings"))
    except ValueError as error:
        return [str(error)]
    if episode.get("program") != program(chosen):
        errors.append("episode program does not match settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        errors.append("episode needs 2..6 demonstrations")
        train = []
    if type(test) is not list or not 1 <= len(test) <= 4:
        errors.append("episode needs 1..4 queries")
        test = []
    seen: set[str] = set()
    demo_keys: set[int] = set()
    valid_train = bool(train)
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            label = f"{split}[{index}]"
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                errors.append(f"{label} must contain input and output")
                if split == "train":
                    valid_train = False
                continue
            try:
                source = _grid(pair["input"])
                profile = analyze_input(source)
                expected = apply_python(source, chosen)
            except ValueError as error:
                errors.append(f"{label} invalid input: {error}")
                if split == "train":
                    valid_train = False
                continue
            try:
                _output_grid(pair["output"])
            except ValueError as error:
                errors.append(f"{label} invalid output: {error}")
                if split == "train":
                    valid_train = False
                continue
            key = json.dumps(source, separators=(",", ":"))
            if key in seen:
                errors.append(f"{label} duplicates an earlier input")
            seen.add(key)
            if split == "train":
                demo_keys.add(profile["key"])
            if pair["output"] != expected:
                errors.append(f"{label} output does not match settings")
    if valid_train and teaching_survivors({"train": train}) != [chosen]:
        errors.append("demonstrations do not identify the selected setting uniquely")
    if train and test:
        for index, pair in enumerate(test):
            try:
                key = analyze_input(pair["input"])["key"]
            except (ValueError, TypeError, KeyError):
                continue
            if key not in demo_keys:
                errors.append(f"test[{index}] uses transform key {key} absent from demonstrations")
    return errors


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    if not 0 <= query_index < len(episode["test"]):
        raise IndexError("query_index is outside the private episode")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_turn_id(episode: Any, query_index: Any = 0) -> str:
    return public_challenge_id(public_turn(episode, query_index))
