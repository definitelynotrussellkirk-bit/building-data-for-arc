"""Matched-input all-outline/anchor-area-selected-fill rectangle family.

The canonical setting completes every same-color diagonal endpoint pair as an
outline.  The alternate orders the reconstructed rectangles by first visible
endpoint, measures the first rectangle's input-derived area A, selects rectangle
(A-1) mod n, and fills that rectangle while preserving outlines for every other
rectangle.  Selection is an intermediate consumed by the rendering stage.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import normalize_grid, public_challenge_bytes


HOME = Path(__file__).resolve().parent
TASK_ID = "aa14c6a9f111"
MODES = ("all_outlines", "anchor_area_fill")
SETTINGS = tuple({"render_rule": mode} for mode in MODES)
RIVALS = (
    "fill_first",
    "fill_second",
    "fill_third",
    "fill_largest_area",
    "fill_smallest_area",
    "fill_largest_perimeter",
    "fill_smallest_perimeter",
    "perimeter_index",
    "area_mod",
    "lowest_color",
    "highest_color",
    "all_filled",
)
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
ANCHOR_FILL_PROGRAM = (HOME / "anchor_area_fill.rkt").read_text(encoding="utf-8")

# Six demonstrations followed by four independently revealable queries.  Box
# tuples are (top, left, bottom, right) in first-endpoint reading order.  The
# first two anchors select indices 2 and 0, and their selected rectangles are
# neither consistently largest nor smallest.
_PROFILES = (
    {"canvas": (18, 24), "boxes": ((1, 1, 3, 4), (5, 10, 9, 15), (12, 2, 15, 6)), "colors": (0, 2, 1)},
    {"canvas": (18, 24), "boxes": ((1, 15, 4, 18), (6, 1, 8, 3), (11, 10, 15, 15)), "colors": (2, 0, 1)},
    {"canvas": (20, 20), "boxes": ((1, 1, 18, 18), (4, 4, 15, 15), (7, 8, 11, 13)), "colors": (1, 0, 2)},
    {"canvas": (20, 26), "boxes": ((1, 1, 2, 4), (5, 12, 9, 15), (12, 2, 17, 6)), "colors": (0, 1, 2)},
    {"canvas": (20, 26), "boxes": ((1, 10, 5, 14), (7, 1, 9, 4), (11, 17, 16, 23)), "colors": (1, 2, 0)},
    {"canvas": (20, 22), "boxes": ((1, 1, 16, 17), (4, 4, 13, 14), (7, 7, 10, 11)), "colors": (2, 1, 0)},
    {"canvas": (22, 28), "boxes": ((1, 1, 3, 6), (6, 15, 9, 20), (13, 2, 17, 8)), "colors": (0, 2, 1)},
    {"canvas": (16, 16), "boxes": ((1, 1, 13, 13), (3, 3, 10, 10), (5, 5, 8, 8)), "colors": (1, 0, 2)},
    {"canvas": (22, 28), "boxes": ((1, 18, 2, 24), (6, 2, 10, 7), (13, 14, 18, 20)), "colors": (2, 1, 0)},
    {"canvas": (30, 30), "boxes": ((0, 0, 29, 29), (3, 4, 25, 26), (8, 9, 20, 21)), "colors": (0, 2, 1)},
)
_PALETTES = ((2, 5, 8), (1, 4, 7), (3, 6, 9))


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def mode_from_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"render_rule"}:
        raise ValueError("settings must contain exactly render_rule")
    mode = settings["render_rule"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("render_rule must be all_outlines or anchor_area_fill")
    return mode


def program(settings: Any) -> str:
    return CANONICAL_PROGRAM if mode_from_settings(settings) == "all_outlines" else ANCHOR_FILL_PROGRAM


def _rng(seed: int, index: int, salt: str) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}|v1|{seed}|{index}|{salt}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _render_profile(seed: int, index: int) -> list[list[int]]:
    profile = _PROFILES[index]
    height, width = profile["canvas"]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    rng = _rng(seed, index, "scene")
    palette = _PALETTES[rng.randrange(len(_PALETTES))]
    colors = [palette[i] for i in profile["colors"]]
    for box, color in zip(profile["boxes"], colors):
        top, left, bottom, right = box
        orientation = "main" if rng.randrange(2) == 0 else "anti"
        if orientation == "main":
            first, second = (top, left), (bottom, right)
        else:
            first, second = (top, right), (bottom, left)
        if grid[first[0]][first[1]] or grid[second[0]][second[1]]:
            raise RuntimeError("profile endpoint collision")
        grid[first[0]][first[1]] = color
        grid[second[0]][second[1]] = color
    return grid


def _outline(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = box
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }


def _fill(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = box
    return {(row, col) for row in range(top, bottom + 1) for col in range(left, right + 1)}


def _records(grid: Any) -> list[dict[str, Any]]:
    normalized = normalize_grid(grid)
    by_color: dict[int, list[tuple[int, int]]] = {}
    first_seen: list[int] = []
    for row, values in enumerate(normalized):
        for col, value in enumerate(values):
            if value == 0:
                continue
            if value not in by_color:
                by_color[value] = []
                first_seen.append(value)
            by_color[value].append((row, col))
    if len(first_seen) != 3:
        raise ValueError("family inputs require exactly three active colors")
    records: list[dict[str, Any]] = []
    for color in first_seen:
        cells = by_color[color]
        if len(cells) != 2:
            raise ValueError("each active color must appear exactly twice")
        (r1, c1), (r2, c2) = cells
        if r1 == r2 or c1 == c2:
            raise ValueError("same-color cells must be diagonal rectangle corners")
        box = (min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2))
        height = box[2] - box[0] + 1
        width = box[3] - box[1] + 1
        records.append({
            "color": color,
            "box": list(box),
            "area": height * width,
            "perimeter": 2 * (height + width) - 4,
            "height": height,
            "width": width,
        })
    return records


def _selected_index(records: list[dict[str, Any]], policy: str) -> int | None:
    count = len(records)
    if policy == "all_outlines":
        return None
    if policy == "anchor_area_fill":
        return (records[0]["area"] - 1) % count
    if policy == "fill_first":
        return 0
    if policy == "fill_second":
        return 1
    if policy == "fill_third":
        return 2
    if policy == "fill_largest_area":
        return max(range(count), key=lambda i: (records[i]["area"], -i))
    if policy == "fill_smallest_area":
        return min(range(count), key=lambda i: (records[i]["area"], i))
    if policy == "fill_largest_perimeter":
        return max(range(count), key=lambda i: (records[i]["perimeter"], -i))
    if policy == "fill_smallest_perimeter":
        return min(range(count), key=lambda i: (records[i]["perimeter"], i))
    if policy == "perimeter_index":
        return (records[0]["perimeter"] - 1) % count
    if policy == "area_mod":
        return records[0]["area"] % count
    if policy == "lowest_color":
        return min(range(count), key=lambda i: records[i]["color"])
    if policy == "highest_color":
        return max(range(count), key=lambda i: records[i]["color"])
    if policy == "all_filled":
        return -1
    raise ValueError(f"unknown policy {policy!r}")


def _solve_policy(grid: Any, policy: str) -> tuple[list[list[int]], dict[str, Any]]:
    normalized = normalize_grid(grid)
    records = _records(normalized)
    selected = _selected_index(records, policy)
    output = [[0 for _ in row] for row in normalized]
    for index, record in enumerate(records):
        box = tuple(record["box"])
        cells = _fill(box) if selected == -1 or selected == index else _outline(box)
        for row, col in cells:
            output[row][col] = record["color"]
    intermediate = {
        "ordered_rectangles": deepcopy(records),
        "anchor_area": records[0]["area"],
        "selected_index": selected,
        "selected_box": None if selected is None or selected == -1 else list(records[selected]["box"]),
        "policy": policy,
    }
    return output, intermediate


def solve(grid: Any, mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError("mode must be all_outlines or anchor_area_fill")
    return _solve_policy(grid, mode)[0]


def dependency_intermediate(grid: Any, mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError("mode must be all_outlines or anchor_area_fill")
    return _solve_policy(grid, mode)[1]


def rival_outputs(grid: Any, selected_mode: str) -> dict[str, list[list[int]]]:
    if selected_mode not in MODES:
        raise ValueError("selected_mode must be all_outlines or anchor_area_fill")
    return {name: _solve_policy(grid, name)[0] for name in RIVALS}


@lru_cache(maxsize=128)
def _episode_inputs_cached(seed: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    return tuple(tuple(map(tuple, _render_profile(seed, index))) for index in range(len(_PROFILES)))


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
    return {
        "train": [{"input": deepcopy(grid), "output": solve(grid, mode)} for grid in inputs["train"][:demos]],
        "test": [{"input": deepcopy(grid), "output": solve(grid, mode)} for grid in inputs["test"][:queries]],
        "program_solution": program(settings),
    }


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    query_index = _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    visible = {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
    return json.loads(public_challenge_bytes(visible))
