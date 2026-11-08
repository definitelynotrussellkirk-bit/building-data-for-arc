"""Independent geometry oracle and shortcut probe for task 2c4efc97c37d.

This module intentionally does not import production helper functions.  It is
usable from task tests and by future reviewers to inspect an exact grid.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "2c4efc97c37d"


def _bootstrap_reviewer_support() -> None:
    for ancestor in Path(__file__).resolve().parents:
        packet_runtime = ancestor / "shared" / "runtime"
        if (packet_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(packet_runtime))
            return
        if (ancestor / "reviewer_support.py").is_file():
            sys.path.insert(0, str(ancestor))
            return


_bootstrap_reviewer_support()
from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402


def root() -> Path:
    return find_root(__file__)


def load_generator(path: str | os.PathLike[str] | None = None):
    base = root()
    default = base / "generators" / TASK_ID / "generator.py"
    if not default.is_file():
        default = base / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", default))
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return [deepcopy(pair) for pair in _canonical_pairs(TASK_ID, root=root(), labeled_only=True)]


def _components_with_backgrounds(
    grid: list[list[int]], backgrounds: set[int]
) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if (row, col) in seen or grid[row][col] in backgrounds:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    point = (r + dr, c + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] not in backgrounds
                    ):
                        seen.add(point)
                        stack.append(point)
            found.append(cells)
    found.sort(key=lambda cells: (min(c for _, c in cells), min(r for r, _ in cells)))
    return found


def components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Return authority components, sorted by left edge then top edge.

    The Racket authority treats colors 0 and 9 as background and merges touching
    non-background colors into the same binary-mask component.
    """
    return _components_with_backgrounds(grid, {0, 9})


def onion_depth(cells: Iterable[tuple[int, int]]) -> int:
    remaining = set(cells)
    depth = 0
    while remaining:
        depth += 1
        boundary = {
            (row, col)
            for row, col in remaining
            if any(
                (row + dr, col + dc) not in remaining
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
        }
        remaining.difference_update(boundary)
    return depth


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    return [[onion_depth(cells) for cells in components(grid)]]


def bbox_shortcut_output(grid: list[list[int]]) -> list[list[int]]:
    values = []
    for cells in components(grid):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        height = max(rows) - min(rows) + 1
        width = max(cols) - min(cols) + 1
        values.append((min(height, width) + 1) // 2)
    return [values]


def color_partition_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: treat each foreground color as one object."""
    groups: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value not in (0, 9):
                groups.setdefault(value, []).append((row, col))
    ordered = sorted(
        groups.values(),
        key=lambda cells: (min(col for _, col in cells), min(row for row, _ in cells)),
    )
    return [[onion_depth(cells) for cells in ordered]]


def nonzero_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: only zero is background, so color 9 is foreground."""
    return [[onion_depth(cells) for cells in _components_with_backgrounds(grid, {0})]]


def is_rectangle(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return len(cells) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def observed(grid: list[list[int]]) -> dict[str, int]:
    comps = components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "object_count": len(comps),
        "max_depth": max(onion_depth(cells) for cells in comps),
        "irregular_count": sum(not is_rectangle(cells) for cells in comps),
    }


def exact_counterexample() -> list[list[int]]:
    """A 9x25 input where bbox thickness overestimates an L-shaped path."""
    grid = [[0] * 25 for _ in range(9)]
    # Every cell of this 3x3-bounding-box L is boundary, so its true depth is
    # 1 even though the rectangle shortcut returns ceil(3 / 2) = 2.
    for row, col in ((2, 3), (3, 3), (4, 3), (4, 2), (4, 1)):
        grid[row][col] = 2
    for row in range(3, 6):
        for col in range(8, 11):
            grid[row][col] = 3
    for row in range(2, 7):
        for col in range(16, 21):
            if abs(row - 4) + abs(col - 18) <= 2:
                grid[row][col] = 4
    return grid


def binary_mask_counterexample() -> list[list[int]]:
    """Exact witness for bbox, color-partition, and nonzero shortcuts."""
    grid = exact_counterexample()
    # Disconnected first and second components share color 2.  A color-grouping
    # shortcut therefore collapses two true components into one.
    for row in range(3, 6):
        for col in range(8, 11):
            grid[row][col] = 2
    # The third binary component is visibly multicolored but remains connected.
    grid[2][18] = 5
    # The authority ignores 9; a nonzero-foreground shortcut creates an extra
    # rightmost singleton component.
    grid[0][24] = 9
    return grid


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grid", nargs="?", help="JSON file containing a grid; omit for the built-in witness")
    args = parser.parse_args(argv)
    if args.grid:
        payload = json.loads(Path(args.grid).read_text(encoding="utf-8"))
        grid = payload.get("input", payload)
    else:
        grid = exact_counterexample()
    report = {
        "input": grid,
        "observed": observed(grid),
        "intended_output": intended_output(grid),
        "bbox_shortcut_output": bbox_shortcut_output(grid),
        "color_partition_output": color_partition_output(grid),
        "nonzero_output": nonzero_output(grid),
        "disagreements": {
            "bbox_rectangle_depth": intended_output(grid) != bbox_shortcut_output(grid),
            "color_partition_depth": intended_output(grid) != color_partition_output(grid),
            "nonzero_foreground_depth": intended_output(grid) != nonzero_output(grid),
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
