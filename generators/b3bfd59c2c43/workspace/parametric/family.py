"""Native canonical and signal-selected onion-depth family.

The canonical setting is the byte-exact selected rule: every nonzero, non-9
binary component has its exposed outer four-neighbor layer recolored to 8.
The alternative counts the unique color-9 signal object's cells and uses that
input-derived count as the onion-layer depth to recolor.  Color 9 is ignored by
the canonical shape mask, so inputs are lawful and matched across settings.
"""
from __future__ import annotations

import copy
import hashlib
import random
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
POLICIES = ("outer_boundary", "signal_depth")
SETTINGS = tuple({"layer_policy": policy} for policy in POLICIES)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_COLORS = (2, 3, 4, 5, 6, 7)

_TRAIN_PROFILES = (
    ((13, 17), 2, 2, 0),
    ((16, 20), 3, 2, 1),
    ((19, 23), 2, 3, 2),
    ((21, 25), 3, 3, 0),
    ((24, 27), 2, 3, 1),
    ((27, 29), 3, 3, 2),
)
_QUERY_PROFILES = (
    ((15, 18), 3, 2, 2),
    ((20, 22), 2, 3, 0),
    ((25, 27), 3, 3, 1),
    ((30, 30), 2, 3, 2),
)


def _policy(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"layer_policy"}
        or type(settings["layer_policy"]) is not str
        or settings["layer_policy"] not in POLICIES
    ):
        raise ValueError(
            "settings must contain only layer_policy='outer_boundary' or 'signal_depth'"
        )
    return settings["layer_policy"]


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    policy = _policy(settings)
    name = "canonical.rkt" if policy == "outer_boundary" else "signal_depth.rkt"
    return (HERE / name).read_text()


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a rectangular 1..30 ARC grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must use exact integer colors 0..9")
    return value


def _binary_components(grid: Any) -> list[frozenset[tuple[int, int]]]:
    source = _grid(grid)
    height, width = len(source), len(source[0])
    unseen = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if source[row][column] not in (0, 9)
    }
    result: list[frozenset[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, column = stack.pop()
            for dr, dc in _CARDINAL:
                point = row + dr, column + dc
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append(frozenset(cells))
    return result


def _onion_layers(grid: Any) -> dict[tuple[int, int], int]:
    source = _grid(grid)
    height, width = len(source), len(source[0])
    layers: dict[tuple[int, int], int] = {}
    for component in _binary_components(source):
        remaining = set(component)
        depth = 1
        while remaining:
            boundary = {
                (row, column)
                for row, column in remaining
                if any(
                    not (0 <= row + dr < height and 0 <= column + dc < width)
                    or (row + dr, column + dc) not in remaining
                    for dr, dc in _CARDINAL
                )
            }
            if not boundary:
                raise ValueError("component peeling made no progress")
            for cell in boundary:
                layers[cell] = depth
            remaining.difference_update(boundary)
            depth += 1
    return layers


def _signal_cells(grid: Any) -> tuple[tuple[int, int], ...]:
    source = _grid(grid)
    cells = tuple(
        (row, column)
        for row, values in enumerate(source)
        for column, value in enumerate(values)
        if value == 9
    )
    if len(cells) not in (2, 3):
        raise ValueError("input must contain one color-9 signal of size 2 or 3")
    connected = {cells[0]}
    frontier = [cells[0]]
    cell_set = set(cells)
    while frontier:
        row, column = frontier.pop()
        for dr, dc in _CARDINAL:
            point = row + dr, column + dc
            if point in cell_set and point not in connected:
                connected.add(point)
                frontier.append(point)
    if connected != cell_set:
        raise ValueError("color-9 signal must be one connected object")
    return tuple(sorted(cells))


def signal_intermediate(grid: Any) -> dict[str, Any]:
    cells = _signal_cells(grid)
    layers = _onion_layers(grid)
    depth = len(cells)
    return {
        "depth": depth,
        "signal_cells": [list(cell) for cell in cells],
        "selected_cell_count": sum(value == depth for value in layers.values()),
        "maximum_depth": max(layers.values(), default=0),
        "component_count": len(_binary_components(grid)),
    }


def apply_depth(grid: Any, depth: Any) -> list[list[int]]:
    source = _grid(grid)
    depth = _exact_int(depth, "depth", 1, 30)
    layers = _onion_layers(source)
    out = [list(row) for row in source]
    for (row, column), layer in layers.items():
        if layer == depth:
            out[row][column] = 8
    return out


def apply_outer_boundary(grid: Any) -> list[list[int]]:
    return apply_depth(grid, 1)


def transform(grid: Any, settings: Any) -> list[list[int]]:
    policy = _policy(settings)
    if policy == "outer_boundary":
        return apply_outer_boundary(grid)
    return apply_depth(grid, signal_intermediate(grid)["depth"])


def _rng(seed: int, split: str, index: int, salt: str) -> random.Random:
    raw = f"b3bfd59c2c43-native-v1:{seed}:{split}:{index}:{salt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _rectangle(size: int) -> frozenset[tuple[int, int]]:
    return frozenset((row, column) for row in range(size) for column in range(size))


def _diamond(size: int) -> frozenset[tuple[int, int]]:
    radius = size // 2
    return frozenset(
        (row, column)
        for row in range(size)
        for column in range(size)
        if abs(row - radius) + abs(column - radius) <= radius
    )


def _rounded(size: int) -> frozenset[tuple[int, int]]:
    corners = {(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)}
    return frozenset(
        (row, column)
        for row in range(size)
        for column in range(size)
        if (row, column) not in corners
    )


def _rotate_shapes(offset: int, size: int) -> tuple[frozenset[tuple[int, int]], ...]:
    values = (_diamond(size), _rounded(size), _rectangle(size))
    offset %= len(values)
    return values[offset:] + values[:offset]


def _place(
    grid: list[list[int]],
    cells: Iterable[tuple[int, int]],
    top: int,
    left: int,
    color: int,
) -> None:
    height, width = len(grid), len(grid[0])
    for dr, dc in cells:
        row, column = top + dr, left + dc
        if not (0 <= row < height and 0 <= column < width):
            raise ValueError("constructed shape leaves canvas")
        if grid[row][column] != 0:
            raise ValueError("constructed shapes overlap")
        grid[row][column] = color


_SIGNAL_SHAPES = {
    2: (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
    ),
    3: (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 1), (1, 0), (1, 1)),
    ),
}


