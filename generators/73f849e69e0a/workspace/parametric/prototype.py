#!/usr/bin/env python3
"""Native finite parametric family for 73f849e69e0a.

A locates the first full color-5 separator and extracts the stride-2 logical
3x3 icon above it. The intermediate is ``{separator row, logical icon}``.
B stamps that icon at every red marker either unchanged or rotated clockwise.
Sampling is independent of the hidden orientation setting.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from reviewer_support import normalize_grid

TASK_ID = "73f849e69e0a"
SETTINGS = ({"orientation": "identity"}, {"orientation": "rotate_cw"})
DEFAULT_SETTINGS = SETTINGS[0]
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
HERE = Path(__file__).resolve().parent

# (separator row, marker-field height, width, marker count, icon palette size)
_DEMO_PROFILES = (
    (6, 5, 6, 4, 3),
    (7, 6, 7, 5, 4),
    (8, 7, 8, 6, 4),
    (6, 8, 9, 7, 5),
    (7, 9, 10, 8, 5),
    (8, 10, 9, 9, 6),
)
_QUERY_PROFILES = (
    (7, 6, 8, 5, 4),
    (8, 8, 9, 7, 5),
    (6, 9, 10, 8, 5),
    (8, 10, 10, 10, 6),
)


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"orientation"}:
        raise ValueError("settings must name exactly orientation")
    if value["orientation"] not in ("identity", "rotate_cw"):
        raise ValueError("orientation must be 'identity' or 'rotate_cw'")
    return {"orientation": value["orientation"]}


def _exact_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rotate_cw(icon: list[list[int]]) -> list[list[int]]:
    return [[icon[2 - col][row] for col in range(3)] for row in range(3)]


def _analyze(grid: list[list[int]]) -> dict[str, Any]:
    source = normalize_grid(grid)
    height, width = len(source), len(source[0])
    separator_rows = [row for row in range(height) if all(value == 5 for value in source[row])]
    if len(separator_rows) != 1:
        raise ValueError("input must contain exactly one full color-5 separator row")
    sep_row = separator_rows[0]
    if sep_row < 6 or width < 6 or sep_row + 1 >= height:
        raise ValueError("separator must follow a 6x6 icon and precede a marker field")
    if any(value != 0 for row in source[6:sep_row] for value in row):
        raise ValueError("rows between icon and separator must be zero padding")
    if any(source[row][col] != 0 for row in range(6) for col in range(6, width)):
        raise ValueError("top columns after the 6x6 icon must be zero padding")
    icon = [[0] * 3 for _ in range(3)]
    for icon_row in range(3):
        for icon_col in range(3):
            block = {
                source[2 * icon_row + dr][2 * icon_col + dc]
                for dr in range(2)
                for dc in range(2)
            }
            if len(block) != 1:
                raise ValueError("every encoded icon block must be uniform 2x2")
            value = next(iter(block))
            if value == 5:
                raise ValueError("color 5 is reserved for the separator")
            icon[icon_row][icon_col] = value
    bot_start = sep_row + 1
    bot_h = height - bot_start
    bot_w = width
    if any(value not in (0, 2) for row in source[bot_start:] for value in row):
        raise ValueError("marker field may contain only 0 and 2")
    markers = [
        [row, col]
        for row in range(bot_h)
        for col in range(bot_w)
        if source[bot_start + row][col] == 2
    ]
    if not markers:
        raise ValueError("marker field needs at least one red marker")
    colors = sorted({value for row in icon for value in row if value != 0})
    marker_bbox = [
        min(row for row, _ in markers),
        min(col for _, col in markers),
        max(row for row, _ in markers),
        max(col for _, col in markers),
    ]
    return {
        "source": source,
        "sep_row": sep_row,
        "bot_start": bot_start,
        "bot_h": bot_h,
        "bot_w": bot_w,
        "icon": icon,
        "markers": markers,
        "marker_count": len(markers),
        "marker_bbox": marker_bbox,
        "icon_colors": colors,
    }


def semantic_observables(grid: list[list[int]]) -> dict[str, Any]:
    analysis = _analyze(grid)
    icon = analysis["icon"]
    return {
        "sep_row": analysis["sep_row"],
        "bot_h": analysis["bot_h"],
        "bot_w": analysis["bot_w"],
        "icon": copy.deepcopy(icon),
        "icon_color_count": len(analysis["icon_colors"]),
        "icon_contains_red": 2 in analysis["icon_colors"],
        "icon_asymmetric_under_rotate_cw": icon != _rotate_cw(icon),
        "markers": copy.deepcopy(analysis["markers"]),
        "marker_count": analysis["marker_count"],
        "marker_bbox": analysis["marker_bbox"],
    }


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    orientation = _settings(settings)["orientation"]
    analysis = _analyze(grid)
    icon = analysis["icon"] if orientation == "identity" else _rotate_cw(analysis["icon"])
    output = [[0] * (analysis["bot_w"] * 3) for _ in range(analysis["bot_h"] * 3)]
    for marker_row, marker_col in analysis["markers"]:
        row_origin, col_origin = marker_row * 3, marker_col * 3
        for icon_row in range(3):
            for icon_col in range(3):
                value = icon[icon_row][icon_col]
                if value != 0:
                    output[row_origin + icon_row][col_origin + icon_col] = value
    return output


def program(settings: dict[str, Any]) -> str:
    orientation = _settings(settings)["orientation"]
    return (HERE / "rules" / f"{orientation}.rkt").read_text(encoding="utf-8")


def digest(grid: list[list[int]]) -> str:
    normalized = normalize_grid(grid)
    return hashlib.sha256(
        json.dumps(normalized, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}|v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _icon(rng: random.Random, palette_size: int) -> list[list[int]]:
    pool = [1, 3, 4, 6, 7, 8, 9]
    rng.shuffle(pool)
    colors = [2] + pool[: palette_size - 1]
    # Two unequal zero corners make the geometry decisively non-rotation-invariant;
    # cycling the shuffled colors varies payload while preserving all palette roles.
    active = ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2))
    values = (colors * ((len(active) + len(colors) - 1) // len(colors)))[: len(active)]
    icon = [[0] * 3 for _ in range(3)]
    for (row, col), value in zip(active, values):
        icon[row][col] = value
    if icon == _rotate_cw(icon):
        raise AssertionError("constructed icon unexpectedly has clockwise symmetry")
    if len({value for row in icon for value in row if value}) < 3:
        raise AssertionError("constructed icon lacks decisive color roles")
    return icon


def _markers(rng: random.Random, height: int, width: int, count: int) -> list[tuple[int, int]]:
    forced = [(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)]
    forced = list(dict.fromkeys(forced))
    cells = [(row, col) for row in range(height) for col in range(width) if (row, col) not in forced]
    rng.shuffle(cells)
    return forced + cells[: count - len(forced)]


def _build_input(seed: int, split: str, index: int, profile: tuple[int, ...]) -> list[list[int]]:
    sep_row, bot_h, bot_w, marker_count, palette_size = profile
    rng = _rng(seed, split, index)
    icon = _icon(rng, palette_size)
    height = sep_row + 1 + bot_h
    grid = [[0] * bot_w for _ in range(height)]
    for icon_row in range(3):
        for icon_col in range(3):
            value = icon[icon_row][icon_col]
            for dr in range(2):
                for dc in range(2):
                    grid[2 * icon_row + dr][2 * icon_col + dc] = value
    grid[sep_row] = [5] * bot_w
    for marker_row, marker_col in _markers(rng, bot_h, bot_w, marker_count):
        grid[sep_row + 1 + marker_row][marker_col] = 2
    facts = semantic_observables(grid)
    if (
        facts["sep_row"] != sep_row
        or facts["marker_count"] != marker_count
        or facts["icon_color_count"] != palette_size
        or not facts["icon_contains_red"]
        or not facts["icon_asymmetric_under_rotate_cw"]
    ):
        raise AssertionError("constructed scene failed its declared profile")
    return grid


def _input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    return _build_input(seed, split, index, profiles[index])


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    seed = _exact_int("seed", seed, 0, 2**63 - 1)
    selected = _settings(settings)
    demos = _exact_int("demos", demos, *DEMO_LIMITS)
    queries = _exact_int("queries", queries, *QUERY_LIMITS)

    def pairs(split: str, count: int) -> list[dict[str, list[list[int]]]]:
        result = []
        for index in range(count):
            input_grid = _input(seed, split, index)
            result.append({"input": input_grid, "output": transform(input_grid, selected)})
        return result

    train = pairs("demo", demos)
    test = pairs("query", queries)
    inputs = [pair["input"] for pair in train + test]
    if len({digest(grid) for grid in inputs}) != len(inputs):
        raise RuntimeError("constructed inputs are not distinct")
    return {"train": train, "test": test, "program_solution": program(selected)}
