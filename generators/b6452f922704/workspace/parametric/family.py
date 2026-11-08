"""Matched-input spatial/largest-overlap-first gallery family.

The canonical setting builds one key-colored rectangle per frame and packs the
parts in spatial frame order.  The alternate first computes every local red/blue
bounding-box overlap, selects the unique largest overlap, and then cyclically
rotates the gallery so that selected frame appears first.  The selected frame
index is an input-dependent intermediate consumed by the later packing step.
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
TASK_ID = "b6452f922704"
MODES = ("spatial", "largest_overlap_first")
SETTINGS = tuple({"gallery_order": mode} for mode in MODES)
RIVALS = (
    "fixed_second",
    "fixed_third",
    "smallest_overlap_first",
    "widest_overlap_first",
    "tallest_overlap_first",
    "area_descending",
    "key_ascending",
    "top_align",
)
CANONICAL_PROGRAM = (HOME / "canonical.rkt").read_text(encoding="utf-8")
LARGEST_FIRST_PROGRAM = (HOME / "largest_overlap_first.rkt").read_text(encoding="utf-8")

# Six demonstrations then four queries.  Part tuples are exact overlap
# (height, width) values in spatial frame order.  The first two demonstrations
# put the unique largest overlap at indices 1 and 2 and make the remaining
# cyclic order non-monotone by area, defeating fixed-start and area-sort rivals.
_PROFILES = (
    {"canvas": (12, 28), "positions": ((2, 1), (2, 10), (2, 19)), "parts": ((4, 2), (3, 3), (1, 2)), "keys": (1, 2, 0)},
    {"canvas": (20, 28), "positions": ((2, 0), (2, 20), (11, 10)), "parts": ((1, 3), (4, 2), (3, 3)), "keys": (2, 0, 1)},
    {"canvas": (20, 28), "positions": ((2, 10), (11, 0), (11, 20)), "parts": ((4, 3), (2, 4), (1, 5)), "keys": (0, 2, 1)},
    {"canvas": (28, 20), "positions": ((2, 1), (11, 11), (20, 1)), "parts": ((2, 5), (4, 4), (3, 3)), "keys": (1, 0, 2)},
    {"canvas": (28, 20), "positions": ((2, 11), (11, 1), (20, 11)), "parts": ((1, 4), (3, 3), (5, 2)), "keys": (2, 1, 0)},
    {"canvas": (20, 28), "positions": ((2, 0), (11, 10), (2, 20)), "parts": ((5, 3), (2, 5), (3, 4)), "keys": (0, 1, 2)},
    {"canvas": (22, 28), "positions": ((2, 1), (2, 19), (13, 10)), "parts": ((2, 4), (3, 3), (4, 3)), "keys": (1, 2, 0)},
    {"canvas": (28, 22), "positions": ((2, 1), (11, 13), (20, 1)), "parts": ((3, 2), (5, 2), (2, 4)), "keys": (2, 0, 1)},
    {"canvas": (22, 28), "positions": ((2, 10), (13, 0), (13, 20)), "parts": ((4, 3), (5, 3), (2, 5)), "keys": (0, 2, 1)},
    {"canvas": (30, 30), "positions": ((1, 0), (11, 11), (22, 22)), "parts": ((2, 5), (4, 3), (5, 4)), "keys": (1, 0, 2)},
)
_FRAME_H = 8
_FRAME_W = 8
_KEY_PALETTES = ((3, 5, 7), (4, 6, 8))
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def mode_from_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"gallery_order"}:
        raise ValueError("settings must contain exactly gallery_order")
    mode = settings["gallery_order"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("gallery_order must be spatial or largest_overlap_first")
    return mode


def program(settings: Any) -> str:
    return CANONICAL_PROGRAM if mode_from_settings(settings) == "spatial" else LARGEST_FIRST_PROGRAM


def _rng(seed: int, index: int, salt: str) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}|v1|{seed}|{index}|{salt}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _opposed_l_shapes(
    height: int,
    width: int,
    overlap_h: int,
    overlap_w: int,
    *,
    flip_vertical: bool,
    flip_horizontal: bool,
    swap_colors: bool,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    if not (1 <= overlap_h <= height - 1 and 1 <= overlap_w <= width - 1):
        raise ValueError("requested overlap does not fit")
    a = {(0, col) for col in range(width - 1)} | {(row, 0) for row in range(height - 1)}
    b_row0 = height - (overlap_h + 1)
    b_col0 = width - (overlap_w + 1)
    b = {(height - 1, col) for col in range(b_col0, width)} | {
        (row, width - 1) for row in range(b_row0, height)
    }

    def transform(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
        result = set()
        for row, col in cells:
            if flip_vertical:
                row = height - 1 - row
            if flip_horizontal:
                col = width - 1 - col
            result.add((row, col))
        return result

    blue, red = transform(a), transform(b)
    if blue & red:
        raise RuntimeError("constructive shapes collided")
    return (red, blue) if swap_colors else (blue, red)


def _render_profile(seed: int, index: int) -> list[list[int]]:
    profile = _PROFILES[index]
    height, width = profile["canvas"]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    rng = _rng(seed, index, "scene")
    palette = _KEY_PALETTES[rng.randrange(len(_KEY_PALETTES))]
    keys = [palette[i] for i in profile["keys"]]
    interior_h, interior_w = _FRAME_H - 2, _FRAME_W - 2

    for part_index, ((frame_row, frame_col), (overlap_h, overlap_w), key) in enumerate(
        zip(profile["positions"], profile["parts"], keys)
    ):
        bottom = frame_row + _FRAME_H - 1
        right = frame_col + _FRAME_W - 1
        if frame_row <= 0 or bottom >= height or frame_col < 0 or right >= width:
            raise RuntimeError("profile frame does not fit")
        for col in range(frame_col, right + 1):
            grid[frame_row][col] = 9
            grid[bottom][col] = 9
        for row in range(frame_row, bottom + 1):
            grid[row][frame_col] = 9
            grid[row][right] = 9
        key_col = frame_col + rng.randrange(_FRAME_W)
        grid[frame_row - 1][key_col] = key
        blue, red = _opposed_l_shapes(
            interior_h,
            interior_w,
            overlap_h,
            overlap_w,
            flip_vertical=bool(rng.randrange(2)),
            flip_horizontal=bool(rng.randrange(2)),
            swap_colors=bool(rng.randrange(2)),
        )
        for row, col in blue:
            grid[frame_row + 1 + row][frame_col + 1 + col] = 1
        for row, col in red:
            grid[frame_row + 1 + row][frame_col + 1 + col] = 2
    return grid


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    pending = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    components: list[set[tuple[int, int]]] = []
    while pending:
        start = min(pending)
        pending.remove(start)
        cells = {start}
        todo = [start]
        while todo:
            row, col = todo.pop()
            for dr, dc in _DIRS4:
                point = row + dr, col + dc
                if point in pending:
                    pending.remove(point)
                    cells.add(point)
                    todo.append(point)
        components.append(cells)
    return components


def _bbox(cells: set[tuple[int, int]] | list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _frame_records(grid: Any) -> list[dict[str, Any]]:
    normalized = normalize_grid(grid)
    height, width = len(normalized), len(normalized[0])
    components = _components(normalized, 9)
    if len(components) != 3:
        raise ValueError("family inputs need exactly three color-9 frames")
    records: list[dict[str, Any]] = []
    for cells in components:
        top, left, bottom, right = _bbox(cells)
        perimeter = {
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
            if row in (top, bottom) or col in (left, right)
        }
        if cells != perimeter or top == 0:
            raise ValueError("invalid frame")
        keys = [normalized[top - 1][col] for col in range(left, right + 1) if normalized[top - 1][col] not in (0, 9)]
        if len(keys) != 1 or keys[0] in (1, 2, 9):
            raise ValueError("invalid local key")
        interior = [(row, col) for row in range(top + 1, bottom) for col in range(left + 1, right)]
        blue = [(row, col) for row, col in interior if normalized[row][col] == 1]
        red = [(row, col) for row, col in interior if normalized[row][col] == 2]
        if not blue or not red:
            raise ValueError("missing red or blue shape")
        br0, bc0, br1, bc1 = _bbox(blue)
        rr0, rc0, rr1, rc1 = _bbox(red)
        overlap_h = min(br1, rr1) - max(br0, rr0) + 1
        overlap_w = min(bc1, rc1) - max(bc0, rc0) + 1
        if overlap_h <= 0 or overlap_w <= 0:
            raise ValueError("non-overlapping shape bboxes")
        records.append({
            "origin": [top, left],
            "key": keys[0],
            "height": overlap_h,
            "width": overlap_w,
            "area": overlap_h * overlap_w,
        })
    records.sort(key=lambda item: tuple(item["origin"]))
    if len({item["area"] for item in records}) != 3:
        raise ValueError("family overlap areas must be distinct")
    return records


def _rotate(records: list[dict[str, Any]], index: int) -> list[dict[str, Any]]:
    return records[index:] + records[:index]


def _order(records: list[dict[str, Any]], policy: str) -> list[dict[str, Any]]:
    if policy == "spatial":
        return list(records)
    if policy == "largest_overlap_first":
        return _rotate(records, max(range(3), key=lambda i: records[i]["area"]))
    if policy == "fixed_second":
        return _rotate(records, 1)
    if policy == "fixed_third":
        return _rotate(records, 2)
    if policy == "smallest_overlap_first":
        return _rotate(records, min(range(3), key=lambda i: records[i]["area"]))
    if policy == "widest_overlap_first":
        return _rotate(records, max(range(3), key=lambda i: (records[i]["width"], -i)))
    if policy == "tallest_overlap_first":
        return _rotate(records, max(range(3), key=lambda i: (records[i]["height"], -i)))
    if policy == "area_descending":
        return sorted(records, key=lambda item: item["area"], reverse=True)
    if policy == "key_ascending":
        return sorted(records, key=lambda item: item["key"])
    if policy == "top_align":
        return list(records)
    raise ValueError(f"unknown policy {policy!r}")


def _pack(records: list[dict[str, Any]], *, top_align: bool = False) -> list[list[int]]:
    height = max(item["height"] for item in records)
    width = sum(item["width"] for item in records) + len(records) - 1
    output = [[0 for _ in range(width)] for _ in range(height)]
    left = 0
    for item in records:
        top = 0 if top_align else (height - item["height"]) // 2
        for row in range(item["height"]):
            for col in range(item["width"]):
                output[top + row][left + col] = item["key"]
        left += item["width"] + 1
    return output


def _solve_policy(grid: Any, policy: str) -> tuple[list[list[int]], dict[str, Any]]:
    records = _frame_records(grid)
    ordered = _order(records, policy)
    output = _pack(ordered, top_align=policy == "top_align")
    largest_index = max(range(3), key=lambda i: records[i]["area"])
    return output, {
        "spatial_parts": deepcopy(records),
        "largest_index": largest_index,
        "largest_area": records[largest_index]["area"],
        "ordered_origins": [item["origin"] for item in ordered],
        "policy": policy,
    }


def solve(grid: Any, mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError("mode must be spatial or largest_overlap_first")
    return _solve_policy(grid, mode)[0]


def dependency_intermediate(grid: Any, mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError("mode must be spatial or largest_overlap_first")
    return _solve_policy(grid, mode)[1]


def rival_outputs(grid: Any, selected_mode: str) -> dict[str, list[list[int]]]:
    if selected_mode not in MODES:
        raise ValueError("selected_mode must be spatial or largest_overlap_first")
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