def _signal_shape(
    depth: int, seed: int, split: str, index: int, offset: int
) -> tuple[tuple[int, int], ...]:
    # The first two demonstrations deliberately decouple count from width,
    # height and bounding-box area. Later profiles rotate topology as well.
    if split == "train" and index == 0:
        return _SIGNAL_SHAPES[2][1]
    if split == "train" and index == 1:
        return _SIGNAL_SHAPES[3][0]
    shapes = _SIGNAL_SHAPES[depth]
    return shapes[(seed + index + offset + (1 if split == "test" else 0)) % len(shapes)]


def _scene(
    seed: int,
    split: str,
    index: int,
    size: tuple[int, int],
    depth: int,
    object_count: int,
    offset: int,
) -> list[list[int]]:
    height, width = size
    if depth not in (2, 3) or object_count not in (2, 3):
        raise ValueError("invalid scene profile")
    shape_size = 9 if min(size) >= 28 else 7 if min(size) >= 18 else 5
    shapes = _rotate_shapes(offset, shape_size)
    rng = _rng(seed, split, index, "scene")
    colors = list(_COLORS)
    rng.shuffle(colors)

    if object_count == 2:
        placements = ((0, 0), (height - shape_size, width - shape_size))
    else:
        placements = (
            (0, 0),
            (0, width - shape_size),
            (height - shape_size, (width - shape_size) // 2),
        )
    grid = [[0] * width for _ in range(height)]
    for ordinal, (top, left) in enumerate(placements):
        _place(grid, shapes[ordinal], top, left, colors[ordinal])

    signal = _signal_shape(depth, seed, split, index, offset)
    signal_height = 1 + max(row for row, _ in signal)
    signal_width = 1 + max(column for _, column in signal)
    if object_count == 2:
        signal_top, signal_left = height - signal_height, 0
    else:
        signal_top, signal_left = height - signal_height, width - signal_width
    _place(grid, signal, signal_top, signal_left, 9)

    intermediate = signal_intermediate(grid)
    if intermediate["depth"] != depth:
        raise ValueError("constructed signal depth drifted")
    if intermediate["component_count"] != object_count:
        raise ValueError("constructed object count drifted")
    if intermediate["selected_cell_count"] == 0 or intermediate["maximum_depth"] < 3:
        raise ValueError("constructed objects do not expose the intended onion depth")
    return grid


def _profile_pairs(
    seed: int,
    split: str,
    profiles: tuple[tuple[tuple[int, int], int, int, int], ...],
    count: int,
    settings: dict[str, str],
) -> list[dict[str, list[list[int]]]]:
    result = []
    for index, (size, depth, object_count, offset) in enumerate(profiles[:count]):
        grid = _scene(seed, split, index, size, depth, object_count, offset)
        result.append({"input": grid, "output": transform(grid, settings)})
    return result


def _recolor_all(grid: Any) -> list[list[int]]:
    source = _grid(grid)
    return [[8 if value not in (0, 9) else value for value in row] for row in source]


def _bbox_perimeter(grid: Any) -> list[list[int]]:
    source = _grid(grid)
    out = [list(row) for row in source]
    for component in _binary_components(source):
        top = min(row for row, _ in component)
        bottom = max(row for row, _ in component)
        left = min(column for _, column in component)
        right = max(column for _, column in component)
        for row, column in component:
            if row in (top, bottom) or column in (left, right):
                out[row][column] = 8
    return out


RIVALS = (
    "canonical_outer",
    "fixed_depth_2",
    "fixed_depth_3",
    "fixed_depth_4",
    "deepest_layer",
    "recolor_entire_component",
    "bounding_box_perimeter",
    "signal_bbox_width",
    "signal_bbox_height",
    "signal_bbox_area",
    "signal_minus_one",
    "signal_plus_one",
    "reverse_signal_depth",
)


def _rival_output(grid: Any, name: str) -> list[list[int]]:
    if name == "canonical_outer":
        return apply_outer_boundary(grid)
    if name.startswith("fixed_depth_"):
        return apply_depth(grid, int(name.removeprefix("fixed_depth_")))
    if name == "deepest_layer":
        return apply_depth(grid, max(_onion_layers(grid).values()))
    if name == "recolor_entire_component":
        return _recolor_all(grid)
    if name == "bounding_box_perimeter":
        return _bbox_perimeter(grid)
    if name in {"signal_bbox_width", "signal_bbox_height", "signal_bbox_area"}:
        cells = _signal_cells(grid)
        height = max(row for row, _ in cells) - min(row for row, _ in cells) + 1
        width = max(column for _, column in cells) - min(column for _, column in cells) + 1
        target = {
            "signal_bbox_width": width,
            "signal_bbox_height": height,
            "signal_bbox_area": height * width,
        }[name]
        return apply_depth(grid, target)
    depth = signal_intermediate(grid)["depth"]
    if name == "signal_minus_one":
        return apply_depth(grid, max(1, depth - 1))
    if name == "signal_plus_one":
        return apply_depth(grid, depth + 1)
    if name == "reverse_signal_depth":
        return apply_depth(grid, 5 - depth)
    raise ValueError(f"undeclared rival {name!r}")


def teaching_check(episode: Any, settings: Any) -> dict[str, Any]:
    policy = _policy(settings)
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a demonstration list")
    demos = episode["train"]
    survivors = [
        {"layer_policy": candidate}
        for candidate in POLICIES
        if all(
            transform(pair["input"], {"layer_policy": candidate}) == pair["output"]
            for pair in demos
        )
    ]
    rivals = [
        name
        for name in RIVALS
        if not (policy == "outer_boundary" and name == "canonical_outer")
    ]
    surviving_rivals = [
        name
        for name in rivals
        if all(_rival_output(pair["input"], name) == pair["output"] for pair in demos)
    ]
    return {
        "survivors": survivors,
        "surviving_rivals": surviving_rivals,
        "rivals_tested": rivals,
        "basis": "demonstrations_only",
        "scope": "two declared settings and thirteen named shortcut families",
    }


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    policy = _policy(settings)
    normalized = {"layer_policy": policy}
    episode = {
        "train": _profile_pairs(seed, "train", _TRAIN_PROFILES, demos, normalized),
        "test": _profile_pairs(seed, "test", _QUERY_PROFILES, queries, normalized),
        "program_solution": program(normalized),
        "seed": seed,
        "settings": copy.deepcopy(normalized),
    }
    inputs = [repr(pair["input"]) for split in ("train", "test") for pair in episode[split]]
    if len(inputs) != len(set(inputs)):
        raise ValueError("all demonstration and query inputs must be distinct")
    check = teaching_check(episode, normalized)
    if check["survivors"] != [normalized] or check["surviving_rivals"]:
        raise ValueError(f"constructive demonstrations failed teaching contrasts: {check}")
    return episode


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if (
        type(episode) is not dict
        or type(episode.get("train")) is not list
        or type(episode.get("test")) is not list
    ):
        raise ValueError("episode must contain train and test lists")
    _exact_int(query_index, "query_index", 0, len(episode["test"]) - 1)
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
