"""Independent review helpers for task 3a96552d8c7c.

This module deliberately does not import semantic helpers from generator.py.
It gives future reviewers a small oracle/inspector that can be copied with the
focused task tests.
"""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
from typing import Any

TASK_HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or TASK_HOME / "generator.py")
    spec = importlib.util.spec_from_file_location("review_3a96552d8c7c_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_grid(grid: Any) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and isinstance(grid[0], (list, tuple))
        and bool(grid[0])
        and all(isinstance(row, (list, tuple)) and len(row) == len(grid[0]) for row in grid)
        and all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    )


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    """Mirror the selected Racket rule, independently of generator.py."""
    if not valid_grid(grid):
        raise ValueError("expected a nonempty rectangular ARC grid")
    out = copy.deepcopy(grid)
    for row_index, row in enumerate(grid):
        fives = [column for column, value in enumerate(row) if value == 5]
        if len(fives) != 2:
            continue
        left, right = fives
        if right <= left + 1:
            continue
        if all(row[column] == 0 for column in range(left + 1, right)):
            for column in range(left + 1, right):
                out[row_index][column] = 3
    return out


def _classify_row(row: list[int]) -> tuple[str, int | None]:
    nonzero = [(column, value) for column, value in enumerate(row) if value]
    if not nonzero:
        return "empty", None
    fives = [column for column, value in nonzero if value == 5]
    fours = [column for column, value in nonzero if value == 4]
    values = {value for _, value in nonzero}
    if values == {5} and len(fives) == 2 and fives[1] > fives[0] + 1:
        return "trigger", fives[1] - fives[0] - 1
    if values == {5} and len(fives) == 3:
        return "three_fives", None
    if values == {4} and len(fours) == 2 and fours[1] > fours[0] + 1:
        return "wrong_color", None
    if values == {4, 5} and len(fives) == 2 and len(fours) in (1, 2):
        left, right = fives
        if all(left < column < right for column in fours):
            if len(fours) == 2 and fours[1] > fours[0] + 1:
                return "blocked_wrong_color", None
            if len(fours) == 1:
                return "blocked", None
    return "malformed", None


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    """Recover the intended exact controls from pixels without trusting the generator."""
    if not valid_grid(grid):
        raise ValueError("malformed grid")
    row_kinds: list[str] = []
    gaps: list[int] = []
    for row in grid:
        kind, gap = _classify_row(list(row))
        if kind == "malformed":
            raise ValueError(f"row outside reviewed grammar: {row}")
        row_kinds.append(kind)
        if gap is not None:
            gaps.append(gap)
    has_short = any(gap <= 2 for gap in gaps)
    has_long = any(gap >= 3 for gap in gaps)
    span_style = "mixed" if has_short and has_long else "short" if has_short else "long"
    negatives = [kind for kind in row_kinds if kind not in {"empty", "trigger"}]
    if not negatives:
        negative_mode = "none"
    elif negatives == ["blocked"]:
        negative_mode = "blocked"
    elif negatives == ["three_fives"]:
        negative_mode = "three_fives"
    elif negatives == ["wrong_color"]:
        negative_mode = "wrong_color"
    elif sorted(negatives) == ["blocked_wrong_color", "three_fives"]:
        negative_mode = "mixed"
    else:
        raise ValueError(f"unrecognized negative curriculum: {negatives}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_fill_rows": row_kinds.count("trigger"),
        "span_style": span_style,
        "negative_mode": negative_mode,
        "row_kinds": row_kinds,
        "gaps": gaps,
    }


def has_one_zero_span(grid: list[list[int]]) -> bool:
    return any(
        len([value for value in row if value == 5]) == 2
        and (lambda p: p[1] - p[0] == 2)([i for i, value in enumerate(row) if value == 5])
        and all(value in (0, 5) for value in row)
        for row in grid
    )
