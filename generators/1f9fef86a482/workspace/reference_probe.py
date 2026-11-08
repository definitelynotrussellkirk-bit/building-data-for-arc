"""Independent contact-graph oracle and review probes for 1f9fef86a482.

This module deliberately does not import generator internals.  It is reusable
from task tests and by future reviewers comparing a retained baseline through
``GENERATOR_UNDER_TEST``.  The canonical Racket program remains label authority;
``authority_output`` is an independently written Python parity oracle.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

TASK = "1f9fef86a482"
ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = ROOT / "generators" / TASK / "generator.py"


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or GENERATOR_PATH).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_1f9fef86a482", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, list[list[int]]]]:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK:
                continue
            test = row.get("test")
            tests = test if isinstance(test, list) else [test]
            return list(row.get("train") or []) + [pair for pair in tests if pair]
    raise AssertionError(f"canonical task {TASK} not found")


def _grid_shape(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must have rows")
    if not all(isinstance(row, (list, tuple)) for row in grid):
        raise ValueError("rows must be sequences")
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or 0 in widths:
        raise ValueError("grid must be nonempty and rectangular")
    return len(grid), next(iter(widths))


def components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Same-color 4-components below the header, in reading order."""
    height, width = _grid_shape(grid)
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(1, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = current[0] + dr, current[1] + dc
                    if (
                        1 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            ordered = tuple(sorted(cells))
            result.append(
                {
                    "color": color,
                    "cells": ordered,
                    "cell_set": frozenset(ordered),
                    "size": len(ordered),
                    "top_left": ordered[0],
                }
            )
    result.sort(key=lambda obj: obj["top_left"])
    return result


def contact_graph(objects: list[dict[str, Any]]) -> tuple[frozenset[int], ...]:
    graph = [set() for _ in objects]
    for first_index, first in enumerate(objects):
        for second_index in range(first_index + 1, len(objects)):
            second = objects[second_index]["cell_set"]
            if any(
                (row + dr, col + dc) in second
                for row, col in first["cells"]
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                graph[first_index].add(second_index)
                graph[second_index].add(first_index)
    return tuple(frozenset(neighbors) for neighbors in graph)


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _grid_shape(grid)
    objects = components(grid)
    graph = contact_graph(objects)
    degrees = tuple(len(neighbors) for neighbors in graph)
    header_positions = tuple(col for col, value in enumerate(grid[0]) if value == 1)
    return {
        "height": height,
        "width": width,
        "header_positions": header_positions,
        "target_degree": len(header_positions),
        "components": objects,
        "graph": graph,
        "degrees": degrees,
        "palette_size": len({value for row in grid for value in row}),
    }


def authority_output(grid: list[list[int]]) -> list[list[int]]:
    facts = analyze(grid)
    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for obj, degree in zip(facts["components"], facts["degrees"]):
        if degree == facts["target_degree"]:
            for row, col in obj["cells"]:
                output[row][col] = 8
    return output


def profile_name(grid: list[list[int]]) -> str | None:
    facts = analyze(grid)
    degrees = tuple(sorted(facts["degrees"]))
    sizes = tuple(sorted(obj["size"] for obj in facts["components"]))
    if degrees == (0, 1, 1, 2) and sizes == (3, 4, 4, 4):
        return "chain"
    if degrees == (0, 1, 1, 1, 3) and sizes == (1, 1, 1, 4, 4):
        return "star"
    if degrees == (0, 1, 1, 1, 1, 1, 2, 3, 4) and sizes == (1,) * 9:
        return "all_degrees"
    return None


def header_style(grid: list[list[int]]) -> str:
    positions = analyze(grid)["header_positions"]
    if positions and positions == tuple(range(positions[0], positions[0] + len(positions))):
        return "contiguous"
    return "spaced"


def observed(grid: list[list[int]]) -> dict[str, Any]:
    facts = analyze(grid)
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "scene_profile": profile_name(grid),
        "header_style": header_style(grid),
    }


def _paint_selected(grid: list[list[int]], predicate) -> list[list[int]]:
    facts = analyze(grid)
    output = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for obj, degree in zip(facts["components"], facts["degrees"]):
        if predicate(obj, degree, facts):
            for row, col in obj["cells"]:
                output[row][col] = 8
    return output


def maximum_degree_output(grid: list[list[int]]) -> list[list[int]]:
    facts = analyze(grid)
    maximum = max(facts["degrees"], default=-1)
    return _paint_selected(grid, lambda _obj, degree, _facts: degree == maximum)


def fixed_degree_two_output(grid: list[list[int]]) -> list[list[int]]:
    return _paint_selected(grid, lambda _obj, degree, _facts: degree == 2)


def color_three_output(grid: list[list[int]]) -> list[list[int]]:
    return _paint_selected(grid, lambda obj, _degree, _facts: obj["color"] == 3)


def lesson_pairs(module, *, seed: int, start: int, band: str) -> list[dict[str, Any]]:
    pairs = []
    for sample_index in range(start, start + 4):
        grid = module.generate(seed, sample_index, difficulty=band)
        pairs.append({"input": grid, "output": authority_output(grid)})
    return pairs


def unchanged_after_calls(module, grid: list[list[int]]) -> bool:
    snapshot = deepcopy(grid)
    module.self_check(grid)
    module.observe_overrides(grid)
    if hasattr(module, "rule_mirror"):
        module.rule_mirror(grid)
    return grid == snapshot
