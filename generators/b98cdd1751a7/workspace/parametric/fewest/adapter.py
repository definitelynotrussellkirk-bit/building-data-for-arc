"""Native row-group ordering family for ARC generator b98cdd1751a7.

Step A is the canonical input-dependent partition: find four same-color
8-connected objects, sort by top row, derive the midpoint from the first and
last top rows, and split into upper/lower groups. Step B consumes those groups
and orders each group either left-to-right (the exact canonical rule) or by
fewest cells first before copying normalized crops into the four output slots.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Callable

from reviewer_support import canonical_path, find_root


TASK_ID = "b98cdd1751a7"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
ORDERS = ("left_to_right", "fewest_cells_first")
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
POSITIONS = ((0, 0), (0, 4), (4, 0), (4, 4))


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _order(value):
    if type(value) is not str or value not in ORDERS:
        raise ValueError("within_group_order must be left_to_right or fewest_cells_first")
    return value


def _settings(value):
    if type(value) is not dict or set(value) != {"within_group_order"}:
        raise ValueError("settings must contain exactly within_group_order")
    return _order(value["within_group_order"])


@lru_cache(maxsize=1)
def canonical_program():
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("require one exact canonical Racket authority")
    return programs.pop()


def program(settings):
    selected = _settings(settings)
    if selected == "left_to_right":
        return canonical_program()
    return (HERE / "fewest_cells_first.rkt").read_text(encoding="utf-8")


def _grid(value):
    if (
        type(value) is not list
        or not 10 <= len(value) <= 30
        or type(value[0]) is not list
        or not 10 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 10..30 with exact colors 0..9")
    return value


def _normalize(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _objects8(value):
    _grid(value)
    height, width = len(value), len(value[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = value[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                here_row, here_col = stack.pop()
                cells.append((here_row, here_col))
                for row_delta in (-1, 0, 1):
                    for col_delta in (-1, 0, 1):
                        if row_delta == col_delta == 0:
                            continue
                        neighbor = (here_row + row_delta, here_col + col_delta)
                        if (
                            0 <= neighbor[0] < height
                            and 0 <= neighbor[1] < width
                            and neighbor not in seen
                            and value[neighbor[0]][neighbor[1]] == color
                        ):
                            seen.add(neighbor)
                            stack.append(neighbor)
            row0 = min(r for r, _ in cells)
            row1 = max(r for r, _ in cells)
            col0 = min(c for _, c in cells)
            col1 = max(c for _, c in cells)
            objects.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "row0": row0,
                    "row1": row1,
                    "col0": col0,
                    "col1": col1,
                    "shape": _normalize(cells),
                }
            )
    return objects


def _partition(objects, midpoint):
    upper = [obj for obj in objects if obj["row0"] < midpoint]
    lower = [obj for obj in objects if obj["row0"] >= midpoint]
    return upper, lower


def _validate_objects(value):
    objects = sorted(_objects8(value), key=lambda obj: (obj["row0"], obj["col0"]))
    if len(objects) != 4:
        raise ValueError(f"admitted grammar requires exactly four objects, got {len(objects)}")
    for index, obj in enumerate(objects):
        height = obj["row1"] - obj["row0"] + 1
        width = obj["col1"] - obj["col0"] + 1
        if not 1 <= height <= 3 or not 1 <= width <= 3:
            raise ValueError(f"object {index} must fit in a 3x3 crop")
        if not 2 <= len(obj["cells"]) <= 9:
            raise ValueError(f"object {index} must contain 2..9 cells")
    midpoint = (objects[0]["row0"] + objects[-1]["row0"]) / 2.0
    upper, lower = _partition(objects, midpoint)
    if (len(upper), len(lower)) != (2, 2):
        raise ValueError("canonical first/last midpoint must split two upper and two lower objects")
    if len({obj["col0"] for obj in upper}) != 2 or len({obj["col0"] for obj in lower}) != 2:
        raise ValueError("objects in each canonical group need distinct left columns")
    return objects, midpoint, upper, lower


def _group_key(selected):
    selected = _order(selected)
    if selected == "left_to_right":
        return lambda obj: obj["col0"]
    return lambda obj: (len(obj["cells"]), obj["col0"])


def _render(value, ordered):
    output = [[0] * 7 for _ in range(7)]
    for obj, (target_row, target_col) in zip(ordered[:4], POSITIONS):
        for row, col in obj["cells"]:
            new_row = target_row + row - obj["row0"]
            new_col = target_col + col - obj["col0"]
            if 0 <= new_row < 7 and 0 <= new_col < 7:
                output[new_row][new_col] = value[row][col]
    return output


def _solve_with_groups(value, groups, selected):
    key = _group_key(selected)
    ordered = []
    for group in groups:
        ordered.extend(sorted(group, key=key))
    return _render(value, ordered)


def solve(value, within_group_order="left_to_right"):
    selected = _order(within_group_order)
    _, _, upper, lower = _validate_objects(value)
    return _solve_with_groups(value, (upper, lower), selected)


def solve_with_literal_canvas_midpoint(value, within_group_order="left_to_right"):
    selected = _order(within_group_order)
    objects, _, _, _ = _validate_objects(value)
    upper, lower = _partition(objects, len(value) / 2.0)
    return _solve_with_groups(value, (upper, lower), selected)


def analyze(value):
    objects, midpoint, upper, lower = _validate_objects(value)
    canvas_upper, canvas_lower = _partition(objects, len(value) / 2.0)
    return {
        "height": len(value),
        "width": len(value[0]),
        "canonical_midpoint": midpoint,
        "literal_canvas_midpoint": len(value) / 2.0,
        "canonical_group_sizes": [len(upper), len(lower)],
        "literal_canvas_group_sizes": [len(canvas_upper), len(canvas_lower)],
        "objects": [
            {
                "row0": obj["row0"],
                "col0": obj["col0"],
                "color": obj["color"],
                "cells": len(obj["cells"]),
                "bbox": [obj["row0"], obj["col0"], obj["row1"], obj["col1"]],
            }
            for obj in objects
        ],
    }


def dependency_intermediate(value, within_group_order):
    selected = _order(within_group_order)
    objects, midpoint, upper, lower = _validate_objects(value)
    groups = (upper, lower)
    ordered_groups = [sorted(group, key=_group_key(selected)) for group in groups]
    return {
        "canonical_midpoint": midpoint,
        "literal_canvas_midpoint": len(value) / 2.0,
        "group_sizes": [len(group) for group in groups],
        "group_cell_counts": [[len(obj["cells"]) for obj in group] for group in groups],
        "ordered_cell_counts": [
            [len(obj["cells"]) for obj in group] for group in ordered_groups
        ],
        "group_members": [
            [[obj["row0"], obj["col0"], len(obj["cells"])] for obj in group]
            for group in groups
        ],
        "all_objects": [
            [obj["row0"], obj["col0"], len(obj["cells"])] for obj in objects
        ],
    }


def _normalize_shape(shape):
    return _normalize(shape)


def _shape_variants(shape):
    variants = set()
    transformed = tuple(shape)
    for mirrored in (False, True):
        current = tuple((row, -col) if mirrored else (row, col) for row, col in transformed)
        for _ in range(4):
            variants.add(_normalize_shape(current))
            current = tuple((col, -row) for row, col in current)
    return tuple(sorted(variants))


_BASE_SHAPES = {
    2: ((0, 0), (0, 1)),
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (1, 0), (2, 0)),
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    6: tuple((row, col) for row in range(2) for col in range(3)),
    7: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1)),
    8: tuple(
        (row, col)
        for row in range(3)
        for col in range(3)
        if (row, col) != (1, 1)
    ),
    9: tuple((row, col) for row in range(3) for col in range(3)),
}
_SHAPES = {area: _shape_variants(shape) for area, shape in _BASE_SHAPES.items()}


_DEMO_SPECS = (
    {
        "size": (22, 24), "row_mode": "below", "areas": (8, 3, 2, 7),
        "row_offsets": (0, 1, 1, 0), "color_ranks": (0, 2, 3, 1),
    },
    {
        "size": (20, 23), "row_mode": "above", "areas": (2, 7, 8, 3),
        "row_offsets": (1, 0, 0, 1), "color_ranks": (2, 0, 1, 3),
    },
    {
        "size": (15, 19), "row_mode": "straddle", "areas": (9, 4, 8, 3),
        "row_offsets": (0, 1, 0, 1), "color_ranks": None,
    },
    {
        "size": (18, 21), "row_mode": "below", "areas": (7, 2, 6, 3),
        "row_offsets": (1, 0, 0, 1), "color_ranks": (1, 3, 0, 2),
    },
    {
        "size": (21, 25), "row_mode": "above", "areas": (4, 9, 7, 2),
        "row_offsets": (0, 1, 1, 0), "color_ranks": None,
    },
    {
        "size": (25, 27), "row_mode": "straddle", "areas": (8, 5, 9, 4),
        "row_offsets": (1, 0, 0, 1), "color_ranks": (3, 0, 2, 1),
    },
)

_QUERY_SPECS = (
    {
        "size": (12, 15), "row_mode": "straddle", "areas": (6, 2, 8, 3),
        "row_offsets": (0, 1, 1, 0), "color_ranks": None,
    },
    {
        "size": (18, 22), "row_mode": "above", "areas": (9, 4, 7, 2),
        "row_offsets": (1, 0, 0, 1), "color_ranks": (2, 0, 3, 1),
    },
    {
        "size": (24, 27), "row_mode": "below", "areas": (7, 3, 8, 2),
        "row_offsets": (0, 1, 1, 0), "color_ranks": None,
    },
    {
        "size": (30, 30), "row_mode": "below", "areas": (8, 3, 9, 4),
        "row_offsets": (0, 1, 1, 0), "color_ranks": (1, 3, 0, 2), "edge": True,
    },
)


def _rng(seed, split, index, attempt):
    payload = f"b98cdd1751a7-row-group-v1:{seed}:{split}:{index}:{attempt}".encode()
    return random.Random(hashlib.sha256(payload).digest())


def _shape_dimensions(shape):
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _colors(spec, rng):
    ranks = spec.get("color_ranks")
    if ranks is None:
        color = rng.randint(1, 9)
        return (color,) * 4
    palette = sorted(rng.sample(range(1, 10), 4))
    return tuple(palette[index] for index in ranks)


def _row_anchors(spec, shapes):
    height = spec["size"][0]
    upper_height = max(_shape_dimensions(shape)[0] for shape in shapes[:2])
    lower_height = max(_shape_dimensions(shape)[0] for shape in shapes[2:])
    mode = spec["row_mode"]
    if mode == "above":
        upper = 0
        lower = height // 2 - lower_height - 1
    elif mode == "below":
        upper = height // 2 + 1
        lower = height - lower_height - 1
    elif mode == "straddle":
        upper = 1
        lower = height - lower_height - 1
    else:
        raise ValueError(f"unknown row mode: {mode}")
    offsets = spec["row_offsets"]
    rows = (upper + offsets[0], upper + offsets[1], lower + offsets[2], lower + offsets[3])
    for row, shape in zip(rows, shapes):
        shape_height, _ = _shape_dimensions(shape)
        if not 0 <= row <= height - shape_height:
            raise RuntimeError("row profile cannot fit selected shape")
    return rows


def _column_anchors(spec, shapes, rng):
    width = spec["size"][1]
    edge = spec.get("edge", False)
    columns = []
    for index, shape in enumerate(shapes):
        _, shape_width = _shape_dimensions(shape)
        if index % 2 == 0:
            margin = 0 if edge else 1 + rng.randrange(2)
            columns.append(margin)
        else:
            margin = 0 if edge else 1 + rng.randrange(2)
            columns.append(width - shape_width - margin)
    return tuple(columns)


def _paint(grid, shape, row0, col0, color):
    for row, col in shape:
        if grid[row0 + row][col0 + col] != 0:
            raise RuntimeError("scene profiles must not overlap")
        grid[row0 + row][col0 + col] = color


def _scene(seed, split, index, attempt):
    spec = _DEMO_SPECS[index] if split == "train" else _QUERY_SPECS[index]
    rng = _rng(seed, split, index, attempt)
    shapes = tuple(rng.choice(_SHAPES[area]) for area in spec["areas"])
    rows = _row_anchors(spec, shapes)
    columns = _column_anchors(spec, shapes, rng)
    colors = _colors(spec, rng)
    height, width = spec["size"]
    grid = [[0] * width for _ in range(height)]
    for shape, row, col, color in zip(shapes, rows, columns, colors):
        _paint(grid, shape, row, col, color)
    facts = analyze(grid)
    if facts["canonical_group_sizes"] != [2, 2]:
        raise RuntimeError("scene lost canonical 2+2 grouping")
    if solve(grid, "left_to_right") == solve(grid, "fewest_cells_first"):
        raise RuntimeError("scene does not distinguish ordering settings")
    if spec["row_mode"] == "below" and facts["literal_canvas_group_sizes"] != [0, 4]:
        raise RuntimeError("below-midline profile lost its shortcut witness")
    if spec["row_mode"] == "above" and facts["literal_canvas_group_sizes"] != [4, 0]:
        raise RuntimeError("above-midline profile lost its shortcut witness")
    return grid


def _ordered_by(value, group_key: Callable):
    _, _, upper, lower = _validate_objects(value)
    return _render(value, sorted(upper, key=group_key) + sorted(lower, key=group_key))


def _rival_outputs(value):
    objects, _, upper, lower = _validate_objects(value)
    return {
        "literal_canvas_midpoint": solve_with_literal_canvas_midpoint(value, "left_to_right"),
        "right_to_left": _render(
            value,
            sorted(upper, key=lambda obj: -obj["col0"])
            + sorted(lower, key=lambda obj: -obj["col0"]),
        ),
        "largest_cells_first": _render(
            value,
            sorted(upper, key=lambda obj: (-len(obj["cells"]), obj["col0"]))
            + sorted(lower, key=lambda obj: (-len(obj["cells"]), obj["col0"])),
        ),
        "global_fewest_cells": _render(
            value,
            sorted(objects, key=lambda obj: (len(obj["cells"]), obj["row0"], obj["col0"])),
        ),
        "row_major_objects": _render(value, sorted(objects, key=lambda obj: (obj["row0"], obj["col0"]))),
        "color_ascending_within_group": _render(
            value,
            sorted(upper, key=lambda obj: (obj["color"], obj["col0"]))
            + sorted(lower, key=lambda obj: (obj["color"], obj["col0"])),
        ),
    }


def audit_episode(episode, selected):
    selected = _order(selected)
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    setting_survivors = [
        candidate
        for candidate in ORDERS
        if all(solve(pair["input"], candidate) == pair["output"] for pair in episode["train"])
    ]
    rival_names = tuple(_rival_outputs(episode["train"][0]["input"]))
    surviving = []
    ambiguous = []
    for name in rival_names:
        if all(_rival_outputs(pair["input"])[name] == pair["output"] for pair in episode["train"]):
            surviving.append(name)
            if any(_rival_outputs(pair["input"])[name] != pair["output"] for pair in episode["test"]):
                ambiguous.append(name)
    return {
        "selected": selected,
        "setting_survivors": setting_survivors,
        "surviving_rivals": surviving,
        "ambiguous_query_rivals": ambiguous,
        "rivals_tested": list(rival_names),
    }


def _episode_inputs(seed, demos):
    seen = set()
    result = {"train": [], "test": []}
    for split, count in (("train", demos), ("test", QUERY_COUNT)):
        for index in range(count):
            for attempt in range(16):
                value = _scene(seed, split, index, attempt)
                signature = json.dumps(value, separators=(",", ":"))
                if signature not in seen:
                    seen.add(signature)
                    result[split].append(value)
                    break
            else:
                raise ValueError("distinct-input generation budget exhausted")
    return result


def generate(seed, settings, demos, queries):
    seed = _integer(seed, "seed", 0, MAX_SEED)
    selected = _settings(settings)
    demos = _integer(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    _integer(queries, "queries", QUERY_COUNT, QUERY_COUNT)
    inputs = _episode_inputs(seed, demos)
    episode = {
        "train": [
            {"input": deepcopy(value), "output": solve(value, selected)}
            for value in inputs["train"]
        ],
        "test": [
            {"input": deepcopy(value), "output": solve(value, selected)}
            for value in inputs["test"]
        ],
        "program_solution": program(settings),
        "seed": seed,
        "settings": deepcopy(settings),
    }
    audit = audit_episode(episode, selected)
    if audit["setting_survivors"] != [selected] or audit["surviving_rivals"]:
        raise RuntimeError(f"constructed demonstrations are ambiguous: {audit}")
    return deepcopy(episode)


def public_turn(episode, query_index):
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    _integer(query_index, "query_index", 0, len(episode["test"]) - 1)
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
