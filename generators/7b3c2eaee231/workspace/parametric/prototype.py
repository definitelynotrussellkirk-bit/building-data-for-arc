"""Parametric packing episodes for 7b3c2eaee231; proposed, not accepted."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "7b3c2eaee231"
SCHEMA = "arcpuzzles-packing-axis-v1"
HOME = Path(__file__).resolve().parent
PACKING_RULES = ("canonical", "tallest_color_axis")
CANONICAL_PROGRAM_SHA256 = "afe9721b6609ea3f3ec4f6bddf3e0be9a1598a70b8826b6ab1f0ece5b27a3beb"
DEMO_PROFILES = (
    (10, 15, "even"),
    (11, 16, "odd"),
    (14, 18, "even"),
    (16, 21, "odd"),
    (20, 24, "even"),
    (24, 27, "odd"),
)
QUERY_PROFILES = (
    (12, 17, "odd"),
    (18, 21, "even"),
    (24, 27, "odd"),
    (30, 30, "even"),
)
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings: object) -> dict[str, str]:
    if (
        type(settings) is not dict
        or set(settings) != {"packing_rule"}
        or type(settings["packing_rule"]) is not str
        or settings["packing_rule"] not in PACKING_RULES
    ):
        raise ValueError("settings must contain exactly packing_rule=canonical|tallest_color_axis")
    return {"packing_rule": settings["packing_rule"]}


def program(settings: object) -> str:
    rule = settings_value(settings)["packing_rule"]
    return (HOME / "rules" / f"{rule}.rkt").read_text(encoding="utf-8")


def strict_grid(grid: object) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid requires rectangular rows and exact integer colors 0..9")
    return grid


def _rng(seed: int, split: str, index: int, height: int, width: int, parity: str) -> random.Random:
    raw = json.dumps(
        [TASK_ID, SCHEMA, seed, split, index, height, width, parity],
        separators=(",", ":"),
    ).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def components(grid: object) -> list[dict[str, object]]:
    grid = strict_grid(grid)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, object]] = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0, c0, r1, c1 = _bbox(cells)
            crop = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
            for rr, cc in cells:
                crop[rr - r0][cc - c0] = color
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "height": len(crop),
                    "width": len(crop[0]),
                    "crop": crop,
                }
            )
    if len(result) != 3 or len({item["color"] for item in result}) != 3:
        raise ValueError("packing grammar requires exactly three distinct monochrome objects")
    return result


def control_color(grid: object) -> int:
    objects = components(grid)
    controller = min(
        objects,
        key=lambda item: (-int(item["height"]), -int(item["width"]), int(item["color"])),
    )
    return int(controller["color"])


def _hstack_center(crops: list[list[list[int]]]) -> list[list[int]]:
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    out = [[0] * width for _ in range(height)]
    left = 0
    for crop in crops:
        top = (height - len(crop)) // 2
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value:
                    out[top + r][left + c] = value
        left += len(crop[0]) + 1
    return out


def _vstack_center(crops: list[list[list[int]]]) -> list[list[int]]:
    height = sum(len(crop) for crop in crops) + len(crops) - 1
    width = max(len(crop[0]) for crop in crops)
    out = [[0] * width for _ in range(height)]
    top = 0
    for crop in crops:
        left = (width - len(crop[0])) // 2
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value:
                    out[top + r][left + c] = value
        top += len(crop) + 1
    return out


def transform(grid: object, settings: object) -> list[list[int]]:
    rule = settings_value(settings)["packing_rule"]
    objects = components(grid)
    if rule == "canonical" or control_color(grid) % 2 == 0:
        ordered = sorted(
            objects,
            key=lambda item: (int(item["width"]), int(item["height"]), int(item["color"])),
        )
        return _hstack_center([item["crop"] for item in ordered])
    ordered = sorted(
        objects,
        key=lambda item: (int(item["height"]), int(item["width"]), int(item["color"])),
    )
    return _vstack_center([item["crop"] for item in ordered])


def _connected_shape(height: int, width: int, rng: random.Random) -> set[tuple[int, int]]:
    cells = {(0, c) for c in range(width)} | {(r, 0) for r in range(height)}
    target = max(len(cells), round(height * width * 0.58))
    while len(cells) < target:
        frontier = sorted(
            {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in _CARDINAL
                if 0 <= r + dr < height
                and 0 <= c + dc < width
                and (r + dr, c + dc) not in cells
            }
        )
        if not frontier:
            break
        cells.add(rng.choice(frontier))
    return cells


def sample_input(
    seed: int,
    split: str,
    index: int,
    *,
    height: int | None = None,
    width: int | None = None,
    control_parity: str | None = None,
) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 10_000, "index")
    if type(split) is not str or not split:
        raise ValueError("split must be a nonempty string")
    if height is None or width is None or control_parity is None:
        profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
        if not 0 <= index < len(profiles):
            raise ValueError("profile index out of range")
        default_h, default_w, default_parity = profiles[index]
        height = default_h if height is None else height
        width = default_w if width is None else width
        control_parity = default_parity if control_parity is None else control_parity
    height = _integer(height, 9, 30, "height")
    width = _integer(width, 13, 30, "width")
    if control_parity not in {"even", "odd"}:
        raise ValueError("control_parity must be even or odd")
    rng = _rng(seed, split, index, height, width, control_parity)

    boundaries = (0, width // 3, (2 * width) // 3, width)
    usable_widths = [boundaries[i + 1] - boundaries[i] - (1 if i < 2 else 0) for i in range(3)]
    max_width = min(usable_widths)
    if max_width < 3:
        raise ValueError("canvas is too narrow for three separated objects")
    max_height = min(height - 1, max(5, round(height * 0.36)))
    widths = (max(2, max_width - 2), max(3, max_width - 1), max(3, max_width - 1))
    heights = (max(2, max_height - 4), max(3, max_height - 2), max_height)

    parity_colors = [2, 4, 6, 8] if control_parity == "even" else [1, 3, 5, 7, 9]
    control = rng.choice(parity_colors)
    other_colors = [color for color in range(1, 10) if color != control]
    rng.shuffle(other_colors)
    colors = [other_colors[0], other_colors[1], control]
    objects = []
    for object_index, (shape_h, shape_w, color) in enumerate(zip(heights, widths, colors)):
        shape_rng = _rng(seed, split + ":shape", index * 3 + object_index, shape_h, shape_w, control_parity)
        objects.append((shape_h, shape_w, color, _connected_shape(shape_h, shape_w, shape_rng)))
    rng.shuffle(objects)

    grid = [[0] * width for _ in range(height)]
    for strip, (shape_h, shape_w, color, cells) in enumerate(objects):
        start, stop = boundaries[strip], boundaries[strip + 1]
        if strip < 2:
            stop -= 1
        if stop - start < shape_w:
            raise ValueError("shape does not fit its separated strip")
        top = rng.randint(0, height - shape_h)
        left = rng.randint(start, stop - shape_w)
        for r, c in cells:
            grid[top + r][left + c] = color
    components(grid)
    if control_color(grid) != control:
        raise RuntimeError("constructed controller object was not uniquely selected")
    return grid


def generate(seed: int, settings: object, demos: int, queries: int) -> dict[str, object]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    normalized = settings_value(settings)
    train_inputs = [sample_input(seed, "demo", index) for index in range(demos)]
    query_bank = [sample_input(seed, "query", index) for index in range(4)]
    make_pair = lambda grid: {"input": grid, "output": transform(grid, normalized)}
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": normalized,
        "train": [make_pair(grid) for grid in train_inputs],
        "test": [make_pair(grid) for grid in query_bank[:queries]],
        "program_solution": program(normalized),
    }
