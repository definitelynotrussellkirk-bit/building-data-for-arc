"""Source-bound native parametric family for ``d1bf9a8e4c69``.

``corners_only`` is the exact canonical task: erase each same-color 4-connected
component and paint its four bounding-box corners in the component color.

``nearest_corner_bridge`` first computes exactly that corner-only intermediate.
It then finds the unique minimum-Manhattan pair of corners belonging to different
input components and paints the zero cells on a deterministic row-then-column
Manhattan route between them with color 4.  The bridge endpoints therefore do
not exist as a candidate set until the canonical corner extraction has run.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import random
from typing import Callable, Iterable

TASK_ID = "d1bf9a8e4c69"
FINISHES = ("corners_only", "nearest_corner_bridge")
BRIDGE_COLOR = 4
PALETTE = (1, 2, 3, 5, 6, 7, 8, 9)
HOME = Path(__file__).resolve().parent

Cell = tuple[int, int]
Grid = list[list[int]]


@dataclass(frozen=True)
class Box:
    top: int
    left: int
    height: int
    width: int
    missing: str
    style: str


@dataclass(frozen=True)
class Profile:
    height: int
    width: int
    boxes: tuple[Box, ...]
    repeated_pair: tuple[int, int] | None = None


# First two profiles jointly eliminate the finite authoring rivals: both use a
# non-first-two, diagonal winner with omitted facing corners; profile 1 also
# contains disconnected same-color components.
DEMO_PROFILES: tuple[Profile, ...] = (
    Profile(
        12,
        14,
        (
            Box(1, 10, 3, 3, "bl", "zigzag"),
            Box(5, 1, 4, 4, "br", "irregular"),
            Box(9, 8, 3, 4, "tl", "l"),
        ),
    ),
    Profile(
        14,
        16,
        (
            Box(1, 11, 3, 4, "bl", "irregular"),
            Box(8, 2, 4, 4, "br", "zigzag"),
            Box(10, 10, 4, 4, "tl", "dense"),
        ),
        repeated_pair=(0, 1),
    ),
    Profile(
        14,
        16,
        (
            Box(1, 1, 5, 4, "br", "zigzag"),
            Box(8, 9, 5, 5, "tl", "irregular"),
        ),
    ),
    Profile(
        15,
        17,
        (
            Box(1, 11, 5, 5, "bl", "dense"),
            Box(8, 2, 5, 5, "tr", "zigzag"),
        ),
    ),
    Profile(
        18,
        20,
        (
            Box(1, 1, 4, 4, "br", "l"),
            Box(7, 3, 5, 5, "br", "irregular"),
            Box(8, 12, 5, 5, "tl", "zigzag"),
            Box(15, 1, 3, 4, "tr", "dense"),
        ),
    ),
    Profile(
        20,
        22,
        (
            Box(1, 2, 4, 5, "br", "irregular"),
            Box(8, 9, 5, 5, "br", "dense"),
            Box(15, 10, 4, 4, "tr", "zigzag"),
        ),
        repeated_pair=(0, 2),
    ),
)

QUERY_PROFILES: tuple[Profile, ...] = (
    Profile(
        11,
        13,
        (
            Box(1, 1, 4, 4, "br", "irregular"),
            Box(6, 7, 4, 5, "tl", "zigzag"),
        ),
    ),
    Profile(
        18,
        20,
        (
            Box(1, 14, 3, 4, "bl", "l"),
            Box(6, 1, 5, 5, "br", "dense"),
            Box(10, 11, 5, 5, "tl", "irregular"),
            Box(14, 2, 3, 4, "tr", "zigzag"),
        ),
    ),
    Profile(
        24,
        26,
        (
            Box(1, 19, 5, 6, "bl", "irregular"),
            Box(13, 2, 7, 7, "br", "dense"),
            Box(17, 16, 7, 8, "tl", "zigzag"),
        ),
        repeated_pair=(0, 1),
    ),
    Profile(
        30,
        30,
        (
            Box(1, 1, 8, 8, "br", "dense"),
            Box(1, 21, 7, 8, "bl", "dense"),
            Box(19, 2, 9, 9, "br", "dense"),
            Box(19, 21, 10, 8, "tl", "dense"),
        ),
        repeated_pair=(0, 2),
    ),
)


def _integer(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _validate_grid(grid: object) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer ARC colors")
    return len(grid), width


def _components(grid: Grid) -> list[tuple[int, list[Cell]]]:
    height, width = _validate_grid(grid)
    seen: set[Cell] = set()
    result: list[tuple[int, list[Cell]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                rr, cc = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = rr + dr, cc + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append((color, sorted(cells)))
    return result


def _bbox(cells: Iterable[Cell]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    if not points:
        raise ValueError("empty component")
    return (
        min(row for row, _ in points),
        min(col for _, col in points),
        max(row for row, _ in points),
        max(col for _, col in points),
    )


def _corners(cells: Iterable[Cell]) -> tuple[Cell, Cell, Cell, Cell]:
    r1, c1, r2, c2 = _bbox(cells)
    return (r1, c1), (r1, c2), (r2, c1), (r2, c2)


def _corner_groups(grid: Grid, *, merge_by_color: bool = False) -> list[dict]:
    components = _components(grid)
    if merge_by_color:
        by_color: dict[int, list[Cell]] = defaultdict(list)
        for color, cells in components:
            by_color[color].extend(cells)
        components = [(color, sorted(cells)) for color, cells in by_color.items()]
    return [
        {"color": color, "cells": tuple(cells), "corners": _corners(cells)}
        for color, cells in components
    ]


def _distance(left: Cell, right: Cell) -> int:
    return abs(left[0] - right[0]) + abs(left[1] - right[1])


def _pair_candidates(groups: list[dict], key: str) -> list[tuple[int, int, int, Cell, Cell]]:
    result = []
    for left_index in range(len(groups)):
        for right_index in range(left_index + 1, len(groups)):
            for left in groups[left_index][key]:
                for right in groups[right_index][key]:
                    result.append((_distance(left, right), left_index, right_index, left, right))
    return result


def _choose_pair(groups: list[dict], *, key: str = "corners", farthest: bool = False, first_two: bool = False):
    selected = groups[:2] if first_two else groups
    candidates = _pair_candidates(selected, key)
    if not candidates:
        raise ValueError("at least two components are required")
    best_distance = (max if farthest else min)(candidate[0] for candidate in candidates)
    # Match Racket's strict-update fold: keep the first candidate at a tied score.
    return next(candidate for candidate in candidates if candidate[0] == best_distance)


def _bridge_cells(left: Cell, right: Cell, *, column_first: bool = False) -> list[Cell]:
    r1, c1 = left
    r2, c2 = right
    cells: list[Cell] = []
    if column_first:
        cells.extend((row, c1) for row in range(min(r1, r2), max(r1, r2) + 1))
        cells.extend((r2, col) for col in range(min(c1, c2), max(c1, c2) + 1))
    else:
        cells.extend((r1, col) for col in range(min(c1, c2), max(c1, c2) + 1))
        cells.extend((row, c2) for row in range(min(r1, r2), max(r1, r2) + 1))
    return cells


def _corner_grid(grid: Grid, groups: list[dict] | None = None) -> Grid:
    height, width = _validate_grid(grid)
    groups = _corner_groups(grid) if groups is None else groups
    out = [[0] * width for _ in range(height)]
    for group in groups:
        for row, col in group["corners"]:
            out[row][col] = group["color"]
    return out


def _bridge_from_groups(
    grid: Grid,
    groups: list[dict],
    *,
    key: str = "corners",
    farthest: bool = False,
    first_two: bool = False,
    column_first: bool = False,
) -> Grid:
    out = _corner_grid(grid, groups)
    _distance_value, _left_index, _right_index, left, right = _choose_pair(
        groups, key=key, farthest=farthest, first_two=first_two
    )
    for row, col in _bridge_cells(left, right, column_first=column_first):
        if out[row][col] == 0:
            out[row][col] = BRIDGE_COLOR
    return out


def solve(grid: Grid, finish: str) -> Grid:
    if type(finish) is not str or finish not in FINISHES:
        raise ValueError("finish must be a supported string")
    groups = _corner_groups(grid)
    if len(groups) < 2:
        raise ValueError("at least two components are required")
    if finish == "corners_only":
        return _corner_grid(grid, groups)
    return _bridge_from_groups(grid, groups)


def wrong_intermediate_solve(grid: Grid) -> Grid:
    """Ablation: choose bridge endpoints from original occupied cells, not A's corners."""
    groups = _corner_groups(grid)
    return _bridge_from_groups(grid, groups, key="cells")


