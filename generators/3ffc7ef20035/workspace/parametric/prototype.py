"""Native-ready parametric authoring for 3ffc7ef20035.

The canonical setting keeps the exact source rule: fill the tight bbox of every
blue cell.  The alternative keeps the same bbox operation but makes its object
scope depend on a visible selector bar: horizontal chooses the first row-major
blue object, vertical chooses the second, then that object's bbox is filled.
"""
from __future__ import annotations

from functools import lru_cache
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable, Iterable

from reviewer_support import canonical_path, find_root


TASK_ID = "3ffc7ef20035"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
SCOPES = ("all_blue_bbox", "bar_orientation_component")
DEFAULT_SCOPE = "all_blue_bbox"
CANONICAL_PROGRAM_SHA256 = "9def40d6c822da10f74a0c9db35672e1c16209db56723d189c7c324948ad3a75"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 8

# Ordinary objects are deliberately asymmetric.  The first row-major object is
# always larger and farther right; the second is smaller, farther left, and near
# the selector.  With one horizontal and one vertical demonstration this breaks
# fixed-index, size, horizontal-position, and proximity shortcuts.
_FIRST_SHAPES = (
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (2, 3), (3, 3), (4, 3), (4, 4)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (3, 1), (3, 2), (3, 3), (4, 3), (5, 3), (5, 4)),
    ((0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (4, 3), (4, 4), (5, 4), (5, 5), (6, 5)),
)
_SECOND_SHAPES = (
    ((0, 2), (1, 2), (1, 1), (2, 1), (3, 1), (3, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 3), (1, 3), (1, 2), (2, 2), (3, 2), (3, 1), (4, 1)),
)

# Large 4-connected paths with many blank cells inside their bboxes.  Their
# sizes are part of the retained 30x30 stress contract.
_STRESS_FIRST = tuple(
    [(0, c) for c in range(8)]
    + [(r, 7) for r in range(1, 8)]
    + [(7, c) for c in range(6, -1, -1)]
    + [(r, 0) for r in range(8, 10)]
)
_STRESS_SECOND = tuple(
    [(0, c) for c in range(9)]
    + [(r, 8) for r in range(1, 9)]
    + [(8, c) for c in range(7, -1, -1)]
    + [(r, 0) for r in range(9, 11)]
)


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _scope(value: Any) -> str:
    if type(value) is not str or value not in SCOPES:
        raise ValueError(f"scope must be one of {SCOPES}")
    return value


def _copy_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("cannot bound an empty cell set")
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _components(cells: Iterable[tuple[int, int]], connectivity: int = 8) -> list[set[tuple[int, int]]]:
    pending = set(cells)
    if connectivity == 4:
        deltas = ((1, 0), (-1, 0), (0, 1), (0, -1))
    elif connectivity == 8:
        deltas = tuple(
            (dr, dc)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr, dc) != (0, 0)
        )
    else:
        raise ValueError("connectivity must be 4 or 8")
    result: list[set[tuple[int, int]]] = []
    while pending:
        start = min(pending)
        pending.remove(start)
        stack = [start]
        component = {start}
        while stack:
            row, col = stack.pop()
            for dr, dc in deltas:
                neighbor = (row + dr, col + dc)
                if neighbor in pending:
                    pending.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0, c0, _r1, _c1 = _bbox(cells)
    return tuple(sorted((row - r0, col - c0) for row, col in cells))


def _transform_shape(
    cells: tuple[tuple[int, int], ...], transform: int
) -> tuple[tuple[int, int], ...]:
    transform %= 8
    points = list(cells)
    if transform >= 4:
        points = [(row, -col) for row, col in points]
    for _ in range(transform % 4):
        points = [(col, -row) for row, col in points]
    return _normalize(points)


