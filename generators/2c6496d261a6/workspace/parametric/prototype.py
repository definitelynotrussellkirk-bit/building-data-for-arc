"""Matched-input family for global row-count filtering.

``one_row_only`` is the byte-identical canonical rule.  ``fewest_rows`` first
computes the minimum number of distinct rows occupied by any nonzero color, then
keeps every color attaining that input-derived minimum.  Thus step A produces a
row-count threshold and step B consumes it to filter the complete grid.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "2c6496d261a6"
PARAMETER = "row_selection"
MODES = ("one_row_only", "fewest_rows")
_DIR = Path(__file__).resolve().parent
_PROGRAMS = {
    "one_row_only": (_DIR / "canonical.rkt").read_text(encoding="utf-8"),
    "fewest_rows": (_DIR / "fewest_rows.rkt").read_text(encoding="utf-8"),
}
_DEMO_DIMS = ((8, 10), (10, 13), (12, 16), (16, 20), (22, 26), (30, 30))
_QUERY_DIMS = ((9, 12), (15, 18), (24, 27), (30, 30))
_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError("settings must name exactly row_selection")
    mode = settings[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"row_selection must be one of {MODES}")
    return mode


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAMS[_mode(settings)]


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        raise ValueError("grid must fit within 30x30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def _positions(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    _validate_grid(grid)
    result: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                result.setdefault(value, []).append((r, c))
    if not result:
        raise ValueError("input must contain nonzero colors")
    return result


def _row_counts(grid: list[list[int]]) -> dict[int, int]:
    return {color: len({r for r, _ in cells}) for color, cells in _positions(grid).items()}


def _selected(grid: list[list[int]], mode: str) -> tuple[dict[int, int], int, list[int]]:
    counts = _row_counts(grid)
    threshold = 1 if mode == "one_row_only" else min(counts.values())
    selected = sorted(color for color, count in counts.items() if count == threshold)
    return counts, threshold, selected


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _mode(settings)
    _, _, selected = _selected(grid, mode)
    keep = set(selected)
    return [[value if value in keep else 0 for value in row] for row in grid]


def intermediate(grid: list[list[int]], settings: dict[str, Any]) -> dict[str, Any]:
    mode = _mode(settings)
    counts, threshold, selected = _selected(grid, mode)
    occurrences = Counter(value for row in grid for value in row if value)
    return {
        "mode": mode,
        "row_counts": dict(sorted(counts.items())),
        "occurrence_counts": dict(sorted(occurrences.items())),
        "threshold": threshold,
        "selected_colors": selected,
    }


def output_from_intermediate(grid: list[list[int]], value: dict[str, Any]) -> list[list[int]]:
    _validate_grid(grid)
    if type(value) is not dict or type(value.get("selected_colors")) is not list:
        raise ValueError("intermediate must contain selected_colors")
    selected = value["selected_colors"]
    if any(type(color) is not int or not 1 <= color <= 9 for color in selected):
        raise ValueError("selected colors must be exact nonzero ARC colors")
    keep = set(selected)
    return [[cell if cell in keep else 0 for cell in row] for row in grid]


def validate_input(grid: Any) -> list[str]:
    try:
        positions = _positions(grid)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    if not 3 <= len(positions) <= 8:
        errors.append(f"parametric grammar requires 3..8 colors, found {len(positions)}")
    if any(len(cells) < len({r for r, _ in cells}) for cells in positions.values()):
        errors.append("every occupied row for a color must contain at least one cell")
    return errors


def _rng(seed: int, split: str, index: int, attempt: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|row-selection-v1|{seed}|{split}|{index}|{attempt}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _profile(split: str, index: int, height: int) -> tuple[list[int], bool]:
    # Demo 0 separates the settings; demo 1 supplies positive canonical action.
    mixed = split == "train" and index % 2 == 1
    color_count = min(8, 4 + index)
    start = 1 if mixed else 2 + (1 if index in (2, 4) else 0)
    counts = [min(height - 1, start + offset) for offset in range(color_count)]
    # Clamp without introducing duplicate role counts at the high end.
    for i in range(len(counts) - 2, -1, -1):
        counts[i] = min(counts[i], counts[i + 1] - 1)
    if counts[0] < 1:
        raise AssertionError("row-count profile collapsed")
    return counts, mixed


def _candidate_scene(seed: int, split: str, index: int, attempt: int) -> list[list[int]]:
    dims = _DEMO_DIMS if split == "train" else _QUERY_DIMS
    height, width = dims[index]
    rng = _rng(seed, split, index, attempt)
    row_counts, mixed = _profile(split, index, height)
    colors = list(_COLORS[: len(row_counts)])
    rng.shuffle(colors)

    # Stress scenes use three cells on every occupied color-row; smaller scenes
    # alternate one and two cells.  Reserve one background cell per row.
    copies = [3 if (height, width) == (30, 30) else 1 + ((i + index) % 2)
              for i in range(len(colors))]
    # Make row-count and cell-count rankings disagree in the first teaching
    # role: the minimum-row color is deliberately denser than the next role.
    # This directly refutes the plausible "fewest cells" shortcut.
    if len(copies) >= 2:
        copies[0], copies[1] = 3, 1
    selected_rows: list[list[int]] = []
    demand = [0] * height
    for i, count in enumerate(row_counts):
        for _ in range(128):
            rows = sorted(rng.sample(range(height), count))
            if i == 0:
                rows[0] = 0
                rows = sorted(set(rows))
                while len(rows) < count:
                    candidate = rng.randrange(height)
                    if candidate not in rows:
                        rows.append(candidate)
                        rows.sort()
            if i == 1:
                # The next-higher row-count role shares the top row with the
                # selected minimum role and also reaches the bottom.  This
                # constructively refutes both a top-row selector and a local
                # boundary-span shortcut without changing the true row counts.
                rows[0] = 0
                rows[-1] = height - 1
                rows = sorted(set(rows))
                while len(rows) < count:
                    candidate = rng.randrange(height)
                    if candidate not in rows:
                        rows.append(candidate)
                        rows.sort()
            local = demand[:]
            for row in rows:
                local[row] += copies[i]
            if max(local) <= width - 1:
                demand = local
                selected_rows.append(rows)
                break
        else:
            raise AssertionError("failed to balance row occupancy")

    grid = [[0] * width for _ in range(height)]
    free = [list(range(width)) for _ in range(height)]
    for row in range(height):
        rng.shuffle(free[row])
    for color, rows, per_row in zip(colors, selected_rows, copies, strict=True):
        for row in rows:
            for _ in range(per_row):
                col = free[row].pop()
                grid[row][col] = color
    # Extra same-row cells break any shortcut equating distinct-row count with
    # total cell count while preserving the row-count intermediate.
    for i, (color, rows) in enumerate(zip(colors, selected_rows, strict=True)):
        extras = 2 if (height, width) == (30, 30) else (i + index) % 3
        row = rows[(i + attempt) % len(rows)]
        for _ in range(min(extras, max(0, len(free[row]) - 1))):
            grid[row][free[row].pop()] = color
    if mixed and min(_row_counts(grid).values()) != 1:
        raise AssertionError("mixed profile lost its one-row role")
    return grid


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    dims = _DEMO_DIMS if split == "train" else _QUERY_DIMS
    if not 0 <= index < len(dims):
        raise ValueError(f"unsupported {split} index {index}")
    for attempt in range(256):
        grid = _candidate_scene(seed, split, index, attempt)
        if validate_input(grid):
            continue
        counts = _row_counts(grid)
        mixed = split == "train" and index % 2 == 1
        if mixed:
            if min(counts.values()) != 1 or max(counts.values()) < 3:
                continue
        else:
            if min(counts.values()) < 2:
                continue
            if solve(grid, {PARAMETER: MODES[0]}) == solve(grid, {PARAMETER: MODES[1]}):
                continue
        if dims[index] == (30, 30) and sum(v != 0 for row in grid for v in row) < 90:
            continue
        return grid
    raise RuntimeError(f"failed to construct a lawful {split} scene {index}")


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    mode = _mode(settings)
    train: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    seen: set[bytes] = set()
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = _scene(seed, split, index)
            key = json.dumps(grid, separators=(",", ":")).encode()
            if key in seen:
                raise AssertionError("deterministic schedule emitted a duplicate input")
            seen.add(key)
            target.append({"input": grid, "output": solve(grid, {PARAMETER: mode})})
    return {"train": train, "test": test, "program_solution": program({PARAMETER: mode})}


def public_view(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def _filter_by(grid: list[list[int]], predicate: Callable[[int, int, int], bool]) -> list[list[int]]:
    positions = _positions(grid)
    row_counts = {color: len({r for r, _ in cells}) for color, cells in positions.items()}
    cell_counts = {color: len(cells) for color, cells in positions.items()}
    keep = {color for color in positions if predicate(color, row_counts[color], cell_counts[color])}
    return [[value if value in keep else 0 for value in row] for row in grid]


def _identity(grid):
    return copy.deepcopy(grid)


def _erase_all(grid):
    return [[0] * len(grid[0]) for _ in grid]


def _at_most_two_rows(grid):
    return _filter_by(grid, lambda _c, rows, _cells: rows <= 2)


def _most_rows(grid):
    counts = _row_counts(grid)
    maximum = max(counts.values())
    return _filter_by(grid, lambda _c, rows, _cells: rows == maximum)


def _fewest_cells(grid):
    positions = _positions(grid)
    minimum = min(map(len, positions.values()))
    return _filter_by(grid, lambda _c, _rows, cells: cells == minimum)


def _even_rows(grid):
    return _filter_by(grid, lambda _c, rows, _cells: rows % 2 == 0)


def _top_row(grid):
    positions = _positions(grid)
    keep = {color for color, cells in positions.items() if any(r == 0 for r, _ in cells)}
    return [[value if value in keep else 0 for value in row] for row in grid]


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    MODES[0]: lambda grid: solve(grid, {PARAMETER: MODES[0]}),
    MODES[1]: lambda grid: solve(grid, {PARAMETER: MODES[1]}),
    "identity": _identity,
    "erase_all": _erase_all,
    "at_most_two_rows": _at_most_two_rows,
    "most_rows": _most_rows,
    "fewest_cells": _fewest_cells,
    "even_rows": _even_rows,
    "top_row": _top_row,
}


def audit_episode(seed: int, mode: str, *, demos: int = 2, queries: int = 4) -> dict[str, Any]:
    episode = generate(seed, {PARAMETER: mode}, demos, queries)
    survivors: list[str] = []
    harmful: list[str] = []
    for name, rival in RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in episode["train"]):
            survivors.append(name)
            if any(rival(pair["input"]) != pair["output"] for pair in episode["test"]):
                harmful.append(name)
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {PARAMETER: mode},
        "fit_uses": "demonstrations_only",
        "rivals": sorted(RIVALS),
        "survivors": survivors,
        "harmful_survivors": harmful,
        "query_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["test"]],
        "intermediate": intermediate(episode["test"][0]["input"], {PARAMETER: mode}),
    }
