"""Independent geometry probes for task 1e07c169ac61.

This module deliberately does not import implementation helpers from the selected
generator.  Task-local tests and future reviewers can use it to recover exact
controls, compute the intended rotation, and score short curriculum windows.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Iterable, Sequence

TASK_ID = "1e07c169ac61"
PROFILES = (
    "mono_connected",
    "multicolor_connected",
    "mono_disconnected",
    "multicolor_disconnected",
)


def load_generator(path: str | None = None) -> ModuleType:
    source = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    source = source.resolve()
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rows(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)):
        raise ValueError("grid is not a row sequence")
    rows = []
    for row in grid:
        if not isinstance(row, (list, tuple)):
            raise ValueError("row is not a sequence")
        rows.append(list(row))
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("grid must be nonempty and rectangular")
    return rows


def anchor(grid: Any) -> tuple[int, int]:
    rows = _rows(grid)
    hits = [
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(hits) != 1:
        raise ValueError(f"expected one color-9 anchor, found {hits}")
    return hits[0]


def components4(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def observed(grid: Any) -> dict[str, object]:
    rows = _rows(grid)
    foreground = [
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    colors = {rows[r][c] for r, c in foreground}
    connected = len(components4(foreground)) == 1
    profile = (
        ("mono_" if len(colors) == 1 else "multicolor_")
        + ("connected" if connected else "disconnected")
    )
    return {
        "grid_h": len(rows),
        "grid_w": len(rows[0]),
        "foreground_size": len(foreground),
        "profile": profile,
    }


def rotation_output(grid: Any, *, pivot: tuple[int, int] | None = None,
                    selected: Callable[[int, int, int], bool] | None = None) -> list[list[int]]:
    """Reference output from an immutable input snapshot.

    The true task uses the unique 9 anchor as ``pivot``.  Supplying a pivot or a
    cell-selection predicate makes independent rival probes convenient.  Like the
    selected Racket rule, destinations outside the canvas are dropped.
    """
    rows = _rows(grid)
    h, w = len(rows), len(rows[0])
    ar, ac = anchor(rows) if pivot is None else pivot
    out = [[0 for _ in range(w)] for _ in range(h)]
    actual_anchor = anchor(rows)
    out[actual_anchor[0]][actual_anchor[1]] = 9
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            if selected is not None and not selected(r, c, value):
                continue
            rr = ar + (c - ac)
            cc = ac - (r - ar)
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value
    return out


def first_color_only(grid: Any) -> list[list[int]]:
    rows = _rows(grid)
    first = next(value for row in rows for value in row if value not in (0, 9))
    return rotation_output(rows, selected=lambda _r, _c, value: value == first)


def largest_component_only(grid: Any) -> list[list[int]]:
    rows = _rows(grid)
    cells = [(r, c) for r, row in enumerate(rows) for c, v in enumerate(row) if v not in (0, 9)]
    comps = components4(cells)
    chosen = min(comps, key=lambda comp: (-len(comp), min(comp)))
    return rotation_output(rows, selected=lambda r, c, _value: (r, c) in chosen)


def center_pivot(grid: Any) -> list[list[int]]:
    rows = _rows(grid)
    return rotation_output(rows, pivot=(len(rows) // 2, len(rows[0]) // 2))


def ambiguity_records(
    pairs: Sequence[dict[str, list[list[int]]]],
    competitors: dict[str, Callable[[Any], list[list[int]]]],
) -> list[dict[str, object]]:
    """Return named competitors that fit every demo but alter a held-out query."""
    problems: list[dict[str, object]] = []
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        for name, solve in competitors.items():
            if all(solve(pair["input"]) == pair["output"] for pair in demos):
                rival = solve(query["input"])
                if rival != query["output"]:
                    problems.append({"query_index": query_index, "rival": name})
    return problems


def malformed_grids() -> list[Any]:
    return [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[False] * 6 for _ in range(6)],
        [[0] * 6 for _ in range(6)],
        [[9, 9] + [0] * 4] + [[0] * 6 for _ in range(5)],
    ]