def _shape_dimensions(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    r0, c0, r1, c1 = _bbox(cells)
    return r1 - r0 + 1, c1 - c0 + 1


def _paint_rect(
    grid: list[list[int]], bbox: tuple[int, int, int, int], color: int = 8
) -> list[list[int]]:
    output = _copy_grid(grid)
    r0, c0, r1, c1 = bbox
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            output[row][col] = color
    return output


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("exactly one canonical authority is required")
    program = programs.pop()
    if hashlib.sha256(program.encode()).hexdigest() != CANONICAL_PROGRAM_SHA256:
        raise ValueError("canonical program bytes changed; review the prototype")
    return program


@lru_cache(maxsize=2)
def program_for(scope: str) -> str:
    scope = _scope(scope)
    if scope == DEFAULT_SCOPE:
        return canonical_program()
    return (HERE / "orientation_component.rkt").read_text(encoding="utf-8")


def wrong_orientation_program() -> str:
    return (HERE / "wrong_orientation_component.rkt").read_text(encoding="utf-8")


def observe_scene(grid: list[list[int]]) -> dict[str, Any]:
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    blue = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    }
    blue_components = _components(blue, connectivity=8)
    if len(blue_components) != 2:
        raise ValueError(f"expected exactly two blue objects, got {len(blue_components)}")
    blue_components.sort(key=lambda cells: _bbox(cells))
    component_records = []
    for cells in blue_components:
        bbox = _bbox(cells)
        r0, c0, r1, c1 = bbox
        area = (r1 - r0 + 1) * (c1 - c0 + 1)
        if len(cells) >= area:
            raise ValueError("every blue object must have a blank cell inside its bbox")
        component_records.append(
            {
                "cells": tuple(sorted(cells)),
                "bbox": bbox,
                "size": len(cells),
            }
        )
    if component_records[0]["bbox"][0] >= component_records[1]["bbox"][0]:
        raise ValueError("blue row-major order must be strict")

    other_colors = sorted(
        {
            value
            for row in grid
            for value in row
            if value not in (0, 1)
        }
    )
    if len(other_colors) != 1 or other_colors[0] == 8:
        raise ValueError("expected exactly one non-blue, non-cyan selector color")
    selector_color = other_colors[0]
    selector = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == selector_color
    }
    if len(selector) not in (2, 3) or len(_components(selector, connectivity=4)) != 1:
        raise ValueError("selector must be one 2-3 cell 4-connected bar")
    rows = {row for row, _ in selector}
    cols = {col for _, col in selector}
    if len(rows) == 1:
        orientation = "horizontal"
        ordered = sorted(col for _, col in selector)
    elif len(cols) == 1:
        orientation = "vertical"
        ordered = sorted(row for row, _ in selector)
    else:
        raise ValueError("selector must be horizontal or vertical")
    if ordered != list(range(ordered[0], ordered[-1] + 1)):
        raise ValueError("selector bar must be contiguous")

    global_bbox = _bbox(blue)
    gr0, gc0, gr1, gc1 = global_bbox
    if any(gr0 <= row <= gr1 and gc0 <= col <= gc1 for row, col in selector):
        raise ValueError("selector must stay outside the global blue bbox")
    if any(
        max(abs(br - sr), abs(bc - sc)) <= 1
        for br, bc in blue
        for sr, sc in selector
    ):
        raise ValueError("selector must not touch a blue object")
    return {
        "height": height,
        "width": width,
        "blue_components": component_records,
        "global_blue_bbox": global_bbox,
        "selector_cells": tuple(sorted(selector)),
        "selector_bbox": _bbox(selector),
        "selector_color": selector_color,
        "selector_size": len(selector),
        "selector_orientation": orientation,
    }


def _selected_index(scene: dict[str, Any], *, reversed_mapping: bool = False) -> int:
    horizontal = scene["selector_orientation"] == "horizontal"
    index = 0 if horizontal else 1
    return 1 - index if reversed_mapping else index


def transform_python(grid: list[list[int]], scope: str) -> list[list[int]]:
    scope = _scope(scope)
    scene = observe_scene(grid)
    if scope == "all_blue_bbox":
        return _paint_rect(grid, scene["global_blue_bbox"])
    component = scene["blue_components"][_selected_index(scene)]
    return _paint_rect(grid, component["bbox"])


def _paint_component_bbox(grid: list[list[int]], index: int) -> list[list[int]]:
    scene = observe_scene(grid)
    return _paint_rect(grid, scene["blue_components"][index]["bbox"])


def _paint_both_component_bboxes(grid: list[list[int]]) -> list[list[int]]:
    scene = observe_scene(grid)
    output = _copy_grid(grid)
    for component in scene["blue_components"]:
        output = _paint_rect(output, component["bbox"])
    return output


def _paint_selected_cells_only(grid: list[list[int]]) -> list[list[int]]:
    scene = observe_scene(grid)
    selected = scene["blue_components"][_selected_index(scene)]
    output = _copy_grid(grid)
    for row, col in selected["cells"]:
        output[row][col] = 8
    return output


def _component_center(component: dict[str, Any]) -> tuple[float, float]:
    r0, c0, r1, c1 = component["bbox"]
    return ((r0 + r1) / 2, (c0 + c1) / 2)


def _selector_center(scene: dict[str, Any]) -> tuple[float, float]:
    r0, c0, r1, c1 = scene["selector_bbox"]
    return ((r0 + r1) / 2, (c0 + c1) / 2)


def _distance_to_selector(scene: dict[str, Any], index: int) -> float:
    sr, sc = _selector_center(scene)
    cr, cc = _component_center(scene["blue_components"][index])
    return abs(sr - cr) + abs(sc - cc)


def _all_foreground_bbox(grid: list[list[int]]) -> list[list[int]]:
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    return _paint_rect(grid, _bbox(cells))


