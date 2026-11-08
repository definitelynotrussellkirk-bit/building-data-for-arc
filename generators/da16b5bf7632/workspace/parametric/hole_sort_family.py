"""Source-bound hole-count sort family for task da16b5bf7632.

The canonical setting sorts tight component crops by enclosed-hole count
(descending) with source reading-order ties.  The alternative reverses only the
hole-count direction.  Input sampling is independent of the private setting and
includes ties, sparse boxes, source-order decoys, boundary contacts, and a
substantive 30x30 case.
"""
from __future__ import annotations

import json
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "da16b5bf7632"
HOME = Path(__file__).resolve().parent
SORT_DIRECTIONS = ("most_holes_first", "fewest_holes_first")

Shape = tuple[tuple[int, int], ...]


def _rectangle_frame(height: int, width: int) -> Shape:
    return tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    )


def _partition_frame(height: int, holes: int) -> Shape:
    width = 2 * holes + 1
    return tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col % 2 == 0
    )


_SHAPES: dict[str, Shape] = {
    "dot": ((0, 0),),
    "l3": ((0, 0), (1, 0), (1, 1)),
    "t4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "z4": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "solid_2x3": tuple((r, c) for r in range(2) for c in range(3)),
    "solid4": tuple((r, c) for r in range(4) for c in range(4)),
    "frame3": _rectangle_frame(3, 3),
    "frame4": _rectangle_frame(4, 4),
    "frame3x4": _rectangle_frame(3, 4),
    "double3x5": _partition_frame(3, 2),
    "double4x5": _partition_frame(4, 2),
    "triple3x7": _partition_frame(3, 3),
    "triple4x7": _partition_frame(4, 3),
}

# Names are deliberately in neither ascending nor descending hole order.
_DEMO_PROFILES = (
    (12, 20, ("frame4", "triple3x7", "solid4", "double3x5")),
    (14, 22, ("double4x5", "frame3", "triple4x7", "t4", "dot")),
    (16, 24, ("frame3x4", "solid_2x3", "double3x5", "triple3x7", "frame3")),
    (18, 24, ("triple4x7", "z4", "frame4", "double4x5", "dot")),
    (20, 26, ("double3x5", "frame3", "l3", "triple3x7", "frame4", "dot")),
    (22, 28, ("frame4", "double4x5", "t4", "triple4x7", "frame3", "solid_2x3")),
)
_QUERY_PROFILES = (
    (11, 18, ("triple3x7", "frame3", "l3", "double3x5")),
    (18, 23, ("frame4", "t4", "double4x5", "triple3x7", "dot")),
    (24, 27, ("double3x5", "frame3x4", "triple4x7", "l3", "frame3", "dot")),
    (30, 30, ("frame4", "triple3x7", "l3", "double3x5", "frame3", "dot")),
)

_SLOT_CATEGORIES = {
    4: ((0, 0), (0, 2), (2, 0), (2, 2)),
    5: ((0, 0), (0, 2), (1, 1), (2, 0), (2, 2)),
    6: ((0, 0), (0, 2), (1, 1), (2, 0), (2, 2), (1, 0)),
}


