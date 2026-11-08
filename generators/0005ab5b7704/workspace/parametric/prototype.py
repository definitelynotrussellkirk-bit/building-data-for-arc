"""Matched-input family for marker selection followed by column ordering."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "0005ab5b7704"
HERE = Path(__file__).resolve().parent
ORDERS = ("left_to_right", "body_density_desc")
RIVALS = (
    "left_to_right",
    "body_density_desc",
    "body_density_asc",
    "reverse_left_to_right",
    "all_columns_density_desc",
)
DEMO_PROFILES = ((8, 10), (10, 12), (12, 15), (15, 18), (18, 22), (22, 26))
QUERY_PROFILES = ((12, 16), (18, 22), (24, 27), (30, 30))
BODY_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_order(value: Any) -> str:
    if type(value) is not str or value not in ORDERS:
        raise ValueError(f"column_order must be one of {ORDERS}")
    return value


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"column_order"}:
        raise ValueError("settings must contain exactly column_order")
    return validate_order(settings["column_order"])


def program(settings: Any) -> str:
    order = validate_settings(settings)
    filename = "canonical.rkt" if order == "left_to_right" else "body_density_desc.rkt"
    return (HERE / "rules" / filename).read_text(encoding="utf-8")


def _validate_grid(value: Any) -> list[list[int]]:
    if type(value) is not list or not 2 <= len(value) <= 30:
        raise ValueError("grid must have 2..30 rows")
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


def _body_count(grid: list[list[int]], col: int) -> int:
    return sum(grid[row][col] != 0 for row in range(1, len(grid)))


def _body_columns(grid: list[list[int]], columns: list[int]) -> list[list[int]]:
    return [[grid[row][col] for col in columns] for row in range(1, len(grid))]


def analyze(value: Any) -> dict[str, Any]:
    grid = _validate_grid(value)
    height, width = len(grid), len(grid[0])
    if any(cell not in (0, 4) for cell in grid[0]):
        raise ValueError("header must contain only background and yellow markers")
    if any(grid[row][col] == 4 for row in range(1, height) for col in range(width)):
        raise ValueError("marker color may not appear in the body")
    selected = [col for col in range(width) if grid[0][col] == 4]
    unselected = [col for col in range(width) if grid[0][col] != 4]
    if len(selected) < 3 or not unselected:
        raise ValueError("grammar requires at least three marked columns and an unmarked column")
    counts = [_body_count(grid, col) for col in selected]
    if any(count <= 0 for count in counts) or len(set(counts)) != len(counts):
        raise ValueError("marked columns must have distinct positive body counts")
    density_order = sorted(selected, key=lambda col: (-_body_count(grid, col), col))
    if density_order == selected:
        raise ValueError("density order must differ from left-to-right order")
    unselected_counts = [_body_count(grid, col) for col in unselected]
    if max(unselected_counts, default=0) <= min(counts):
        raise ValueError("an unmarked density distractor must outrank a marked column")
    selected_vectors = [tuple(grid[row][col] for row in range(1, height)) for col in selected]
    if len(set(selected_vectors)) != len(selected_vectors):
        raise ValueError("marked body columns must be visibly distinct")
    return {
        "height": height,
        "width": width,
        "foreground_cells": sum(cell != 0 for row in grid for cell in row),
        "selected_columns": selected,
        "selected_counts": counts,
        "selected_with_counts": [[col, _body_count(grid, col)] for col in selected],
        "density_order": density_order,
        "unselected_columns": unselected,
        "unselected_counts": unselected_counts,
        "max_unselected_count": max(unselected_counts, default=0),
    }


def solve_python(grid: Any, order: str) -> list[list[int]]:
    if order not in RIVALS:
        raise ValueError(f"unknown column order {order}")
    checked = _validate_grid(grid)
    info = analyze(checked)
    selected = list(info["selected_columns"])
    if order == "left_to_right":
        columns = selected
    elif order == "body_density_desc":
        columns = list(info["density_order"])
    elif order == "body_density_asc":
        columns = sorted(selected, key=lambda col: (_body_count(checked, col), col))
    elif order == "reverse_left_to_right":
        columns = list(reversed(selected))
    else:
        columns = sorted(range(len(checked[0])), key=lambda col: (-_body_count(checked, col), col))[: len(selected)]
    return _body_columns(checked, columns)


def _digest(seed: int, split: str, index: int, salt: str) -> int:
    raw = f"{TASK_ID}|column-order-v1|{seed}|{split}|{index}|{salt}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _selected_columns(seed: int, split: str, index: int, width: int, count: int) -> list[int]:
    rng = random.Random(_digest(seed, split, index, "selected"))
    return sorted(rng.sample(range(width), count))


def _selected_counts(seed: int, split: str, index: int, body_height: int, count: int) -> list[int]:
    if count > body_height:
        raise RuntimeError("profile cannot host distinct marked-column counts")
    if count == 1:
        values = [body_height]
    else:
        values = [1 + (rank * (body_height - 1)) // (count - 1) for rank in range(count)]
    if len(set(values)) != count:
        raise RuntimeError("profile produced duplicate selected counts")
    shift = 1 + _digest(seed, split, index, "count-shift") % (count - 1)
    arranged = values[shift:] + values[:shift]
    if arranged == sorted(arranged) or arranged == sorted(arranged, reverse=True):
        raise RuntimeError("selected density order collapsed to a positional order")
    return arranged


def _column_rows(seed: int, split: str, index: int, col: int, height: int, count: int, *, force_top: bool) -> list[int]:
    if not 0 <= count <= height - 1:
        raise ValueError("column count outside body")
    if count == 0:
        return []
    rng = random.Random(_digest(seed, split, index, f"rows-{col}"))
    if force_top:
        if count == 1:
            return [1]
        return [1, *sorted(rng.sample(range(2, height), count - 1))]
    return sorted(rng.sample(range(1, height), count))


def make_input(seed: int, split: str, index: int) -> list[list[int]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    _exact_int(index, "index", 0, len(profiles) - 1)
    height, width = profiles[index]
    body_height = height - 1
    requested = (3 + min(index, 4)) if split == "demo" else (4 + min(index, 4))
    count = min(requested, body_height, width - 2, len(BODY_COLORS))
    if count < 3:
        raise RuntimeError("profile cannot host the marker-order grammar")
    selected = _selected_columns(seed, split, index, width, count)
    selected_counts = _selected_counts(seed, split, index, body_height, count)
    selected_count_by_col = dict(zip(selected, selected_counts, strict=True))
    unselected = [col for col in range(width) if col not in selected]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for col in selected:
        grid[0][col] = 4

    unselected_counts: dict[int, int] = {}
    spread = max(2, body_height // 3)
    for col in unselected:
        unselected_counts[col] = min(
            body_height,
            max(2, body_height // 2 + ((col + index + seed) % spread)),
        )
    # A dense unmarked distractor makes marker selection causally necessary.
    unselected_counts[unselected[0]] = body_height

    selected_rank = {col: rank for rank, col in enumerate(selected)}
    for col in range(width):
        is_selected = col in selected_count_by_col
        cells = _column_rows(
            seed,
            split,
            index,
            col,
            height,
            selected_count_by_col[col] if is_selected else unselected_counts[col],
            force_top=is_selected,
        )
        for position, row in enumerate(cells):
            if is_selected and row == 1:
                color = BODY_COLORS[selected_rank[col]]
            else:
                color = BODY_COLORS[(col * 3 + row * 5 + position + seed + index) % len(BODY_COLORS)]
            grid[row][col] = color

    info = analyze(grid)
    if (height, width) == (30, 30) and info["foreground_cells"] < 350:
        raise RuntimeError("30x30 stress case is not substantive")
    return grid


def teaching_check(episode: dict[str, Any], order: str) -> dict[str, Any]:
    rows = []
    for rival in RIVALS:
        if rival == order:
            continue
        demo_differences = [
            index
            for index, pair in enumerate(episode["train"])
            if solve_python(pair["input"], rival) != pair["output"]
        ]
        query_differences = [] if demo_differences else [
            index
            for index, pair in enumerate(episode["test"])
            if solve_python(pair["input"], rival) != pair["output"]
        ]
        rows.append(
            {
                "order": rival,
                "demo_differences": demo_differences,
                "demo_survives": not demo_differences,
                "query_differences": query_differences,
                "harmful": not demo_differences and bool(query_differences),
            }
        )
    return {
        "order": order,
        "rivals": rows,
        "demo_survivors": [row["order"] for row in rows if row["demo_survives"]],
        "harmful_survivors": [row["order"] for row in rows if row["harmful"]],
    }


def generate_episode(seed: int, order: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    order = validate_order(order)
    demos = _exact_int(demos, "demos", 2, 6)
    queries = _exact_int(queries, "queries", 1, 4)
    demo_inputs = [make_input(seed, "demo", index) for index in range(6)]
    query_inputs = [make_input(seed, "query", index) for index in range(4)]
    selected_inputs = demo_inputs[:demos] + query_inputs[:queries]
    if len({json.dumps(grid, separators=(",", ":")) for grid in selected_inputs}) != len(selected_inputs):
        raise RuntimeError("input sampler produced duplicate visible grids")
    episode = {
        "train": [
            {"input": deepcopy(grid), "output": solve_python(grid, order)}
            for grid in demo_inputs[:demos]
        ],
        "test": [
            {"input": deepcopy(grid), "output": solve_python(grid, order)}
            for grid in query_inputs[:queries]
        ],
        "program_solution": program({"column_order": order}),
    }
    certificate = teaching_check(episode, order)
    if certificate["demo_survivors"] or certificate["harmful_survivors"]:
        raise AssertionError(f"teaching hole: {certificate}")
    return episode


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    order = validate_settings(settings)
    return deepcopy(generate_episode(seed, order, demos=demos, queries=queries))


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    query_index = _exact_int(query_index, "query_index", 0, len(episode.get("test", [])) - 1)
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def dependency_trace(grid: Any) -> dict[str, Any]:
    info = analyze(grid)
    return {
        "step_a": "select the header-marked columns and measure their body occupancy",
        "intermediate_value": deepcopy(info["selected_with_counts"]),
        "step_b": "sort the selected columns by descending occupancy and pack their body cells",
        "output": solve_python(grid, "body_density_desc"),
        "wrong_intermediate_output": solve_python(grid, "all_columns_density_desc"),
        "ablation": "wrong_intermediate",
    }
