"""Independent authority and distribution probes for task 50b472d4fc63.

The production generator only samples inputs; the Racket program remains the
output authority.  These probes intentionally implement the rule and its main
plausible shortcuts independently so task-local tests cannot validate the
sampler with production helper code.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
TASK_ID = "50b472d4fc63"


def load_generator(path: str | os.PathLike[str] | None = None) -> ModuleType:
    source = Path(path) if path else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("review_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _decode_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def canonical_pairs() -> list[dict[str, list[list[int]]]]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            return [
                {"input": _decode_grid(pair["input"]), "output": _decode_grid(pair["output"])}
                for pair in row["train"] + row["test"]
            ]
    raise KeyError(f"canonical task {TASK_ID} not found in {path}")


def occupancy_segments(grid: list[list[int]]) -> list[dict[str, object]]:
    """Maximal contiguous nonzero blocks, classified without production code."""
    height, width = len(grid), len(grid[0])
    result: list[dict[str, object]] = []
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] == 0:
                row += 1
                continue
            start = row
            values: list[int] = []
            while row < height and grid[row][col] != 0:
                values.append(grid[row][col])
                row += 1
            result.append(
                {
                    "col": col,
                    "start": start,
                    "end": row - 1,
                    "values": tuple(values),
                    "length": len(values),
                    "uniform": len(set(values)) == 1,
                }
            )
    return result


def observed(grid: list[list[int]]) -> dict[str, int]:
    segments = occupancy_segments(grid)
    colors = {value for row in grid for value in row if value != 0}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_targets": sum(s["length"] == 3 and s["uniform"] for s in segments),
        "n_mixed": sum(s["length"] == 3 and not s["uniform"] for s in segments),
        "n_short": sum(s["length"] == 2 and s["uniform"] for s in segments),
        "n_long": sum(s["length"] == 4 and s["uniform"] for s in segments),
        "palette_size": len(colors),
    }



def same_color_component_count(grid: list[list[int]]) -> int:
    """Count 4-connected same-color foreground components like the corpus linter."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    count = 0
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            count += 1
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count

def _same_color_runs(grid: list[list[int]]):
    height, width = len(grid), len(grid[0])
    for col in range(width):
        row = 0
        while row < height:
            value = grid[row][col]
            if value == 0:
                row += 1
                continue
            start = row
            while row < height and grid[row][col] == value:
                row += 1
            yield col, start, row - 1, value


def exact_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python transcription of the selected Racket authority."""
    out = deepcopy(grid)
    for col, start, end, _ in _same_color_runs(grid):
        if end - start + 1 == 3:
            out[start][col] = 8
            out[end][col] = 8
    return out


def occupancy_exact_three_output(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: ignore color changes inside a three-cell occupancy block."""
    out = deepcopy(grid)
    for segment in occupancy_segments(grid):
        if segment["length"] == 3:
            out[segment["start"]][segment["col"]] = 8
            out[segment["end"]][segment["col"]] = 8
    return out


def same_color_non_singleton_output(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: mark endpoints of every same-color run of length >=2."""
    out = deepcopy(grid)
    for col, start, end, _ in _same_color_runs(grid):
        if end - start + 1 >= 2:
            out[start][col] = 8
            out[end][col] = 8
    return out


def same_color_at_least_three_output(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: mark all same-color runs of length >=3."""
    out = deepcopy(grid)
    for col, start, end, _ in _same_color_runs(grid):
        if end - start + 1 >= 3:
            out[start][col] = 8
            out[end][col] = 8
    return out