def _integer(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def _direction(value: object) -> str:
    if type(value) is not str or value not in SORT_DIRECTIONS:
        raise ValueError("sort_direction must be most_holes_first or fewest_holes_first")
    return value


def program_for(direction: str) -> str:
    direction = _direction(direction)
    name = "canonical.rkt" if direction == "most_holes_first" else "fewest_first.rkt"
    return (HOME / "rules" / name).read_text(encoding="utf-8")


def _dims(shape: Shape) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _reflect(shape: Shape, rng: random.Random) -> Shape:
    height, width = _dims(shape)
    flip_v = bool(rng.getrandbits(1))
    flip_h = bool(rng.getrandbits(1))
    return tuple(sorted(
        (height - 1 - row if flip_v else row,
         width - 1 - col if flip_h else col)
        for row, col in shape
    ))


def _anchor(size: int, object_size: int, category: int) -> int:
    if category == 0:
        return 0
    if category == 2:
        return size - object_size
    return (size - object_size) // 2


def _build(seed: int, profile_index: int, profile) -> list[list[int]]:
    _integer("seed", seed, 0, 2**63 - 1)
    height, width, names = profile
    rng = random.Random((seed + 1) * 1_000_003 + profile_index * 9_973)
    shapes = [_reflect(_SHAPES[name], rng) for name in names]
    colors = rng.sample(range(1, 10), len(shapes))
    # Break any accidental relation between color and hole order.
    colors = colors[2:] + colors[:2]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    for shape, color, (vrank, hrank) in zip(shapes, colors, _SLOT_CATEGORIES[len(shapes)]):
        shape_h, shape_w = _dims(shape)
        top = _anchor(height, shape_h, vrank)
        left = _anchor(width, shape_w, hrank)
        cells = {(top + row, left + col) for row, col in shape}
        if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
            raise AssertionError("profile object escaped its canvas")
        if any(
            (row + dr, col + dc) in occupied
            for row, col in cells
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
        ):
            raise AssertionError("profile components violate the one-cell moat")
        for row, col in cells:
            grid[row][col] = color
        occupied.update(cells)
    return grid


def sample_demo(seed: int, index: int) -> list[list[int]]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demo index", index, 0, len(_DEMO_PROFILES) - 1)
    return _build(seed, index, _DEMO_PROFILES[index])


def sample_query(seed: int, index: int) -> list[list[int]]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("query index", index, 0, len(_QUERY_PROFILES) - 1)
    return _build(seed ^ 0x5DEECE66D, 100 + index, _QUERY_PROFILES[index])


def _validate_grid(grid) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be a rectangular list of lists")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("cells must be exact ARC integer colors 0..9")
    return len(grid), width


def _components(grid) -> list[dict]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
            c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
            result.append({"color": color, "cells": tuple(sorted(cells)),
                           "bbox": (r0, c0, r1, c1)})
    if len(result) < 2:
        raise ValueError("hole-sort needs at least two foreground components")
    return result


def _crop(grid, component: dict) -> list[list[int]]:
    r0, c0, r1, c1 = component["bbox"]
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _hole_count(crop: list[list[int]]) -> int:
    height, width = len(crop), len(crop[0])
    background = {(r, c) for r in range(height) for c in range(width) if crop[r][c] == 0}
    seen: set[tuple[int, int]] = set()
    holes = 0
    for start in sorted(background):
        if start in seen:
            continue
        stack = [start]; seen.add(start); touches = False
        while stack:
            row, col = stack.pop()
            touches |= row in (0, height - 1) or col in (0, width - 1)
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + dr, col + dc)
                if nxt in background and nxt not in seen:
                    seen.add(nxt); stack.append(nxt)
        holes += int(not touches)
    return holes


def _records(grid) -> list[dict]:
    rows = []
    for component in _components(grid):
        crop = _crop(grid, component)
        rows.append({**component, "crop": crop, "holes": _hole_count(crop),
                     "cell_count": len(component["cells"]),
                     "bbox_area": len(crop) * len(crop[0]),
                     "zero_count": sum(value == 0 for row in crop for value in row)})
    return rows


def _ordered(grid, direction: str, rival: str | None = None) -> list[dict]:
    direction = _direction(direction)
    rows = _records(grid)
    sign = -1 if direction == "most_holes_first" else 1
    if rival is None:
        return sorted(rows, key=lambda row: (sign * row["holes"], row["bbox"][0], row["bbox"][1]))
    if rival == "opposite_direction":
        return _ordered(grid, "fewest_holes_first" if direction == "most_holes_first" else "most_holes_first")
    if rival == "scan_order":
        return rows
    if rival in {"bbox_area", "cell_count", "zero_count", "color"}:
        key_name = rival
        return sorted(rows, key=lambda row: (sign * row[key_name], row["bbox"][0], row["bbox"][1]))
    if rival == "reverse_ties":
        return sorted(rows, key=lambda row: (sign * row["holes"], -row["bbox"][0], -row["bbox"][1]))
    raise ValueError(f"unknown rival: {rival}")


