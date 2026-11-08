#!/usr/bin/env python3
"""Native finite parametric family for 78fd2bcdbb99.

A computes both mirror mismatch counts and selects left/right on ties.
The intermediate is that input-dependent selected axis. B then applies one of
exactly two episode-fixed repair policies on the same near-symmetric scene:
``fill`` restores a missing mirror value, while ``erase`` removes its unmatched
nonzero mate. Input sampling never depends on the hidden policy.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from reviewer_support import normalize_grid

TASK_ID = "78fd2bcdbb99"
SETTINGS = ({"repair": "fill"}, {"repair": "erase"})
DEFAULT_SETTINGS = SETTINGS[0]
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
HERE = Path(__file__).resolve().parent

# (height, width, selected axis, palette size, missing pairs, density)
_DEMO_PROFILES = (
    (7, 9, "lr", 2, 2, 0.32),
    (8, 8, "ud", 2, 3, 0.34),
    (9, 11, "lr", 3, 3, 0.38),
    (10, 10, "ud", 3, 4, 0.40),
    (12, 13, "lr", 4, 5, 0.36),
    (14, 12, "ud", 4, 6, 0.40),
)
_QUERY_PROFILES = (
    (12, 16, "ud", 3, 5, 0.32),
    (18, 21, "lr", 4, 8, 0.28),
    (24, 19, "ud", 4, 10, 0.30),
    (30, 30, "lr", 5, 18, 0.35),
)


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"repair"}:
        raise ValueError("settings must name exactly repair")
    if value["repair"] not in ("fill", "erase"):
        raise ValueError("repair must be 'fill' or 'erase'")
    return {"repair": value["repair"]}


def _exact_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mirror(height: int, width: int, axis: str, row: int, col: int) -> tuple[int, int]:
    return (row, width - 1 - col) if axis == "lr" else (height - 1 - row, col)


def _mismatch_count(grid: list[list[int]], axis: str) -> int:
    height, width = len(grid), len(grid[0])
    return sum(
        grid[row][col] != grid[mirror_row][mirror_col]
        for row in range(height)
        for col in range(width)
        for mirror_row, mirror_col in [_mirror(height, width, axis, row, col)]
    )


def selected_axis(grid: list[list[int]]) -> str:
    grid = normalize_grid(grid)
    return "lr" if _mismatch_count(grid, "lr") <= _mismatch_count(grid, "ud") else "ud"


def semantic_observables(grid: list[list[int]]) -> dict[str, Any]:
    grid = normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    axis = selected_axis(grid)
    fillable: list[list[int]] = []
    orphan_nonzero: list[list[int]] = []
    occupied: list[tuple[int, int]] = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            mirror_row, mirror_col = _mirror(height, width, axis, row, col)
            mirror = grid[mirror_row][mirror_col]
            if value == 0 and mirror != 0:
                fillable.append([row, col])
            if value != 0 and mirror == 0:
                orphan_nonzero.append([row, col])
            if value != 0:
                occupied.append((row, col))
    colors = sorted({grid[row][col] for row, col in occupied})
    bbox = None
    if occupied:
        bbox = [
            min(row for row, _ in occupied),
            min(col for _, col in occupied),
            max(row for row, _ in occupied),
            max(col for _, col in occupied),
        ]
    return {
        "height": height,
        "width": width,
        "lr_mismatches": _mismatch_count(grid, "lr"),
        "ud_mismatches": _mismatch_count(grid, "ud"),
        "selected_axis": axis,
        "palette_size": len(colors),
        "colors": colors,
        "fillable_count": len(fillable),
        "orphan_nonzero_count": len(orphan_nonzero),
        "nonzero_count": len(occupied),
        "bbox": bbox,
    }


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    policy = _settings(settings)["repair"]
    source = normalize_grid(grid)
    height, width = len(source), len(source[0])
    axis = selected_axis(source)
    output = copy.deepcopy(source)
    for row in range(height):
        for col in range(width):
            mirror_row, mirror_col = _mirror(height, width, axis, row, col)
            value = source[row][col]
            mirror = source[mirror_row][mirror_col]
            if policy == "fill" and value == 0 and mirror != 0:
                output[row][col] = mirror
            elif policy == "erase" and value != 0 and mirror == 0:
                output[row][col] = 0
    return output


def program(settings: dict[str, Any]) -> str:
    policy = _settings(settings)["repair"]
    return (HERE / "rules" / f"{policy}.rkt").read_text(encoding="utf-8")


def digest(grid: list[list[int]]) -> str:
    normalized = normalize_grid(grid)
    body = json.dumps(normalized, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(body).hexdigest()


def _rng(seed: int, split: str, index: int, attempt: int) -> random.Random:
    material = f"{TASK_ID}|v1|{seed}|{split}|{index}|{attempt}".encode()
    number = int.from_bytes(hashlib.sha256(material).digest()[:16], "big")
    return random.Random(number)


def _half_cells(height: int, width: int, axis: str) -> list[tuple[int, int]]:
    if axis == "lr":
        return [(row, col) for row in range(height) for col in range(width // 2)]
    return [(row, col) for row in range(height // 2) for col in range(width)]


def _forced_cells(height: int, width: int, axis: str) -> list[tuple[int, int]]:
    if axis == "lr":
        return [(0, 0), (height - 1, 0), (height // 3, width // 2 - 1),
                (max(0, height - 1 - height // 3), width // 2 - 1)]
    return [(0, 0), (0, width - 1), (height // 2 - 1, width // 3),
            (height // 2 - 1, max(0, width - 1 - width // 3))]


def _build_scene(seed: int, split: str, index: int, profile: tuple[Any, ...]) -> list[list[int]]:
    height, width, axis, palette_size, holes, density = profile
    candidates = _half_cells(height, width, axis)
    forced = list(dict.fromkeys(_forced_cells(height, width, axis)))
    minimum = max(len(forced), holes + 2, palette_size * 2)
    target_pairs = min(len(candidates), max(minimum, int(round(len(candidates) * density))))
    if target_pairs <= holes or len(candidates) < minimum:
        raise ValueError("profile cannot support the requested teaching scene")

    for attempt in range(64):
        rng = _rng(seed, split, index, attempt)
        palette = list(range(1, 10))
        rng.shuffle(palette)
        palette = palette[:palette_size]
        remaining = [cell for cell in candidates if cell not in forced]
        rng.shuffle(remaining)
        chosen = forced + remaining[: target_pairs - len(forced)]
        grid = [[0] * width for _ in range(height)]
        for position, (row, col) in enumerate(chosen):
            mirror_row, mirror_col = _mirror(height, width, axis, row, col)
            # Forced opposite boundaries deliberately receive different colors,
            # making the nonselected axis substantially worse.
            color = palette[position % len(palette)]
            grid[row][col] = color
            grid[mirror_row][mirror_col] = color
        hole_candidates = [cell for cell in chosen if cell not in forced]
        rng.shuffle(hole_candidates)
        for row, col in hole_candidates[:holes]:
            mirror_row, mirror_col = _mirror(height, width, axis, row, col)
            if rng.randrange(2):
                grid[row][col] = 0
            else:
                grid[mirror_row][mirror_col] = 0
        facts = semantic_observables(grid)
        if (
            facts["selected_axis"] == axis
            and facts["fillable_count"] == holes
            and facts["orphan_nonzero_count"] == holes
            and facts["palette_size"] == palette_size
            and facts["bbox"] == [0, 0, height - 1, width - 1]
        ):
            return grid
    raise RuntimeError(f"could not construct a stable {axis} scene for {split}[{index}]")


def _input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    return _build_scene(seed, split, index, profiles[index])


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
    all_inputs = [pair["input"] for pair in train + test]
    if len({digest(grid) for grid in all_inputs}) != len(all_inputs):
        raise RuntimeError("constructed inputs are not distinct")
    return {
        "train": train,
        "test": test,
        "program_solution": program(selected),
    }
