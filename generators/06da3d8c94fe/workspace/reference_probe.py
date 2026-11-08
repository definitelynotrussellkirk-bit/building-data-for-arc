"""Independent review helpers for task 06da3d8c94fe.

This file deliberately re-parses the five-panel representation instead of
calling production generator helpers.  It is test/review tooling, not selected
runtime code.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Iterable

TASK_ID = "06da3d8c94fe"
HERE = Path(__file__).resolve().parent
GENERATOR_DIR = HERE.parent
REPO = GENERATOR_DIR.parents[1]


def load_generator(path: str | Path | None = None):
    target = Path(path or GENERATOR_DIR / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_06da3d8c94fe", target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict:
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == TASK_ID:
                return row
    raise LookupError(f"canonical row {TASK_ID} not found")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(tests)


def split_panels(grid: list[list[int]]) -> tuple[list[list[list[int]]], int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected nonempty grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if (width - 4) % 5:
        raise ValueError("width is not 5*panel_width+4")
    panel_width = (width - 4) // 5
    panels = []
    for index in range(5):
        left = index * (panel_width + 1)
        panels.append([row[left:left + panel_width] for row in grid])
    return panels, panel_width


def independent_binop(kind: str, left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    if kind not in ("union", "intersection", "xor"):
        raise ValueError(kind)
    result = []
    for left_row, right_row in zip(left, right):
        row = []
        for left_value, right_value in zip(left_row, right_row):
            a = left_value != 0
            b = right_value != 0
            keep = (a or b) if kind == "union" else ((a and b) if kind == "intersection" else (a != b))
            row.append(2 if keep else 0)
        result.append(row)
    return result


def infer_kind(grid: list[list[int]]) -> str:
    panels, _ = split_panels(grid)
    matches = [
        kind
        for kind in ("union", "intersection", "xor")
        if independent_binop(kind, panels[0], panels[1]) == panels[2]
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one operation, got {matches}")
    return matches[0]


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    panels, _ = split_panels(grid)
    return independent_binop(infer_kind(grid), panels[3], panels[4])


def fixed_operation(grid: list[list[int]], kind: str) -> list[list[int]]:
    panels, _ = split_panels(grid)
    return independent_binop(kind, panels[3], panels[4])


def never_union(grid: list[list[int]]) -> list[list[int]]:
    kind = infer_kind(grid)
    return fixed_operation(grid, "xor" if kind == "union" else kind)


def panel_component_counts(grid: list[list[int]]) -> list[int]:
    panels, _ = split_panels(grid)
    counts = []
    for panel in panels:
        occupied = {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0}
        components = 0
        while occupied:
            components += 1
            pending = [occupied.pop()]
            while pending:
                r, c = pending.pop()
                for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if point in occupied:
                        occupied.remove(point)
                        pending.append(point)
        counts.append(components)
    return counts


def all_outputs_distinct(grid: list[list[int]]) -> bool:
    panels, _ = split_panels(grid)
    outputs = [independent_binop(kind, panels[3], panels[4]) for kind in ("union", "intersection", "xor")]
    return len({json.dumps(output, separators=(",", ":")) for output in outputs}) == 3


def palette(grid: Iterable[Iterable[int]]) -> set[int]:
    return {value for row in grid for value in row}
