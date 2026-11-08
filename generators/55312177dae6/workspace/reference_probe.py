"""Independent pixel-level probes for ARC task 55312177dae6.

This module deliberately does not import implementation helpers from generator.py.
It provides a small oracle, canonical-pair loader, observable-axis decoder and
source-file loader for regression tests and later reviewers.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "55312177dae6"
HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = HOME.parents[1]

Point = tuple[int, int]
Shape = tuple[Point, ...]


def normalize_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)):
        raise ValueError("grid must be a list or tuple")
    result: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            result.append([int(value) for value in row])
        elif isinstance(row, (list, tuple)):
            result.append(list(row))
        else:
            raise ValueError("grid rows must be sequences or digit strings")
    return result


def canonical_row() -> dict[str, Any]:
    path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical task {TASK_ID} not found")


def canonical_pairs() -> list[dict[str, list[list[int]]]]:
    row = canonical_row()
    pairs = list(row.get("train") or [])
    test = row.get("test")
    pairs.extend(test if isinstance(test, list) else [test])
    return [
        {"input": normalize_grid(pair["input"]),
         "output": normalize_grid(pair["output"])}
        for pair in pairs
    ]


def load_generator(path: str | os.PathLike[str] | None = None):
    selected = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or HOME / "generator.py")
    spec = importlib.util.spec_from_file_location(
        f"generator_under_test_{TASK_ID}", selected
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {selected}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def norm(cells: Iterable[Point]) -> Shape:
    points = tuple(cells)
    if not points:
        return ()
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def rot90(shape: Shape) -> Shape:
    shape = norm(shape)
    if not shape:
        return ()
    height = max(row for row, _ in shape) + 1
    return norm((col, height - 1 - row) for row, col in shape)


def canonical_rotation(shape: Shape) -> Shape:
    forms: list[Shape] = []
    current = norm(shape)
    for _ in range(4):
        forms.append(current)
        current = rot90(current)
    return min(forms)


def reflection(shape: Shape) -> Shape:
    shape = norm(shape)
    width = max(col for _, col in shape) + 1
    return norm((row, width - 1 - col) for row, col in shape)


def dihedral_canonical(shape: Shape) -> Shape:
    return min(canonical_rotation(shape), canonical_rotation(reflection(shape)))


def components(grid: Any) -> list[tuple[Point, ...]]:
    values = normalize_grid(grid)
    remaining = {
        (row, col)
        for row, line in enumerate(values)
        for col, value in enumerate(line)
        if value != 0
    }
    found: list[tuple[Point, ...]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        todo = [start]
        cells: list[Point] = []
        while todo:
            row, col = todo.pop()
            cells.append((row, col))
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (row + drow, col + dcol)
                if nxt in remaining:
                    remaining.remove(nxt)
                    todo.append(nxt)
        found.append(tuple(sorted(cells)))
    return sorted(found, key=lambda cells: cells[0])


def analyze(grid: Any) -> dict[str, Any]:
    values = normalize_grid(grid)
    objects = components(values)
    signatures = [norm(obj) for obj in objects]
    rotation_keys = [canonical_rotation(shape) for shape in signatures]
    counts = Counter(rotation_keys)
    repeated = [key for key, count in counts.items() if count >= 2]
    if len(repeated) != 1:
        raise ValueError(f"expected one repeated rotational class, found {len(repeated)}")
    target_key = repeated[0]
    target_indices = [index for index, key in enumerate(rotation_keys) if key == target_key]
    return {
        "grid": values,
        "components": objects,
        "signatures": signatures,
        "rotation_keys": rotation_keys,
        "counts": counts,
        "target_key": target_key,
        "target_indices": target_indices,
        "target_components": [objects[index] for index in target_indices],
        "distractor_indices": [index for index in range(len(objects)) if index not in target_indices],
    }


def authority_output(grid: Any) -> list[list[int]]:
    info = analyze(grid)
    target = info["target_key"]
    height = max(row for row, _ in target) + 1
    width = max(col for _, col in target) + 1
    output = [[0] * width for _ in range(height)]
    for row, col in target:
        output[row][col] = 8
    return output


def _turn_index(shape: Shape, canonical: Shape) -> int:
    current = canonical
    for turn in range(4):
        if current == norm(shape):
            return turn
        current = rot90(current)
    raise ValueError("shape is not rotation-equivalent to canonical target")


def observed(grid: Any) -> dict[str, Any]:
    info = analyze(grid)
    values = info["grid"]
    target_shapes = [info["signatures"][index] for index in info["target_indices"]]
    turns = [_turn_index(shape, info["target_key"]) for shape in target_shapes]
    if len(turns) != 2:
        raise ValueError("observable contract expects exactly two matching objects")
    return {
        "grid_h": len(values),
        "grid_w": len(values[0]),
        "n_distractors": len(info["distractor_indices"]),
        "target_area": len(info["target_key"]),
        "match_rotation": (turns[1] - turns[0]) % 4,
    }
