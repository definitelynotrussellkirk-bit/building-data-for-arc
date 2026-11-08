"""Matched-input family for normalized subtraction and residual selection."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "00f37833e26f"
HERE = Path(__file__).resolve().parent
POLICIES = ("all", "largest_component")
RIVALS = (
    "all",
    "largest_component",
    "smallest_component",
    "first_component",
    "last_component",
    "source_without_subtraction",
    "mask_intersection",
)
DEMO_PROFILES = ((12, 15), (14, 18), (16, 21), (18, 24), (21, 27), (24, 30))
QUERY_PROFILES = ((15, 19), (19, 23), (24, 28), (30, 30))
_DECOR_COLORS = (1, 2, 4, 6, 7, 8, 9)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_policy(value: Any) -> str:
    if type(value) is not str or value not in POLICIES:
        raise ValueError(f"residual_policy must be one of {POLICIES}")
    return value


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"residual_policy"}:
        raise ValueError("settings must contain exactly residual_policy")
    return validate_policy(settings["residual_policy"])


def program(settings: Any) -> str:
    policy = validate_settings(settings)
    filename = "canonical.rkt" if policy == "all" else "largest_component.rkt"
    return (HERE / "rules" / filename).read_text(encoding="utf-8")


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
        raise ValueError("grid must be rectangular with exact ARC colors")
    return value


def _color_components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
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
                    if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            result.append(sorted(cells))
    return result


def _normalize(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    cells = list(cells)
    if not cells:
        raise ValueError("cannot normalize an empty cell set")
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return sorted((row - top, col - left) for row, col in cells)


def _components_from_cells(cells: Iterable[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    remaining = set(cells)
    result: list[list[tuple[int, int]]] = []
    for start in sorted(remaining):
        if start not in remaining:
            continue
        remaining.remove(start)
        pending = [start]
        component: list[tuple[int, int]] = []
        while pending:
            row, col = pending.pop()
            component.append((row, col))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (row + dr, col + dc)
                if point in remaining:
                    remaining.remove(point)
                    pending.append(point)
        result.append(sorted(component))
    return result


def _crop_green(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    cells = list(cells)
    if not cells:
        raise ValueError("cannot crop an empty cell set")
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    bottom = max(row for row, _ in cells)
    right = max(col for _, col in cells)
    out = [[0 for _ in range(right - left + 1)] for _ in range(bottom - top + 1)]
    for row, col in cells:
        out[row - top][col - left] = 3
    return out


def analyze(value: Any) -> dict[str, Any]:
    grid = _validate_grid(value)
    green = _color_components(grid, 3)
    gray = _color_components(grid, 5)
    if len(green) != 1 or len(gray) != 1:
        raise ValueError("grammar requires exactly one green and one gray component")
    source = _normalize(green[0])
    mask = _normalize(gray[0])
    if not set(mask) < set(source):
        raise ValueError("normalized gray mask must be a strict source subset")
    residual = sorted(set(source) - set(mask))
    if not residual:
        raise ValueError("subtraction must leave cells")
    components = _components_from_cells(residual)
    sizes = [len(component) for component in components]
    if len(components) < 3 or sizes.count(max(sizes)) != 1:
        raise ValueError("grammar requires at least three residual components and a unique largest")
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "foreground_cells": sum(cell != 0 for row in grid for cell in row),
        "source_cells": [list(point) for point in source],
        "mask_cells": [list(point) for point in mask],
        "residual_cells": [list(point) for point in residual],
        "residual_components": [[list(point) for point in component] for component in components],
        "residual_component_sizes": sizes,
    }


def solve_python(grid: Any, policy: str) -> list[list[int]]:
    if policy not in RIVALS:
        raise ValueError(f"unknown residual policy {policy}")
    info = analyze(grid)
    source = [tuple(point) for point in info["source_cells"]]
    mask = [tuple(point) for point in info["mask_cells"]]
    residual = [tuple(point) for point in info["residual_cells"]]
    components = [[tuple(point) for point in component] for component in info["residual_components"]]
    if policy == "all":
        selected = residual
    elif policy == "largest_component":
        selected = max(components, key=len)
    elif policy == "smallest_component":
        selected = min(components, key=len)
    elif policy == "first_component":
        selected = components[0]
    elif policy == "last_component":
        selected = components[-1]
    elif policy == "source_without_subtraction":
        selected = source
    else:  # mask_intersection
        selected = sorted(set(source) & set(mask))
    return _crop_green(selected)


def _digest(seed: int, split: str, index: int, salt: str) -> int:
    raw = f"{TASK_ID}|residual-v1|{seed}|{split}|{index}|{salt}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _transform(cells: set[tuple[int, int]], side: int, turns: int, reflect: bool) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for row, col in cells:
        if reflect:
            col = side - 1 - col
        for _ in range(turns % 4):
            row, col = col, side - 1 - row
        result.add((row, col))
    return result


def _normalized_shapes(seed: int, split: str, index: int, side: int) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    mask = {(0, col) for col in range(side)} | {(row, 0) for row in range(1, side)}
    rows = list(range(1, side, 2))
    values = list(range(1, 2 * len(rows), 2))
    values[-1] = side - 1
    values = sorted(set(min(side - 1, value) for value in values))
    while len(values) < len(rows):
        candidate = 1
        while candidate in values:
            candidate += 1
        values.append(candidate)
    values = sorted(values)[: len(rows)]
    maximum = values[-1]
    minimum = values[0]
    middle = len(rows) // 2
    remaining = [value for value in values if value not in {minimum, maximum}]
    rng = random.Random(_digest(seed, split, index, "lengths"))
    rng.shuffle(remaining)
    arranged: list[int | None] = [None] * len(rows)
    arranged[0] = minimum
    arranged[middle] = maximum
    slots = [slot for slot, value in enumerate(arranged) if value is None]
    for slot, value in zip(slots, remaining, strict=True):
        arranged[slot] = value
    lengths = [int(value) for value in arranged]
    source = set(mask)
    for row, length in zip(rows, lengths, strict=True):
        source.update((row, col) for col in range(1, length + 1))
    # The two mandatory demonstrations deliberately keep branch rows horizontal
    # (one upright, one rotated 180 degrees).  This makes the unique largest
    # post-subtraction component interior in scan order, so positional
    # first/last-component shortcuts cannot fit the visible lessons.
    turns = 2 * index if split == "demo" and index < 2 else _digest(seed, split, index, "turns") % 4
    reflect = bool(_digest(seed, split, index, "reflect") % 2)
    return _transform(source, side, turns, reflect), _transform(mask, side, turns, reflect)


def make_input(seed: int, split: str, index: int) -> list[list[int]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    _exact_int(index, "index", 0, len(profiles) - 1)
    height, width = profiles[index]
    requested = 6 + index if split == "demo" else 7 + 2 * index
    side = min(requested, height - 2, (width - 3) // 2)
    if side < 6:
        raise RuntimeError("profile cannot host the residual grammar")
    source, mask = _normalized_shapes(seed, split, index, side)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    row_room = height - side
    source_row = _digest(seed, split, index, "source-row") % (row_room + 1)
    mask_row = _digest(seed, split, index, "mask-row") % (row_room + 1)
    source_col = 0
    mask_col = width - side
    for row, col in source:
        grid[source_row + row][source_col + col] = 3
    for row, col in mask:
        grid[mask_row + row][mask_col + col] = 5

    rng = random.Random(_digest(seed, split, index, "decor"))
    candidates = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 0]
    rng.shuffle(candidates)
    target = 70 if (height, width) == (30, 30) else 8 + (height * width) // 28
    for slot, (row, col) in enumerate(candidates[:target]):
        grid[row][col] = _DECOR_COLORS[(slot + seed + index) % len(_DECOR_COLORS)]
    analyze(grid)
    return grid


def teaching_check(episode: dict[str, Any], policy: str) -> dict[str, Any]:
    rows = []
    for rival in RIVALS:
        if rival == policy:
            continue
        demo_differences = [
            index for index, pair in enumerate(episode["train"])
            if solve_python(pair["input"], rival) != pair["output"]
        ]
        query_differences = [] if demo_differences else [
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
    return {
        "policy": policy,
        "rivals": rows,
        "demo_survivors": [row["policy"] for row in rows if row["demo_survives"]],
        "harmful_survivors": [row["policy"] for row in rows if row["harmful"]],
    }


def generate_episode(seed: int, policy: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    policy = validate_policy(policy)
    demos = _exact_int(demos, "demos", 2, 6)
    queries = _exact_int(queries, "queries", 1, 4)
    demo_inputs = [make_input(seed, "demo", index) for index in range(6)]
    query_inputs = [make_input(seed, "query", index) for index in range(4)]
    selected = demo_inputs[:demos] + query_inputs[:queries]
    if len({json.dumps(grid, separators=(",", ":")) for grid in selected}) != len(selected):
        raise RuntimeError("input sampler produced duplicate visible grids")
    episode = {
        "train": [{"input": deepcopy(grid), "output": solve_python(grid, policy)} for grid in demo_inputs[:demos]],
        "test": [{"input": deepcopy(grid), "output": solve_python(grid, policy)} for grid in query_inputs[:queries]],
        "program_solution": program({"residual_policy": policy}),
    }
    certificate = teaching_check(episode, policy)
    if certificate["demo_survivors"] or certificate["harmful_survivors"]:
        raise AssertionError(f"teaching hole: {certificate}")
    return episode


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    policy = validate_settings(settings)
    return deepcopy(generate_episode(seed, policy, demos=demos, queries=queries))


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    query_index = _exact_int(query_index, "query_index", 0, len(episode.get("test", [])) - 1)
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def dependency_trace(grid: Any) -> dict[str, Any]:
    info = analyze(grid)
    return {
        "step_a": "normalize the green source and gray mask, then subtract the mask",
        "intermediate_value": deepcopy(info["residual_cells"]),
        "step_b": "split the residual into components, choose the unique largest, crop, and paint it green",
        "output": solve_python(grid, "largest_component"),
        "wrong_intermediate_output": solve_python(grid, "source_without_subtraction"),
        "ablation": "wrong_intermediate",
    }
