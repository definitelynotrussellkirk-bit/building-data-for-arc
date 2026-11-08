"""Source-bound sort-and-pack family used by the native adapter and audits.

The canonical rule sorts tight component crops by
``(cell_count, bbox_height, bbox_width, color)`` ascending.  The alternative
reverses that complete lexicographic order.  Input sampling is independent of
the private setting and deliberately contains sort-key ties, sparse bboxes,
source-order decoys, boundary contacts, and a substantive 30x30 case.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import random
from typing import Iterable

from reviewer_support import load_selected_generator

TASK_ID = "78143e5d7ed1"
HOME = Path(__file__).resolve().parent
REPO = HOME.parents[3]
SORT_DIRECTIONS = ("smallest_first", "largest_first")

Shape = tuple[tuple[int, int], ...]

# Connected sparse/dense polyominoes. Reflections preserve their dimensions and
# therefore preserve the intended sort-key lesson while varying exact texture.
_SHAPES: dict[str, Shape] = {
    "a4_l_2x3": ((0, 0), (1, 0), (1, 1), (1, 2)),
    "a4_square": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "a5_p_2x3": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    "a5_tall_3x2": ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
    "a5_sparse_3x3": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    "a5_plus_3x3": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "a6_rect_2x3": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    "a6_rect_3x2": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    "a6_hook_3x3": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
    "a7_u_3x3": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2)),
    "a7_stair_4x3": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 1)),
    "a8_3x4": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (2, 1), (2, 2)),
    "a8_4x3": ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (2, 2), (1, 2)),
    "a9_3x4": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    "a10_4x4": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (3, 3)),
}

# The first two demonstrations jointly reject all declared shortcuts. Demo 0
# supplies area/height/width/color evidence; demo 1 reverses cell-count versus
# bbox-area order. Additional demos diversify dimensions and textures.
_DEMO_PROFILES = (
    (12, 20, ("a4_l_2x3", "a5_p_2x3", "a5_tall_3x2", "a5_sparse_3x3", "a5_plus_3x3"), False),
    (13, 20, ("a5_sparse_3x3", "a5_plus_3x3", "a6_rect_2x3", "a4_l_2x3", "a7_stair_4x3"), True),
    (14, 20, ("a4_square", "a5_p_2x3", "a6_hook_3x3", "a7_u_3x3"), False),
    (15, 22, ("a5_tall_3x2", "a5_sparse_3x3", "a6_rect_2x3", "a8_3x4", "a9_3x4"), True),
    (16, 24, ("a4_l_2x3", "a6_rect_3x2", "a7_stair_4x3", "a8_4x3", "a10_4x4"), False),
    (18, 26, ("a5_p_2x3", "a5_plus_3x3", "a6_hook_3x3", "a7_u_3x3", "a8_3x4", "a9_3x4"), True),
)
_QUERY_PROFILES = (
    (11, 16, ("a4_square", "a5_tall_3x2", "a6_hook_3x3", "a7_u_3x3"), True),
    (18, 21, ("a5_sparse_3x3", "a6_rect_2x3", "a7_stair_4x3", "a8_3x4", "a9_3x4"), False),
    (24, 27, ("a4_l_2x3", "a5_plus_3x3", "a6_rect_3x2", "a7_u_3x3", "a8_4x3", "a10_4x4"), True),
    (30, 30, ("a4_l_2x3", "a5_p_2x3", "a5_tall_3x2", "a5_sparse_3x3", "a6_rect_2x3", "a8_3x4", "a10_4x4"), True),
)


def _integer(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def _direction(value: object) -> str:
    if type(value) is not str or value not in SORT_DIRECTIONS:
        raise ValueError("sort_direction must be smallest_first or largest_first")
    return value


@lru_cache(maxsize=1)
def _generator():
    return load_selected_generator(TASK_ID, root=REPO)[0]


def program_for(direction: str) -> str:
    direction = _direction(direction)
    name = "canonical.rkt" if direction == "smallest_first" else "largest_first.rkt"
    return (HOME / "rules" / name).read_text(encoding="utf-8")


def _dims(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _reflect(shape: Shape, rng: random.Random) -> Shape:
    height, width = _dims(shape)
    vertical = bool(rng.getrandbits(1))
    horizontal = bool(rng.getrandbits(1))
    cells = []
    for row, col in shape:
        cells.append((height - 1 - row if vertical else row,
                      width - 1 - col if horizontal else col))
    return tuple(sorted(cells))


def _base_key(shape: Shape) -> tuple[int, int, int]:
    height, width = _dims(shape)
    return len(shape), height, width


def _rank_permutation(count: int) -> list[int]:
    # Indices here refer to the full-key ascending rank. The permutations are
    # neither ascending nor descending, so row-major source order is a decoy.
    known = {
        4: [2, 0, 3, 1],
        5: [2, 0, 4, 1, 3],
        6: [3, 0, 5, 1, 4, 2],
        7: [3, 0, 6, 1, 5, 2, 4],
    }
    if count not in known:
        raise ValueError("supported profiles need four through seven components")
    return known[count]


def _slot_categories(count: int) -> list[tuple[int, int]]:
    return {
        4: [(0, 0), (0, 2), (2, 0), (2, 2)],
        5: [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],
        6: [(0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)],
        7: [(0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)],
    }[count]


def _anchor(size: int, object_size: int, category: int, touch: bool) -> int:
    margin = 0 if touch else 1
    if category == 0:
        return margin
    if category == 2:
        return size - object_size - margin
    return (size - object_size) // 2


def _build(seed: int, profile_index: int, profile) -> list[list[int]]:
    _integer("seed", seed, 0, 2**63 - 1)
    height, width, names, touch = profile
    rng = random.Random((seed + 1) * 1_000_003 + profile_index * 9_973)
    shapes = [_reflect(_SHAPES[name], rng) for name in names]

    # Assign larger colors to smaller geometry keys. This makes color-first
    # sorting a guaranteed wrong rule in both directions while retaining seed
    # variation through the sampled palette subset.
    palette = sorted(rng.sample(range(1, 10), len(shapes)))
    base_order = sorted(range(len(shapes)), key=lambda i: (_base_key(shapes[i]), i))
    colors = [0] * len(shapes)
    for index, color in zip(base_order, reversed(palette)):
        colors[index] = color
    full_keys = [(*_base_key(shape), color) for shape, color in zip(shapes, colors)]
    ascending = sorted(range(len(shapes)), key=lambda i: full_keys[i])
    # Demo 0 presents the equal-base color pair in descending source order;
    # demo 1 presents it in ascending source order. Thus omitting the color key
    # cannot fit both smallest-first and largest-first teaching sets via stable
    # source order.
    source_rank_order = ([3, 0, 4, 1, 2] if profile_index == 1
                         else _rank_permutation(len(shapes)))
    source_objects = [ascending[rank] for rank in source_rank_order]

    grid = [[0 for _ in range(width)] for _ in range(height)]
    occupied: dict[tuple[int, int], int] = {}
    for slot, object_index in zip(_slot_categories(len(shapes)), source_objects):
        shape, color = shapes[object_index], colors[object_index]
        shape_h, shape_w = _dims(shape)
        top = _anchor(height, shape_h, slot[0], touch)
        left = _anchor(width, shape_w, slot[1], touch)
        cells = {(top + r, left + c) for r, c in shape}
        if any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
            raise AssertionError("profile object escaped its canvas")
        for row, col in cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    owner = occupied.get((row + dr, col + dc))
                    if owner is not None and owner != object_index:
                        raise AssertionError("profile components violate the one-cell moat")
        for row, col in cells:
            occupied[(row, col)] = object_index
            grid[row][col] = color
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


def _components(grid):
    _validate_grid(grid)
    components = _generator()._extract_components(grid)
    if len(components) < 2:
        raise ValueError("sort-and-pack needs at least two foreground components")
    return components


def _ordered(grid, direction: str, rival: str | None = None):
    direction = _direction(direction)
    components = _components(grid)
    reverse = direction == "largest_first"
    if rival is None:
        return sorted(components, key=lambda obj: obj.key, reverse=reverse)
    if rival == "opposite_direction":
        return sorted(components, key=lambda obj: obj.key, reverse=not reverse)
    if rival == "scan_order":
        return list(reversed(components)) if reverse else components
    if rival == "area_only":
        return sorted(components, key=lambda obj: obj.area, reverse=reverse)
    if rival == "omit_height":
        return sorted(components, key=lambda obj: (obj.area, obj.width, obj.color), reverse=reverse)
    if rival == "omit_width":
        return sorted(components, key=lambda obj: (obj.area, obj.height, obj.color), reverse=reverse)
    if rival == "omit_color":
        return sorted(components, key=lambda obj: (obj.area, obj.height, obj.width), reverse=reverse)
    if rival == "bbox_area":
        return sorted(components,
                      key=lambda obj: (obj.height * obj.width, obj.area, obj.height, obj.width, obj.color),
                      reverse=reverse)
    if rival == "color_first":
        return sorted(components,
                      key=lambda obj: (obj.color, obj.area, obj.height, obj.width),
                      reverse=reverse)
    raise ValueError(f"unknown ordering rival {rival!r}")


def solve(grid, direction: str) -> list[list[int]]:
    return _generator()._pack_components(grid, _ordered(grid, direction))


def rival_output(grid, direction: str, rival: str) -> list[list[int]]:
    if rival == "top_aligned":
        return _generator()._pack_components(grid, _ordered(grid, direction), alignment="top")
    if rival == "no_gap":
        return _generator()._pack_components(grid, _ordered(grid, direction), gap=0)
    if rival == "fill_bbox_crops":
        return _generator()._pack_components(grid, _ordered(grid, direction), fill_bboxes=True)
    return _generator()._pack_components(grid, _ordered(grid, direction, rival))


DECLARED_RIVALS = (
    "opposite_direction", "scan_order", "area_only", "omit_height",
    "omit_width", "omit_color", "bbox_area", "color_first",
    "top_aligned", "no_gap", "fill_bbox_crops",
)


def sort_intermediate(grid, direction: str) -> dict:
    ordered = _ordered(grid, direction)
    return {
        "sort_direction": _direction(direction),
        "ordered_components": [
            {
                "key": list(obj.key),
                "bbox": [obj.r1, obj.c1, obj.r2, obj.c2],
                "cells": [list(cell) for cell in obj.cells],
            }
            for obj in ordered
        ],
    }


def analyze(grid) -> dict:
    height, width = _validate_grid(grid)
    components = _components(grid)
    foreground = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    packed = solve(grid, "smallest_first")
    return {
        "shape": [height, width],
        "component_count": len(components),
        "foreground_cells": len(foreground),
        "touches_all_canvas_sides": (
            any(r == 0 for r, _ in foreground)
            and any(r == height - 1 for r, _ in foreground)
            and any(c == 0 for _, c in foreground)
            and any(c == width - 1 for _, c in foreground)
        ),
        "packed_shape": [len(packed), len(packed[0])],
        "keys": [list(obj.key) for obj in components],
    }


def episode_pairs(seed: int, direction: str, demos: int, queries: int = 4):
    _integer("seed", seed, 0, 2**63 - 1)
    _direction(direction)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 4, 4)
    train = []
    for index in range(demos):
        grid = sample_demo(seed, index)
        train.append({"input": grid, "output": solve(grid, direction)})
    test = []
    for index in range(queries):
        grid = sample_query(seed, index)
        test.append({"input": grid, "output": solve(grid, direction)})
    serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(serialized) != len(set(serialized)):
        raise AssertionError("sampler emitted duplicate episode inputs")
    return train, test


def audit_episode(seed: int, direction: str, *, demos: int = 2, queries: int = 4) -> dict:
    train, test = episode_pairs(seed, direction, demos, queries)
    survivors = []
    for rival in DECLARED_RIVALS:
        if all(rival_output(pair["input"], direction, rival) == pair["output"] for pair in train):
            survivors.append(rival)
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