def _pack(rows: Iterable[dict], *, bottom: bool = False, gap: int = 1,
          fill_bbox: bool = False) -> list[list[int]]:
    rows = list(rows)
    crops = [row["crop"] for row in rows]
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + gap * (len(crops) - 1)
    out = [[0 for _ in range(width)] for _ in range(height)]
    left = 0
    for record, crop in zip(rows, crops):
        top = height - len(crop) if bottom else 0
        for r, values in enumerate(crop):
            for c, value in enumerate(values):
                if fill_bbox:
                    value = record["color"]
                if value != 0:
                    out[top + r][left + c] = value
        left += len(crop[0]) + gap
    return out


def solve(grid, direction: str) -> list[list[int]]:
    return _pack(_ordered(grid, direction))


def rival_output(grid, direction: str, rival: str) -> list[list[int]]:
    if rival == "bottom_aligned":
        return _pack(_ordered(grid, direction), bottom=True)
    if rival == "no_gap":
        return _pack(_ordered(grid, direction), gap=0)
    if rival == "fill_bbox_crops":
        return _pack(_ordered(grid, direction), fill_bbox=True)
    return _pack(_ordered(grid, direction, rival))


DECLARED_RIVALS = (
    "opposite_direction", "scan_order", "bbox_area", "cell_count",
    "zero_count", "color", "reverse_ties", "bottom_aligned", "no_gap",
    "fill_bbox_crops",
)


def sort_intermediate(grid, direction: str) -> dict:
    ordered = _ordered(grid, direction)
    return {
        "sort_direction": _direction(direction),
        "ordered_components": [
            {"holes": row["holes"], "bbox": list(row["bbox"]),
             "color": row["color"], "cells": [list(cell) for cell in row["cells"]]}
            for row in ordered
        ],
    }


def analyze(grid) -> dict:
    height, width = _validate_grid(grid)
    rows = _records(grid)
    foreground = [(r, c) for r, line in enumerate(grid) for c, value in enumerate(line) if value]
    packed = solve(grid, "most_holes_first")
    return {
        "shape": [height, width],
        "component_count": len(rows),
        "foreground_cells": len(foreground),
        "touches_all_canvas_sides": (
            any(r == 0 for r, _ in foreground) and any(r == height - 1 for r, _ in foreground)
            and any(c == 0 for _, c in foreground) and any(c == width - 1 for _, c in foreground)
        ),
        "packed_shape": [len(packed), len(packed[0])],
        "hole_counts": [row["holes"] for row in rows],
        "bboxes": [list(row["bbox"]) for row in rows],
    }


def episode_pairs(seed: int, direction: str, demos: int, queries: int = 4):
    _integer("seed", seed, 0, 2**63 - 1)
    _direction(direction)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 4, 4)
    train = [{"input": sample_demo(seed, index),
              "output": solve(sample_demo(seed, index), direction)} for index in range(demos)]
    test = [{"input": sample_query(seed, index),
             "output": solve(sample_query(seed, index), direction)} for index in range(queries)]
    encoded = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(encoded) != len(set(encoded)):
        raise AssertionError("sampler emitted duplicate episode inputs")
    return train, test


def audit_episode(seed: int, direction: str, *, demos: int = 2, queries: int = 4) -> dict:
    train, test = episode_pairs(seed, direction, demos, queries)
    survivors = [
        rival for rival in DECLARED_RIVALS
        if all(rival_output(pair["input"], direction, rival) == pair["output"] for pair in train)
    ]
    return {
        "seed": seed,
        "sort_direction": direction,
        "demo_count": demos,
        "query_count": queries,
        "surviving_rivals": survivors,
        "has_30x30_query": any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30 for pair in test),
        "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in test],
        "scope": "finite declared rivals only; not universal rule uniqueness",
    }
