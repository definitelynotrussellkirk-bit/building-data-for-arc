"""Independent geometry helpers for reviewing generator 2dbcb80623f9.

The Python oracle is supplementary test evidence.  The canonical Racket rule
remains label authority; this module deliberately does not import production
solver helpers from the generator under review.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "2dbcb80623f9"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / "generators" / TASK_ID / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_2dbcb80623f9", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _positions(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    found: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                found[value].append((r, c))
    return dict(found)


def _step(a: tuple[int, int], b: tuple[int, int], *, include_axis: bool) -> tuple[int, int] | None:
    dr, dc = b[0] - a[0], b[1] - a[1]
    if dr != 0 and abs(dr) == abs(dc):
        return (1 if dr > 0 else -1, 1 if dc > 0 else -1)
    if include_axis and dr == 0 and dc != 0:
        return (0, 1 if dc > 0 else -1)
    if include_axis and dc == 0 and dr != 0:
        return (1 if dr > 0 else -1, 0)
    return None


def _path(a: tuple[int, int], b: tuple[int, int], step: tuple[int, int]) -> list[tuple[int, int]]:
    result = [a]
    r, c = a
    while (r, c) != b:
        r += step[0]
        c += step[1]
        result.append((r, c))
    return result


def solve_geometry(grid: list[list[int]], *, include_axis: bool = False) -> list[list[int]]:
    """Execute the selected pair-connection geometry from original input cells."""
    out = deepcopy(grid)
    positions = _positions(grid)
    for color in sorted(positions):
        cells = positions[color]
        for i, a in enumerate(cells):
            for b in cells[i + 1 :]:
                step = _step(a, b, include_axis=include_axis)
                if step is None:
                    continue
                path = _path(a, b, step)
                if any(grid[r][c] != 0 for r, c in path[1:-1]):
                    continue
                for r, c in path:
                    out[r][c] = color
    return out


def axis_or_diagonal_rival(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: also connect clear horizontal/vertical pairs."""
    return solve_geometry(grid, include_axis=True)


def observe(grid: list[list[int]]) -> dict[str, int]:
    """Recover the intended exact controls solely from returned pixels."""
    positions = _positions(grid)
    aligned = 0
    distractors = 0
    axis_distractors = 0
    for cells in positions.values():
        if len(cells) != 2:
            raise ValueError(f"expected exactly two cells per nonzero color, got {cells}")
        a, b = cells
        dr, dc = b[0] - a[0], b[1] - a[1]
        if dr != 0 and abs(dr) == abs(dc):
            aligned += 1
        else:
            distractors += 1
            axis_distractors += int((dr == 0) ^ (dc == 0))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": aligned,
        "n_distractors": distractors,
        "axis_distractors": axis_distractors,
    }


def path_footprints(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    """Return clear diagonal path footprints for overlap checks."""
    footprints: list[set[tuple[int, int]]] = []
    for cells in _positions(grid).values():
        if len(cells) != 2:
            continue
        step = _step(cells[0], cells[1], include_axis=False)
        if step is None:
            continue
        path = _path(cells[0], cells[1], step)
        if all(grid[r][c] == 0 for r, c in path[1:-1]):
            footprints.append(set(path))
    return footprints


def pairwise_disjoint(items: Iterable[set[tuple[int, int]]]) -> bool:
    used: set[tuple[int, int]] = set()
    for item in items:
        if used & item:
            return False
        used.update(item)
    return True