def _copy_input(grid: list[list[int]]) -> list[list[int]]:
    return _copy_grid(grid)


def _predict(grid: list[list[int]], hypothesis: str) -> list[list[int]]:
    scene = observe_scene(grid)
    if hypothesis in SCOPES:
        return transform_python(grid, hypothesis)
    if hypothesis == "reversed_orientation_component":
        return _paint_rect(
            grid,
            scene["blue_components"][_selected_index(scene, reversed_mapping=True)]["bbox"],
        )
    if hypothesis == "always_first_component":
        return _paint_component_bbox(grid, 0)
    if hypothesis == "always_second_component":
        return _paint_component_bbox(grid, 1)
    if hypothesis == "largest_component":
        index = max(range(2), key=lambda i: scene["blue_components"][i]["size"])
        return _paint_component_bbox(grid, index)
    if hypothesis == "smallest_component":
        index = min(range(2), key=lambda i: scene["blue_components"][i]["size"])
        return _paint_component_bbox(grid, index)
    if hypothesis == "leftmost_component":
        index = min(range(2), key=lambda i: scene["blue_components"][i]["bbox"][1])
        return _paint_component_bbox(grid, index)
    if hypothesis == "rightmost_component":
        index = max(range(2), key=lambda i: scene["blue_components"][i]["bbox"][3])
        return _paint_component_bbox(grid, index)
    if hypothesis == "nearest_component":
        index = min(range(2), key=lambda i: _distance_to_selector(scene, i))
        return _paint_component_bbox(grid, index)
    if hypothesis == "farthest_component":
        index = max(range(2), key=lambda i: _distance_to_selector(scene, i))
        return _paint_component_bbox(grid, index)
    if hypothesis == "per_component_bboxes":
        return _paint_both_component_bboxes(grid)
    if hypothesis == "paint_selected_blue_only":
        return _paint_selected_cells_only(grid)
    if hypothesis == "bar_color_parity_component":
        return _paint_component_bbox(grid, 0 if scene["selector_color"] % 2 == 0 else 1)
    if hypothesis == "bar_size_component":
        return _paint_component_bbox(grid, 0 if scene["selector_size"] == 2 else 1)
    if hypothesis == "all_foreground_bbox":
        return _all_foreground_bbox(grid)
    if hypothesis == "copy_input":
        return _copy_input(grid)
    raise ValueError(f"unknown hypothesis {hypothesis}")


HYPOTHESES = (
    *SCOPES,
    "reversed_orientation_component",
    "always_first_component",
    "always_second_component",
    "largest_component",
    "smallest_component",
    "leftmost_component",
    "rightmost_component",
    "nearest_component",
    "farthest_component",
    "per_component_bboxes",
    "paint_selected_blue_only",
    "bar_color_parity_component",
    "bar_size_component",
    "all_foreground_bbox",
    "copy_input",
)


def audit_episode(episode: dict[str, Any]) -> dict[str, Any]:
    scope = _scope(episode.get("scope"))
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode needs train and test lists")
    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(_predict(pair["input"], hypothesis) == pair["output"] for pair in train)
    ]
    blocking = [
        hypothesis
        for hypothesis in survivors
        if hypothesis != scope
        and any(_predict(pair["input"], hypothesis) != pair["output"] for pair in test)
    ]
    return {
        "schema": "3ffc7ef20035-parametric-teaching-audit-v1",
        "selected_scope": scope,
        "hypothesis_count": len(HYPOTHESES),
        "surviving_hypotheses": survivors,
        "blocking_rivals": blocking,
        "demo_count": len(train),
        "query_count": len(test),
    }


def _scene_rng(seed: int, absolute_index: int) -> random.Random:
    digest = hashlib.sha256(
        f"3ffc7ef20035-orientation-input-v1:{seed}:{absolute_index}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _place_shape(
    grid: list[list[int]],
    shape: Iterable[tuple[int, int]],
    top: int,
    left: int,
    color: int,
) -> None:
    for row, col in shape:
        target = (top + row, left + col)
        if grid[target[0]][target[1]] != 0:
            raise AssertionError("constructed objects overlap")
        grid[target[0]][target[1]] = color