def column_first_solve(grid: Grid) -> Grid:
    return _bridge_from_groups(grid, _corner_groups(grid), column_first=True)


def first_two_solve(grid: Grid) -> Grid:
    return _bridge_from_groups(grid, _corner_groups(grid), first_two=True)


def per_color_solve(grid: Grid) -> Grid:
    groups = _corner_groups(grid, merge_by_color=True)
    if len(groups) < 2:
        return _corner_grid(grid, groups)
    return _bridge_from_groups(grid, groups)


def farthest_solve(grid: Grid) -> Grid:
    return _bridge_from_groups(grid, _corner_groups(grid), farthest=True)


RIVAL_SOLVERS: dict[str, Callable[[Grid], Grid]] = {
    "corners_only": lambda grid: solve(grid, "corners_only"),
    "nearest_corner_bridge": lambda grid: solve(grid, "nearest_corner_bridge"),
    "nearest_original_cells": wrong_intermediate_solve,
    "column_first_bridge": column_first_solve,
    "first_two_components": first_two_solve,
    "per_color_groups": per_color_solve,
    "farthest_corner_bridge": farthest_solve,
}


def _base_shape(height: int, width: int, style: str, rng: random.Random) -> set[Cell]:
    """Return a connected shape whose exact bbox misses only bottom-right."""
    if height < 3 or width < 3:
        raise ValueError("shape boxes must be at least 3x3")
    cells = {(0, col) for col in range(width)} | {(row, 0) for row in range(height)}
    if style == "l":
        pass
    elif style == "zigzag":
        for row in range(1, height):
            reach = 1 + ((row + rng.randrange(max(1, width - 2))) % max(1, width - 1))
            reach = min(width - 2, reach)
            cells.update((row, col) for col in range(reach + 1))
    elif style == "irregular":
        cells.update((height - 1, col) for col in range(width - 1))
        for row in range(1, height - 1):
            if (row + rng.randrange(2)) % 2 == 0:
                cells.update((row, col) for col in range(min(width - 1, 2 + row % max(2, width - 1))))
    elif style == "dense":
        cells = {(row, col) for row in range(height) for col in range(width)}
        cells.remove((height - 1, width - 1))
        # Keep a few deterministic holes without disconnecting the shape.
        for row in range(1, height - 1):
            for col in range(1, width - 1):
                if (row * 7 + col * 11 + rng.randrange(3)) % 13 == 0:
                    cells.discard((row, col))
    else:
        raise ValueError(f"unknown shape style: {style}")
    return cells


