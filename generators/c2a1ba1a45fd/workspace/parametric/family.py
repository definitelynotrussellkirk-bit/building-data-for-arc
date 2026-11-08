"""Native object-order family for ARC task c2a1ba1a45fd.

The exact canonical/default program pairs row-major legend colors with row-major
external source objects.  The alternate preserves source selection, 8-connected
object parsing, legend parsing, and painting, but orders the same objects by
ascending cell count (row-major top-left breaks hypothetical ties).
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

from reviewer_support import canonical_path, find_root

TASK_ID = "c2a1ba1a45fd"
PARAMETER_NAME = "object_order"
SETTINGS = ("row_major", "size_ascending")
DEFAULT_SETTINGS = {PARAMETER_NAME: "row_major"}
DEMO_SIZES = ((18, 20), (19, 22), (21, 23), (23, 25), (25, 27), (27, 29))
QUERY_SIZES = ((20, 24), (24, 27), (28, 30), (30, 30))
NON_GRAY_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
CANONICAL_SHA256 = "72403ece6d949da887735d0c55196024a247f735485d4200d56b6b96aec9d3a9"

_CANONICAL_OBJECT_KEY = '''(lambda (o)
                                        (+ (* 1000 (min-list (map fst (obj-cells o))))
                                           (min-list (map snd (obj-cells o))))))'''
_SIZE_OBJECT_KEY = '''(lambda (o)
                                        (+ (* 1000000 (obj-size o))
                                           (+ (* 1000 (min-list (map fst (obj-cells o))))
                                              (min-list (map snd (obj-cells o)))))))'''

DELTAS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
DELTAS_4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


@lru_cache(maxsize=1)
def _canonical_program() -> str:
    root = find_root(__file__)
    programs: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected exactly one canonical program for {TASK_ID}, got {len(programs)}")
    source = programs.pop()
    actual = hashlib.sha256(source.encode()).hexdigest()
    if actual != CANONICAL_SHA256:
        raise ValueError(f"canonical program hash mismatch: {actual} != {CANONICAL_SHA256}")
    if source.count(_CANONICAL_OBJECT_KEY) != 1:
        raise ValueError("canonical program no longer contains the unique row-major object key")
    return source


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain exactly {PARAMETER_NAME!r}")
    value = settings[PARAMETER_NAME]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"unsupported {PARAMETER_NAME}: {value!r}")
    return value


def program(settings: dict[str, Any]) -> str:
    """Return the exact Racket program for one declared setting."""
    setting = _setting(settings)
    canonical = _canonical_program()
    if setting == "row_major":
        return canonical
    alternate = canonical.replace(_CANONICAL_OBJECT_KEY, _SIZE_OBJECT_KEY)
    if alternate == canonical or alternate.count("(obj-size o)") != 1:
        raise ValueError("failed to materialize the size-order program")
    return alternate


def _exact_integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (bool is forbidden)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> None:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must contain 1..30 list rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must contain 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular lists")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact ARC color integers")


def _legend_bbox(grid: list[list[int]]) -> tuple[int, int, int, int]:
    gray = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not gray:
        raise ValueError("legend requires gray cells")
    return (
        min(row for row, _ in gray),
        min(col for _, col in gray),
        max(row for row, _ in gray),
        max(col for _, col in gray),
    )


def _inside(cell: tuple[int, int], bbox: tuple[int, int, int, int]) -> bool:
    return bbox[0] <= cell[0] <= bbox[2] and bbox[1] <= cell[1] <= bbox[3]


def _components(grid: list[list[int]], deltas=DELTAS_8) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                here = queue.popleft()
                cells.append(here)
                for dr, dc in deltas:
                    nxt = (here[0] + dr, here[1] + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            ordered = tuple(sorted(cells))
            found.append(
                {
                    "color": color,
                    "cells": ordered,
                    "size": len(ordered),
                    "top_left": min(ordered),
                }
            )
    return found


def cardinal_component_count(cells: Any) -> int:
    remaining = {tuple(cell) for cell in cells}
    count = 0
    while remaining:
        count += 1
        queue = [remaining.pop()]
        while queue:
            row, col = queue.pop()
            for dr, dc in DELTAS_4:
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
    return count


def _source_and_counts(
    grid: list[list[int]], bbox: tuple[int, int, int, int]
) -> tuple[int, dict[int, int]]:
    counts = {
        color: sum(
            value == color and not _inside((row, col), bbox)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
        )
        for color in range(1, 10)
    }
    source, best = 0, 0
    for color in range(1, 10):
        if counts[color] > best:
            source, best = color, counts[color]
    return source, counts


def _rule_parts(
    grid: list[list[int]],
    *,
    connectivity: int = 8,
    dot_order: str = "row_major",
    include_source_dot: bool = False,
) -> tuple[dict[str, Any], list[tuple[int, int, int]], list[dict[str, Any]]]:
    _validate_grid(grid)
    bbox = _legend_bbox(grid)
    source, counts = _source_and_counts(grid, bbox)
    dots = [
        (row, col, grid[row][col])
        for row in range(bbox[0], bbox[2] + 1)
        for col in range(bbox[1], bbox[3] + 1)
        if grid[row][col] not in ((0, 5) if include_source_dot else (0, 5, source))
    ]
    if dot_order == "column_major":
        dots.sort(key=lambda item: (item[1], item[0]))
    elif dot_order == "row_major":
        dots.sort(key=lambda item: (item[0], item[1]))
    else:
        raise ValueError(f"unknown dot order: {dot_order}")
    components = _components(grid, DELTAS_8 if connectivity == 8 else DELTAS_4)
    objects = sorted(
        (
            item
            for item in components
            if item["color"] == source
            and not any(_inside(cell, bbox) for cell in item["cells"])
        ),
        key=lambda item: item["top_left"],
    )
    base = {
        "legend_bbox": bbox,
        "source_color": source,
        "source_count": counts[source],
        "outside_counts": counts,
    }
    return base, dots, objects


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    base, dots, objects = _rule_parts(grid)
    bbox = base["legend_bbox"]
    source = base["source_color"]
    row_indices = list(range(len(objects)))
    size_indices = sorted(row_indices, key=lambda index: (objects[index]["size"], objects[index]["top_left"]))
    source_inside = [
        (row, col)
        for row in range(bbox[0], bbox[2] + 1)
        for col in range(bbox[1], bbox[3] + 1)
        if grid[row][col] == source
    ]
    distractor_count = sum(
        value not in (0, 5, source) and not _inside((row, col), bbox)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    )
    return {
        **base,
        "dots": tuple(dots),
        "source_objects": tuple(objects),
        "row_major_indices": row_indices,
        "size_ascending_indices": size_indices,
        "source_colored_legend_cells": tuple(source_inside),
        "distractor_cell_count": distractor_count,
    }


def _apply(
    grid: list[list[int]],
    *,
    object_order: str,
    connectivity: int = 8,
    dot_order: str = "row_major",
    include_source_dot: bool = False,
    first_dot_only: bool = False,
) -> list[list[int]]:
    _, dots, objects = _rule_parts(
        grid,
        connectivity=connectivity,
        dot_order=dot_order,
        include_source_dot=include_source_dot,
    )
    if object_order == "row_major":
        ordered = list(objects)
    elif object_order == "size_ascending":
        ordered = sorted(objects, key=lambda item: (item["size"], item["top_left"]))
    elif object_order == "size_descending":
        ordered = sorted(objects, key=lambda item: (-item["size"], item["top_left"]))
    elif object_order == "reverse_row_major":
        ordered = list(reversed(objects))
    else:
        raise ValueError(f"unknown object order: {object_order}")
    output = deepcopy(grid)
    for index, (dot, obj) in enumerate(zip(dots, ordered)):
        color = dots[0][2] if first_dot_only else dot[2]
        for row, col in obj["cells"]:
            output[row][col] = color
    return output


def transform(grid: list[list[int]], setting: str) -> list[list[int]]:
    if type(setting) is not str or setting not in SETTINGS:
        raise ValueError(f"unsupported {PARAMETER_NAME}: {setting!r}")
    return _apply(grid, object_order=setting)


def finite_program_survivors(train: list[dict[str, Any]]) -> list[str]:
    return [
        setting
        for setting in SETTINGS
        if all(transform(pair["input"], setting) == pair["output"] for pair in train)
    ]


SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "size_descending": lambda grid: _apply(grid, object_order="size_descending"),
    "reverse_row_major": lambda grid: _apply(grid, object_order="reverse_row_major"),
    "legend_column_major": lambda grid: _apply(grid, object_order="row_major", dot_order="column_major"),
    "four_connected_objects": lambda grid: _apply(grid, object_order="row_major", connectivity=4),
    "include_source_legend_cell": lambda grid: _apply(
        grid, object_order="row_major", include_source_dot=True
    ),
    "first_dot_every_object": lambda grid: _apply(
        grid, object_order="row_major", first_dot_only=True
    ),
}


def audit_shortcuts(train: list[dict[str, Any]], *, selected: str) -> list[dict[str, Any]]:
    if selected not in SETTINGS:
        raise ValueError(f"unsupported selected setting: {selected!r}")
    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
        setting: (lambda grid, value=setting: transform(grid, value))
        for setting in SETTINGS
        if setting != selected
    }
    rivals.update(SHORTCUTS)
    reports = []
    for name, rival in rivals.items():
        mismatches = [
            index
            for index, pair in enumerate(train)
            if rival(pair["input"]) != pair["output"]
        ]
        reports.append(
            {
                "rival": name,
                "refuted": bool(mismatches),
                "mismatching_demo_indices": mismatches,
            }
        )
    return reports


def _rng(seed: int, lane: str, index: int) -> random.Random:
    payload = f"c2a1ba1a45fd-parametric-v1|{seed}|{lane}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _snake_cells(height: int, width: int, target: int, *, vertical: bool) -> list[tuple[int, int]]:
    if not 1 <= target <= height * width:
        raise ValueError("target must fit the slot")
    cells: list[tuple[int, int]] = []
    if vertical:
        for col in range(width):
            rows = range(height) if col % 2 == 0 else range(height - 1, -1, -1)
            for row in rows:
                cells.append((row, col))
    else:
        for row in range(height):
            cols = range(width) if row % 2 == 0 else range(width - 1, -1, -1)
            for col in cols:
                cells.append((row, col))
    return cells[:target]


def _diagonal_blocks(block: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row0, col0 in ((0, 0), (block, block))
        for row in range(row0, row0 + block)
        for col in range(col0, col0 + block)
    ]


def _paint_cells(
    grid: list[list[int]],
    cells: list[tuple[int, int]],
    color: int,
    row0: int,
    col0: int,
) -> None:
    for row, col in cells:
        target = (row0 + row, col0 + col)
        if not (0 <= target[0] < len(grid) and 0 <= target[1] < len(grid[0])):
            raise RuntimeError("constructed source shape escaped its slot")
        if grid[target[0]][target[1]] != 0:
            raise RuntimeError("constructed source shape overlaps existing content")
        grid[target[0]][target[1]] = color


def build_input(seed: int, lane: str, index: int, height: int, width: int) -> list[list[int]]:
    _exact_integer(seed, 0, 2**63 - 1, "seed")
    if lane not in ("demo", "query"):
        raise ValueError("lane must be demo or query")
    _exact_integer(index, 0, 5, "index")
    if not (18 <= height <= 30 and 20 <= width <= 30):
        raise ValueError("scene dimensions must remain in the admitted 18x20..30x30 grammar")
    rng = _rng(seed, lane, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    source = rng.choice(NON_GRAY_COLORS)
    palette = [color for color in NON_GRAY_COLORS if color != source]
    dot_colors = rng.sample(palette, 4)
    distractor_colors = rng.sample([color for color in palette if color not in dot_colors], 2)

    legend_height = 6 if height < 24 else 7
    legend_width = 7 if width < 27 else 8
    legend_row = 1
    legend_col = width - legend_width - 1
    for row in range(legend_row, legend_row + legend_height):
        for col in range(legend_col, legend_col + legend_width):
            grid[row][col] = 5
    # A source-colored interior cell is deliberately earlier than the true dots.
    # It teaches that the source color is ignored as a legend token.
    grid[legend_row + 1][legend_col + 1] = source
    dot_positions = ((1, 3), (2, 1), (3, 4), (4, 2))
    for (dr, dc), color in zip(dot_positions, dot_colors):
        grid[legend_row + dr][legend_col + dc] = color

    scale = min(height, width) - 18
    diagonal_block = 2 if min(height, width) < 24 else 3
    object_sizes = (18 + scale, 2 * diagonal_block * diagonal_block, 30 + 2 * scale, 14 + scale)
    if not (object_sizes[1] < object_sizes[3] < object_sizes[0] < object_sizes[2]):
        raise RuntimeError(f"object sizes do not establish the intended order contrast: {object_sizes}")

    top_height = legend_height
    top_width = legend_col - 2
    top_cells = _snake_cells(
        top_height,
        top_width,
        object_sizes[0],
        vertical=bool((seed + index) % 2),
    )
    _paint_cells(grid, top_cells, source, 0, 0)

    bottom_row = legend_row + legend_height + 2
    bottom_height = height - bottom_row
    slot_width = (width - 2) // 3
    slot_starts = (0, slot_width + 1, 2 * (slot_width + 1))
    slot_widths = (slot_width, slot_width, width - slot_starts[2])
    if bottom_height < 9 or min(slot_widths) < 6:
        raise RuntimeError("scene dimensions do not support the four-object lesson")

    diagonal = _diagonal_blocks(diagonal_block)
    _paint_cells(grid, diagonal, source, bottom_row, slot_starts[0])
    second = _snake_cells(
        bottom_height,
        slot_widths[1],
        object_sizes[2],
        vertical=bool((seed + index + 1) % 2),
    )
    _paint_cells(grid, second, source, bottom_row, slot_starts[1])
    third = _snake_cells(
        bottom_height,
        slot_widths[2],
        object_sizes[3],
        vertical=bool((seed + index) % 2),
    )
    _paint_cells(grid, third, source, bottom_row, slot_starts[2])

    # Eight outside distractor cells make source-frequency selection visible.
    distractor_row = legend_row + legend_height
    for offset, color in ((0, distractor_colors[0]), (width - 2, distractor_colors[1])):
        for dr in (0, 1):
            for dc in (0, 1):
                row, col = distractor_row + dr, offset + dc
                if grid[row][col] != 0:
                    raise RuntimeError("distractor placement overlaps generated content")
                grid[row][col] = color

    facts = scene_facts(grid)
    sizes = [item["size"] for item in facts["source_objects"]]
    expected = list(object_sizes)
    if sizes != expected:
        raise RuntimeError(f"constructed source object sizes drifted: {sizes} != {expected}")
    if len(facts["dots"]) != 4:
        raise RuntimeError("constructed legend must expose exactly four true dots")
    if facts["source_color"] != source:
        raise RuntimeError("constructed source color is not the outside-frequency winner")
    if facts["source_count"] <= max(
        count for color, count in facts["outside_counts"].items() if color != source
    ):
        raise RuntimeError("constructed source frequency is not uniquely maximal")
    return grid


def _pairs(
    seed: int,
    setting: str,
    lane: str,
    sizes: tuple[tuple[int, int], ...],
    count: int,
) -> list[dict[str, Any]]:
    pairs = []
    for index, (height, width) in enumerate(sizes[:count]):
        grid = build_input(seed, lane, index, height, width)
        pairs.append({"input": grid, "output": transform(grid, setting)})
    return pairs


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    seed = _exact_integer(seed, 0, 2**63 - 1, "seed")
    demos = _exact_integer(demos, 2, 6, "demos")
    queries = _exact_integer(queries, 1, 4, "queries")
    setting = _setting(settings)
    train = _pairs(seed, setting, "demo", DEMO_SIZES, demos)
    test = _pairs(seed, setting, "query", QUERY_SIZES, queries)
    inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(inputs) != len(set(inputs)):
        raise RuntimeError("sampler produced duplicate demonstration/query inputs")
    if finite_program_survivors(train) != [setting]:
        raise RuntimeError("demonstrations do not identify the selected finite setting")
    shortcut_reports = audit_shortcuts(train, selected=setting)
    if any(not row["refuted"] for row in shortcut_reports):
        raise RuntimeError(f"demonstrations leave a declared shortcut alive: {shortcut_reports}")
    return {
        "train": train,
        "test": test,
        "program_solution": program({PARAMETER_NAME: setting}),
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in test],
    }