def _ordinary_scene(seed: int, absolute_index: int) -> list[list[int]]:
    rng = _scene_rng(seed, absolute_index)
    dimensions = (
        (14, 14),
        (15, 16),
        (16, 15),
        (17, 18),
        (18, 17),
        (19, 20),
        (20, 19),
        (21, 22),
        (22, 21),
        (23, 24),
        (24, 23),
        (25, 26),
        (26, 25),
        (28, 28),
    )
    height, width = dimensions[absolute_index % len(dimensions)]
    first = _transform_shape(
        _FIRST_SHAPES[absolute_index % len(_FIRST_SHAPES)],
        rng.randrange(8),
    )
    second = _transform_shape(
        _SECOND_SHAPES[(absolute_index + 1) % len(_SECOND_SHAPES)],
        rng.randrange(8),
    )
    fh, fw = _shape_dimensions(first)
    sh, sw = _shape_dimensions(second)
    # Size the canvas from the transformed extents, not just the schedule.
    # The +8 allowance keeps the two objects strictly separated under
    # 8-connectivity even after both one-cell placement jitters.
    height = max(height, fh + sh + 8)
    width = max(width, fw + sw + 8)
    if height > 30 or width > 30:
        raise AssertionError("ordinary scene exceeds ARC grid limits")
    first_top = 1 + rng.randrange(2)
    first_left = width - fw - 2 - rng.randrange(2)
    second_top = height - sh - 3 - rng.randrange(2)
    second_left = 2 + rng.randrange(2)
    if first_top >= second_top:
        raise AssertionError("scene dimensions do not preserve row-major object order")
    grid = [[0] * width for _ in range(height)]
    _place_shape(grid, first, first_top, first_left, 1)
    _place_shape(grid, second, second_top, second_left, 1)

    orientation = "horizontal" if absolute_index % 2 == 0 else "vertical"
    selector_size = 3 if absolute_index < 2 else 2 + rng.randrange(2)
    selector_color = 6 if absolute_index < 2 else (2, 3, 4, 5, 6, 7, 9)[rng.randrange(7)]
    second_bottom = second_top + sh - 1
    if orientation == "horizontal":
        row = second_bottom + 2
        start_col = second_left + max(0, (sw - selector_size) // 2)
        selector = [(row, start_col + offset) for offset in range(selector_size)]
    else:
        col = second_left - 2
        start_row = second_top + max(0, (sh - selector_size) // 2)
        selector = [(start_row + offset, col) for offset in range(selector_size)]
    for row, col in selector:
        if not (0 <= row < height and 0 <= col < width) or grid[row][col] != 0:
            raise AssertionError("invalid selector placement")
        grid[row][col] = selector_color
    observe_scene(grid)
    return grid


def _stress_scene(seed: int, absolute_index: int) -> list[list[int]]:
    del seed  # The profile is fixed; the episode still varies all other scenes.
    height = width = 30
    grid = [[0] * width for _ in range(height)]
    _place_shape(grid, _STRESS_FIRST, 2, 18, 1)
    _place_shape(grid, _STRESS_SECOND, 17, 2, 1)
    orientation = "horizontal" if absolute_index % 2 == 0 else "vertical"
    selector_color = (2, 3, 4, 5, 6, 7, 9)[absolute_index % 7]
    if orientation == "horizontal":
        selector = [(29, col) for col in range(13, 16)]
    else:
        selector = [(row, 28) for row in range(13, 16)]
    for row, col in selector:
        grid[row][col] = selector_color
    observe_scene(grid)
    return grid


def _inputs(seed: int, demos: int, queries: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demo_inputs = [_ordinary_scene(seed, index) for index in range(demos)]
    query_inputs = []
    for index in range(queries):
        absolute = demos + index
        use_stress = queries >= 4 and index == queries - 1
        query_inputs.append(
            _stress_scene(seed, absolute) if use_stress else _ordinary_scene(seed, absolute)
        )
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in demo_inputs + query_inputs]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("deterministic construction produced duplicate inputs")
    return demo_inputs, query_inputs


def generate_episode(
    seed: int,
    *,
    scope: str,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    scope = _scope(scope)
    demos = _integer("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _integer("queries", queries, MIN_QUERIES, MAX_QUERIES)
    demo_inputs, query_inputs = _inputs(seed, demos, queries)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {
            "input": _copy_grid(grid),
            "output": transform_python(grid, scope),
        }

    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "scope": scope,
        "settings": {"scope": scope},
        "train": [pair(grid) for grid in demo_inputs],
        "test": [pair(grid) for grid in query_inputs],
        "program_solution": program_for(scope),
    }
    audit = audit_episode(episode)
    if audit["surviving_hypotheses"] != [scope] or audit["blocking_rivals"]:
        raise RuntimeError(f"constructed lesson is not identifiable: {audit}")
    return episode


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    test = episode.get("test")
    train = episode.get("train")
    if type(train) is not list or type(test) is not list or not test:
        raise ValueError("episode needs nonempty train and test lists")
    _integer("query_index", query_index, 0, len(test) - 1)
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }


def public_turns(episode: dict[str, Any]) -> list[dict[str, Any]]:
    test = episode.get("test")
    if type(test) is not list:
        raise ValueError("episode needs a test list")
    return [public_turn(episode, index) for index in range(len(test))]
