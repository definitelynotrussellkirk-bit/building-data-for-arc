"""Native two-setting adapter for component-rank metric inference."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

_HOME = Path(__file__).resolve().parent
SETTINGS = ({"rank_metric": "cells"}, {"rank_metric": "bounding_box"})
DEFAULT = SETTINGS[0]
_PROGRAMS = {
    "cells": (_HOME / "canonical.rkt").read_text(),
    "bounding_box": (_HOME / "bounding_box.rkt").read_text(),
}
_COLORS = (1, 5, 6, 7, 8, 9)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _setting(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"rank_metric"}:
        raise ValueError("settings must contain exactly rank_metric")
    value = settings["rank_metric"]
    if type(value) is not str or value not in _PROGRAMS:
        raise ValueError("rank_metric must be cells or bounding_box")
    return {"rank_metric": value}


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _mix(seed: int, stream: str, index: int) -> int:
    payload = f"996fc37f49d9:{seed}:{stream}:{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & ((1 << 63) - 1)


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and at most 30x30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be exact ARC integers 0..9")
    return deepcopy(grid)


def components(grid: Any) -> list[tuple[tuple[int, int], ...]]:
    normalized = _validate_grid(grid)
    height, width = len(normalized), len(normalized[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[tuple[int, int], ...]] = []
    for row0 in range(height):
        for col0 in range(width):
            if normalized[row0][col0] == 0 or (row0, col0) in seen:
                continue
            queue = deque([(row0, col0)])
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for dr, dc in _DIR4:
                    nxt = row + dr, col + dc
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and normalized[nxt[0]][nxt[1]] != 0):
                        seen.add(nxt)
                        queue.append(nxt)
            result.append(tuple(sorted(cells)))
    return result


def _bbox_area(cells: Iterable[tuple[int, int]]) -> int:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def program(settings: dict[str, Any]) -> str:
    return _PROGRAMS[_setting(settings)["rank_metric"]]


def dependency_intermediate(grid: Any, settings: dict[str, Any]) -> dict[str, Any]:
    metric = _setting(settings)["rank_metric"]
    groups = components(grid)
    if len(groups) not in (2, 3):
        raise ValueError("expected exactly two or three nonzero components")
    values = [len(cells) if metric == "cells" else _bbox_area(cells) for cells in groups]
    if len(set(values)) != len(values):
        raise ValueError(f"{metric} metric must be strictly distinct")
    order = sorted(range(len(groups)), key=lambda index: (values[index], groups[index]))
    return {
        "rank_metric": metric,
        "metric_values": values,
        "ordered_components": [[[row, col] for row, col in groups[index]] for index in order],
    }


def solve_from_intermediate(grid: Any, intermediate: dict[str, Any]) -> list[list[int]]:
    normalized = _validate_grid(grid)
    ordered = intermediate.get("ordered_components") if type(intermediate) is dict else None
    if type(ordered) is not list or len(ordered) not in (2, 3):
        raise ValueError("intermediate must contain two or three ordered components")
    output = [[0 for _ in row] for row in normalized]
    for rank, cells in enumerate(ordered):
        if type(cells) is not list or not cells:
            raise ValueError("ordered component must be a nonempty list")
        for cell in cells:
            if type(cell) is not list or len(cell) != 2 or any(type(v) is not int for v in cell):
                raise ValueError("component cell must be a coordinate pair")
            row, col = cell
            if not (0 <= row < len(output) and 0 <= col < len(output[0]) and normalized[row][col] != 0):
                raise ValueError("component cell is invalid for the input")
            output[row][col] = (2, 3, 4)[rank]
    return output


def solve(grid: Any, settings: dict[str, Any]) -> list[list[int]]:
    return solve_from_intermediate(grid, dependency_intermediate(grid, settings))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    return tuple(sorted((row - r0, col - c0) for row, col in cells))


def _variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    current = _normalize(cells)
    variants: set[tuple[tuple[int, int], ...]] = set()
    for _ in range(4):
        variants.add(_normalize(current))
        variants.add(_normalize((row, -col) for row, col in current))
        current = _normalize((col, -row) for row, col in current)
    return tuple(sorted(variants))


def _templates(k: int, count: int) -> list[tuple[tuple[int, int], ...]]:
    sparse = tuple([(row, 0) for row in range(k)] + [(k - 1, col) for col in range(1, k)])
    compact = tuple((row, col) for row in range(2) for col in range(k))
    larger = tuple((row, col) for row in range(3) for col in range(k))
    result = [sparse, compact, larger][:count]
    cell_values = [len(cells) for cells in result]
    box_values = [_bbox_area(cells) for cells in result]
    assert cell_values == sorted(cell_values)
    assert len(set(box_values)) == len(box_values)
    assert sorted(range(count), key=lambda i: cell_values[i]) != sorted(range(count), key=lambda i: box_values[i])
    return result


def _place(
    height: int,
    width: int,
    shapes: list[tuple[tuple[int, int], ...]],
    rng: random.Random,
    *,
    boundary: bool,
) -> list[list[int]]:
    transformed = [rng.choice(_variants(shape)) for shape in shapes]
    colors = rng.sample(_COLORS, len(shapes))
    if boundary:
        placements: list[tuple[int, int]] = []
        for index, shape in enumerate(transformed):
            sh = max(row for row, _ in shape) + 1
            sw = max(col for _, col in shape) + 1
            if index == 0:
                placements.append((0, 0))
            elif index == 1:
                placements.append((height - sh, width - sw))
            else:
                placements.append((0, width - sw))
    else:
        placements = []
        used: set[tuple[int, int]] = set()
        for shape in transformed:
            sh = max(row for row, _ in shape) + 1
            sw = max(col for _, col in shape) + 1
            candidates = [(row, col) for row in range(height - sh + 1) for col in range(width - sw + 1)]
            rng.shuffle(candidates)
            for top, left in candidates:
                cells = {(top + row, left + col) for row, col in shape}
                if any(cell in used or any((cell[0] + dr, cell[1] + dc) in used for dr, dc in _DIR4)
                       for cell in cells):
                    continue
                placements.append((top, left))
                used.update(cells)
                break
            else:
                raise AssertionError("could not place separated components")
    grid = [[0] * width for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    for shape, (top, left), color in zip(transformed, placements, colors):
        cells = {(top + row, left + col) for row, col in shape}
        if any(cell in occupied or any((cell[0] + dr, cell[1] + dc) in occupied for dr, dc in _DIR4)
               for cell in cells):
            raise AssertionError("boundary placement merged components")
        occupied.update(cells)
        for row, col in cells:
            grid[row][col] = color
    return grid


def _scene(seed: int, index: int, height: int, width: int, k: int, count: int, *, boundary: bool = False):
    rng = random.Random(_mix(seed, "scene", index))
    grid = _place(height, width, _templates(k, count), rng, boundary=boundary)
    groups = components(grid)
    if len(groups) != count:
        raise AssertionError("scene components merged")
    for metric in SETTINGS:
        dependency_intermediate(grid, metric)
    return grid



def _paint_fixed(
    height: int,
    width: int,
    items: list[tuple[tuple[tuple[int, int], ...], tuple[int, int], int]],
) -> list[list[int]]:
    grid = [[0] * width for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    for shape, (top, left), color in items:
        cells = {(top + row, left + col) for row, col in shape}
        if (not cells or any(not (0 <= row < height and 0 <= col < width) for row, col in cells)
                or any(cell in occupied or any((cell[0] + dr, cell[1] + dc) in occupied
                                               for dr, dc in _DIR4) for cell in cells)):
            raise AssertionError("fixed teaching components overlap, touch, or leave the canvas")
        occupied.update(cells)
        for row, col in cells:
            grid[row][col] = color
    return grid


def _teaching_scene(seed: int, index: int) -> list[list[int]]:
    """Construct the two minimum-count demonstrations as a shortcut contrast set."""
    rng = random.Random(_mix(seed, "teaching", index))
    sparse_l4 = tuple([(row, 0) for row in range(4)] + [(3, col) for col in range(1, 4)])
    if index == 0:
        compact_2x5 = tuple((row, col) for row in range(2) for col in range(5))
        colors = rng.sample(_COLORS, 2)
        # Scan/height/bbox rank compact first; occupied-cell rank sparse first.
        grid = _paint_fixed(12, 14, [
            (compact_2x5, (1, 8), colors[0]),
            (sparse_l4, (7, 1), colors[1]),
        ])
    elif index == 1:
        # A: 6 cells in a 2x4 box (density .75). B: 7-cell 4x4 L
        # (density .4375). C: 12-cell 6x2 rectangle (density 1).
        # Cell order A,B,C; box order A,C,B; density order B,A,C.
        medium_a = ((0, 0), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3))
        tall_c = tuple((row, col) for row in range(6) for col in range(2))
        low, middle, high = sorted(rng.sample(_COLORS, 3))
        # Scan order B,C,A. Color order B,A,C. Neither is a target rank.
        grid = _paint_fixed(15, 17, [
            (sparse_l4, (0, 0), low),
            (tall_c, (5, 12), high),
            (medium_a, (13, 5), middle),
        ])
    else:
        raise ValueError("teaching scene index must be 0 or 1")
    groups = components(grid)
    if len(groups) != index + 2:
        raise AssertionError("teaching scene component count changed")
    for metric in SETTINGS:
        dependency_intermediate(grid, metric)
    return grid

def _input_banks(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demo_specs = (
        (12, 14, 4, 2),
        (15, 17, 5, 3),
        (18, 20, 6, 3),
        (14, 22, 4, 2),
        (22, 24, 7, 3),
        (24, 27, 8, 3),
    )
    query_specs = (
        (13, 19, 4, 3, False),
        (21, 24, 6, 2, False),
        (26, 30, 8, 3, False),
        (30, 30, 12, 3, True),
    )
    demos = [
        _teaching_scene(seed, 0),
        _teaching_scene(seed, 1),
        *[_scene(seed, index, *spec) for index, spec in enumerate(demo_specs[2:], start=2)],
    ]
    queries = [_scene(seed, 100 + index, h, w, k, count, boundary=boundary)
               for index, (h, w, k, count, boundary) in enumerate(query_specs)]
    return demos, queries


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    selected = _setting(settings)
    demo_inputs, query_inputs = _input_banks(seed)

    def pairs(inputs: list[list[list[int]]]) -> list[dict[str, list[list[int]]]]:
        return [{"input": deepcopy(grid), "output": solve(grid, selected)} for grid in inputs]

    episode = {
        "settings": deepcopy(selected),
        "train": pairs(demo_inputs[:demos]),
        "test": pairs(query_inputs[:queries]),
        "program_solution": program(selected),
    }
    visible = [repr(pair["input"]) for pair in episode["train"] + episode["test"]]
    if len(visible) != len(set(visible)):
        raise AssertionError("generated inputs must be distinct")
    return episode
