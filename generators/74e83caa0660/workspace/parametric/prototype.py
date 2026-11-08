"""Parametric completion episodes for 74e83caa0660; proposed, not accepted."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

TASK_ID = "74e83caa0660"
SCHEMA = "arcpuzzles-orientation-motif-v1"
HOME = Path(__file__).resolve().parent
COMPLETION_RULES = ("canonical_x", "orientation_selects_motif")
CANONICAL_PROGRAM_SHA256 = "68e47a26ff0abe8bb0faaa99d52c81735b38eecee1aa7a3aded589884fc4a74b"
DEMO_PROFILES = (
    (9, 12, 3),
    (12, 15, 4),
    (15, 18, 5),
    (18, 21, 6),
    (21, 24, 7),
    (24, 27, 8),
)
QUERY_PROFILES = (
    (10, 14, 3),
    (16, 20, 5),
    (24, 27, 7),
    (30, 30, 8),
)


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings: object) -> dict[str, str]:
    if (
        type(settings) is not dict
        or set(settings) != {"completion_rule"}
        or type(settings["completion_rule"]) is not str
        or settings["completion_rule"] not in COMPLETION_RULES
    ):
        raise ValueError(
            "settings must contain exactly completion_rule="
            "canonical_x|orientation_selects_motif"
        )
    return {"completion_rule": settings["completion_rule"]}


def program(settings: object) -> str:
    rule = settings_value(settings)["completion_rule"]
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


def _rng(seed: int, split: str, index: int, height: int, width: int, pair_count: int) -> random.Random:
    raw = json.dumps(
        [TASK_ID, SCHEMA, seed, split, index, height, width, pair_count],
        separators=(",", ":"),
    ).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def pairs(grid: object) -> list[dict[str, object]]:
    grid = strict_grid(grid)
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))
    if not by_color:
        raise ValueError("pair grammar requires at least one active color")
    result: list[dict[str, object]] = []
    reserved: set[tuple[int, int]] = set()
    for color, cells in sorted(by_color.items()):
        if len(cells) != 2:
            raise ValueError(f"color {color} must occur exactly twice")
        (r0, c0), (r1, c1) = sorted(cells)
        if r1 - r0 != 2 or abs(c1 - c0) != 2:
            raise ValueError(f"color {color} must occupy opposite corners of an exact 3x3 box")
        left = min(c0, c1)
        box = {(r, c) for r in range(r0, r0 + 3) for c in range(left, left + 3)}
        if box & reserved:
            raise ValueError("pair boxes must be disjoint")
        reserved.update(box)
        result.append(
            {
                "color": color,
                "top": r0,
                "left": left,
                "orientation": "main" if c1 > c0 else "anti",
                "cells": tuple(cells),
            }
        )
    if len(result) > 8:
        raise ValueError("pair grammar supports at most eight colors")
    return result


def _paint_x(out: list[list[int]], top: int, left: int, color: int) -> None:
    for offset in range(3):
        out[top + offset][left + offset] = color
        out[top + offset][left + 2 - offset] = color


def _paint_plus(out: list[list[int]], top: int, left: int, color: int) -> None:
    for offset in range(3):
        out[top + 1][left + offset] = color
        out[top + offset][left + 1] = color


def transform(grid: object, settings: object) -> list[list[int]]:
    source = strict_grid(grid)
    rule = settings_value(settings)["completion_rule"]
    out = [[0] * len(source[0]) for _ in source]
    for pair in pairs(source):
        top, left, color = int(pair["top"]), int(pair["left"]), int(pair["color"])
        if rule == "canonical_x" or pair["orientation"] == "main":
            _paint_x(out, top, left, color)
        else:
            _paint_plus(out, top, left, color)
    return out


def _spread_indices(total: int, count: int) -> list[int]:
    if count == 1:
        return [total // 2]
    return [round(index * (total - 1) / (count - 1)) for index in range(count)]


def sample_input(
    seed: int,
    split: str,
    index: int,
    *,
    height: int | None = None,
    width: int | None = None,
    pair_count: int | None = None,
) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 10_000, "index")
    if type(split) is not str or not split:
        raise ValueError("split must be a nonempty string")
    if height is None or width is None or pair_count is None:
        profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
        if not 0 <= index < len(profiles):
            raise ValueError("profile index out of range")
        default_h, default_w, default_pairs = profiles[index]
        height = default_h if height is None else height
        width = default_w if width is None else width
        pair_count = default_pairs if pair_count is None else pair_count
    height = _integer(height, 5, 30, "height")
    width = _integer(width, 5, 30, "width")
    pair_count = _integer(pair_count, 1, 8, "pair_count")
    row_slots, col_slots = height // 3, width // 3
    capacity = row_slots * col_slots
    if pair_count > capacity:
        raise ValueError(
            f"{height}x{width} supports {capacity} disjoint 3x3 boxes, not {pair_count}"
        )
    rng = _rng(seed, split, index, height, width, pair_count)
    row_margin, col_margin = height - 3 * row_slots, width - 3 * col_slots
    row_offset = rng.randint(0, row_margin)
    col_offset = rng.randint(0, col_margin)
    candidates = [
        (row_offset + 3 * row, col_offset + 3 * col)
        for row in range(row_slots)
        for col in range(col_slots)
    ]
    selected = [candidates[i] for i in _spread_indices(len(candidates), pair_count)]
    colors = list(range(1, 10))
    rng.shuffle(colors)
    colors = colors[:pair_count]
    start = rng.randrange(2)
    orientations = ["main" if (start + i) % 2 == 0 else "anti" for i in range(pair_count)]
    if pair_count == 1:
        orientations[0] = rng.choice(("main", "anti"))
    ordering = list(range(pair_count))
    rng.shuffle(ordering)
    grid = [[0] * width for _ in range(height)]
    for output_index, source_index in enumerate(ordering):
        top, left = selected[source_index]
        color = colors[output_index]
        orientation = orientations[source_index]
        if orientation == "main":
            endpoints = ((top, left), (top + 2, left + 2))
        else:
            endpoints = ((top, left + 2), (top + 2, left))
        for r, c in endpoints:
            grid[r][c] = color
    extracted = pairs(grid)
    if pair_count >= 2 and {pair["orientation"] for pair in extracted} != {"main", "anti"}:
        raise RuntimeError("constructed lesson lost one orientation branch")
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
