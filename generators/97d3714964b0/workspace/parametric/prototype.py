"""Native largest-hollow threshold relay family for 97d3714964b0."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any


TASK_ID = "97d3714964b0"
POLICIES = ("independent", "largest_hollow_threshold")
DEMO_LIMIT = 6
QUERY_LIMIT = 4
HERE = Path(__file__).resolve().parent
PROGRAM_PATHS = {
    "independent": HERE / "canonical.rkt",
    "largest_hollow_threshold": HERE / "largest_hollow_threshold.rkt",
}


def _settings(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"solid_policy"}:
        raise ValueError("settings must name exactly solid_policy")
    policy = value["solid_policy"]
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError(
            "solid_policy must be 'independent' or 'largest_hollow_threshold'"
        )
    return {"solid_policy": policy}


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low},{high}]")
    return value


def program(settings: dict[str, str]) -> str:
    policy = _settings(settings)["solid_policy"]
    source = PROGRAM_PATHS[policy].read_text(encoding="utf-8")
    if not source.startswith("(rule!"):
        raise ValueError(f"{PROGRAM_PATHS[policy].name} is not a rule program")
    return source


def _components7(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 7
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells = {start}
        pending = [start]
        while pending:
            row, col = pending.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    pending.append(neighbor)
        components.append(cells)
    return sorted(components, key=lambda cells: min(cells))


def _validated_grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("input must be a rectangular 1..30 grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or cell not in (0, 7) for cell in row)
        for row in value
    ):
        raise ValueError("input cells must be exact integers in {0,7}")
    return value


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    grid = _validated_grid(grid)
    objects: list[dict[str, Any]] = []
    for cells in _components7(grid):
        rows = [row for row, _col in cells]
        cols = [col for _row, col in cells]
        r0, c0, r1, c1 = min(rows), min(cols), max(rows), max(cols)
        interior = [
            (row, col)
            for row in range(r0 + 1, r1)
            for col in range(c0 + 1, c1)
        ]
        hollow = any(grid[row][col] == 0 and (row, col) not in cells for row, col in interior)
        bbox_area = (r1 - r0 + 1) * (c1 - c0 + 1)
        objects.append(
            {
                "kind": "hollow" if hollow else "solid",
                "bbox": [r0, c0, r1, c1],
                "bbox_area": bbox_area,
                "cell_count": len(cells),
                "cells": [list(cell) for cell in sorted(cells)],
            }
        )
    hollows = [obj for obj in objects if obj["kind"] == "hollow"]
    solids = [obj for obj in objects if obj["kind"] == "solid"]
    if len(hollows) < 1 or len(solids) < 1:
        raise ValueError("input must contain at least one hollow and one solid color-7 object")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "objects": objects,
        "largest_hollow_bbox_area": max(obj["bbox_area"] for obj in hollows),
        "hollow_count": len(hollows),
        "solid_count": len(solids),
    }


def native_transform(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    policy = _settings(settings)["solid_policy"]
    analysis = analyze_input(grid)
    threshold = analysis["largest_hollow_bbox_area"]
    output = copy.deepcopy(grid)
    for obj in analysis["objects"]:
        if obj["kind"] == "hollow":
            color = 4
        elif policy == "independent" or obj["bbox_area"] >= threshold:
            color = 2
        else:
            color = 7
        for row, col in obj["cells"]:
            output[row][col] = color
    return output


def _draw_frame(
    grid: list[list[int]], row0: int, col0: int, height: int, width: int
) -> None:
    for row in range(row0, row0 + height):
        for col in range(col0, col0 + width):
            if row in (row0, row0 + height - 1) or col in (col0, col0 + width - 1):
                grid[row][col] = 7


def _draw_solid(
    grid: list[list[int]], row0: int, col0: int, height: int, width: int
) -> None:
    for row in range(row0, row0 + height):
        for col in range(col0, col0 + width):
            grid[row][col] = 7


def _regions(height: int, width: int) -> list[tuple[int, int, int, int]]:
    split_row, split_col = height // 2, width // 2
    return [
        (0, split_row - 1, 0, split_col - 1),
        (0, split_row - 1, split_col + 1, width - 1),
        (split_row + 1, height - 1, 0, split_col - 1),
        (split_row + 1, height - 1, split_col + 1, width - 1),
    ]


def _region_size(region: tuple[int, int, int, int]) -> tuple[int, int]:
    r0, r1, c0, c1 = region
    return r1 - r0 + 1, c1 - c0 + 1


def _place(
    rng: random.Random,
    grid: list[list[int]],
    region: tuple[int, int, int, int],
    size: tuple[int, int],
    kind: str,
) -> None:
    rr0, rr1, cc0, cc1 = region
    height, width = size
    row0 = rng.randint(rr0, rr1 - height + 1)
    col0 = rng.randint(cc0, cc1 - width + 1)
    if kind == "hollow":
        _draw_frame(grid, row0, col0, height, width)
    else:
        _draw_solid(grid, row0, col0, height, width)


def _scene_rng(seed: int, phase: str, index: int, attempt: int) -> random.Random:
    material = f"{TASK_ID}:{seed}:{phase}:{index}:{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _scene(seed: int, phase: str, index: int, attempt: int, *, stress: bool) -> list[list[int]]:
    rng = _scene_rng(seed, phase, index, attempt)
    if stress:
        height = width = 30
    else:
        height = rng.randint(16, 24)
        width = rng.randint(18, 26)
    regions = _regions(height, width)
    region_dims = [_region_size(region) for region in regions]
    min_h = min(value[0] for value in region_dims)
    min_w = min(value[1] for value in region_dims)

    if stress:
        large_size = (12, 12)
        small_hollow_size = (7, 8)
        small_solid_size = (4, 5)
    else:
        large_h = rng.randint(5, min(8, min_h))
        large_w = rng.randint(5, min(8, min_w))
        large_size = (large_h, large_w)
        small_hollow_size = (
            rng.randint(3, min(5, min_h)),
            rng.randint(3, min(5, min_w)),
        )
        small_solid_size = (
            rng.randint(2, min(3, min_h)),
            rng.randint(2, min(4, min_w)),
        )

    large_area = large_size[0] * large_size[1]
    if small_hollow_size[0] * small_hollow_size[1] >= large_area:
        raise AssertionError("small hollow must not define the threshold")
    if small_solid_size[0] * small_solid_size[1] >= large_area:
        raise AssertionError("small solid must remain below the threshold")

    objects = [
        ("hollow", large_size),
        ("hollow", small_hollow_size),
        ("solid", large_size),
        ("solid", small_solid_size),
    ]
    rng.shuffle(regions)
    grid = [[0 for _col in range(width)] for _row in range(height)]
    for (kind, size), region in zip(objects, regions):
        _place(rng, grid, region, size, kind)

    analysis = analyze_input(grid)
    solids = sorted(obj["bbox_area"] for obj in analysis["objects"] if obj["kind"] == "solid")
    hollows = sorted(obj["bbox_area"] for obj in analysis["objects"] if obj["kind"] == "hollow")
    threshold = analysis["largest_hollow_bbox_area"]
    if not (len(solids) == len(hollows) == 2 and solids[0] < threshold <= solids[-1]):
        raise AssertionError("constructed scene lost the cross-object relay contrast")
    return grid


def _fingerprint(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _input_pool(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    accepted: set[str] = set()
    demos: list[list[list[int]]] = []
    queries: list[list[list[int]]] = []
    for phase, count in (("demo", DEMO_LIMIT), ("query", QUERY_LIMIT)):
        destination = demos if phase == "demo" else queries
        for index in range(count):
            stress = phase == "query" and index == QUERY_LIMIT - 1
            for attempt in range(100):
                grid = _scene(seed, phase, index, attempt, stress=stress)
                fingerprint = _fingerprint(grid)
                if fingerprint not in accepted:
                    accepted.add(fingerprint)
                    destination.append(grid)
                    break
            else:
                raise RuntimeError(f"could not construct unique {phase} input {index}")
    return demos, queries


def generate(
    seed: int,
    settings: dict[str, str],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    normalized = _settings(settings)
    _integer("demos", demos, 2, DEMO_LIMIT)
    _integer("queries", queries, 1, QUERY_LIMIT)
    demo_inputs, query_inputs = _input_pool(seed)
    return {
        "train": [
            {"input": copy.deepcopy(grid), "output": native_transform(grid, normalized)}
            for grid in demo_inputs[:demos]
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": native_transform(grid, normalized)}
            for grid in query_inputs[:queries]
        ],
        "program_solution": program(normalized),
    }


def teaching_certificate(episode: dict[str, Any]) -> dict[str, Any]:
    survivors = [
        policy
        for policy in POLICIES
        if all(
            native_transform(pair["input"], {"solid_policy": policy}) == pair["output"]
            for pair in episode["train"]
        )
    ]
    return {"setting_survivors": survivors, "demonstrations_checked": len(episode["train"])}


def dependency_witness() -> dict[str, Any]:
    settings = {"solid_policy": "largest_hollow_threshold"}
    episode = generate(0, settings, 2, 1)
    grid = episode["train"][0]["input"]
    threshold = analyze_input(grid)["largest_hollow_bbox_area"]
    return {
        "settings": settings,
        "ablation": "wrong_intermediate",
        "input": copy.deepcopy(grid),
        "intermediate_value": {"largest_hollow_bbox_area": threshold},
        "wrong_intermediate_value": {"largest_hollow_bbox_area": 0},
        "output": native_transform(grid, settings),
        "counterfactual_output": native_transform(grid, {"solid_policy": "independent"}),
        "step_a": "classify color-7 components and select the largest hollow bbox area",
        "step_b": "recolor a solid red only when its bbox area reaches that threshold",
        "why_b_depends_on_a": "the selected hollow area is the comparison threshold for every solid",
    }
