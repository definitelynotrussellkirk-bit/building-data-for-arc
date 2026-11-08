"""Native row/column endpoint connection family for 539d4ac45311.

Inputs are shared across settings. ``cascade`` applies the exact horizontal
rule first, then runs the vertical analogue on that input-dependent result.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
MODES = ("horizontal", "vertical", "cascade")
DEFAULT = {"connection_mode": "horizontal"}


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"connection_mode"}
            or type(settings["connection_mode"]) is not str
            or settings["connection_mode"] not in MODES):
        raise ValueError("settings must contain only a supported connection_mode")
    return settings["connection_mode"]


def program(settings) -> str:
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "horizontal" else f"{mode}.rkt"
    return (HERE / name).read_text()


def _validate_grid(grid) -> tuple[int, int]:
    if (type(grid) is not list or not 5 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 5 <= len(grid[0]) <= 30):
        raise ValueError("expected a rectangular 5..30 grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid cells must be exact ARC integer colors")
    return len(grid), width


def _unique_nonzero(values):
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _connect_rows(grid):
    height, width = _validate_grid(grid)
    source = [list(row) for row in grid]
    out = [list(row) for row in grid]
    for row in range(height):
        for color in _unique_nonzero(source[row]):
            hits = [column for column in range(width) if source[row][column] == color]
            if len(hits) == 2 and all(source[row][column] == 0 for column in range(hits[0] + 1, hits[1])):
                for column in range(hits[0], hits[1] + 1):
                    out[row][column] = color
    return out


def _connect_columns(grid):
    height, width = _validate_grid(grid)
    source = [list(row) for row in grid]
    out = [list(row) for row in grid]
    for column in range(width):
        for color in _unique_nonzero([source[row][column] for row in range(height)]):
            hits = [row for row in range(height) if source[row][column] == color]
            if len(hits) == 2 and all(source[row][column] == 0 for row in range(hits[0] + 1, hits[1])):
                for row in range(hits[0], hits[1] + 1):
                    out[row][column] = color
    return out


def solve(grid, connection_mode="horizontal"):
    if type(connection_mode) is not str or connection_mode not in MODES:
        raise ValueError("unknown connection mode")
    _validate_grid(grid)
    if connection_mode == "horizontal":
        return _connect_rows(grid)
    if connection_mode == "vertical":
        return _connect_columns(grid)
    return _connect_columns(_connect_rows(grid))


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"539d4ac45311-parametric-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _put(grid, row: int, column: int, color: int) -> None:
    if grid[row][column] != 0:
        raise ValueError("profile placement collision")
    grid[row][column] = color


def _block(grid, r1: int, r2: int, c1: int, c2: int, color: int) -> None:
    if not (r1 < r2 and c1 < c2):
        raise ValueError("block needs positive extent")
    if any(grid[r][c] for r, c in ((r1, c1), (r1, c2), (r2, c1), (r2, c2))):
        raise ValueError("block corner collision")
    if any(grid[r][c] for r in (r1, r2) for c in range(c1, c2 + 1)):
        raise ValueError("block row segment is occupied")
    for r, c in ((r1, c1), (r1, c2), (r2, c1), (r2, c2)):
        _put(grid, r, c, color)


def _cross(grid, row: int, c1: int, c2: int, column: int, r1: int, r2: int,
           horizontal_color: int, vertical_color: int) -> None:
    if not (c1 < column < c2 and r1 < row < r2):
        raise ValueError("cross needs a strict interior intersection")
    if any(grid[row][c] for c in range(c1, c2 + 1)):
        raise ValueError("cross row is occupied")
    if any(grid[r][column] for r in range(r1, r2 + 1)):
        raise ValueError("cross column is occupied")
    _put(grid, row, c1, horizontal_color)
    _put(grid, row, c2, horizontal_color)
    _put(grid, r1, column, vertical_color)
    _put(grid, r2, column, vertical_color)


def _profile(seed: int, split: str, index: int):
    demo_sizes = ((12, 16), (14, 18), (8, 12), (18, 20), (24, 27), (22, 26))
    query_sizes = ((9, 13), (18, 22), (30, 30), (27, 29))
    height, width = (demo_sizes if split == "train" else query_sizes)[index]
    rng = _rng(seed, split, index)
    colors = list(range(1, 10))
    rng.shuffle(colors)
    grid = [[0] * width for _ in range(height)]

    rh = max(2, height // 5)
    cw = max(3, width // 5)
    specs = [
        (0, rh, 0, cw),
        (0, rh, width - 1 - cw, width - 1),
        (height - 1 - rh, height - 1, 0, cw),
        (height - 1 - rh, height - 1, width - 1 - cw, width - 1),
    ]
    if height >= 18 and width >= 20:
        mid_top = max(rh + 2, height // 3 - 1)
        mid_bottom = min(height - rh - 3, mid_top + max(2, height // 8))
        specs.extend([
            (mid_top, mid_bottom, 1, max(4, width // 4)),
            (mid_top, mid_bottom, min(width - 5, width - 1 - width // 4), width - 2),
        ])
    for color, spec in zip(colors, specs):
        _block(grid, *spec, color)

    row = height // 2
    column = width // 2
    r1, r2 = max(rh + 1, row - 2), min(height - rh - 2, row + 2)
    if not r1 < row < r2:
        r1, r2 = row - 1, row + 1
    _cross(grid, row, cw + 1, width - cw - 2, column, r1, r2,
           colors[len(specs)], colors[len(specs) + 1])

    if rng.randrange(2):
        grid.reverse()
    if rng.randrange(2):
        grid = [list(reversed(line)) for line in grid]
    return grid


def generate(seed, settings, demos, queries):
    mode = _mode(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    banks = {
        "train": [_profile(seed, "train", index) for index in range(6)],
        "test": [_profile(seed, "test", index) for index in range(4)],
    }
    result = {}
    for split, count in (("train", demos), ("test", queries)):
        result[split] = [
            {"input": copy.deepcopy(grid), "output": solve(grid, mode)}
            for grid in banks[split][:count]
        ]
    return {**result, "program_solution": program(settings), "seed": seed,
            "settings": copy.deepcopy(settings)}


def public_turn(episode, query_index):
    _integer(query_index, 0, 3, "query_index")
    if (type(episode) is not dict or type(episode.get("train")) is not list
            or type(episode.get("test")) is not list or query_index >= len(episode["test"])):
        raise ValueError("episode does not contain the requested query")
    return {"train": copy.deepcopy(episode["train"]),
            "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}]}
