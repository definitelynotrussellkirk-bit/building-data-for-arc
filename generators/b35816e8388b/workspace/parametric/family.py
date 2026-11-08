"""Native midpoint-to-key-to-payload parametric family for b35816e8388b."""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "b35816e8388b"
HERE = Path(__file__).resolve().parent
MODES = ("canonical", "midpoint_key_relay")
DEFAULT_MODE = "canonical"
HYPOTHESES = MODES + (
    "grid_center_key",
    "left_key",
    "right_key",
    "constant_color_1",
    "constant_color_2",
    "constant_color_3",
)
DEMO_PROFILES = (
    (14, 17, 1),
    (16, 19, 3),
    (18, 21, 2),
    (20, 23, 1),
    (22, 25, 3),
    (24, 27, 2),
)
QUERY_PROFILES = (
    (15, 18, 3),
    (19, 22, 2),
    (24, 28, 1),
    (30, 30, 3),
)
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _read(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def _mode(value: Any, *, hypothesis: bool = False) -> str:
    options = HYPOTHESES if hypothesis else MODES
    if type(value) is not str or value not in options:
        raise ValueError(f"mode must be one of {options}")
    return value


def program_for(mode: str) -> str:
    selected = _mode(mode)
    return _read("canonical.rkt" if selected == "canonical" else "midpoint_key_relay.rkt")


def counterfactual_program() -> str:
    return _read("wrong_grid_center_key.rkt")


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def validate_grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return value


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _rect(height: int, width: int) -> set[tuple[int, int]]:
    return {(r, c) for r in range(height) for c in range(width)}


def _l_shape(height: int, width: int) -> set[tuple[int, int]]:
    return {(r, 0) for r in range(height)} | {(height - 1, c) for c in range(width)}


def _t_shape(height: int, width: int) -> set[tuple[int, int]]:
    center = width // 2
    return {(0, c) for c in range(width)} | {(r, center) for r in range(height)}


def _paint(grid: list[list[int]], shape: Iterable[tuple[int, int]], top: int, left: int, color: int) -> None:
    height, width = len(grid), len(grid[0])
    cells = {(top + r, left + c) for r, c in shape}
    if any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
        raise ValueError("shape falls outside scene")
    if any(grid[r][c] != 0 for r, c in cells):
        raise ValueError("shape overlaps existing content")
    for r, c in cells:
        grid[r][c] = color


def _components(value: Any) -> list[dict[str, Any]]:
    grid = validate_grid(value)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while queue:
                r, c = queue.popleft()
                cells.add((r, c))
                for dr, dc in DIR4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            objects.append({
                "color": color,
                "cells": cells,
                "top": min(r for r, _ in cells),
                "left": min(c for _, c in cells),
            })
    return objects


def _first_two_nonzero(grid: list[list[int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if len(points) < 2:
        raise ValueError("scene needs at least two nonzero points")
    return points[0], points[1]


def _midpoint(grid: list[list[int]]) -> tuple[int, int]:
    (r1, c1), (r2, c2) = _first_two_nonzero(grid)
    dr = 0 if r2 == r1 else (1 if r2 > r1 else -1)
    dc = 0 if c2 == c1 else (1 if c2 > c1 else -1)
    steps = max(abs(r2 - r1), abs(c2 - c1))
    if steps % 2:
        raise ValueError("controller span must have a lattice midpoint")
    return r1 + dr * (steps // 2), c1 + dc * (steps // 2)


def _key_layout(grid: list[list[int]]) -> tuple[int, list[int], dict[int, int]]:
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(anchors) != 1:
        raise ValueError("scene needs one color-9 key-row anchor")
    row = anchors[0][0]
    keyed = [(c, grid[row][c]) for c in range(len(grid[0])) if grid[row][c] in (1, 2, 3)]
    if len(keyed) != 3 or {color for _, color in keyed} != {1, 2, 3}:
        raise ValueError("key row must contain one cell of each key color")
    keyed.sort()
    return row, [column for column, _ in keyed], {column: color for column, color in keyed}


def _payload_output(grid: list[list[int]], color: int) -> list[list[int]]:
    payloads = [obj for obj in _components(grid) if obj["color"] == color and len(obj["cells"]) > 1]
    if len(payloads) != 1:
        raise ValueError(f"expected one payload for key color {color}, found {len(payloads)}")
    out = _blank(len(grid), len(grid[0]))
    for r, c in payloads[0]["cells"]:
        out[r][c] = 8
    return out


def _canonical(grid: list[list[int]]) -> list[list[int]]:
    row, col = _midpoint(grid)
    out = _blank(len(grid), len(grid[0]))
    out[row][col] = 8
    return out


def transform(value: Any, mode: str) -> list[list[int]]:
    grid = validate_grid(value)
    selected = _mode(mode, hypothesis=True)
    if selected == "canonical":
        return _canonical(grid)
    _, columns, colors = _key_layout(grid)
    if selected == "midpoint_key_relay":
        column = _midpoint(grid)[1]
        color = colors[column]
    elif selected == "grid_center_key":
        color = colors[len(grid[0]) // 2]
    elif selected == "left_key":
        color = colors[columns[0]]
    elif selected == "right_key":
        color = colors[columns[-1]]
    elif selected.startswith("constant_color_"):
        color = int(selected[-1])
    else:
        raise ValueError(f"unsupported hypothesis {selected}")
    return _payload_output(grid, color)


def explain_dependency(value: Any) -> dict[str, Any]:
    grid = validate_grid(value)
    midpoint = _midpoint(grid)
    _, columns, colors = _key_layout(grid)
    key_color = colors[midpoint[1]]
    center_color = colors[len(grid[0]) // 2]
    return {
        "step_a": "find the exact midpoint of the first two row-major nonzero endpoints",
        "intermediate": "the key color located in the key row at the midpoint column",
        "step_b": "select the remote payload carrying that key color and repaint its cells color 8",
        "why_b_depends_on_a": "the payload color is not known until midpoint extraction identifies which key cell to read",
        "midpoint": list(midpoint),
        "lane_index": columns.index(midpoint[1]) + 1,
        "key_color": key_color,
        "counterfactual_key_color": center_color,
        "output": transform(grid, "midpoint_key_relay"),
        "counterfactual_output": transform(grid, "grid_center_key"),
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"b35816e8388b-parametric-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _profile(seed: int, split: str, index: int) -> tuple[int, int, int]:
    del seed
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    return profiles[index]


def _mapped_key_colors(seed: int, index: int) -> tuple[int, int, int]:
    base = ((1, 2, 3), (3, 1, 2), (2, 3, 1))[index % 3]
    mappings = ((1, 2, 3), (2, 3, 1), (3, 1, 2), (2, 1, 3), (3, 2, 1), (1, 3, 2))
    mapping = mappings[seed % len(mappings)]
    return tuple(mapping[color - 1] for color in base)


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    height, width, lane = _profile(seed, split, index)
    rng = _rng(seed, split, index)
    grid = _blank(height, width)
    columns = (4, width // 2, width - 5)
    if len(set(columns)) != 3:
        raise ValueError("key columns must be distinct")
    midpoint_column = columns[lane - 1]
    half_span = 2 + ((seed + index) % 2)
    if midpoint_column - half_span < 0 or midpoint_column + half_span >= width:
        half_span = 2
    grid[0][midpoint_column - half_span] = 4
    grid[0][midpoint_column + half_span] = 4

    key_row = 3 + (index % 2)
    grid[key_row][0] = 9
    key_colors = _mapped_key_colors(seed, index)
    for column, color in zip(columns, key_colors):
        grid[key_row][column] = color

    if (height, width) == (30, 30):
        shapes = (_rect(6, 8), _rect(5, 7), _rect(4, 9))
        slots = ((18, 0), (19, 10), (26, 21))
    else:
        shapes = (_rect(3, 4), _l_shape(4, 3), _t_shape(3, 5))
        top = height - 6
        slots = ((top + 1, 0), (top, 6), (top + 2, width - 5))
    payload_colors = [1, 2, 3]
    rng.shuffle(payload_colors)
    for shape, (top, left), color in zip(shapes, slots, payload_colors):
        _paint(grid, shape, top, left, color)

    _paint(grid, _rect(2, 2), key_row + 2, 1, 5)
    _paint(grid, _rect(1, 3), key_row + 3, width // 2 - 1, 6)
    _paint(grid, _rect(3, 1), key_row + 2, width - 2, 7)
    _validate_scene(grid, expected_lane=lane)
    return grid


def _validate_scene(value: Any, *, expected_lane: int | None = None) -> None:
    grid = validate_grid(value)
    first, second = _first_two_nonzero(grid)
    if grid[first[0]][first[1]] != 4 or grid[second[0]][second[1]] != 4 or first[0] != second[0]:
        raise ValueError("the first two nonzero cells must be horizontal color-4 endpoints")
    midpoint = _midpoint(grid)
    _, columns, colors = _key_layout(grid)
    if midpoint[1] not in colors:
        raise ValueError("controller midpoint must align to a key cell")
    lane = columns.index(midpoint[1]) + 1
    if expected_lane is not None and lane != expected_lane:
        raise ValueError(f"observed lane {lane} differs from requested {expected_lane}")
    for color in (1, 2, 3):
        _payload_output(grid, color)


def certificate(train: list[dict[str, Any]], query_inputs: list[list[list[int]]]) -> dict[str, Any]:
    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(transform(pair["input"], hypothesis) == pair["output"] for pair in train)
    ]
    declared = [mode for mode in MODES if mode in survivors]
    selected = declared[0] if len(declared) == 1 else None
    query_changing = []
    if selected is not None:
        for hypothesis in survivors:
            if any(transform(grid, hypothesis) != transform(grid, selected) for grid in query_inputs):
                query_changing.append(hypothesis)
    return {
        "survivors": survivors,
        "selected_declared_mode": selected,
        "query_changing_survivors": query_changing,
        "hypotheses": list(HYPOTHESES),
    }


def build_episode(seed: int, mode: str, demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    selected = _mode(mode)
    seen: set[tuple[tuple[int, ...], ...]] = set()

    def collect(split: str, count: int) -> list[dict[str, list[list[int]]]]:
        pairs = []
        for index in range(count):
            grid = _scene(seed, split, index)
            key = tuple(tuple(row) for row in grid)
            if key in seen:
                raise RuntimeError("scene schedule produced a duplicate input")
            seen.add(key)
            pairs.append({"input": grid, "output": transform(grid, selected)})
        return pairs

    return {
        "train": collect("train", demos),
        "test": collect("test", queries),
        "program_solution": program_for(selected),
    }
