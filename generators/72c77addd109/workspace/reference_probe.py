"""Independent oracle and distribution observations for task 72c77addd109.

This module is reviewer test tooling.  The selected Racket program remains label
and rule authority; these functions independently encode the geometry exercised
by the task-local regression suite.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
TASK = "72c77addd109"


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def components(grid: list[list[int]]) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[dict] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append({"color": color, "cells": tuple(sorted(cells))})
    return found


def bbox(obj: dict) -> tuple[int, int, int, int]:
    rows = [r for r, _ in obj["cells"]]
    cols = [c for _, c in obj["cells"]]
    return min(rows), min(cols), max(rows), max(cols)


def dims(obj: dict) -> tuple[int, int]:
    r1, c1, r2, c2 = bbox(obj)
    return r2 - r1 + 1, c2 - c1 + 1


def is_frame(obj: dict) -> bool:
    r1, c1, r2, c2 = bbox(obj)
    h, w = r2 - r1 + 1, c2 - c1 + 1
    if h < 3 or w < 3:
        return False
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return set(obj["cells"]) == border


def is_filled_rectangle(obj: dict) -> bool:
    r1, c1, r2, c2 = bbox(obj)
    return set(obj["cells"]) == {
        (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
    }


def split_objects(grid: list[list[int]]) -> tuple[list[dict], list[dict]]:
    objects = components(grid)
    frames = [obj for obj in objects if is_frame(obj)]
    solids = [obj for obj in objects if not is_frame(obj)]
    return frames, solids


def frame_interior_area(obj: dict) -> int:
    h, w = dims(obj)
    return (h - 2) * (w - 2)


def reading_key(obj: dict) -> tuple[int, int]:
    r1, c1, _, _ = bbox(obj)
    return r1, c1


def render(grid: list[list[int]], solid_key: Callable[[dict], object]) -> list[list[int]]:
    frames, solids = split_objects(grid)
    frames = sorted(frames, key=frame_interior_area)
    solids = sorted(solids, key=solid_key)
    out = [[0] * len(grid[0]) for _ in grid]
    for frame in frames:
        for r, c in frame["cells"]:
            out[r][c] = frame["color"]
    for solid, frame in zip(solids, frames):
        sr1, sc1, sr2, sc2 = bbox(solid)
        fr1, fc1, fr2, fc2 = bbox(frame)
        sh, sw = sr2 - sr1 + 1, sc2 - sc1 + 1
        fh, fw = fr2 - fr1 + 1, fc2 - fc1 + 1
        top = fr1 + (fh - sh) // 2
        left = fc1 + (fw - sw) // 2
        for r, c in solid["cells"]:
            out[top + r - sr1][left + c - sc1] = solid["color"]
    return out


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    return render(grid, lambda obj: len(obj["cells"]))


def reading_order_rival(grid: list[list[int]]) -> list[list[int]]:
    return render(grid, reading_key)


def color_order_rival(grid: list[list[int]]) -> list[list[int]]:
    return render(grid, lambda obj: obj["color"])


def observed(grid: list[list[int]]) -> dict[str, int | str]:
    frames, solids = split_objects(grid)
    by_frame_area = sorted(frames, key=frame_interior_area)
    by_solid_area = sorted(solids, key=lambda obj: len(obj["cells"]))
    frame_reading = sorted(frames, key=reading_key)
    solid_reading = sorted(solids, key=reading_key)
    rectangular = [is_filled_rectangle(obj) for obj in solids]
    if all(rectangular):
        style = "rectangles"
    elif not any(rectangular):
        style = "irregular"
    else:
        style = "mixed"
    solid_colors = {obj["color"] for obj in solids}
    frame_colors = {obj["color"] for obj in frames}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "solid_style": style,
        "solid_rank_order": "ascending" if solid_reading == by_solid_area else "descending",
        "frame_rank_order": "ascending" if frame_reading == by_frame_area else "descending",
        "solid_color_order": (
            "ascending"
            if [obj["color"] for obj in by_solid_area] == sorted(solid_colors)
            else "descending"
        ),
        "palette_kind": (
            "canonical"
            if solid_colors == {2, 5} and frame_colors == {7, 8}
            else "varied"
        ),
    }


def has_border_overwrite(grid: list[list[int]]) -> bool:
    frames, solids = split_objects(grid)
    frames = sorted(frames, key=frame_interior_area)
    solids = sorted(solids, key=lambda obj: len(obj["cells"]))
    for frame, solid in zip(frames, solids):
        fh, fw = dims(frame)
        sh, sw = dims(solid)
        if sh > fh - 2 or sw > fw - 2:
            return True
    return False


def changed_cells(a: list[list[int]], b: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]
