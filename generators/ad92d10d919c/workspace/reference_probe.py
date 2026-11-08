"""Independent test oracle and structural probes for ad92d10d919c."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from types import ModuleType

TASK_ID = "ad92d10d919c"
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None) -> ModuleType:
    target = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or HOME / "generator.py")
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    return len(grid), width


def diagonal_values(grid, row: int, col: int) -> tuple[int, int, int, int]:
    return (
        grid[row - 1][col - 1],
        grid[row - 1][col + 1],
        grid[row + 1][col - 1],
        grid[row + 1][col + 1],
    )


def classify_centers(grid):
    """Return positive, partial-3, and mixed-2+2 zero centers."""
    height, width = _shape(grid)
    facts = {"positive": [], "partial": [], "mixed": []}
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            diagonals = diagonal_values(grid, row, col)
            nonzero = [value for value in diagonals if value != 0]
            counts = Counter(nonzero)
            if len(nonzero) == 4 and len(counts) == 1:
                facts["positive"].append((row, col, nonzero[0]))
            elif len(nonzero) == 3 and len(counts) == 1:
                facts["partial"].append((row, col, nonzero[0]))
            elif len(nonzero) == 4 and sorted(counts.values()) == [2, 2]:
                facts["mixed"].append((row, col, tuple(sorted(counts))))
    return facts


def observed(grid):
    facts = classify_centers(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "motif_count": len(facts["positive"]),
    }


def rule_output(grid):
    """Independent mirror of the selected four-equal-diagonals authority."""
    height, width = _shape(grid)
    result = deepcopy(grid)
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            values = diagonal_values(grid, row, col)
            if values[0] != 0 and all(value == values[0] for value in values[1:]):
                result[row][col] = values[0]
    return result


def at_least_three_rival(grid):
    """Canonical-fitting shortcut: three matching nonzero diagonals suffice."""
    height, width = _shape(grid)
    result = deepcopy(grid)
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            counts = Counter(value for value in diagonal_values(grid, row, col) if value)
            if counts:
                color, count = counts.most_common(1)[0]
                if count >= 3:
                    result[row][col] = color
    return result


def any_four_nonzero_rival(grid):
    """Canonical-fitting shortcut: any four colored diagonals fill the center."""
    height, width = _shape(grid)
    result = deepcopy(grid)
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            values = diagonal_values(grid, row, col)
            if all(values):
                result[row][col] = values[0]
    return result


def four_connected_object_count(grid) -> int:
    """Independent same-color 4-connected component count."""
    height, width = _shape(grid)
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    count = 0
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        count += 1
    return count
