"""Independent probes for task 2a41d6b25262.

This file deliberately does not import production helpers when computing the
expected answer.  The task-local tests use it to catch a generator and a mirror
being wrong in the same way.
"""
from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

TASK_ID = "2a41d6b25262"


def load_generator(path: str | os.PathLike[str] | None = None):
    selected = path or os.environ.get("GENERATOR_UNDER_TEST")
    if selected:
        selected = Path(selected).resolve()
        spec = importlib.util.spec_from_file_location(
            f"review_target_{TASK_ID}", selected
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load generator from {selected}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )


def _library_root() -> Path:
    if os.environ.get("ARCPUZZLES_HOME"):
        root = Path(os.environ["ARCPUZZLES_HOME"]).resolve()
        if (root / "shared/data/canonical/puzzles.jsonl").is_file():
            return root
    for parent in Path(__file__).resolve().parents:
        if (parent / "shared/data/canonical/puzzles.jsonl").is_file():
            return parent
    raise FileNotFoundError("cannot locate shared/data/canonical/puzzles.jsonl")


def _pairs(value):
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _grid(value):
    if isinstance(value, list) and value and all(isinstance(row, str) for row in value):
        return [[int(cell) for cell in row] for row in value]
    return deepcopy(value)


def canonical_pairs() -> list[dict]:
    path = _library_root() / "shared/data/canonical/puzzles.jsonl"
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        for pair in _pairs(row.get("train")) + _pairs(row.get("test")):
            if "input" in pair and "output" in pair:
                result.append({"input": _grid(pair["input"]), "output": _grid(pair["output"])})
    return result


def cells(grid, color: int) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }


def normalize(points: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    points = set(points)
    if not points:
        return frozenset()
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return frozenset((row - top, col - left) for row, col in points)


def normalized_shapes(grid) -> tuple[frozenset, frozenset]:
    return normalize(cells(grid, 2)), normalize(cells(grid, 3))


def reference_output(grid) -> list[list[int]]:
    """Independent statement of the selected Racket rule."""
    red, green = normalized_shapes(grid)
    marker = sorted(cells(grid, 1))
    if len(marker) != 1:
        raise ValueError(f"expected one marker, found {len(marker)}")
    out = [[0 for _ in row] for row in grid]
    mr, mc = marker[0]
    for dr, dc in red ^ green:
        row, col = mr + dr, mc + dc
        if not (0 <= row < len(out) and 0 <= col < len(out[0])):
            raise ValueError("XOR stamp leaves the canvas")
        out[row][col] = 8
    return out


def observed(grid) -> dict[str, int]:
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def shape_signature(grid):
    red, green = normalized_shapes(grid)
    return tuple(sorted(red)), tuple(sorted(green))


def role_order(grid) -> tuple[int, int, int]:
    """Top-left reading order of red, green, marker, encoded as their colors."""
    items = []
    for color in (2, 3, 1):
        pts = cells(grid, color)
        items.append((min(pts), color))
    return tuple(color for _position, color in sorted(items))
