"""Color-to-axis role family for ARC task 6387de413b52.

The exact canonical setting uses color-2 object bounding-box rows and color-3
object bounding-box columns.  The alternate swaps those roles.  Step A computes
the two input-dependent axis sets; step B paints their Cartesian product cyan.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import find_root

TASK_ID = "6387de413b52"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
ROW_SOURCES = ("color2", "color3")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
Grid = list[list[int]]
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Six prefix-stable demonstrations and four query-bank scenes.
_PROFILES = (
    (12, 14, 2, 2),
    (14, 17, 2, 3),
    (16, 20, 3, 2),
    (18, 22, 3, 3),
    (20, 24, 4, 3),
    (24, 28, 4, 4),
    (8, 9, 2, 2),
    (22, 25, 3, 4),
    (27, 29, 4, 4),
    (30, 30, 4, 4),
)


def _setting(settings: dict[str, Any]) -> str:
    if (type(settings) is not dict or set(settings) != {"row_source"}
            or settings["row_source"] not in ROW_SOURCES):
        raise ValueError("Exactly row_source=color2|color3 is required")
    return settings["row_source"]


def _integer(value: Any, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an exact integer in {low}..{high}")
    return value


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def program(settings: dict[str, Any]) -> str:
    source = _setting(settings)
    return (HERE / ("canonical.rkt" if source == "color2" else "swapped.rkt")).read_text(encoding="utf-8")


def _validate_grid(grid: Grid) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact ARC colors")
    return len(grid), width


def components(grid: Grid) -> list[dict[str, Any]]:
    h, w = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            queue = deque([(row, col)])
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _DIR4:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append({"color": color, "cells": tuple(cells),
                           "bbox": (min(rows), min(cols), max(rows), max(cols))})
    return result


def _axis_values(records: Iterable[dict[str, Any]], color: int, axis: str) -> list[int]:
    values: set[int] = set()
    for record in records:
        if record["color"] != color:
            continue
        r0, c0, r1, c1 = record["bbox"]
        values.update(range(r0, r1 + 1) if axis == "rows" else range(c0, c1 + 1))
    return sorted(values)


def intermediate(grid: Grid, settings: dict[str, Any]) -> dict[str, Any]:
    source = _setting(settings)
    h, w = _validate_grid(grid)
    records = components(grid)
    row_color = 2 if source == "color2" else 3
    col_color = 3 if row_color == 2 else 2
    rows = _axis_values(records, row_color, "rows")
    cols = _axis_values(records, col_color, "cols")
    if not rows or not cols:
        raise ValueError("role grammar requires both colors to contribute axes")
    return {"row_source": source, "row_color": row_color, "col_color": col_color,
            "height": h, "width": w, "active_rows": rows, "active_cols": cols,
            "row_bboxes": [list(r["bbox"]) for r in records if r["color"] == row_color],
            "col_bboxes": [list(r["bbox"]) for r in records if r["color"] == col_color]}


def paint_intermediate(stage: dict[str, Any], *, value: int = 8, preserve_input: Grid | None = None,
                       union: bool = False) -> Grid:
    h, w = stage["height"], stage["width"]
    output = deepcopy(preserve_input) if preserve_input is not None else [[0] * w for _ in range(h)]
    rows, cols = set(stage["active_rows"]), set(stage["active_cols"])
    for r in range(h):
        for c in range(w):
            selected = (r in rows or c in cols) if union else (r in rows and c in cols)
            if selected:
                output[r][c] = value
    return output


def predict(grid: Grid, source_or_settings: str | dict[str, Any]) -> Grid:
    settings = ({"row_source": source_or_settings}
                if isinstance(source_or_settings, str) else source_or_settings)
    return paint_intermediate(intermediate(grid, settings))


def original_pairs() -> list[dict[str, Grid]]:
    records = []
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                records.append(row)
    pairs: list[dict[str, Grid]] = []
    for record in records:
        for split in ("train", "test"):
            values = record.get(split, [])
            if isinstance(values, dict):
                values = [values]
            for pair in values:
                if isinstance(pair, dict) and "output" in pair:
                    pairs.append({"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])})
    return pairs


def _blob_cells(height: int, width: int, variant: int, dense: bool) -> tuple[tuple[int, int], ...]:
    if dense or variant % 4 == 2:
        cells = {(r, c) for r in range(height) for c in range(width)
                 if r in (0, height - 1) or c in (0, width - 1)}
    elif variant % 4 == 0:
        cells = {(0, c) for c in range(width)} | {(r, 0) for r in range(height)}
    elif variant % 4 == 1:
        cells = {(height - 1, c) for c in range(width)} | {(r, width - 1) for r in range(height)}
    else:
        cells = {(0, c) for c in range(width)} | {(r, width - 1) for r in range(height)} | {
            (height - 1, c) for c in range(width)}
    if variant & 4:
        cells = {(r, width - 1 - c) for r, c in cells}
    return tuple(sorted(cells))


def _spaced_tops(total: int, heights: list[int], phase: int) -> list[int]:
    blanks = total - sum(heights)
    if blanks < len(heights) - 1:
        raise ValueError("vertical profile is overfull")
    gaps = [0] * (len(heights) + 1)
    for i in range(blanks):
        gaps[(i + phase) % len(gaps)] += 1
    tops = []
    cursor = gaps[0]
    for i, height in enumerate(heights):
        tops.append(cursor)
        cursor += height + gaps[i + 1]
    return tops


def _scene(seed: int, index: int) -> Grid:
    h, w, n2, n3 = _PROFILES[index]
    rng = _rng(seed, f"scene:{index}")
    dense = index >= 8
    edge_width = 2 if w <= 10 else 3 if w < 23 else (7 if dense else 4)
    h2 = [min(h // 3, (4 if dense else 2) + ((index + i) % 3)) for i in range(n2)]
    w2 = [max(2, edge_width - (i % 2)) for i in range(n2)]
    tops2 = _spaced_tops(h, h2, phase=0)

    central_left = edge_width + 1
    right_edge_start = w - edge_width
    central_right = right_edge_start - 2
    available = central_right - central_left + 1
    if available < 3:
        raise ValueError("central role zone is too narrow")
    h3 = [min(4 if dense else 3, 2 + ((index + i + 1) % 2)) for i in range(n3)]
    w3 = [min(available, (5 if dense else 3) + ((index + i) % 3)) for i in range(n3)]
    tops3 = _spaced_tops(h, h3, phase=2)

    grid = [[0] * w for _ in range(h)]
    occupied: set[tuple[int, int]] = set()

    def place(color: int, top: int, left: int, bh: int, bw: int, variant: int) -> None:
        cells = _blob_cells(bh, bw, variant, dense)
        absolute = {(top + r, left + c) for r, c in cells}
        if any(not (0 <= r < h and 0 <= c < w) for r, c in absolute):
            raise ValueError("blob leaves canvas")
        if occupied & absolute:
            raise ValueError("blob overlap")
        for r, c in absolute:
            grid[r][c] = color
        occupied.update(absolute)

    for i, (top, bh, bw) in enumerate(zip(tops2, h2, w2)):
        left = 0 if i % 2 == 0 else w - bw
        place(2, top, left, bh, bw, rng.randrange(8))

    for i, (top, bh, bw) in enumerate(zip(tops3, h3, w3)):
        choices = (central_left, central_right - bw + 1,
                   central_left + max(0, (available - bw) // 2))
        left = choices[(i + index) % len(choices)]
        place(3, top, left, bh, bw, rng.randrange(8))

    records = components(grid)
    if sum(record["color"] == 2 for record in records) != n2:
        raise ValueError("color-2 components merged")
    if sum(record["color"] == 3 for record in records) != n3:
        raise ValueError("color-3 components merged")
    if predict(grid, "color2") == predict(grid, "color3"):
        raise ValueError("profile failed to distinguish axis roles")
    return grid


@lru_cache(maxsize=32)
def _bank(seed: int) -> tuple[Grid, ...]:
    return tuple(_scene(seed, index) for index in range(len(_PROFILES)))


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    source = _setting(settings)
    _integer(demos, MIN_DEMOS, MAX_DEMOS, "demos")
    _integer(queries, MIN_QUERIES, MAX_QUERIES, "queries")
    scenes = _bank(seed)
    order = list(range(6, 10))
    _rng(seed, "presentation").shuffle(order)
    train_indices = list(range(demos))
    test_indices = order[:queries]
    chosen = [scenes[i] for i in train_indices + test_indices]
    if len({json.dumps(grid, separators=(",", ":")) for grid in chosen}) != len(chosen):
        raise ValueError("episode inputs must be distinct")
    def pair(i: int) -> dict[str, Grid]:
        grid = scenes[i]
        return {"input": grid, "output": predict(grid, source)}
    return deepcopy({"train": [pair(i) for i in train_indices],
                     "test": [pair(i) for i in test_indices],
                     "program_solution": program(settings)})


def public_view(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return deepcopy({"train": [{"input": p["input"], "output": p["output"]}
                                for p in episode["train"]],
                     "test": [{"input": episode["test"][query_index]["input"]}]})


def describe_scene(grid: Grid) -> dict[str, Any]:
    records = components(grid)
    canonical = intermediate(grid, {"row_source": "color2"})
    swapped = intermediate(grid, {"row_source": "color3"})
    return {"color2_components": sum(r["color"] == 2 for r in records),
            "color3_components": sum(r["color"] == 3 for r in records),
            "occupied": sum(value != 0 for row in grid for value in row),
            "canonical_rows": len(canonical["active_rows"]),
            "canonical_cols": len(canonical["active_cols"]),
            "canonical_cells": len(canonical["active_rows"]) * len(canonical["active_cols"]),
            "swapped_rows": len(swapped["active_rows"]),
            "swapped_cols": len(swapped["active_cols"]),
            "swapped_cells": len(swapped["active_rows"]) * len(swapped["active_cols"])}


def _stage(records: list[dict[str, Any]], h: int, w: int, row_color: int, col_color: int,
           *, occupied_only: bool = False, first_only: bool = False,
           global_bbox: bool = False) -> dict[str, Any]:
    row_records = [r for r in records if r["color"] == row_color]
    col_records = [r for r in records if r["color"] == col_color]
    if first_only:
        row_records, col_records = row_records[:1], col_records[:1]
    if occupied_only:
        rows = sorted({r for record in row_records for r, _ in record["cells"]})
        cols = sorted({c for record in col_records for _, c in record["cells"]})
    else:
        rows = _axis_values(row_records, row_color, "rows")
        cols = _axis_values(col_records, col_color, "cols")
    if global_bbox:
        rows = list(range(min(rows), max(rows) + 1))
        cols = list(range(min(cols), max(cols) + 1))
    return {"height": h, "width": w, "active_rows": rows, "active_cols": cols}


def rival_predictions(grid: Grid, intended: str) -> dict[str, Grid]:
    h, w = _validate_grid(grid)
    records = components(grid)
    row_color = 2 if intended == "color2" else 3
    col_color = 3 if row_color == 2 else 2
    intended_stage = _stage(records, h, w, row_color, col_color)
    opposite_stage = _stage(records, h, w, col_color, row_color)
    all_rows = sorted({x for color in (2, 3) for x in _axis_values(records, color, "rows")})
    all_cols = sorted({x for color in (2, 3) for x in _axis_values(records, color, "cols")})
    same_row = _stage(records, h, w, row_color, row_color)
    same_col = _stage(records, h, w, col_color, col_color)
    return {
        "opposite_setting": paint_intermediate(opposite_stage),
        "occupied_cells_only": paint_intermediate(_stage(records, h, w, row_color, col_color, occupied_only=True)),
        "first_blob_only": paint_intermediate(_stage(records, h, w, row_color, col_color, first_only=True)),
        "global_bbox_ranges": paint_intermediate(_stage(records, h, w, row_color, col_color, global_bbox=True)),
        "ignore_color_roles": paint_intermediate({"height": h, "width": w, "active_rows": all_rows, "active_cols": all_cols}),
        "row_color_for_both_axes": paint_intermediate(same_row),
        "col_color_for_both_axes": paint_intermediate(same_col),
        "union_instead_of_cross": paint_intermediate(intended_stage, union=True),
        "preserve_input": paint_intermediate(intended_stage, preserve_input=grid),
        "paint_red": paint_intermediate(intended_stage, value=2),
        "paint_green": paint_intermediate(intended_stage, value=3),
    }
