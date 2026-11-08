"""Native matched-input family for canonical halos and post-halo selection.

The canonical setting is byte-for-byte the selected ARC authority.  The
composed setting performs that halo transform first, then finds the unique
largest four-connected blue component in the resulting grid and recolors only
that component to color 8.  The selected component does not exist in the input,
so the second stage consumes a genuine input-dependent intermediate.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "27a915a2c9b3"
HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
HALO_FINISHES = ("canonical", "largest_component_to_8")
RIVALS = (
    "canonical",
    "largest_component_to_8",
    "smallest_component_to_8",
    "all_components_to_8",
    "first_component_to_8",
    "last_component_to_8",
    "largest_component_to_9",
)

_DEMO_SHAPES = ((14, 22), (16, 24), (18, 26), (20, 28), (22, 30), (24, 27))
_QUERY_SHAPES = ((16, 25), (20, 30), (24, 30), (30, 30))
_COUNT_SCHEDULE = (
    (1, 2, 3),  # largest is row-major last
    (3, 1, 2),  # largest is row-major first
    (2, 3, 1),
    (3, 2, 1),
    (1, 3, 2),
    (2, 1, 3),
)


def _load_base():
    path = HOME / "generator.py"
    name = "_parametric_base_27a915a2c9b3_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"halo_finish"}:
        raise ValueError("settings must contain exactly halo_finish")
    finish = settings["halo_finish"]
    if type(finish) is not str or finish not in HALO_FINISHES:
        raise ValueError(f"halo_finish must be one of {HALO_FINISHES}")
    return finish


def program(settings: Any) -> str:
    finish = validate_settings(settings)
    filename = "canonical.rkt" if finish == "canonical" else "largest_component_to_8.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            seen.add((row, col))
            pending = [(row, col)]
            cells: list[tuple[int, int]] = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            result.append(sorted(cells))
    return result


def _validate_grid(value: Any) -> list[list[int]]:
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    if any(cell not in (0, 2, 3) for row in value for cell in row):
        raise ValueError("halo-family inputs use only colors 0, 2, and 3")
    return value


def analyze(value: Any) -> dict[str, Any]:
    grid = _validate_grid(value)
    intermediate = _BASE.rule_mirror(grid)
    components = _components(intermediate, 1)
    if len(components) < 3:
        raise ValueError("parametric grammar requires at least three blue halo components")
    sizes = [len(cells) for cells in components]
    largest = max(sizes)
    if sizes.count(largest) != 1:
        raise ValueError("blue halo components must have a unique largest component")
    selected = components[sizes.index(largest)]
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "intermediate": intermediate,
        "blue_components": [[list(point) for point in cells] for cells in components],
        "blue_component_sizes": sizes,
        "selected_blue_component": [list(point) for point in selected],
    }


def _apply_component_finish(grid: list[list[int]], policy: str) -> list[list[int]]:
    info = analyze(grid)
    intermediate = deepcopy(info["intermediate"])
    components = [list(map(tuple, cells)) for cells in info["blue_components"]]
    if policy == "canonical":
        return intermediate
    if policy == "largest_component_to_8":
        selected = max(components, key=len)
        color = 8
    elif policy == "smallest_component_to_8":
        selected = min(components, key=len)
        color = 8
    elif policy == "all_components_to_8":
        selected = [point for component in components for point in component]
        color = 8
    elif policy == "first_component_to_8":
        selected = components[0]
        color = 8
    elif policy == "last_component_to_8":
        selected = components[-1]
        color = 8
    elif policy == "largest_component_to_9":
        selected = max(components, key=len)
        color = 9
    else:
        raise ValueError(f"unknown finish policy {policy}")
    for row, col in selected:
        intermediate[row][col] = color
    return intermediate


def solve_python(grid: Any, finish: str) -> list[list[int]]:
    if finish not in RIVALS:
        raise ValueError("unknown halo finish")
    return _apply_component_finish(_validate_grid(grid), finish)


def _rectangles(height: int, width: int, stress: bool) -> list[tuple[int, int, int, int]]:
    if stress:
        rh, rw = 9, 10
    else:
        rh = 5 if height < 20 else 6
        rw = 6 if width < 27 else 7
    return [
        (0, 0, rh - 1, rw - 1),
        (0, width - rw, rh - 1, width - 1),
        (height - rh, (width - rw) // 2, height - 1, (width - rw) // 2 + rw - 1),
    ]


def _marker_cluster(box: tuple[int, int, int, int], count: int, *, edge: bool) -> list[tuple[int, int]]:
    top, left, bottom, right = box
    row = top if edge else (top + bottom) // 2
    width = right - left + 1
    start = left + max(1, (width - count) // 2)
    if start + count - 1 >= right:
        start = right - count
    return [(row, start + offset) for offset in range(count)]


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    shapes = _DEMO_SHAPES if split == "demo" else _QUERY_SHAPES
    height, width = shapes[index]
    stress = (height, width) == (30, 30)
    rng = random.Random((seed * 0x9E3779B185EBCA87 + index * 0xC2B2AE3D27D4EB4F + (0 if split == "demo" else 0x27A915A2C9B3)) & ((1 << 64) - 1))
    grid = [[0] * width for _ in range(height)]
    boxes = _rectangles(height, width, stress)
    for top, left, bottom, right in boxes:
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                grid[row][col] = 3

    if stress:
        counts = (2, 4, 6)
    else:
        counts = _COUNT_SCHEDULE[(index + (0 if split == "demo" else 2)) % len(_COUNT_SCHEDULE)]
    markers: list[tuple[int, int]] = []
    for box_index, (box, count) in enumerate(zip(boxes, counts, strict=True)):
        cluster = _marker_cluster(
            box, count,
            edge=(index >= 2 and box_index < 2 and (index + box_index) % 2 == 0),
        )
        markers.extend(cluster)
        for row, col in cluster:
            grid[row][col] = 2

    forbidden = set()
    for row, col in markers:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                forbidden.add((row + dr, col + dc))
    inside_boxes = {
        (row, col)
        for top, left, bottom, right in boxes
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in inside_boxes and (row, col) not in forbidden
    ]
    rng.shuffle(candidates)
    external_count = 6 + ((seed + index) % 8)
    for row, col in candidates[:external_count]:
        grid[row][col] = 2

    info = analyze(grid)
    if stress:
        foreground = sum(value != 0 for row in grid for value in row)
        if foreground < 180:
            raise RuntimeError("30x30 stress scene is not substantive")
    if len(set(info["blue_component_sizes"])) != len(info["blue_component_sizes"]):
        # The family only needs a unique largest, but all-distinct sizes make
        # teaching rivals materially easier to diagnose.
        raise RuntimeError(f"unexpected tied halo sizes: {info['blue_component_sizes']}")
    return grid


def teaching_check(episode: dict[str, Any], finish: str) -> dict[str, Any]:
    rows = []
    for rival in RIVALS:
        if rival == finish:
            continue
        demo_differences = [
            index
            for index, pair in enumerate(episode["train"])
            if solve_python(pair["input"], rival) != pair["output"]
        ]
        query_differences = []
        if not demo_differences:
            query_differences = [
                index
                for index, pair in enumerate(episode["test"])
                if solve_python(pair["input"], rival) != pair["output"]
            ]
        rows.append({
            "policy": rival,
            "demo_differences": demo_differences,
            "demo_survives": not demo_differences,
            "query_differences": query_differences,
            "harmful": not demo_differences and bool(query_differences),
        })
    other = "largest_component_to_8" if finish == "canonical" else "canonical"
    return {
        "finish": finish,
        "rivals": rows,
        "demo_survivors": [row["policy"] for row in rows if row["demo_survives"]],
        "harmful_survivors": [row["policy"] for row in rows if row["harmful"]],
        "settings_disagree_on_demos": any(
            solve_python(pair["input"], other) != pair["output"]
            for pair in episode["train"]
        ),
    }


def generate_episode(seed: int, finish: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    if finish not in HALO_FINISHES:
        raise ValueError("unsupported halo finish")
    demos = _exact_int(demos, "demos", 2, 6)
    queries = _exact_int(queries, "queries", 1, 4)
    demo_inputs = [_scene(seed, "demo", index) for index in range(6)]
    query_inputs = [_scene(seed, "query", index) for index in range(4)]
    selected = demo_inputs[:demos] + query_inputs[:queries]
    if len({_compact(grid) for grid in selected}) != len(selected):
        raise RuntimeError("input sampler produced duplicate visible grids")
    episode = {
        "train": [{"input": deepcopy(grid), "output": solve_python(grid, finish)} for grid in demo_inputs[:demos]],
        "test": [{"input": deepcopy(grid), "output": solve_python(grid, finish)} for grid in query_inputs[:queries]],
        "program_solution": program({"halo_finish": finish}),
        "settings": {"halo_finish": finish},
        "seed": seed,
    }
    review = teaching_check(episode, finish)
    if review["demo_survivors"] or review["harmful_survivors"]:
        raise AssertionError(f"teaching hole: {review}")
    return episode


def _compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    finish = validate_settings(settings)
    episode = generate_episode(seed, finish, demos=demos, queries=queries)
    return {
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
        "program_solution": episode["program_solution"],
    }
