"""Native size-rank and dominant-axis family for task 2f8ecb96521c.

The canonical program assigns interior colors by increasing object area.  The
second fixed setting reverses that rank.  The sequential ``dominant_axis``
setting first compares the two rectangle-center separations to derive a row or
column intermediate, then consumes that axis to order the rectangles before the
canonical interior recoloring step.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "2f8ecb96521c"
PARAMETER = "rank_order"
MODES = ("small_to_large", "large_to_small", "dominant_axis")
DEFAULT = {PARAMETER: "small_to_large"}
HERE = Path(__file__).resolve().parent
_ASCENDING_FRAGMENT = "(sort-by (objects grid 0) obj-size)"
_DESCENDING_FRAGMENT = "(reverse (sort-by (objects grid 0) obj-size))"
_DOMINANT_EXPRESSION = """(let* ((raw-objs (objects grid 0))
             (a (first raw-objs))
             (b (second raw-objs))
             (row-distance
               (abs (- (+ (obj-r1 a) (obj-r2 a))
                       (+ (obj-r1 b) (obj-r2 b)))))
             (col-distance
               (abs (- (+ (obj-c1 a) (obj-c2 a))
                       (+ (obj-c1 b) (obj-c2 b)))))
             (row-axis (> row-distance col-distance)))
        (sort raw-objs
              (lambda (x y)
                (if row-axis
                    (if (= (obj-r1 x) (obj-r1 y))
                        (< (obj-c1 x) (obj-c1 y))
                        (< (obj-r1 x) (obj-r1 y)))
                    (if (= (obj-c1 x) (obj-c1 y))
                        (< (obj-r1 x) (obj-r1 y))
                        (< (obj-c1 x) (obj-c1 y)))))))"""

RIVALS = MODES + (
    "top_to_bottom",
    "left_to_right",
    "perpendicular_axis",
    "dominant_axis_reverse",
    "nearest_origin",
    "row_major",
)

# height, width, small rectangle (r,c,h,w), large rectangle, expected axis,
# expected first role under dominant-axis ordering.
DEMO_SPECS = (
    (10, 16, (5, 1, 3, 4), (0, 10, 5, 5), "column", "small"),
    (16, 12, (11, 1, 3, 4), (1, 6, 5, 5), "row", "large"),
    (18, 14, (1, 8, 4, 3), (11, 1, 5, 6), "row", "small"),
    (18, 20, (1, 15, 3, 4), (8, 1, 6, 5), "column", "large"),
    (22, 20, (16, 1, 4, 5), (0, 11, 7, 6), "row", "large"),
    (24, 26, (15, 0, 5, 4), (1, 18, 7, 7), "column", "small"),
)
QUERY_SPECS = (
    (12, 18, (8, 0, 3, 4), (0, 12, 5, 6), "column", "small"),
    (18, 14, (15, 0, 3, 4), (0, 8, 6, 6), "row", "large"),
    (25, 27, (16, 0, 5, 5), (1, 18, 7, 8), "column", "small"),
    (30, 30, (17, 0, 13, 14), (0, 16, 14, 14), "row", "large"),
)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must contain exactly rank_order")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"rank_order must be one of {MODES}")
    return mode


def _canonical() -> str:
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


def program(settings: dict[str, str]) -> str:
    mode = _mode(settings)
    canonical = _canonical()
    if canonical.count(_ASCENDING_FRAGMENT) != 1:
        raise ValueError("canonical rank-order fragment drifted")
    if mode == "small_to_large":
        return canonical
    replacement = _DESCENDING_FRAGMENT if mode == "large_to_small" else _DOMINANT_EXPRESSION
    return canonical.replace(_ASCENDING_FRAGMENT, replacement, 1)


def counterfactual_program(force_axis: str) -> str:
    if force_axis not in ("row", "column"):
        raise ValueError("force_axis must be row or column")
    source = program({PARAMETER: "dominant_axis"})
    anchor = "(row-axis (> row-distance col-distance))"
    replacement = f"(row-axis {'#t' if force_axis == 'row' else '#f'})"
    if source.count(anchor) != 1:
        raise ValueError("dominant-axis anchor drifted")
    return source.replace(anchor, replacement, 1)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not 3 <= len(grid) <= 30:
        raise ValueError("grid must have 3..30 rows")
    if type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 3..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or value not in (0, 4) for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular and contain only exact colors 0 and 4")
    return len(grid), width


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for sr in range(height):
        for sc in range(width):
            if grid[sr][sc] != 4 or (sr, sc) in seen:
                continue
            seen.add((sr, sc))
            pending = [(sr, sc)]
            cells: list[tuple[int, int]] = []
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 4
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            result.append(sorted(cells))
    return result


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    components = _components(grid)
    if len(components) != 2:
        raise ValueError("exactly two color-4 rectangles are required")
    objects: list[dict[str, Any]] = []
    for cells in components:
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        height, width = r2 - r1 + 1, c2 - c1 + 1
        if height < 3 or width < 3 or len(cells) != height * width:
            raise ValueError("each object must be a solid rectangle with nonempty interior")
        objects.append(
            {
                "cells": cells,
                "area": len(cells),
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
                "center_row2": r1 + r2,
                "center_col2": c1 + c2,
            }
        )
    if objects[0]["area"] == objects[1]["area"]:
        raise ValueError("rectangle areas must be distinct")
    row_distance = abs(objects[0]["center_row2"] - objects[1]["center_row2"])
    col_distance = abs(objects[0]["center_col2"] - objects[1]["center_col2"])
    if row_distance == col_distance:
        raise ValueError("dominant center-separation axis must be unique")
    axis = "row" if row_distance > col_distance else "column"
    axis_key = (
        (lambda obj: (obj["r1"], obj["c1"]))
        if axis == "row"
        else (lambda obj: (obj["c1"], obj["r1"]))
    )
    ordered = sorted(objects, key=axis_key)
    smaller = min(objects, key=lambda obj: obj["area"])
    return {
        "objects": objects,
        "areas": [obj["area"] for obj in objects],
        "row_distance": row_distance,
        "column_distance": col_distance,
        "dominant_axis": axis,
        "axis_order": ordered,
        "axis_first_is_small": ordered[0] is smaller,
    }


def _ordered_objects(grid: list[list[int]], mode: str) -> list[dict[str, Any]]:
    info = analyze(grid)
    objects = info["objects"]
    if mode == "small_to_large":
        return sorted(objects, key=lambda obj: obj["area"])
    if mode == "large_to_small":
        return sorted(objects, key=lambda obj: -obj["area"])
    if mode == "dominant_axis":
        return list(info["axis_order"])
    if mode == "top_to_bottom":
        return sorted(objects, key=lambda obj: (obj["r1"], obj["c1"]))
    if mode == "left_to_right":
        return sorted(objects, key=lambda obj: (obj["c1"], obj["r1"]))
    if mode == "perpendicular_axis":
        key = (
            (lambda obj: (obj["c1"], obj["r1"]))
            if info["dominant_axis"] == "row"
            else (lambda obj: (obj["r1"], obj["c1"]))
        )
        return sorted(objects, key=key)
    if mode == "dominant_axis_reverse":
        return list(reversed(info["axis_order"]))
    if mode == "nearest_origin":
        return sorted(objects, key=lambda obj: (obj["r1"] + obj["c1"], obj["r1"], obj["c1"]))
    if mode == "row_major":
        return sorted(objects, key=lambda obj: (obj["r1"], obj["c1"]))
    raise ValueError(f"unknown rank claim: {mode!r}")


def claim(grid: list[list[int]], mode: str) -> list[list[int]]:
    if type(mode) is not str or mode not in RIVALS:
        raise ValueError(f"unknown rank claim: {mode!r}")
    ordered = _ordered_objects(grid, mode)
    out = deepcopy(grid)
    for color, obj in enumerate(ordered, start=1):
        for r in range(obj["r1"] + 1, obj["r2"]):
            for c in range(obj["c1"] + 1, obj["c2"]):
                if grid[r][c] == 4:
                    out[r][c] = color
    return out


def _scene(
    seed: int,
    stream: str,
    spec: tuple[
        int,
        int,
        tuple[int, int, int, int],
        tuple[int, int, int, int],
        str,
        str,
    ],
) -> list[list[int]]:
    height, width, small, large, expected_axis, expected_first = spec
    digest = hashlib.sha256(f"{TASK_ID}:native-v3:{seed}:{stream}".encode("utf-8")).digest()
    rects = (small, large)
    min_r = min(rect[0] for rect in rects)
    max_r = max(rect[0] + rect[2] for rect in rects)
    min_c = min(rect[1] for rect in rects)
    max_c = max(rect[1] + rect[3] for rect in rects)
    row_low, row_high = -min_r, height - max_r
    col_low, col_high = -min_c, width - max_c
    row_shift = row_low + digest[0] % (row_high - row_low + 1)
    col_shift = col_low + digest[1] % (col_high - col_low + 1)
    small = (small[0] + row_shift, small[1] + col_shift, small[2], small[3])
    large = (large[0] + row_shift, large[1] + col_shift, large[2], large[3])
    grid = [[0] * width for _ in range(height)]
    for r, c, rh, rw in (small, large):
        if not (0 <= r and 0 <= c and r + rh <= height and c + rw <= width):
            raise ValueError("rectangle lies outside scene")
        for rr in range(r, r + rh):
            for cc in range(c, c + rw):
                if grid[rr][cc] != 0:
                    raise ValueError("rectangles overlap")
                grid[rr][cc] = 4
    info = analyze(grid)
    first_role = "small" if info["axis_first_is_small"] else "large"
    if info["dominant_axis"] != expected_axis or first_role != expected_first:
        raise RuntimeError("constructed scene violated dominant-axis profile")
    return grid


def teaching_check(episode: dict[str, Any]) -> list[dict[str, Any]]:
    selected = _mode(episode.get("settings"))
    findings: list[dict[str, Any]] = []
    for rival in RIVALS:
        if rival == selected:
            continue
        fits = all(claim(pair["input"], rival) == pair["output"] for pair in episode["train"])
        if not fits:
            continue
        disagree = [
            index
            for index, pair in enumerate(episode["test"])
            if claim(pair["input"], rival) != pair["output"]
        ]
        if disagree:
            findings.append({"rival": rival, "query_indices": disagree})
    return findings


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    mode = _mode(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")

    def pair(spec, stream):
        grid = _scene(seed, stream, spec)
        return {"input": grid, "output": claim(grid, mode)}

    episode = {
        "train": [pair(spec, f"demo:{index}") for index, spec in enumerate(DEMO_SPECS[:demos])],
        "test": [pair(spec, f"query:{index}") for index, spec in enumerate(QUERY_SPECS[:queries])],
        "program_solution": program(settings),
        "settings": dict(settings),
    }
    episode["certificate"] = {
        "finite_rivals": list(RIVALS),
        "findings": teaching_check(episode),
    }
    return episode


def public_turn_bytes(episode: dict[str, Any], index: int = 0) -> bytes:
    if type(index) is not int or not 0 <= index < len(episode.get("test", [])):
        raise ValueError("query index out of range")
    public = {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][index]["input"])}],
    }
    return (json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
