"""Native nested-frame family with an input-derived legend anchor.

The canonical setting fills rings outer-to-inner with the left-to-right legend.
The alternate first measures every adjacent frame inset, selects the unique
widest one, and rotates the legend assignment so legend[0] colors the ring
immediately outside that gap.  The measured anchor is therefore required by
step B rather than being decorative metadata.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import json
from pathlib import Path
import random
from typing import Any, Callable

HOME = Path(__file__).resolve().parent
MODES = ("outer_to_inner", "widest_gap_anchor")
PROGRAMS = {
    "outer_to_inner": (HOME / "canonical.rkt").read_text(encoding="utf-8"),
    "widest_gap_anchor": (HOME / "widest_gap_anchor.rkt").read_text(encoding="utf-8"),
}
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
# (height, width, depth, widest-adjacent-gap index)
DEMO_SPECS = (
    (20, 21, 3, 1),
    (19, 22, 3, 0),
    (24, 25, 4, 2),
    (26, 27, 4, 1),
    (27, 24, 4, 0),
    (28, 29, 4, 2),
)
QUERY_SPECS = (
    (21, 24, 3, 1),
    (25, 28, 4, 0),
    (29, 27, 4, 2),
    (30, 30, 4, 1),
)


def _plain_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be a plain integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"ring_order"}:
        raise ValueError("settings must contain exactly ring_order")
    value = settings["ring_order"]
    if type(value) is not str or value not in MODES:
        raise ValueError("ring_order must be outer_to_inner or widest_gap_anchor")
    return value


def _components_of_8(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(1, h) for c in range(w) if grid[r][c] == 8}
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = [start]
        while queue:
            row, col = queue.popleft()
            for dr, dc in CARDINAL:
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
                    cells.append(nxt)
        components.append(sorted(cells))
    return components


def frame_boxes(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    boxes = []
    for cells in _components_of_8(grid):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        box = (min(rows), min(cols), max(rows), max(cols))
        r1, c1, r2, c2 = box
        if r2 - r1 < 2 or c2 - c1 < 2:
            raise ValueError("color-8 component is too small to be a frame")
        expected = {
            (row, col)
            for row in range(r1, r2 + 1)
            for col in range(c1, c2 + 1)
            if row in (r1, r2) or col in (c1, c2)
        }
        if set(cells) != expected:
            raise ValueError("color-8 component is not a complete rectangular border")
        boxes.append(box)
    boxes.sort(key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1), reverse=True)
    if len(boxes) < 2:
        raise ValueError("scene must contain at least two nested frames")
    for outer, inner in zip(boxes, boxes[1:], strict=False):
        if not (outer[0] < inner[0] < inner[2] < outer[2]
                and outer[1] < inner[1] < inner[3] < outer[3]):
            raise ValueError("frames must be strictly nested")
    return boxes


def gap_widths(grid: list[list[int]]) -> list[int]:
    boxes = frame_boxes(grid)
    return [
        min(
            inner[0] - outer[0],
            inner[1] - outer[1],
            outer[2] - inner[2],
            outer[3] - inner[3],
        )
        for outer, inner in zip(boxes, boxes[1:], strict=False)
    ]


def widest_gap_index(grid: list[list[int]]) -> int:
    gaps = gap_widths(grid)
    largest = max(gaps)
    if gaps.count(largest) != 1:
        raise ValueError("widest adjacent frame gap must be unique")
    return gaps.index(largest)


def _legend(grid: list[list[int]], depth: int | None = None) -> list[int]:
    values = [value for value in grid[0] if value != 0]
    if not values or len(values) != len(set(values)):
        raise ValueError("legend must contain distinct nonzero colors")
    if depth is not None and len(values) != depth:
        raise ValueError("legend length must equal frame depth")
    return values


def transform(
    grid: list[list[int]],
    mode: str,
    *,
    forced_anchor: int | None = None,
) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError("unknown ring order")
    boxes = frame_boxes(grid)
    legend = _legend(grid, len(boxes))
    if forced_anchor is not None:
        if type(forced_anchor) is not int or not 0 <= forced_anchor < len(boxes) - 1:
            raise ValueError("forced_anchor is outside the adjacent-gap range")
        anchor = forced_anchor
    elif mode == "widest_gap_anchor":
        anchor = widest_gap_index(grid)
    else:
        anchor = 0

    out = deepcopy(grid)
    for index, outer in enumerate(boxes):
        inner = boxes[index + 1] if index + 1 < len(boxes) else None
        color_index = index if mode == "outer_to_inner" else (index - anchor) % len(legend)
        color = legend[color_index]
        for row in range(outer[0] + 1, outer[2]):
            for col in range(outer[1] + 1, outer[3]):
                if inner and inner[0] <= row <= inner[2] and inner[1] <= col <= inner[3]:
                    continue
                out[row][col] = color
    return out


def _gap_schedule(depth: int, anchor: int) -> list[int]:
    if depth == 3:
        schedules = {0: [5, 2], 1: [2, 5]}
    elif depth == 4:
        schedules = {0: [5, 2, 3], 1: [2, 5, 3], 2: [2, 3, 5]}
    else:
        raise ValueError("depth must be 3 or 4")
    try:
        return schedules[anchor]
    except KeyError as exc:
        raise ValueError("anchor is invalid for depth") from exc


def _draw_frame(grid: list[list[int]], box: tuple[int, int, int, int]) -> None:
    r1, c1, r2, c2 = box
    for col in range(c1, c2 + 1):
        grid[r1][col] = 8
        grid[r2][col] = 8
    for row in range(r1, r2 + 1):
        grid[row][c1] = 8
        grid[row][c2] = 8


def build_input(seed: int, pair_index: int, spec: tuple[int, int, int, int]) -> list[list[int]]:
    height, width, depth, anchor = spec
    gaps = _gap_schedule(depth, anchor)
    minimum = 2 * sum(gaps) + 3
    if height - 1 < minimum or width < minimum:
        raise ValueError("canvas is too small for requested nested frames")
    rng = random.Random((seed * 1_000_003 + pair_index * 97_409 + height * 1_009 + width * 131) ^ 0x5E5205E54C96)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    # Keep all family legend colors distinct from the color-8 frame material;
    # production generation separately covers the canonical color-8 legend case.
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], depth)
    legend_columns = sorted(rng.sample(range(width), depth))
    for col, color in zip(legend_columns, colors, strict=True):
        grid[0][col] = color

    max_row_shrink = min(2, (height - 1) - minimum)
    max_col_shrink = min(2, width - minimum)
    row_shrink = rng.randint(0, max_row_shrink)
    col_shrink = rng.randint(0, max_col_shrink)
    outer_h = height - 1 - row_shrink
    outer_w = width - col_shrink
    top_choices = (1, height - outer_h)
    left_choices = (0, width - outer_w)
    top = top_choices[pair_index % 2]
    left = left_choices[(pair_index // 2) % 2]
    box = (top, left, top + outer_h - 1, left + outer_w - 1)
    boxes = [box]
    for gap in gaps:
        box = (box[0] + gap, box[1] + gap, box[2] - gap, box[3] - gap)
        boxes.append(box)
    for frame in boxes:
        _draw_frame(grid, frame)

    if frame_boxes(grid) != boxes:
        raise RuntimeError("generated frame geometry was not recovered exactly")
    if widest_gap_index(grid) != anchor:
        raise RuntimeError("generated widest-gap anchor does not match specification")
    if anchor != 0 and transform(grid, "outer_to_inner") == transform(grid, "widest_gap_anchor"):
        raise RuntimeError("nonzero-anchor scene does not distinguish declared settings")
    return grid


def program(settings: dict[str, Any]) -> str:
    return PROGRAMS[_mode(settings)]


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _plain_int("seed", seed, 0, 2**63 - 1)
    _plain_int("demos", demos, 2, 6)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    mode = _mode(settings)
    specs = list(DEMO_SPECS[:demos]) + list(QUERY_SPECS)
    inputs = [build_input(seed, index, spec) for index, spec in enumerate(specs)]
    keys = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    if len(keys) != len(set(keys)):
        raise RuntimeError("episode inputs must be distinct")
    pairs = [{"input": deepcopy(grid), "output": transform(grid, mode)} for grid in inputs]
    return {"train": pairs[:demos], "test": pairs[demos:], "program_solution": PROGRAMS[mode]}


def teaching_check(episode: dict[str, Any], selected_mode: str) -> dict[str, Any]:
    survivors = [
        mode
        for mode in MODES
        if all(transform(pair["input"], mode) == pair["output"] for pair in episode["train"])
    ]
    return {"selected_mode": selected_mode, "surviving_modes": survivors}


def _anchor_transform(grid: list[list[int]], anchor: int) -> list[list[int]]:
    return transform(grid, "widest_gap_anchor", forced_anchor=anchor)


def _narrowest_gap_anchor(grid: list[list[int]]) -> list[list[int]]:
    gaps = gap_widths(grid)
    return _anchor_transform(grid, gaps.index(min(gaps)))


def _reverse_outer_order(grid: list[list[int]]) -> list[list[int]]:
    boxes = frame_boxes(grid)
    legend = _legend(grid, len(boxes))
    out = deepcopy(grid)
    for index, outer in enumerate(boxes):
        inner = boxes[index + 1] if index + 1 < len(boxes) else None
        color = legend[-1 - index]
        for row in range(outer[0] + 1, outer[2]):
            for col in range(outer[1] + 1, outer[3]):
                if inner and inner[0] <= row <= inner[2] and inner[1] <= col <= inner[3]:
                    continue
                out[row][col] = color
    return out


def _all_first_color(grid: list[list[int]]) -> list[list[int]]:
    boxes = frame_boxes(grid)
    legend = _legend(grid, len(boxes))
    out = deepcopy(grid)
    for index, outer in enumerate(boxes):
        inner = boxes[index + 1] if index + 1 < len(boxes) else None
        for row in range(outer[0] + 1, outer[2]):
            for col in range(outer[1] + 1, outer[3]):
                if inner and inner[0] <= row <= inner[2] and inner[1] <= col <= inner[3]:
                    continue
                out[row][col] = legend[0]
    return out


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fixed_anchor_one": lambda grid: _anchor_transform(grid, 1),
    "narrowest_gap_anchor": _narrowest_gap_anchor,
    "reverse_outer_order": _reverse_outer_order,
    "all_first_color": _all_first_color,
}
