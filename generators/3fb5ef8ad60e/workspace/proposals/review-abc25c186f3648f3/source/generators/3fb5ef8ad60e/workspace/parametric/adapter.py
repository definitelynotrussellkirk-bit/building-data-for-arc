"""Native quadrant-summary family with an indexed color-controlled rotation.

The default setting returns the exact selected canonical Racket program.  The
alternative first computes that canonical 2x2 summary.  A 1..4-hole code in a
fixed cyan-border control strip selects one summary cell; the selected color's
value modulo four determines the final quarter-turn rotation.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import random
from typing import Any

HOME = Path(__file__).resolve().parent
TASK_ID = "3fb5ef8ad60e"
MODES = ("quadrant_summary", "indexed_color_rotate")
PROGRAM_FILES = {
    "quadrant_summary": "canonical.rkt",
    "indexed_color_rotate": "indexed_color_rotate.rkt",
}
PALETTE = (1, 2, 3, 5)
# height, width, selected summary index, required selected color
TRAIN_PROFILES = (
    (14, 15, 0, 1),
    (16, 17, 2, 2),
    (18, 20, 3, 3),
    (20, 19, 1, 5),
    (22, 24, 2, 1),
    (25, 23, 0, 2),
)
QUERY_PROFILES = (
    (15, 19, 1, 3),
    (19, 22, 3, 5),
    (26, 24, 0, 2),
    (30, 30, 2, 1),
)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"finish_mode"}:
        raise ValueError("settings must contain exactly finish_mode")
    mode = settings["finish_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("finish_mode must be quadrant_summary or indexed_color_rotate")
    return mode


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 by 1..30 with exact integer colors 0..9")
    return [row[:] for row in grid]


def program(settings: dict[str, Any]) -> str:
    return (HOME / PROGRAM_FILES[_mode(settings)]).read_text()


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _color_centers(grid: list[list[int]]) -> list[tuple[int, Fraction, Fraction]]:
    order: list[int] = []
    cells: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for column, value in enumerate(values):
            if value in (0, 8):
                continue
            if value not in cells:
                order.append(value)
                cells[value] = []
            cells[value].append((row, column))
    if not order:
        raise ValueError("scene needs colored block cells")
    return [
        (
            color,
            Fraction(sum(row for row, _ in cells[color]), len(cells[color])),
            Fraction(sum(column for _, column in cells[color]), len(cells[color])),
        )
        for color in order
    ]


def quadrant_summary(grid: Any) -> list[list[int]]:
    source = validate_grid(grid)
    blocks = _color_centers(source)
    row_centers = sorted(row for _, row, _ in blocks)
    column_centers = sorted(column for _, _, column in blocks)
    mid_row = (row_centers[0] + row_centers[-1]) / 2
    mid_column = (column_centers[0] + column_centers[-1]) / 2
    result = [[0, 0], [0, 0]]
    for color, row, column in blocks:
        result[0 if row <= mid_row else 1][0 if column <= mid_column else 1] = color
    return result


def eight_bbox(grid: Any) -> tuple[int, int, int, int]:
    source = validate_grid(grid)
    cells = [(r, c) for r, row in enumerate(source) for c, value in enumerate(row) if value == 8]
    if not cells:
        raise ValueError("scene needs a cyan rectangle")
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def selector_index(grid: Any) -> int:
    source = validate_grid(grid)
    r0, c0, _r1, c1 = eight_bbox(source)
    if c0 + 4 > c1:
        raise ValueError("cyan rectangle is too narrow for the four-cell control strip")
    holes = sum(source[r0][column] == 0 for column in range(c0 + 1, c0 + 5))
    if not 1 <= holes <= 4:
        raise ValueError("control strip must contain one through four holes")
    return holes - 1


def rotate_by_color(summary: Any, color: Any) -> list[list[int]]:
    grid = validate_grid(summary)
    if (len(grid), len(grid[0])) != (2, 2):
        raise ValueError("summary must be 2x2")
    if type(color) is not int or not 0 <= color <= 9:
        raise ValueError("selected color must be an exact ARC color")
    turns = color % 4
    if turns == 0:
        return grid
    if turns == 1:
        return _rotate_cw(grid)
    if turns == 2:
        return _rotate_180(grid)
    return _rotate_ccw(grid)


def transform(grid: Any, settings: dict[str, Any]) -> list[list[int]]:
    mode = _mode(settings)
    summary = quadrant_summary(grid)
    if mode == "quadrant_summary":
        return summary
    index = selector_index(grid)
    selected = summary[index // 2][index % 2]
    return rotate_by_color(summary, selected)


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(sha256(raw).digest(), "big"))


def _profile(split: str, index: int) -> tuple[int, int, int, int]:
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    if not 0 <= index < len(profiles):
        raise ValueError("profile index outside the authored bank")
    return profiles[index]


def _draw_scene(seed: int, split: str, index: int) -> list[list[int]]:
    height, width, selected_index, selected_color = _profile(split, index)
    rng = _rng(seed, split, index)
    grid = [[0] * width for _ in range(height)]
    r0, c0, r1, c1 = 2, 2, height - 3, width - 3
    for row in range(r0, r1 + 1):
        for column in range(c0, c1 + 1):
            grid[row][column] = 8

    remaining = [color for color in PALETTE if color != selected_color]
    rng.shuffle(remaining)
    colors = remaining[:]
    colors.insert(selected_index, selected_color)

    placements: dict[int, tuple[int, int]] = {}
    max_row_jitter = max(0, min(2, (r1 - r0 - 8) // 2))
    max_col_jitter = max(0, min(2, (c1 - c0 - 8) // 2))
    for quadrant in range(4):
        top = quadrant < 2
        left = quadrant % 2 == 0
        block_row = (r0 + 2 + rng.randint(0, max_row_jitter)) if top else (r1 - 3 - rng.randint(0, max_row_jitter))
        block_column = (c0 + 2 + rng.randint(0, max_col_jitter)) if left else (c1 - 3 - rng.randint(0, max_col_jitter))
        placements[quadrant] = (block_row, block_column)
        for row in (block_row, block_row + 1):
            for column in (block_column, block_column + 1):
                grid[row][column] = colors[quadrant]

    # The fixed strip location reveals only which intermediate cell to read.  It
    # does not reveal the selected cell's color or the resulting rotation.
    for offset in range(selected_index + 1):
        grid[r0][c0 + 1 + offset] = 0

    summary = quadrant_summary(grid)
    if summary[selected_index // 2][selected_index % 2] != selected_color:
        raise AssertionError("authored selector cell does not hold the required color")
    if selector_index(grid) != selected_index:
        raise AssertionError("selector strip did not round-trip")
    return grid


def _pair(grid: list[list[int]], settings: dict[str, Any]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": transform(grid, settings)}


def fit_settings(demos: list[dict[str, Any]]) -> list[dict[str, str]]:
    survivors = []
    for mode in MODES:
        setting = {"finish_mode": mode}
        if demos and all(transform(pair["input"], setting) == pair["output"] for pair in demos):
            survivors.append(setting)
    return survivors


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    chosen = {"finish_mode": _mode(settings)}
    train = [_pair(_draw_scene(seed, "train", index), chosen) for index in range(demos)]
    test = [_pair(_draw_scene(seed, "test", index), chosen) for index in range(queries)]
    if fit_settings(train) != [chosen]:
        raise RuntimeError("demonstrations do not uniquely identify finish_mode")
    encoded = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(encoded) != len(set(encoded)):
        raise RuntimeError("episode contains duplicate inputs")
    return {"train": train, "test": test, "program_solution": program(chosen)}
