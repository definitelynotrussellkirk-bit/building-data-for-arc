"""Independent probes for task 019445e9b5a1.

This file is deliberately separate from generator.py.  It gives reviewers and
portable task tests a small oracle, observable signature, and named shortcut
predictions without consulting the Racket implementation.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from types import ModuleType

TASK_ID = "019445e9b5a1"


def load_generator(path: str | None = None) -> ModuleType:
    source = Path(path).resolve() if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror of the written row-header rule."""
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        header = row[0]
        if header == 0:
            continue
        for col_index, value in enumerate(row[1:], start=1):
            if value != 0:
                output[row_index][col_index] = header
    return output


def erase_headerless_payloads(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting wrong rule: header 0 erases instead of preserves."""
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        header = row[0]
        for col_index, value in enumerate(row[1:], start=1):
            if value != 0:
                output[row_index][col_index] = header
    return output


def global_first_header(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: use one global header color for every payload cell."""
    first = next((row[0] for row in grid if row[0] != 0), 0)
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row[1:], start=1):
            if value != 0:
                output[row_index][col_index] = first
    return output


def identity(grid: list[list[int]]) -> list[list[int]]:
    return deepcopy(grid)


def analyze(grid: list[list[int]]) -> dict[str, int]:
    headers = {r: row[0] for r, row in enumerate(grid) if row[0] != 0}
    payload = [(r, c, value) for r, row in enumerate(grid)
               for c, value in enumerate(row[1:], start=1) if value != 0]
    mismatching_rows = {
        r for r, c, value in payload if r in headers and value != headers[r]
    }
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_headers": len(headers),
        "n_payload": len(payload),
        "palette_size": len({value for row in grid for value in row}),
        "headerless_payloads": sum(r not in headers for r, _, _ in payload),
        "header_rows_with_mismatch": len(mismatching_rows),
        "matching_header_payloads": sum(
            r in headers and value == headers[r] for r, _, value in payload
        ),
    }
