"""Matched-input all-window and key-count-relay parametric family.

The canonical setting preserves the exact selected Racket source.  The relay
setting first counts 2x2 windows in the unique color-1 source object, then uses
that input-dependent count (1, 2, or 3) as a rank into three candidate objects
ordered by occupied area.  Only the selected candidate receives the canonical
2x2 top-left markings.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

_HOME = Path(__file__).resolve().parent
_CANONICAL = (_HOME / "canonical.rkt").read_text()
_RELAY = (_HOME / "count_relay.rkt").read_text()

SCOPES = ("all", "key_count_relay")
_CANDIDATE_COLORS = (2, 3, 4, 5, 6, 7)

# profile: height, width, source-window count, area-ranked candidate rectangles,
# rank->slot permutation (TR, BL, BR), source anchor, per-slot candidate anchors.
_DEMO_PROFILES = (
    (18, 22, 1, ((4, 4), (2, 9), (3, 7)), (2, 0, 1), "tl", ("tr", "bl", "br")),
    (20, 24, 3, ((3, 4), (4, 4), (2, 9)), (0, 2, 1), "br", ("tl", "bl", "br")),
    (19, 23, 2, ((4, 4), (2, 9), (3, 7)), (1, 0, 2), "center", ("tr", "tl", "br")),
    (21, 25, 2, ((5, 3), (2, 8), (4, 5)), (2, 1, 0), "bl", ("center", "bl", "tr")),
    (22, 24, 1, ((5, 3), (2, 8), (4, 5)), (1, 2, 0), "tr", ("tl", "center", "br")),
    (22, 26, 3, ((3, 5), (5, 4), (2, 11)), (2, 0, 1), "center", ("tr", "bl", "center")),
)
_QUERY_PROFILES = (
    (23, 27, 2, ((4, 4), (2, 9), (3, 7)), (2, 0, 1), "center", ("tr", "bl", "br")),
    (24, 20, 1, ((5, 3), (2, 8), (4, 5)), (1, 2, 0), "bl", ("tl", "center", "br")),
    (18, 30, 3, ((3, 5), (5, 4), (2, 11)), (0, 2, 1), "tr", ("tr", "bl", "br")),
    (30, 30, 2, ((8, 8), (5, 13), (7, 10)), (2, 0, 1), "tl", ("tr", "bl", "br")),
)


def _scope(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"window_scope"}:
        raise ValueError("settings must contain exactly window_scope")
    value = settings["window_scope"]
    if type(value) is not str or value not in SCOPES:
        raise ValueError(f"window_scope must be one of {SCOPES}")
    return value


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: dict[str, Any]) -> str:
    return _CANONICAL if _scope(settings) == "all" else _RELAY


def _rng(seed: int, stream: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"8c5406fbf66c:key-count-relay:v1:{seed}:{stream}:{index}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _slots(height: int, width: int) -> tuple[tuple[int, int, int, int], ...]:
    middle_row, middle_col = height // 2, width // 2
    return (
        (0, 0, middle_row - 1, middle_col - 1),
        (0, middle_col + 1, middle_row - 1, width - 1),
        (middle_row + 1, 0, height - 1, middle_col - 1),
        (middle_row + 1, middle_col + 1, height - 1, width - 1),
    )


def _origin(
    slot: tuple[int, int, int, int],
    shape: tuple[int, int],
    anchor: str,
    rng: random.Random,
) -> tuple[int, int]:
    r0, c0, r1, c1 = slot
    sh, sw = shape
    if sh > r1 - r0 + 1 or sw > c1 - c0 + 1:
        raise ValueError(f"shape {shape} does not fit slot {slot}")
    choices = {
        "tl": (r0, c0),
        "tr": (r0, c1 - sw + 1),
        "bl": (r1 - sh + 1, c0),
        "br": (r1 - sh + 1, c1 - sw + 1),
        "center": ((r0 + r1 - sh + 1) // 2, (c0 + c1 - sw + 1) // 2),
    }
    if anchor == "random":
        return rng.randint(r0, r1 - sh + 1), rng.randint(c0, c1 - sw + 1)
    if anchor not in choices:
        raise ValueError(f"unknown anchor {anchor}")
    return choices[anchor]


def _paint_rectangle(
    grid: list[list[int]],
    slot: tuple[int, int, int, int],
    shape: tuple[int, int],
    color: int,
    anchor: str,
    rng: random.Random,
) -> None:
    row0, col0 = _origin(slot, shape, anchor, rng)
    height, width = shape
    for row in range(row0, row0 + height):
        for col in range(col0, col0 + width):
            if grid[row][col] != 0:
                raise ValueError("scene objects overlap")
            grid[row][col] = color


def _scene(
    seed: int,
    stream: str,
    index: int,
    profile: tuple[Any, ...],
) -> list[list[int]]:
    height, width, source_windows, shapes, permutation, source_anchor, slot_anchors = profile
    rng = _rng(seed, stream, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    slots = _slots(height, width)

    source_shape = (2, source_windows + 1)
    if rng.randrange(2):
        source_shape = source_shape[::-1]
    _paint_rectangle(grid, slots[0], source_shape, 1, source_anchor, rng)

    colors = rng.sample(list(_CANDIDATE_COLORS), 3)
    for rank, (shape, color) in enumerate(zip(shapes, colors)):
        candidate_slot = permutation[rank]
        _paint_rectangle(
            grid,
            slots[candidate_slot + 1],
            shape,
            color,
            slot_anchors[candidate_slot],
            rng,
        )

    # Color 9 is a non-window distractor.  These isolated cross-gutter cells
    # vary with the seed but never participate in either rule.
    middle_row, middle_col = height // 2, width // 2
    distractors = [
        (middle_row, 0),
        (middle_row, width - 1),
        (0, middle_col),
        (height - 1, middle_col),
    ]
    rng.shuffle(distractors)
    for row, col in distractors[: 2 + rng.randrange(3)]:
        grid[row][col] = 9
    return grid


def _strict_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 2 <= len(grid) <= 30:
        raise ValueError("grid height must be in 2..30")
    if not grid or type(grid[0]) is not list or not 2 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be in 2..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact ARC integers")
    return grid


def _all_window_anchors(grid: list[list[int]]) -> list[tuple[int, int]]:
    result = []
    for row in range(len(grid) - 1):
        for col in range(len(grid[0]) - 1):
            value = grid[row][col]
            if (
                value != 0
                and grid[row][col + 1] == value
                and grid[row + 1][col] == value
                and grid[row + 1][col + 1] == value
            ):
                result.append((row, col))
    return result


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while queue:
                point = queue.popleft()
                cells.add(point)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = point[0] + dr, point[1] + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            found.append(
                {
                    "color": color,
                    "cells": cells,
                    "size": len(cells),
                    "bbox": (
                        min(r for r, _ in cells),
                        min(c for _, c in cells),
                        max(r for r, _ in cells),
                        max(c for _, c in cells),
                    ),
                }
            )
    return found


def _object_anchors(obj: dict[str, Any]) -> list[tuple[int, int]]:
    cells = obj["cells"]
    return sorted(
        (row, col)
        for row, col in cells
        if {
            (row, col),
            (row, col + 1),
            (row + 1, col),
            (row + 1, col + 1),
        }
        <= cells
    )


def analyze_relay(grid: Any) -> dict[str, Any]:
    grid = _strict_grid(grid)
    objects = _objects(grid)
    sources = [obj for obj in objects if obj["color"] == 1]
    candidates = [obj for obj in objects if obj["color"] in _CANDIDATE_COLORS]
    if len(sources) != 1:
        raise ValueError("relay grammar requires one color-1 source object")
    if len(candidates) != 3:
        raise ValueError("relay grammar requires exactly three candidate objects")
    if len({obj["size"] for obj in candidates}) != 3:
        raise ValueError("candidate areas must be distinct")
    source_anchors = _object_anchors(sources[0])
    source_window_count = len(source_anchors)
    if source_window_count not in (1, 2, 3):
        raise ValueError("source must encode one of three candidate ranks")
    by_area = sorted(candidates, key=lambda obj: (obj["size"], obj["bbox"], obj["color"]))
    by_windows = sorted(
        candidates,
        key=lambda obj: (len(_object_anchors(obj)), obj["size"], obj["bbox"], obj["color"]),
    )
    target = by_area[source_window_count - 1]
    return {
        "source_window_count": source_window_count,
        "source_color": 1,
        "source_anchors": source_anchors,
        "target_rank": source_window_count,
        "target_color": target["color"],
        "target_area": target["size"],
        "target_anchors": _object_anchors(target),
        "candidate_colors_by_area": [obj["color"] for obj in by_area],
        "candidate_areas": [obj["size"] for obj in by_area],
        "candidate_window_counts_by_area": [len(_object_anchors(obj)) for obj in by_area],
        "candidate_colors_by_window_count": [obj["color"] for obj in by_windows],
        "candidate_colors_by_reading_order": [
            obj["color"] for obj in sorted(candidates, key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
        ],
        "objects_by_area": by_area,
        "objects_by_window_count": by_windows,
        "candidates": candidates,
        "source": sources[0],
    }


def _mark_objects(grid: list[list[int]], objects: Iterable[dict[str, Any]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    for obj in objects:
        for row, col in _object_anchors(obj):
            output[row][col] = 8
    return output


def solve_relay_with_intermediate(grid: Any, intermediate: int) -> list[list[int]]:
    grid = _strict_grid(grid)
    if type(intermediate) is not int or intermediate not in (1, 2, 3):
        raise ValueError("intermediate must be the exact integer 1, 2, or 3")
    analysis = analyze_relay(grid)
    return _mark_objects(grid, [analysis["objects_by_area"][intermediate - 1]])


def solve_python(grid: Any, scope: str) -> list[list[int]]:
    grid = _strict_grid(grid)
    if scope == "all":
        output = [row[:] for row in grid]
        for row, col in _all_window_anchors(grid):
            output[row][col] = 8
        return output
    if scope == "key_count_relay":
        analysis = analyze_relay(grid)
        return _mark_objects(grid, [analysis["objects_by_area"][analysis["source_window_count"] - 1]])
    raise ValueError(f"unknown scope {scope!r}")


def _rival_predictions(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    analysis = analyze_relay(grid)
    area = analysis["objects_by_area"]
    reading = sorted(analysis["candidates"], key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
    k = analysis["source_window_count"]
    target = area[k - 1]
    return {
        "smallest_area": _mark_objects(grid, [area[0]]),
        "middle_area": _mark_objects(grid, [area[1]]),
        "largest_area": _mark_objects(grid, [area[2]]),
        "window_count_rank": _mark_objects(grid, [analysis["objects_by_window_count"][k - 1]]),
        "top_left_rank": _mark_objects(grid, [reading[0]]),
        "bottom_right_rank": _mark_objects(grid, [reading[-1]]),
        "mark_source_and_target": _mark_objects(grid, [analysis["source"], target]),
        "mark_all_candidates": _mark_objects(grid, area),
        "mark_source_only": _mark_objects(grid, [analysis["source"]]),
    }


def teaching_check(episode: Any, chosen_scope: str) -> dict[str, Any]:
    if chosen_scope not in SCOPES:
        raise ValueError("unknown chosen scope")
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a train list")
    demos = episode["train"]
    if len(demos) < 2:
        raise ValueError("teaching check requires at least two demonstrations")
    setting_survivors = [
        scope
        for scope in SCOPES
        if all(solve_python(pair["input"], scope) == pair["output"] for pair in demos)
    ]
    rival_names = sorted(_rival_predictions(demos[0]["input"]))
    rival_survivors = [
        name
        for name in rival_names
        if all(_rival_predictions(pair["input"])[name] == pair["output"] for pair in demos)
    ]
    return {
        "setting_survivors": setting_survivors,
        "rival_survivors": rival_survivors,
        "refuted_rivals": [name for name in rival_names if name not in rival_survivors],
        "used_query_answers": False,
        "demo_count": len(demos),
        "scope": chosen_scope,
    }


def _pair(grid: list[list[int]], scope: str) -> dict[str, list[list[int]]]:
    return {"input": [row[:] for row in grid], "output": solve_python(grid, scope)}


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    scope = _scope(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")

    demo_inputs = [
        _scene(seed, "demo", index, _DEMO_PROFILES[index]) for index in range(demos)
    ]
    query_inputs = [
        _scene(seed, "query", index, _QUERY_PROFILES[index]) for index in range(queries)
    ]
    all_inputs = demo_inputs + query_inputs
    frozen = [tuple(tuple(row) for row in grid) for grid in all_inputs]
    if len(frozen) != len(set(frozen)):
        raise ValueError("all demonstration and query inputs must be distinct")
    for grid in all_inputs:
        analysis = analyze_relay(grid)
        if solve_python(grid, "all") == solve_python(grid, "key_count_relay"):
            raise ValueError("every input must distinguish the declared settings")
        if len(set(analysis["candidate_window_counts_by_area"])) != 3:
            raise ValueError("candidate window counts must be distinct")

    episode = {
        "train": [_pair(grid, scope) for grid in demo_inputs],
        "test": [_pair(grid, scope) for grid in query_inputs],
        "program_solution": program(settings),
        "settings": {"window_scope": scope},
        "seed": seed,
        "teaching": {
            "used_query_answers": False,
            "dependency": "source 2x2-window count -> area-ranked candidate -> selected markings",
        },
    }
    report = teaching_check(episode, scope)
    if report["setting_survivors"] != [scope] or report["rival_survivors"]:
        raise ValueError(f"demonstrations are not identifying: {report}")
    episode["teaching"]["check"] = report
    return episode


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    if not 0 <= query_index < len(episode["test"]):
        raise IndexError("query_index is outside the private episode")
    try:
        train = []
        for pair in episode["train"]:
            input_grid = deepcopy(pair["input"])
            output_grid = deepcopy(pair["output"])
            _strict_grid(input_grid)
            _strict_grid(output_grid)
            train.append({"input": input_grid, "output": output_grid})
        query_grid = deepcopy(episode["test"][query_index]["input"])
        _strict_grid(query_grid)
        query = {"input": query_grid}
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs require input grids and demonstration outputs") from error
    return {"train": train, "test": [query]}


def turn_bytes(episode: Any, query_index: Any = 0) -> bytes:
    return json.dumps(
        public_turn(episode, query_index),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def public_id(episode: Any, query_index: Any = 0) -> str:
    return hashlib.sha256(turn_bytes(episode, query_index)).hexdigest()
