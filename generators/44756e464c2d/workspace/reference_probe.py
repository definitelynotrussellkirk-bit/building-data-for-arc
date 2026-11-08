"""Independent source-bound probes for reviewer tests of 44756e464c2d.

This module deliberately does not import production helper functions beyond
loading the generator itself.  It reconstructs the visible training pairs from
the selected authority record and mirrors the simple border-selection rule in
plain Python so reviewers can distinguish generator defects from Racket/runtime
failures.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HOME = Path(__file__).resolve().parents[1]
LIBRARY = next(
    (parent for parent in HOME.parents if (parent / "shared/runtime").is_dir()),
    None,
)
if LIBRARY is None:
    raise RuntimeError("could not locate the review library containing shared/runtime")

AUTHORITY_PATH = (
    LIBRARY
    / "shared/data/base/solutions/banks/2f7d84161f6a/H10__44756e464c2d.json"
)


def load_generator(path: str | Path | None = None):
    generator_path = Path(path) if path else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        "review_generator_44756e464c2d", generator_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {generator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authority_record() -> dict[str, Any]:
    return json.loads(AUTHORITY_PATH.read_text())


def canonical_train_pairs() -> list[dict[str, Any]]:
    """Return only public training pairs, never the masked query answer."""
    return authority_record()["visible_context"]["train"]


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror of the selected Racket rule."""
    h, w = len(grid), len(grid[0])
    selected_cols = [c for c in range(w) if grid[0][c] == 1]
    selected_rows = [r for r in range(h) if grid[r][0] == 2]
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r in selected_rows:
        for c in selected_cols:
            out[r][c] = 3
    return out


def observed_axes(grid: list[list[int]]) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_row_marks": sum(value == 1 for value in grid[0]),
        "n_col_marks": sum(row[0] == 2 for row in grid),
    }


def palette(grid: list[list[int]]) -> set[int]:
    return {value for row in grid for value in row}


def differing_cells(a: list[list[int]], b: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, (row_a, row_b) in enumerate(zip(a, b))
        for c, (value_a, value_b) in enumerate(zip(row_a, row_b))
        if value_a != value_b
    ]
