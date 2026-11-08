"""Native fill-bbox family with a non-collapsing post-fill selector.

The canonical setting is the exact selected source rule.  The composed setting
first fills the sparse foreground's bounding rectangle.  It then compares the
intermediate with the original input, finds the unique largest four-connected
region of cells newly created by that fill, and recolors only that region to 8.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "c6fa0b0b24da"
HERE = Path(__file__).resolve().parent
FILL_FINISHES = ("canonical", "largest_new_region_to_8")
RIVALS = (
    "canonical",
    "largest_new_region_to_8",
    "smallest_new_region_to_8",
    "all_new_regions_to_8",
    "first_new_region_to_8",
    "last_new_region_to_8",
    "largest_new_region_to_9",
)

_DEMO_SHAPES = ((8, 10), (10, 13), (12, 16), (14, 18), (16, 20), (18, 22))
_QUERY_SHAPES = ((9, 12), (15, 19), (20, 24), (30, 30))
_COLORS = (2, 3, 4, 5, 6, 7, 9, 1)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"fill_finish"}:
        raise ValueError("settings must contain exactly fill_finish")
    finish = settings["fill_finish"]
    if type(finish) is not str or finish not in FILL_FINISHES:
        raise ValueError(f"fill_finish must be one of {FILL_FINISHES}")
    return finish


def program(settings: Any) -> str:
    finish = validate_settings(settings)
    filename = "canonical.rkt" if finish == "canonical" else "largest_new_region_to_8.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
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
    return value


def _regions(cells: set[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    remaining = set(cells)
    result: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        pending = [start]
        component = {start}
        while pending:
            row, col = pending.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    pending.append(point)
        result.append(sorted(component))
    result.sort(key=lambda region: region[0])
    return result


def analyze(value: Any) -> dict[str, Any]:
    grid = _grid(value)
    foreground = [(r, c, grid[r][c]) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c]]
    if not foreground:
        raise ValueError("input needs foreground cells")
    colors = {value for _r, _c, value in foreground}
    if len(colors) != 1:
        raise ValueError("input foreground must use one color")
    color = next(iter(colors))
    rows = [r for r, _c, _v in foreground]
    cols = [c for _r, c, _v in foreground]
    top, bottom, left, right = min(rows), max(rows), min(cols), max(cols)
    if bottom - top + 1 < 3 or right - left + 1 < 3:
        raise ValueError("bbox must span at least three rows and columns")
    intermediate = [[0] * len(grid[0]) for _ in range(len(grid))]
    new_cells: set[tuple[int, int]] = set()
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            intermediate[row][col] = color
            if grid[row][col] == 0:
                new_cells.add((row, col))
    regions = _regions(new_cells)
    if len(regions) < 2:
        raise ValueError("parametric grammar requires at least two new fill regions")
    sizes = [len(region) for region in regions]
    if sizes.count(max(sizes)) != 1:
        raise ValueError("new fill regions must have a unique largest region")
    selected = regions[sizes.index(max(sizes))]
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "color": color,
        "bbox": [top, left, bottom, right],
        "intermediate": intermediate,
        "new_regions": [[list(point) for point in region] for region in regions],
        "new_region_sizes": sizes,
        "selected_new_region": [list(point) for point in selected],
    }


def solve_python(value: Any, finish: str) -> list[list[int]]:
    if finish not in RIVALS:
        raise ValueError("unknown fill finish")
    info = analyze(value)
    output = deepcopy(info["intermediate"])
    regions = [list(map(tuple, region)) for region in info["new_regions"]]
    if finish == "canonical":
        return output
    if finish == "largest_new_region_to_8":
        selected, color = max(regions, key=len), 8
    elif finish == "smallest_new_region_to_8":
        selected, color = min(regions, key=len), 8
    elif finish == "all_new_regions_to_8":
        selected, color = [point for region in regions for point in region], 8
    elif finish == "first_new_region_to_8":
        selected, color = regions[0], 8
    elif finish == "last_new_region_to_8":
        selected, color = regions[-1], 8
    elif finish == "largest_new_region_to_9":
        selected, color = max(regions, key=len), 9
    else:
        raise ValueError(finish)
    for row, col in selected:
        output[row][col] = color
    return output


def _bbox_for_scene(height: int, width: int, split: str, index: int) -> tuple[int, int, int, int]:
    if (height, width) == (30, 30):
        return 0, 1, 29, 28  # two boundary contacts, one-cell side margins
    margin_top = (index + (0 if split == "demo" else 1)) % 2
    margin_left = (index // 2) % 2
    margin_bottom = 1 if index % 3 == 0 else 0
    margin_right = 1 if index % 3 == 1 else 0
    top, left = margin_top, margin_left
    bottom, right = height - 1 - margin_bottom, width - 1 - margin_right
    if top == 0 and bottom == height - 1 and left == 0 and right == width - 1:
        right -= 1
    return top, left, bottom, right


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    shapes = _DEMO_SHAPES if split == "demo" else _QUERY_SHAPES
    height, width = shapes[index]
    rng = random.Random((seed * 0xD6E8FEB86659FD93 + index * 0x9E3779B97F4A7C15 + (0 if split == "demo" else 0xC6FA0B0B24DA)) & ((1 << 64) - 1))
    grid = [[0] * width for _ in range(height)]
    top, left, bottom, right = _bbox_for_scene(height, width, split, index)
    box_h, box_w = bottom - top + 1, right - left + 1
    orientation = "vertical" if index % 2 == 0 else "horizontal"
    prefer_first = index % 4 in (1, 3)
    if orientation == "vertical":
        offset = max(1, (2 * box_w // 3) if prefer_first else (box_w // 3))
        wall_col = min(right - 1, left + offset)
        for row in range(top, bottom + 1):
            grid[row][wall_col] = _COLORS[(seed + index) % len(_COLORS)]
    else:
        offset = max(1, (2 * box_h // 3) if prefer_first else (box_h // 3))
        wall_row = min(bottom - 1, top + offset)
        for col in range(left, right + 1):
            grid[wall_row][col] = _COLORS[(seed + index) % len(_COLORS)]
    color = _COLORS[(seed + index) % len(_COLORS)]
    grid[top][left] = color
    grid[bottom][right] = color

    # A few isolated same-color markers add morphology without bridging regions.
    for _ in range(min(3, index)):
        row = rng.randint(top + 1, bottom - 1)
        col = rng.randint(left + 1, right - 1)
        if grid[row][col] == 0:
            grid[row][col] = color

    info = analyze(grid)
    if len(set(info["new_region_sizes"])) != len(info["new_region_sizes"]):
        raise RuntimeError(f"unexpected tied new regions: {info['new_region_sizes']}")
    return grid


def teaching_check(episode: dict[str, Any], finish: str) -> dict[str, Any]:
    rows = []
    for rival in RIVALS:
        if rival == finish:
            continue
        demo_differences = [
            index for index, pair in enumerate(episode["train"])
            if solve_python(pair["input"], rival) != pair["output"]
        ]
        query_differences = []
        if not demo_differences:
            query_differences = [
                index for index, pair in enumerate(episode["test"])
                if solve_python(pair["input"], rival) != pair["output"]
            ]
        rows.append({
            "policy": rival,
            "demo_differences": demo_differences,
            "demo_survives": not demo_differences,
            "query_differences": query_differences,
            "harmful": not demo_differences and bool(query_differences),
        })
    other = "largest_new_region_to_8" if finish == "canonical" else "canonical"
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


def _compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def generate_episode(seed: int, finish: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    if finish not in FILL_FINISHES:
        raise ValueError("unsupported fill finish")
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
        "program_solution": program({"fill_finish": finish}),
        "settings": {"fill_finish": finish},
        "seed": seed,
    }
    report = teaching_check(episode, finish)
    if report["demo_survivors"] or report["harmful_survivors"]:
        raise AssertionError(f"teaching hole: {report}")
    return episode


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    finish = validate_settings(settings)
    episode = generate_episode(seed, finish, demos=demos, queries=queries)
    return {
        "train": deepcopy(episode["train"]),
        "test": deepcopy(episode["test"]),
        "program_solution": episode["program_solution"],
    }
