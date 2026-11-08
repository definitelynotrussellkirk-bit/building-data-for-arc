"""Independent geometry oracle and review probe for task 537b409b6744.

This file intentionally does not import implementation helpers from generator.py.
It mirrors the selected Racket rule closely enough to test generated inputs, expose
candidate ranking, and author reproducible nearest-blocker counterexamples.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Iterable

TASK_ID = "537b409b6744"
DIRECTIONS = ("down", "up", "right", "left")


def load_generator(path: str | None = None):
    source = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = spec_from_file_location(f"review_generator_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mode_color(grid: list[list[int]]) -> int:
    flat = [value for row in grid for value in row]
    counts = Counter(flat)
    first = {value: flat.index(value) for value in counts}
    return max(counts, key=lambda value: (counts[value], -first[value]))


def components(grid: list[list[int]], background: int | None = None) -> list[dict]:
    """Return same-color 4-connected components in row-major discovery order."""
    if background is None:
        background = mode_color(grid)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[dict] = []
    for row in range(height):
        for column in range(width):
            if (row, column) in seen or grid[row][column] == background:
                continue
            color = grid[row][column]
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            columns = [c for _, c in cells]
            r1, r2 = min(rows), max(rows)
            c1, c2 = min(columns), max(columns)
            obj = {
                "index": len(objects),
                "color": color,
                "cells": tuple(cells),
                "size": len(cells),
                "r1": r1,
                "r2": r2,
                "c1": c1,
                "c2": c2,
                "h": r2 - r1 + 1,
                "w": c2 - c1 + 1,
            }
            obj["solid"] = obj["size"] == obj["h"] * obj["w"]
            objects.append(obj)
    return objects


def _overlap(a1: int, a2: int, b1: int, b2: int) -> bool:
    return a1 <= b2 and b1 <= a2


def ranked_candidates(grid: list[list[int]]) -> list[dict]:
    """Mirror the Racket candidate enumeration and stable rank order."""
    background = mode_color(grid)
    objects = components(grid, background)
    candidates: list[dict] = []
    for mover in objects:
        for wall in objects:
            if mover is wall or not wall["solid"]:
                continue
            direction = None
            gap = None
            if (
                wall["r1"] > mover["r2"]
                and _overlap(mover["c1"], mover["c2"], wall["c1"], wall["c2"])
                and wall["w"] > mover["w"]
            ):
                direction = "down"
                gap = wall["r1"] - mover["r2"] - 1
            elif (
                mover["r1"] > wall["r2"]
                and _overlap(mover["c1"], mover["c2"], wall["c1"], wall["c2"])
                and wall["w"] > mover["w"]
            ):
                direction = "up"
                gap = mover["r1"] - wall["r2"] - 1
            elif (
                wall["c1"] > mover["c2"]
                and _overlap(mover["r1"], mover["r2"], wall["r1"], wall["r2"])
                and wall["h"] > mover["h"]
            ):
                direction = "right"
                gap = wall["c1"] - mover["c2"] - 1
            elif (
                mover["c1"] > wall["c2"]
                and _overlap(mover["r1"], mover["r2"], wall["r1"], wall["r2"])
                and wall["h"] > mover["h"]
            ):
                direction = "left"
                gap = mover["c1"] - wall["c2"] - 1
            if direction is not None:
                candidates.append(
                    {
                        "enumeration_index": len(candidates),
                        "gap": gap,
                        "wall_size": wall["size"],
                        "direction": direction,
                        "mover": mover,
                        "wall": wall,
                    }
                )
    return sorted(
        candidates,
        key=lambda candidate: (
            candidate["gap"],
            -candidate["wall_size"],
            candidate["enumeration_index"],
        ),
    )


def _put(grid: list[list[int]], row: int, column: int, value: int) -> None:
    if 0 <= row < len(grid) and 0 <= column < len(grid[0]):
        grid[row][column] = value


def apply_candidate(
    grid: list[list[int]], candidate: dict, *, grow_wall: bool = True
) -> list[list[int]]:
    """Apply the selected rule branch to one explicit candidate."""
    background = mode_color(grid)
    mover = candidate["mover"]
    wall = candidate["wall"]
    direction = candidate["direction"]
    output = deepcopy(grid)
    mover_cells = [
        (row, column, grid[row][column]) for row, column in mover["cells"]
    ]
    for row, column, _ in mover_cells:
        output[row][column] = background

    if direction in ("down", "up"):
        for row in range(wall["r1"], wall["r2"] + 1):
            for column in range(mover["c1"], mover["c2"] + 1):
                _put(output, row, column, background)
        if grow_wall:
            padding = max(1, mover["w"] // 2)
            for row in range(wall["r1"], wall["r2"] + 1):
                for distance in range(1, padding + 1):
                    _put(output, row, wall["c1"] - distance, wall["color"])
                    _put(output, row, wall["c2"] + distance, wall["color"])
        destination_row = (
            max(0, wall["r1"] - mover["h"])
            if direction == "up"
            else (
                wall["r2"] - mover["h"] + 1
                if wall["r2"] == len(grid) - 1
                else wall["r2"] + 1
            )
        )
        destination_column = mover["c1"]
    else:
        for row in range(mover["r1"], mover["r2"] + 1):
            for column in range(wall["c1"], wall["c2"] + 1):
                _put(output, row, column, background)
        if grow_wall:
            padding = max(1, mover["h"] // 2)
            for column in range(wall["c1"], wall["c2"] + 1):
                for distance in range(1, padding + 1):
                    _put(output, wall["r1"] - distance, column, wall["color"])
                    _put(output, wall["r2"] + distance, column, wall["color"])
        destination_column = (
            max(0, wall["c1"] - mover["w"])
            if direction == "left"
            else (
                wall["c2"] - mover["w"] + 1
                if wall["c2"] == len(grid[0]) - 1
                else wall["c2"] + 1
            )
        )
        destination_row = mover["r1"]

    for row, column, value in mover_cells:
        _put(
            output,
            destination_row + row - mover["r1"],
            destination_column + column - mover["c1"],
            value,
        )
    return output


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    candidates = ranked_candidates(grid)
    return deepcopy(grid) if not candidates else apply_candidate(grid, candidates[0])


def farthest_candidate_output(grid: list[list[int]]) -> list[list[int]]:
    candidates = ranked_candidates(grid)
    return deepcopy(grid) if not candidates else apply_candidate(grid, candidates[-1])


def no_growth_output(grid: list[list[int]]) -> list[list[int]]:
    candidates = ranked_candidates(grid)
    return (
        deepcopy(grid)
        if not candidates
        else apply_candidate(grid, candidates[0], grow_wall=False)
    )


def observed(grid: list[list[int]]) -> dict:
    candidates = ranked_candidates(grid)
    if not candidates:
        raise ValueError("grid has no qualifying mover/wall candidate")
    selected = candidates[0]
    mover, wall = selected["mover"], selected["wall"]
    object_list = components(grid, mode_color(grid))
    distractors = [
        obj
        for obj in object_list
        if obj["index"] not in (mover["index"], wall["index"])
    ]
    if len(distractors) != 1:
        raise ValueError(f"expected one distractor, found {len(distractors)}")
    distractor = distractors[0]
    vertical = selected["direction"] in ("down", "up")
    mover_span = mover["w"] if vertical else mover["h"]
    mover_depth = mover["h"] if vertical else mover["w"]
    wall_span = wall["w"] if vertical else wall["h"]
    wall_depth = wall["h"] if vertical else wall["w"]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "direction": selected["direction"],
        "mover_span": mover_span,
        "mover_depth": mover_depth,
        "wall_extra": wall_span - mover_span,
        "wall_depth": wall_depth,
        "gap": selected["gap"],
        "distractor_kind": "solid" if distractor["solid"] else "ragged",
    }


def changed_cells(left: list[list[int]], right: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row, column)
        for row in range(len(left))
        for column in range(len(left[0]))
        if left[row][column] != right[row][column]
    ]


def summarize(grids: Iterable[list[list[int]]]) -> dict:
    rows = []
    for grid in grids:
        candidates = ranked_candidates(grid)
        output = rule_output(grid)
        rows.append(
            {
                "observed": observed(grid),
                "background": mode_color(grid),
                "colors": sorted({value for row in grid for value in row}),
                "component_count": len(components(grid)),
                "candidate_count": len(candidates),
                "candidate_gaps": [candidate["gap"] for candidate in candidates],
                "changed_cells": len(changed_cells(grid, output)),
                "farthest_differs": output != farthest_candidate_output(grid),
                "no_growth_differs": output != no_growth_output(grid),
            }
        )
    return {"task_id": TASK_ID, "cases": rows}
