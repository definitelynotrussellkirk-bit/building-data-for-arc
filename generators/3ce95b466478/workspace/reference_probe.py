"""Independent geometry oracle and probes for task 3ce95b466478.

This module intentionally does not import production helpers beyond dynamically
loading the generator under test.  It is reusable by regression tests and by
reviewers inspecting lesson windows.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from typing import Callable, Iterable

TASK_ID = "3ce95b466478"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
CANONICAL_PROFILES = {
    (8, 12, 3),
    (9, 11, 3),
    (9, 13, 3),
    (10, 12, 3),
    (10, 13, 3),
}


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            train = list(row.get("train") or [])
            test = row.get("test") or []
            if isinstance(test, dict):
                test = [test]
            return train + list(test)
    raise LookupError(TASK_ID)


def components(grid: list[list[int]], color: int = 2) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = rr + dr, cc + dc
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and grid[nxt[0]][nxt[1]] == color
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            found.append(cells)
    return found


def perimeter(cells: Iterable[tuple[int, int]]) -> int:
    cell_set = set(cells)
    return sum(
        (r + dr, c + dc) not in cell_set
        for r, c in cell_set
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def crop(cells: Iterable[tuple[int, int]], color: int = 8) -> list[list[int]]:
    cell_set = set(cells)
    r0 = min(r for r, _ in cell_set)
    r1 = max(r for r, _ in cell_set)
    c0 = min(c for _, c in cell_set)
    c1 = max(c for _, c in cell_set)
    return [
        [color if (r, c) in cell_set else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def solve_by_size(grid: list[list[int]]) -> list[list[int]]:
    reds = components(grid)
    target = sorted(reds, key=lambda cells: (-len(cells), min(r for r, _ in cells)))[1]
    return crop(target)


def solve_by_perimeter(grid: list[list[int]]) -> list[list[int]]:
    reds = components(grid)
    target = sorted(
        reds,
        key=lambda cells: (-perimeter(cells), min(r for r, _ in cells)),
    )[1]
    return crop(target)


def observed(grid: list[list[int]]) -> dict[str, int]:
    colors = {value for row in grid for value in row}
    decorations = sorted(colors - {0, 2})
    if len(decorations) != 1:
        raise ValueError(f"expected one decoration color, got {decorations}")
    decoration = decorations[0]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blobs": len(components(grid)),
        "decoration_color": decoration,
        "decoration_size": sum(value == decoration for row in grid for value in row),
    }


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def lesson_reasons(demos: list[dict], query: dict | None = None) -> list[str]:
    del query
    if all(solve_by_perimeter(deepcopy(pair["input"])) == pair["output"] for pair in demos):
        return ["second-largest-by-perimeter rival fits every demonstration"]
    return []


def pinned_profile_seed(band: str, index: int) -> int:
    import hashlib

    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)