def _orient(cells: set[Cell], height: int, width: int, missing: str) -> set[Cell]:
    if missing not in {"br", "bl", "tr", "tl"}:
        raise ValueError("missing corner must be br, bl, tr, or tl")
    result = set(cells)
    if missing in {"bl", "tl"}:
        result = {(row, width - 1 - col) for row, col in result}
    if missing in {"tr", "tl"}:
        result = {(height - 1 - row, col) for row, col in result}
    return result


def _make_input(seed: int, stream: str, index: int, profile: Profile) -> Grid:
    rng = random.Random(f"{TASK_ID}:nearest-corner-bridge-v1:{seed}:{stream}:{index}")
    colors = list(PALETTE)
    rng.shuffle(colors)
    assigned = colors[: len(profile.boxes)]
    if profile.repeated_pair is not None:
        left, right = profile.repeated_pair
        assigned[right] = assigned[left]
    grid = [[0] * profile.width for _ in range(profile.height)]
    for object_index, (box, color) in enumerate(zip(profile.boxes, assigned, strict=True)):
        shape_rng = random.Random(
            f"{TASK_ID}:shape-v1:{seed}:{stream}:{index}:{object_index}:{box.style}"
        )
        shape = _orient(
            _base_shape(box.height, box.width, box.style, shape_rng),
            box.height,
            box.width,
            box.missing,
        )
        for dr, dc in shape:
            row, col = box.top + dr, box.left + dc
            if not (0 <= row < profile.height and 0 <= col < profile.width):
                raise ValueError("profile box exceeds grid")
            if grid[row][col] != 0:
                raise ValueError("profile objects overlap")
            grid[row][col] = color
    state = corner_state(grid)
    if len(state["groups"]) != len(profile.boxes):
        raise ValueError("profile objects merged or split")
    if state["unique_nearest_corner_pair"] is not True:
        raise ValueError("profile must have a unique nearest corner pair")
    if state["nearest_corner_pair"] == state["nearest_original_pair"]:
        raise ValueError("profile must distinguish corner candidates from original cells")
    return grid


