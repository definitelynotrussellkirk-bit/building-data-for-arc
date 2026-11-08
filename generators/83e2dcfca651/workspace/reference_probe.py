"""Independent geometry oracle and portable reference helpers for 83e2dcfca651."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "83e2dcfca651"
TASK_HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or TASK_HOME / "generator.py")
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_under_test", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def positions(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def marker_vector(grid: list[list[int]]) -> tuple[int, int]:
    p1 = positions(grid, 1)
    p2 = positions(grid, 2)
    if len(p1) != 1 or len(p2) != 1:
        raise ValueError("input needs exactly one color-1 and one color-2 marker")
    return p2[0][0] - p1[0][0], p2[0][1] - p1[0][1]


def green_cells(grid: list[list[int]]) -> set[tuple[int, int]]:
    return set(positions(grid, 3))


def components4(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    unseen = set(cells)
    out: list[set[tuple[int, int]]] = []
    while unseen:
        component = {unseen.pop()}
        stack = list(component)
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        out.append(component)
    return out


def translated_output(grid: list[list[int]], *, absolute: bool = False) -> list[list[int]]:
    out = [list(row) for row in grid]
    dr, dc = marker_vector(grid)
    if absolute:
        dr, dc = abs(dr), abs(dc)
    for r, c in green_cells(grid):
        rr, cc = r + dr, c + dc
        if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
            out[rr][cc] = 2
    return out


def observed(grid: list[list[int]]) -> dict[str, int]:
    dr, dc = marker_vector(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "object_size": len(green_cells(grid)),
        "vector_dr": dr,
        "vector_dc": dc,
    }


def shape_signature(grid: list[list[int]]) -> tuple[tuple[int, int], ...]:
    cells = green_cells(grid)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def racket_outputs(grids: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    from arcpuzzles import Catalog

    materialized = list(grids)
    receipt = Catalog(find_root(__file__)).apply(
        TASK_ID, materialized, reference="canonical", timeout=300
    )
    if not receipt.get("rule_hash_matches_catalog"):
        raise RuntimeError("canonical rule hash did not match catalog")
    errors = [row.get("error") for row in receipt["results"]]
    if any(error is not None for error in errors):
        raise RuntimeError(f"Racket apply failed: {errors}")
    return [row["output"] for row in receipt["results"]]
