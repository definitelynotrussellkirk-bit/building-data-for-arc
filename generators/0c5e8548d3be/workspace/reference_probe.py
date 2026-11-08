"""Independent geometry oracle and review probes for task 0c5e8548d3be.

The selected Racket program remains label authority.  This module deliberately
reimplements only the visible panel/rotation relation so task-local tests can
catch generator or Python semantic-contract drift without importing generator
helpers.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

TASK = "0c5e8548d3be"
PANEL_STARTS = (0, 6, 12, 18)


def load_generator(path: str | Path | None = None) -> Any:
    source = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_generator_{TASK}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    try:
        from reviewer_support import canonical_pairs as shared_pairs, find_root

        return shared_pairs(TASK, root=find_root(__file__))
    except (ImportError, FileNotFoundError, ValueError):
        repo = Path(__file__).resolve().parents[3]
        source = repo / "shared" / "data" / "canonical" / "puzzles.jsonl"
        with source.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    return [*row.get("train", []), *row.get("test", [])]
        raise AssertionError(f"canonical task {TASK} not found")


def normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return tuple(sorted((row - top, col - left) for row, col in points))


def rotate(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = normalize(shape)
    if not points:
        return ()
    height = max(row for row, _ in points) + 1
    return normalize((col, height - 1 - row) for row, col in points)


def mirror(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = normalize(shape)
    if not points:
        return ()
    width = max(col for _, col in points) + 1
    return normalize((row, width - 1 - col) for row, col in points)


def rotations(shape: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    values = []
    current = normalize(shape)
    for _ in range(4):
        if current not in values:
            values.append(current)
        current = rotate(current)
    return tuple(values)


def rotation_key(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(rotations(shape))


def dihedral_key(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = normalize(shape)
    return min((*rotations(points), *rotations(mirror(points))))


def panel_shapes(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    height = len(grid)
    return [
        normalize(
            (row, offset)
            for row in range(height)
            for offset in range(5)
            if grid[row][start + offset] != 0
        )
        for start in PANEL_STARTS
    ]


def panel_colors(grid: list[list[int]]) -> list[set[int]]:
    height = len(grid)
    return [
        {
            grid[row][start + offset]
            for row in range(height)
            for offset in range(5)
            if grid[row][start + offset] != 0
        }
        for start in PANEL_STARTS
    ]


def relation_output(grid: list[list[int]]) -> list[list[int]]:
    keys = [rotation_key(shape) for shape in panel_shapes(grid)]
    return [[8 if left == right else 0 for right in keys] for left in keys]


def exact_output(grid: list[list[int]]) -> list[list[int]]:
    shapes = panel_shapes(grid)
    return [[8 if left == right else 0 for right in shapes] for left in shapes]


def count_output(grid: list[list[int]]) -> list[list[int]]:
    counts = [len(shape) for shape in panel_shapes(grid)]
    return [[8 if left == right else 0 for right in counts] for left in counts]


def dihedral_output(grid: list[list[int]]) -> list[list[int]]:
    keys = [dihedral_key(shape) for shape in panel_shapes(grid)]
    return [[8 if left == right else 0 for right in keys] for left in keys]


def color_output(grid: list[list[int]]) -> list[list[int]]:
    colors = [next(iter(values)) if len(values) == 1 else None for values in panel_colors(grid)]
    return [[8 if left == right else 0 for right in colors] for left in colors]


def class_sizes(grid: list[list[int]]) -> tuple[int, ...]:
    keys = [rotation_key(shape) for shape in panel_shapes(grid)]
    return tuple(sorted(keys.count(key) for key in set(keys)))


def relation_profile(grid: list[list[int]]) -> int:
    profiles = {(2, 2): 0, (1, 3): 1, (1, 1, 2): 2}
    sizes = class_sizes(grid)
    if sizes not in profiles:
        raise ValueError(f"unsupported generated relation partition: {sizes}")
    return profiles[sizes]


def facts(grid: list[list[int]]) -> dict[str, Any]:
    shapes = panel_shapes(grid)
    colors = panel_colors(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "shapes": shapes,
        "colors": colors,
        "counts": tuple(len(shape) for shape in shapes),
        "rotation_keys": tuple(rotation_key(shape) for shape in shapes),
        "dihedral_keys": tuple(dihedral_key(shape) for shape in shapes),
        "class_sizes": class_sizes(grid),
        "relation_profile": relation_profile(grid),
    }


def has_rotation_not_exact(grid: list[list[int]]) -> bool:
    shapes = panel_shapes(grid)
    for left in range(4):
        for right in range(left + 1, 4):
            if rotation_key(shapes[left]) == rotation_key(shapes[right]) and shapes[left] != shapes[right]:
                return True
    return False


def has_mirror_only_pair(grid: list[list[int]]) -> bool:
    shapes = panel_shapes(grid)
    for left in range(4):
        for right in range(left + 1, 4):
            if (
                dihedral_key(shapes[left]) == dihedral_key(shapes[right])
                and rotation_key(shapes[left]) != rotation_key(shapes[right])
            ):
                return True
    return False
