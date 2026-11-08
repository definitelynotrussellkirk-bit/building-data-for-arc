"""Native row-major / column-major source-order family for task 0ab5dc1f5386.

The canonical setting preserves the selected Racket source byte-for-byte.  The
alternate changes only the ordering of loose source components: bounding-box
column then row instead of canonical row then column.  Frames still process in
top-left order, and each assignment updates the value-based used-source state
consumed by every later frame.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "0ab5dc1f5386"
HOME = Path(__file__).resolve().parent
PARAMETER = "source_order"
ORDERS = ("row_major", "column_major")
SETTINGS = tuple({PARAMETER: value} for value in ORDERS)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=find_root(__file__)
)

_DEMO_SPECS = (
    (12, 16, 2, 3),
    (14, 18, 3, 4),
    (16, 20, 2, 5),
    (18, 22, 4, 5),
    (20, 24, 3, 6),
    (22, 26, 5, 6),
)
_QUERY_SPECS = (
    (15, 19, 3, 5),
    (20, 23, 4, 6),
    (24, 27, 5, 7),
    (30, 30, 8, 10),
)
_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool and coercions are forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _setting(settings: dict[str, str]) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {PARAMETER}
        or type(settings[PARAMETER]) is not str
        or settings[PARAMETER] not in ORDERS
    ):
        raise ValueError("settings must be exactly {'source_order': 'row_major'|'column_major'}")
    return settings[PARAMETER]


def program(settings: dict[str, str]) -> str:
    order = _setting(settings)
    filename = "canonical.rkt" if order == "row_major" else "column_major.rkt"
    return (HOME / filename).read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = json.dumps(
        [TASK_ID, "source-order-v1", seed, split, index], separators=(",", ":")
    ).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _spec(split: str, index: int) -> tuple[int, int, int, int]:
    specs = _DEMO_SPECS if split == "train" else _QUERY_SPECS
    _integer("index", index, 0, len(specs) - 1)
    return specs[index]


def _draw_frame(grid: list[list[int]], r0: int, c0: int, ih: int, iw: int) -> None:
    r1, c1 = r0 + ih + 1, c0 + iw + 1
    cells = (
        {(r0, c) for c in range(c0, c1 + 1)}
        | {(r1, c) for c in range(c0, c1 + 1)}
        | {(r, c0) for r in range(r0, r1 + 1)}
        | {(r, c1) for r in range(r0, r1 + 1)}
    )
    if any(not (0 <= r < len(grid) and 0 <= c < len(grid[0])) for r, c in cells):
        raise RuntimeError("frame escaped canvas")
    if any(grid[r][c] for r, c in cells):
        raise RuntimeError("frame collision")
    for r, c in cells:
        grid[r][c] = 8


def _make_crop(height: int, width: int, palette: tuple[int, ...], phase: int) -> list[list[int]]:
    crop = [[0 for _ in range(width)] for _ in range(height)]
    for r in range(height):
        for c in range(width):
            border = r in (0, height - 1) or c in (0, width - 1)
            interior = (3 * r + 5 * c + phase) % 4 in (0, 1)
            if border or interior:
                crop[r][c] = palette[(r + 2 * c + phase) % len(palette)]
    return crop


def _put_crop(grid: list[list[int]], r0: int, c0: int, crop: list[list[int]]) -> None:
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value:
                rr, cc = r0 + r, c0 + c
                if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])):
                    raise RuntimeError("source crop escaped canvas")
                if grid[rr][cc]:
                    raise RuntimeError("source crop collision")
                grid[rr][cc] = value


def _build_input(seed: int, split: str, index: int) -> list[list[int]]:
    height, width, ih, iw = _spec(split, index)
    rng = _rng(seed, split, index)
    palette = list(_COLORS)
    rng.shuffle(palette)
    crop_a = _make_crop(ih, iw, tuple(palette[:3]), phase=index + 1)
    crop_b = _make_crop(ih, iw, tuple(palette[3:6]), phase=index + 7)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    # Frames process top-left first and bottom-right second.
    _draw_frame(grid, 0, 0, ih, iw)
    _draw_frame(grid, height - ih - 2, width - iw - 2, ih, iw)

    # Source A is first in row-major order; source B is first in column-major
    # order.  Each touches a different pair of boundaries and remains isolated.
    _put_crop(grid, 0, width - iw, crop_a)
    _put_crop(grid, height - ih, 0, crop_b)

    # One unmatched source makes pure "copy all shapes" readings visibly wrong.
    dr, dc = height // 2, width // 2
    if grid[dr][dc] == 0:
        grid[dr][dc] = palette[6]

    problems = GEN.self_check(grid)
    if problems:
        raise RuntimeError(f"constructed scene violates production grammar: {problems}")
    if solve(grid, {PARAMETER: "row_major"}) == solve(grid, {PARAMETER: "column_major"}):
        raise RuntimeError("constructed scene failed to separate source orders")
    if solve(grid, {PARAMETER: "column_major"}, track_used=False) == solve(
        grid, {PARAMETER: "column_major"}
    ):
        raise RuntimeError("constructed scene failed to expose used-state dependency")
    return grid


def _grid(grid: list[list[int]]) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors 0..9")
    return grid


def _shape_records(grid: list[list[int]]) -> list[dict[str, Any]]:
    records = []
    for start, cells in GEN._components(grid, same_color=False):
        if grid[start[0]][start[1]] == 8:
            continue
        r1, c1, r2, c2 = GEN._bbox(cells)
        crop = tuple(
            tuple(grid[r][c] for c in range(c1, c2 + 1))
            for r in range(r1, r2 + 1)
        )
        records.append(
            {
                "bbox": (r1, c1, r2, c2),
                "height": r2 - r1 + 1,
                "width": c2 - c1 + 1,
                "crop": crop,
                "key": (r2 - r1 + 1, c2 - c1 + 1, crop),
            }
        )
    return records


def _ordered_records(grid: list[list[int]], order: str) -> list[dict[str, Any]]:
    records = _shape_records(grid)
    if order == "row_major":
        return sorted(records, key=lambda item: (item["bbox"][0], item["bbox"][1]))
    return sorted(records, key=lambda item: (item["bbox"][1], item["bbox"][0]))


def solve(
    grid: list[list[int]], settings: dict[str, str], *, track_used: bool = True
) -> list[list[int]]:
    order = _setting(settings)
    grid = _grid(grid)
    out = deepcopy(grid)
    records = _ordered_records(grid, order)
    used: list[tuple[Any, ...]] = []
    for frame in GEN._frame_boxes(grid):
        ih = frame[2] - frame[0] - 1
        iw = frame[3] - frame[1] - 1
        match = next(
            (
                item
                for item in records
                if item["height"] == ih
                and item["width"] == iw
                and (not track_used or item["key"] not in used)
            ),
            None,
        )
        if match is not None:
            if track_used:
                used.append(match["key"])
            GEN._paint_crop(out, frame, match["crop"])
    return out


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    grid = _grid(grid)
    frames = GEN._frame_boxes(grid)
    sizes = {
        (frame[2] - frame[0] - 1, frame[3] - frame[1] - 1)
        for frame in frames
    }
    matching = [item for item in _shape_records(grid) if (item["height"], item["width"]) in sizes]
    row_first = next((item for item in _ordered_records(grid, "row_major")
                      if (item["height"], item["width"]) in sizes), None)
    col_first = next((item for item in _ordered_records(grid, "column_major")
                      if (item["height"], item["width"]) in sizes), None)
    return {
        "shape": [len(grid), len(grid[0])],
        "frame_count": len(frames),
        "matching_source_count": len(matching),
        "row_major_first_bbox": list(row_first["bbox"]) if row_first else None,
        "column_major_first_bbox": list(col_first["bbox"]) if col_first else None,
        "row_major_first_value": [list(row) for row in row_first["crop"]] if row_first else None,
        "column_major_first_value": [list(row) for row in col_first["crop"]] if col_first else None,
        "row_major_output": solve(grid, {PARAMETER: "row_major"}),
        "column_major_output": solve(grid, {PARAMETER: "column_major"}),
        "column_major_without_used_state": solve(
            grid, {PARAMETER: "column_major"}, track_used=False
        ),
    }


def causal_case(grid: list[list[int]]) -> dict[str, Any]:
    """Return a source-bound wrong-intermediate case for owner replay."""
    grid = _grid(grid)
    settings = {PARAMETER: "column_major"}
    intended = solve(grid, settings)
    counterfactual = solve(grid, settings, track_used=False)
    info = analyze_input(grid)
    changed = sum(
        left != right
        for row_left, row_right in zip(intended, counterfactual, strict=True)
        for left, right in zip(row_left, row_right, strict=True)
    )
    return {
        "input": deepcopy(grid),
        "settings": settings,
        "program": program(settings),
        "output": intended,
        "counterfactual_program": (HOME / "column_major_reuse.rkt").read_text(encoding="utf-8"),
        "counterfactual_output": counterfactual,
        "ablation": "wrong_intermediate",
        "intermediate_value": {
            "used_state": "after the first frame, the first column-major crop value is unavailable",
            "first_source_bbox": info["column_major_first_bbox"],
            "changed_final_cells": changed,
        },
    }


def generate(seed: int, settings: dict[str, str], demos: int, queries: int) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    order = _setting(settings)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    chosen = {PARAMETER: order}
    train = []
    test = []
    for split, count in (("train", demos), ("test", queries)):
        destination = train if split == "train" else test
        for index in range(count):
            grid = _build_input(seed, split, index)
            destination.append({"input": grid, "output": solve(grid, chosen)})
    return {
        "train": train,
        "test": test,
        "program_solution": program(chosen),
        "settings": chosen,
        "seed": seed,
    }


def public_turn(episode: dict, query_index: int) -> dict:
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    train = episode.get("train") if isinstance(episode, dict) else None
    test = episode.get("test") if isinstance(episode, dict) else None
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train/test lists")
    if not 0 <= query_index < len(test):
        raise ValueError("query_index is outside the stored query prefix")
    return {
        "train": deepcopy(train),
        "test": [{"input": deepcopy(test[query_index]["input"])}],
    }


def public_turn_bytes(episode: dict, query_index: int) -> bytes:
    public = public_turn(episode, query_index)
    return (
        json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def public_turn_id(episode: dict, query_index: int) -> str:
    return hashlib.sha256(public_turn_bytes(episode, query_index)).hexdigest()
