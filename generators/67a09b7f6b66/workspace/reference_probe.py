"""Independent parser/oracles for task 67a09b7f6b66 review tests.

This module intentionally does not import production helpers from generator.py.
It gives future reviewers one small place to inspect the observable contract,
calculate expected outputs, and reproduce canonical-fitting shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

TASK_ID = "67a09b7f6b66"
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator(path: str | os.PathLike[str] | None = None):
    target = Path(path) if path else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"reviewed_generator_{TASK_ID}", target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    from reviewer_support import canonical_pairs as _canonical_pairs, find_root

    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def retained_degenerate_inputs() -> list[list[list[int]]]:
    path = HOME / "counterexamples" / "review-3ca504134298f6f0-v0001" / "degenerate-inputs.json"
    return json.loads(path.read_text())



def _zero_components(grid: list[list[int]], rows: range, cols: range) -> int:
    remaining = {(row, col) for row in rows for col in cols if grid[row][col] == 0}
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
    return count


def chamber_zero_region_counts(grid: list[list[int]]) -> tuple[int, int, int]:
    width = len(grid[0])
    ch_w = (width - 4) // 3
    walls = (0, ch_w + 1, 2 * ch_w + 2, width - 1)
    return tuple(
        _zero_components(
            grid,
            range(2, len(grid) - 1),
            range(walls[chamber] + 1, walls[chamber + 1]),
        )
        for chamber in range(3)
    )

def observed(grid: Any) -> dict[str, Any]:
    """Parse the complete public axis state from a lawful input grid."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty row sequence")
    if any(not isinstance(row, (list, tuple)) for row in grid):
        raise ValueError("every row must be a sequence")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be non-empty and rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")

    height = len(grid)
    ch_h = height - 3
    if ch_h not in range(5, 10):
        raise ValueError(f"height {height} does not encode ch_h 5..9")
    if (width - 4) % 3:
        raise ValueError(f"width {width} does not encode three equal chambers")
    ch_w = (width - 4) // 3
    if ch_w not in range(3, 6):
        raise ValueError(f"width {width} does not encode ch_w 3..5")

    legend = tuple(grid[0][1:4])
    if len(set(legend)) != 3 or any(value not in range(2, 10) for value in legend):
        raise ValueError(f"invalid legend {legend}")
    if any(value != 0 for col, value in enumerate(grid[0]) if col not in (1, 2, 3)):
        raise ValueError("row 0 may contain colors only at legend columns 1..3")

    walls = (0, ch_w + 1, 2 * ch_w + 2, width - 1)
    if any(value != 8 for value in grid[1]):
        raise ValueError("row 1 must be a complete color-8 wall")
    if any(value != 8 for value in grid[-1]):
        raise ValueError("last row must be a complete color-8 wall")
    if any(grid[row][col] != 8 for row in range(1, height) for col in walls):
        raise ValueError("vertical chamber walls must be color 8")

    counts: list[int] = []
    for chamber in range(3):
        lo, hi = walls[chamber] + 1, walls[chamber + 1]
        cells = [grid[row][col] for row in range(2, height - 1) for col in range(lo, hi)]
        if any(value not in (0, 1) for value in cells):
            raise ValueError("chamber interiors may contain only background 0 and dots 1")
        counts.append(sum(value == 1 for value in cells))
    if sorted(counts) != [1, 2, 3]:
        raise ValueError(f"dot counts must be a permutation of 1,2,3, got {counts}")
    regions = chamber_zero_region_counts(grid)
    if regions != (1, 1, 1):
        raise ValueError(f"each chamber must retain one zero region, got {regions}")

    return {
        "ch_h": ch_h,
        "ch_w": ch_w,
        "palette_kind": "wall_shared" if 8 in legend else "wall_excluded",
        "count_order": "".join(str(value) for value in counts),
    }


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent intended rule: chamber dot count selects legend position."""
    state = observed(grid)
    out = deepcopy(grid)
    legend = grid[0][1:4]
    ch_w = state["ch_w"]
    walls = (0, ch_w + 1, 2 * ch_w + 2, len(grid[0]) - 1)
    counts = tuple(int(ch) for ch in state["count_order"])
    for chamber, count in enumerate(counts):
        for row in range(2, len(grid) - 1):
            for col in range(walls[chamber] + 1, walls[chamber + 1]):
                out[row][col] = legend[count - 1]
    return out


def position_only_output(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting rival: chamber position, not dot count, selects color."""
    state = observed(grid)
    out = deepcopy(grid)
    legend = grid[0][1:4]
    ch_w = state["ch_w"]
    walls = (0, ch_w + 1, 2 * ch_w + 2, len(grid[0]) - 1)
    for chamber in range(3):
        for row in range(2, len(grid) - 1):
            for col in range(walls[chamber] + 1, walls[chamber + 1]):
                out[row][col] = legend[chamber]
    return out


def occupied_rows_output(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting rival: occupied row count selects the legend entry."""
    state = observed(grid)
    out = deepcopy(grid)
    legend = grid[0][1:4]
    ch_w = state["ch_w"]
    walls = (0, ch_w + 1, 2 * ch_w + 2, len(grid[0]) - 1)
    for chamber in range(3):
        rows = {
            row
            for row in range(2, len(grid) - 1)
            for col in range(walls[chamber] + 1, walls[chamber + 1])
            if grid[row][col] == 1
        }
        if len(rows) not in (1, 2, 3):
            raise ValueError(f"occupied-row rival is undefined for {len(rows)} rows")
        for row in range(2, len(grid) - 1):
            for col in range(walls[chamber] + 1, walls[chamber + 1]):
                out[row][col] = legend[len(rows) - 1]
    return out


def has_same_row_dot_pair(grid: list[list[int]]) -> bool:
    """Whether a chamber has more dots than occupied rows."""
    state = observed(grid)
    ch_w = state["ch_w"]
    walls = (0, ch_w + 1, 2 * ch_w + 2, len(grid[0]) - 1)
    for chamber in range(3):
        dots = [
            (row, col)
            for row in range(2, len(grid) - 1)
            for col in range(walls[chamber] + 1, walls[chamber + 1])
            if grid[row][col] == 1
        ]
        if len({row for row, _col in dots}) < len(dots):
            return True
    return False
