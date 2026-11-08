"""Native two-setting crop-and-stamp family for a90d16507995.

``stamp_only`` is the byte-exact canonical rule. ``stamp_majority_frame``
first performs the canonical relocation, then derives the unique majority color
of the stamped crop and draws a one-cell exterior frame at the destination.
"""
from __future__ import annotations

from copy import deepcopy
from collections import Counter
import hashlib
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "a90d16507995"
MODES = ("stamp_only", "stamp_majority_frame")
DEFAULT_MODE = "stamp_only"
HERE = Path(__file__).resolve().parent


def _strict_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return mode


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    mode = _strict_settings(settings)
    name = "canonical.rkt" if mode == "stamp_only" else "stamp_majority_frame.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}|stamp-family-v1".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _mask(height: int, width: int, rng: random.Random, *, dense=False) -> set[tuple[int, int]]:
    cells = {(0, c) for c in range(width)} | {(r, 0) for r in range(height)}
    for r in range(1, height):
        minimum = max(2, width - (r % 3) - (0 if dense else 1))
        run = rng.randint(minimum, width)
        cells.update((r, c) for c in range(run))
        if not dense and run >= 4 and r % 2:
            # A right-edge notch keeps every row left-connected to column 0.
            # Interior holes can strand the row suffix when adjacent rows are shorter.
            cells.discard((r, run - 1))
    return cells


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = list(seen)
    for r, c in queue:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = r + dr, c + dc
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _paint_source(grid, top, left, mask, colors, rng):
    ordered = sorted(mask)
    majority, top_left, accent = colors
    assignments = {}
    assignments[(0, 0)] = top_left
    remaining = [cell for cell in ordered if cell != (0, 0)]
    majority_count = max(len(remaining) // 2 + 1, 2)
    for index, cell in enumerate(remaining):
        if index < majority_count:
            assignments[cell] = majority
        else:
            assignments[cell] = accent if index % 2 == 0 else top_left
    # Keep the majority unique after all assignments.
    counts = Counter(assignments.values())
    if counts[majority] <= max(v for k, v in counts.items() if k != majority):
        for cell in reversed(remaining):
            assignments[cell] = majority
            counts = Counter(assignments.values())
            if counts[majority] > max(v for k, v in counts.items() if k != majority):
                break
    for (r, c), color in assignments.items():
        grid[top + r][left + c] = color


def _ordinary_scene(seed: int, split: str, index: int) -> list[list[int]]:
    rng = _rng(seed, split, index)
    bh = 4 + ((index + (0 if split == "train" else 1)) % 3)
    bw = 5 + ((index + seed) % 3)
    # Size the canvas from the crop so source and framed destination always fit
    # as separated regions; fixed 12..17 canvases fail for the largest crops.
    h = 2 * bh + 5 + rng.randrange(3)
    w = 2 * bw + 5 + rng.randrange(3)
    mask = _mask(bh, bw, rng)
    assert _connected(mask)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], 3)
    source_top = rng.randrange(0, max(1, h // 3 - bh + 2))
    source_left = rng.randrange(0, max(1, w // 3 - bw + 2))
    marker_top_min = max(h // 2, source_top + bh + 1)
    marker_left_min = max(w // 2, source_left + bw + 1)
    marker_r = rng.randint(marker_top_min, h - bh - 1)
    marker_c = rng.randint(marker_left_min, w - bw - 1)
    grid = [[0] * w for _ in range(h)]
    _paint_source(grid, source_top, source_left, mask, colors, rng)
    grid[marker_r][marker_c] = 9
    analyze(grid)
    return grid


def _stress_scene(seed: int) -> list[list[int]]:
    rng = _rng(seed, "test", 3)
    h = w = 30
    bh = bw = 12
    mask = _mask(bh, bw, rng, dense=True)
    # Ensure a substantial but not rectangular connected source.
    for r in range(2, 11, 3):
        mask.discard((r, 9))
        mask.discard((r, 10))
    assert _connected(mask) and len(mask) >= 80
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], 3)
    grid = [[0] * w for _ in range(h)]
    _paint_source(grid, 0, 0, mask, colors, rng)
    grid[16][16] = 9
    analyze(grid)
    return grid


def scene(seed: int, split: str, index: int) -> list[list[int]]:
    _strict_int("seed", seed, 0, 2**63 - 1)
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    limit = 6 if split == "train" else 4
    _strict_int("index", index, 0, limit - 1)
    return _stress_scene(seed) if split == "test" and index == 3 else _ordinary_scene(seed, split, index)


def analyze(grid: Any) -> dict[str, Any]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be nonempty")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact ARC colors")
    h = len(grid)
    markers = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    if len(markers) != 1:
        raise ValueError("need exactly one color-9 marker")
    source = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)]
    if len(source) < 3:
        raise ValueError("need a substantive source blob")
    source_set = set(source)
    if not _connected(source_set):
        raise ValueError("source must be 4-connected")
    r0, r1 = min(r for r, _ in source), max(r for r, _ in source)
    c0, c1 = min(c for _, c in source), max(c for _, c in source)
    crop = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    mr, mc = markers[0]
    bh, bw = len(crop), len(crop[0])
    if not (mr >= 1 and mc >= 1 and mr + bh < h and mc + bw < width):
        raise ValueError("destination needs a one-cell frame margin")
    values = [v for row in crop for v in row if v != 0]
    counts = Counter(values)
    ordered = sorted(counts, key=lambda color: (-counts[color], color))
    if len(ordered) < 2 or counts[ordered[0]] == counts[ordered[1]]:
        raise ValueError("source needs a unique majority color")
    if crop[0][0] == 0 or crop[0][0] == ordered[0]:
        raise ValueError("top-left source color must be a non-majority witness")
    return {
        "marker": [mr, mc],
        "source_cells": source,
        "source_bbox": [r0, c0, r1, c1],
        "crop": crop,
        "crop_height": bh,
        "crop_width": bw,
        "color_counts": dict(counts),
        "majority_color": ordered[0],
    }


def _stamp(grid: Any, *, anchor="top_left", mirror=False) -> list[list[int]]:
    info = analyze(grid)
    crop = deepcopy(info["crop"])
    if mirror:
        crop = [list(reversed(row)) for row in crop]
    mr, mc = info["marker"]
    if anchor == "center":
        mr -= len(crop) // 2
        mc -= len(crop[0]) // 2
    elif anchor == "bottom_right":
        mr -= len(crop) - 1
        mc -= len(crop[0]) - 1
    output = [[0] * len(grid[0]) for _ in grid]
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            rr, cc = mr + r, mc + c
            if value and 0 <= rr < len(output) and 0 <= cc < len(output[0]):
                output[rr][cc] = value
    return output


def _frame(stamped, marker, bh, bw, color):
    output = deepcopy(stamped)
    mr, mc = marker
    top, left, bottom, right = mr - 1, mc - 1, mr + bh, mc + bw
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            if r in (top, bottom) or c in (left, right):
                output[r][c] = color
    return output


def solve(grid: Any, mode: str) -> list[list[int]]:
    info = analyze(grid)
    stamped = _stamp(grid)
    if mode == "stamp_only":
        return stamped
    if mode == "stamp_majority_frame":
        return _frame(stamped, info["marker"], info["crop_height"], info["crop_width"], info["majority_color"])
    raise ValueError(f"unknown mode: {mode}")


def solve_wrong_frame_color(grid: Any) -> list[list[int]]:
    info = analyze(grid)
    return _frame(_stamp(grid), info["marker"], info["crop_height"], info["crop_width"], info["crop"][0][0])


def _copy_not_move(grid):
    output = deepcopy(grid)
    stamped = _stamp(grid)
    for r, row in enumerate(stamped):
        for c, value in enumerate(row):
            if value:
                output[r][c] = value
    return output


def _least_frequency_frame(grid):
    info = analyze(grid)
    least = min(info["color_counts"], key=lambda color: (info["color_counts"][color], color))
    return _frame(_stamp(grid), info["marker"], info["crop_height"], info["crop_width"], least)


def _source_location_frame(grid):
    info = analyze(grid)
    output = _stamp(grid)
    r0, c0, r1, c1 = info["source_bbox"]
    top, left, bottom, right = max(0, r0 - 1), max(0, c0 - 1), min(len(grid) - 1, r1 + 1), min(len(grid[0]) - 1, c1 + 1)
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            if r in (top, bottom) or c in (left, right):
                output[r][c] = info["majority_color"]
    return output


def audit_rivals(mode: str) -> dict[str, Callable[[Any], list[list[int]]]]:
    if mode == "stamp_only":
        return {
            "copy_source_instead_of_move": _copy_not_move,
            "marker_is_center": lambda grid: _stamp(grid, anchor="center"),
            "marker_is_bottom_right": lambda grid: _stamp(grid, anchor="bottom_right"),
        }
    if mode == "stamp_majority_frame":
        return {
            "no_frame": lambda grid: _stamp(grid),
            "frame_uses_top_left_color": solve_wrong_frame_color,
            "frame_uses_least_frequent_color": _least_frequency_frame,
            "frame_at_source_location": _source_location_frame,
        }
    raise ValueError(mode)


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, 2**63 - 1)
    demos = _strict_int("demos", demos, 2, 6)
    queries = _strict_int("queries", queries, 1, 4)
    mode = _strict_settings(settings)
    train = []
    for index in range(demos):
        grid = scene(seed, "train", index)
        train.append({"input": grid, "output": solve(grid, mode)})
    test = []
    for index in range(queries):
        grid = scene(seed, "test", index)
        test.append({"input": grid, "output": solve(grid, mode)})
    return {"train": train, "test": test, "program_solution": program({"mode": mode})}