def _orientation(left: Cell, right: Cell) -> str:
    dr, dc = right[0] - left[0], right[1] - left[1]
    if dr == 0:
        return "horizontal"
    if dc == 0:
        return "vertical"
    return "down_right" if dr * dc > 0 else "down_left"


def corner_state(grid: Grid) -> dict:
    groups = _corner_groups(grid)
    corner_candidates = _pair_candidates(groups, "corners")
    minimum = min(candidate[0] for candidate in corner_candidates)
    best_corner = next(candidate for candidate in corner_candidates if candidate[0] == minimum)
    best_original = _choose_pair(groups, key="cells")
    _, left_index, right_index, left, right = best_corner
    repeated = any(count > 1 for count in Counter(group["color"] for group in groups).values())
    return {
        "groups": [
            {
                "color": group["color"],
                "bbox": list(_bbox(group["cells"])),
                "cells": [list(cell) for cell in group["cells"]],
                "corners": [list(cell) for cell in group["corners"]],
            }
            for group in groups
        ],
        "nearest_corner_distance": minimum,
        "nearest_corner_group_indexes": [left_index, right_index],
        "nearest_corner_pair": [list(left), list(right)],
        "nearest_original_distance": best_original[0],
        "nearest_original_group_indexes": [best_original[1], best_original[2]],
        "nearest_original_pair": [list(best_original[3]), list(best_original[4])],
        "unique_nearest_corner_pair": sum(candidate[0] == minimum for candidate in corner_candidates) == 1,
        "orientation": _orientation(left, right),
        "has_repeated_color_components": repeated,
        "bridge_cells": [list(cell) for cell in _bridge_cells(left, right)],
    }


def build_claimed_episode(*, seed: int, finish: str, n_train: int, n_test: int) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("n_train", n_train, 2, 6)
    _integer("n_test", n_test, 1, 4)
    if finish not in FINISHES:
        raise ValueError("unsupported finish")
    demo_inputs = [
        _make_input(seed, "demo", index, profile)
        for index, profile in enumerate(DEMO_PROFILES)
    ]
    query_inputs = [
        _make_input(seed, "query", index, profile)
        for index, profile in enumerate(QUERY_PROFILES)
    ]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in demo_inputs + query_inputs]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("profile construction produced duplicate visible inputs")

    def pair(grid: Grid) -> dict:
        return {"input": deepcopy(grid), "output": solve(grid, finish)}

    return {
        "train": [pair(grid) for grid in demo_inputs[:n_train]],
        "test": [pair(grid) for grid in query_inputs[:n_test]],
    }
