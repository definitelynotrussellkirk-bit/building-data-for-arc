"""Native episode-fixed endpoint-cap family for task 577d2db13443.

The default setting is the exact selected canonical program.  The alternative
first performs that endpoint pass, then uses the resulting color-1 connectivity
as an input-dependent intermediate to select and highlight its largest component.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import random
from typing import Any, Iterable

HOME = Path(__file__).resolve().parent
TASK_ID = "577d2db13443"
SETTINGS = (
    {"finish": "caps_only"},
    {"finish": "highlight_largest_cap_component"},
)
PALETTE = (2, 3, 4, 5, 6, 7, 9)
RIVALS_BY_FINISH = {
    "caps_only": ("all_nonzero", "left_only", "long_runs_only", "zero_delimited"),
    "highlight_largest_cap_component": (
        "largest_cap_bbox",
        "all_caps_highlighted",
        "smallest_cap_component",
        "first_cap_component",
    ),
}
RIVALS = tuple(dict.fromkeys(name for names in RIVALS_BY_FINISH.values() for name in names))
_PROGRAM_FILES = {
    "caps_only": "canonical.rkt",
    "highlight_largest_cap_component": "highlight_largest_cap_component.rkt",
}
_RIVAL_FILES = {
    "largest_cap_bbox": "largest_cap_bbox.rkt",
    "all_caps_highlighted": "all_caps_highlighted.rkt",
    "smallest_cap_component": "smallest_cap_component.rkt",
    "first_cap_component": "first_cap_component.rkt",
    "all_nonzero": "all_nonzero.rkt",
    "left_only": "left_only.rkt",
    "long_runs_only": "long_runs_only.rkt",
    "zero_delimited": "zero_delimited.rkt",
}
_NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _finish(value: Any) -> str:
    if type(value) is not dict or set(value) != {"finish"}:
        raise ValueError("settings must contain exactly the finish parameter")
    finish = value["finish"]
    if type(finish) is not str or finish not in _PROGRAM_FILES:
        raise ValueError("finish must be caps_only or highlight_largest_cap_component")
    return finish


def program(settings: dict[str, Any]) -> str:
    return (HOME / _PROGRAM_FILES[_finish(settings)]).read_text()


def rival_program(settings: dict[str, Any], name: str) -> str:
    finish = _finish(settings)
    if name not in RIVALS_BY_FINISH[finish]:
        raise ValueError(f"rival {name!r} is not declared for finish={finish}")
    return (HOME / _RIVAL_FILES[name]).read_text()


def validate_grid(grid: Any) -> None:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 by 1..30 with exact integer colors 0..9")


def row_runs(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    validate_grid(grid)
    result: list[tuple[int, int, int, int]] = []
    for row_index, row in enumerate(grid):
        column = 0
        while column < len(row):
            color = row[column]
            if color == 0:
                column += 1
                continue
            end = column
            while end + 1 < len(row) and row[end + 1] == color:
                end += 1
            result.append((row_index, column, end, color))
            column = end + 1
    return result


def cap_endpoints(grid: list[list[int]]) -> list[list[int]]:
    validate_grid(grid)
    result = [row[:] for row in grid]
    for row, start, end, _color in row_runs(grid):
        result[row][start] = 1
        result[row][end] = 1
    return result


def components_of_color(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    validate_grid(grid)
    remaining = {
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, column = stack.pop()
            for dr, dc in _NEIGHBORS4:
                neighbor = (row + dr, column + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        components.append(cells)
    components.sort(key=lambda cells: min(cells))
    return components


def _bbox_area(cells: Iterable[tuple[int, int]]) -> int:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    columns = [column for _, column in cells]
    return (max(rows) - min(rows) + 1) * (max(columns) - min(columns) + 1)


def cap_component_stats(grid: list[list[int]]) -> list[dict[str, Any]]:
    capped = cap_endpoints(grid)
    return [
        {
            "cells": [list(cell) for cell in sorted(cells)],
            "size": len(cells),
            "bbox_area": _bbox_area(cells),
            "top_left": list(min(cells)),
        }
        for cells in components_of_color(capped, 1)
    ]


def _pick(components: list[set[tuple[int, int]]], metric, *, largest: bool) -> set[tuple[int, int]]:
    if not components:
        return set()
    ordered = sorted(components, key=lambda cells: min(cells))
    best = ordered[0]
    for cells in ordered[1:]:
        score, best_score = metric(cells), metric(best)
        if (score > best_score) if largest else (score < best_score):
            best = cells
    return best


def _paint_cells(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    result = [row[:] for row in grid]
    for row, column in cells:
        result[row][column] = color
    return result


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    finish = _finish(settings)
    validate_grid(grid)
    capped = cap_endpoints(grid)
    if finish == "caps_only":
        return capped
    chosen = _pick(components_of_color(capped, 1), len, largest=True)
    return _paint_cells(capped, chosen, 8)


def _zero_delimited(grid: list[list[int]]) -> list[list[int]]:
    result = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        column = 0
        while column < len(row):
            if row[column] == 0:
                column += 1
                continue
            end = column
            while end + 1 < len(row) and row[end + 1] != 0:
                end += 1
            result[row_index][column] = 1
            result[row_index][end] = 1
            column = end + 1
    return result


def rival_output(grid: list[list[int]], settings: dict[str, Any], name: str) -> list[list[int]]:
    finish = _finish(settings)
    validate_grid(grid)
    if name not in RIVALS_BY_FINISH[finish]:
        raise ValueError(f"rival {name!r} is not declared for finish={finish}")
    if name == "all_nonzero":
        return [[1 if value else 0 for value in row] for row in grid]
    if name == "left_only":
        result = [row[:] for row in grid]
        for row, start, _end, _color in row_runs(grid):
            result[row][start] = 1
        return result
    if name == "long_runs_only":
        result = [row[:] for row in grid]
        for row, start, end, _color in row_runs(grid):
            if end - start + 1 >= 3:
                result[row][start] = result[row][end] = 1
        return result
    if name == "zero_delimited":
        return _zero_delimited(grid)

    capped = cap_endpoints(grid)
    components = components_of_color(capped, 1)
    if name == "all_caps_highlighted":
        return [[8 if value == 1 else value for value in row] for row in capped]
    if name == "largest_cap_bbox":
        chosen = _pick(components, _bbox_area, largest=True)
    elif name == "smallest_cap_component":
        chosen = _pick(components, len, largest=False)
    else:
        chosen = components[0] if components else set()
    return _paint_cells(capped, chosen, 8)


def _rng(seed: int, domain: str, index: int) -> random.Random:
    raw = f"{TASK_ID}:{domain}:{seed}:{index}".encode()
    return random.Random(int.from_bytes(sha256(raw).digest(), "big"))


def _normalize(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    cells = set(cells)
    low_row = min(row for row, _ in cells)
    low_column = min(column for _, column in cells)
    return {(row - low_row, column - low_column) for row, column in cells}


def _rotate(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    height = max(row for row, _ in cells) + 1
    return _normalize((column, height - 1 - row) for row, column in cells)


def _orient(cells: set[tuple[int, int]], rng: random.Random) -> set[tuple[int, int]]:
    cells = set(cells)
    for _ in range(rng.randrange(4)):
        cells = _rotate(cells)
    if rng.randrange(2):
        width = max(column for _, column in cells) + 1
        cells = _normalize((row, width - 1 - column) for row, column in cells)
    return cells


def _profiles(index: int) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    profile = index % 4
    if profile == 0:
        target = {(r, c) for r in range(2) for c in range(3)}
        distractor = {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)}
    elif profile == 1:
        target = {(r, c) for r in range(3) for c in range(3)} - {(0, 2), (2, 0)}
        distractor = {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3)}
    elif profile == 2:
        target = {(r, c) for r in range(2) for c in range(4)}
        distractor = {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3), (1, 1)}
    else:
        target = {(r, c) for r in range(3) for c in range(3)}
        distractor = {
            (0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3), (2, 1)
        }
    return target, distractor


class _ColorCycle:
    def __init__(self, rng: random.Random):
        self.colors = list(PALETTE)
        rng.shuffle(self.colors)
        self.index = 0

    def next(self) -> int:
        value = self.colors[self.index % len(self.colors)]
        self.index += 1
        return value


def _runs(sequence: list[int], rng: random.Random) -> list[list[int]]:
    """Partition one contiguous motif row into chunks of length one or two."""
    result: list[list[int]] = []
    position = 0
    prefer_pair = bool(rng.randrange(2))
    while position < len(sequence):
        remaining = len(sequence) - position
        length = 2 if remaining >= 2 and (remaining % 2 == 0 or prefer_pair) else 1
        result.append(sequence[position : position + length])
        position += length
        prefer_pair = not prefer_pair
    return result


def _paint_motif(
    grid: list[list[int]], cells: set[tuple[int, int]], colors: _ColorCycle, rng: random.Random
) -> None:
    by_row: dict[int, list[int]] = {}
    for row, column in cells:
        by_row.setdefault(row, []).append(column)
    for row in sorted(by_row):
        columns = sorted(by_row[row])
        sequences: list[list[int]] = []
        current = [columns[0]]
        for column in columns[1:]:
            if column == current[-1] + 1:
                current.append(column)
            else:
                sequences.append(current)
                current = [column]
        sequences.append(current)
        for sequence in sequences:
            for chunk in _runs(sequence, rng):
                color = colors.next()
                for column in chunk:
                    if grid[row][column] != 0:
                        raise AssertionError("motif overlap")
                    grid[row][column] = color


def _translate(cells: set[tuple[int, int]], top: int, left: int) -> set[tuple[int, int]]:
    return {(row + top, column + left) for row, column in cells}


def _corner_anchor(cells: set[tuple[int, int]], height: int, width: int, corner: int) -> tuple[int, int]:
    shape_h = max(row for row, _ in cells) + 1
    shape_w = max(column for _, column in cells) + 1
    top = 2 if corner < 2 else height - shape_h - 3
    left = 2 if corner % 2 == 0 else width - shape_w - 3
    return top, left


def _neighbors(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    result = set(cells)
    for row, column in tuple(result):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                result.add((row + dr, column + dc))
    return result


def _expected_caps(start: int, length: int) -> set[int]:
    return {start} if length == 1 else {start, start + length - 1}


def scene(seed: int, domain: str, index: int, height: int, width: int) -> list[list[int]]:
    if not (12 <= height <= 30 and 16 <= width <= 30):
        raise ValueError("scene dimensions must be within the authored 12x16..30x30 grammar")
    rng = _rng(seed, domain, index)
    grid = [[0] * width for _ in range(height)]
    colors = _ColorCycle(rng)
    target, distractor = _profiles(index + seed)
    target = _orient(target, rng)
    distractor = _orient(distractor, rng)
    corner = rng.randrange(4)
    target_cells = _translate(target, *_corner_anchor(target, height, width, corner))
    distractor_cells = _translate(
        distractor, *_corner_anchor(distractor, height, width, 3 - corner)
    )
    if _neighbors(target_cells) & distractor_cells:
        raise AssertionError("mandatory motifs overlap")
    _paint_motif(grid, target_cells, colors, rng)
    _paint_motif(grid, distractor_cells, colors, rng)
    blocked = _neighbors(target_cells | distractor_cells)
    cap_positions = set(target_cells | distractor_cells)

    placed_runs: list[tuple[int, int, int]] = []

    def place_run(row: int, start: int, length: int, *, color: int | None = None) -> bool:
        cells = {(row, column) for column in range(start, start + length)}
        caps = {(row, column) for column in _expected_caps(start, length)}
        if (
            start < 0
            or start + length > width
            or any(cell in blocked or grid[cell[0]][cell[1]] != 0 for cell in cells)
            or any(
                (row + dr, column + dc) in cap_positions
                for row, column in caps
                for dr, dc in _NEIGHBORS4
            )
        ):
            return False
        chosen = colors.next() if color is None else color
        for rr, cc in cells:
            grid[rr][cc] = chosen
        cap_positions.update(caps)
        placed_runs.append((row, start, length))
        return True

    # Guaranteed row-major and opposite-corner components make the "first" rival fail
    # and make the large scene occupy the full canvas rather than pad a tiny puzzle.
    if not place_run(0, 0, 5):
        raise AssertionError("top border anchor placement failed")
    if not place_run(height - 1, width - 6, 6):
        raise AssertionError("bottom border anchor placement failed")

    cluster_done = False
    slot_index = 0
    for row in range(0, height, 3):
        for start in range(0, width, 7):
            available = min(6, width - start)
            if available <= 0:
                continue
            if not cluster_done and available >= 4:
                cells = {(row, column) for column in range(start, start + 4)}
                caps = set(cells)
                if (
                    not any(cell in blocked or grid[cell[0]][cell[1]] != 0 for cell in cells)
                    and not any(
                        (rr + dr, cc + dc) in cap_positions
                        for rr, cc in caps
                        for dr, dc in _NEIGHBORS4
                    )
                ):
                    left_color = colors.next()
                    right_color = colors.next()
                    if right_color == left_color:
                        right_color = PALETTE[(PALETTE.index(left_color) + 1) % len(PALETTE)]
                    for column in range(start, start + 2):
                        grid[row][column] = left_color
                    for column in range(start + 2, start + 4):
                        grid[row][column] = right_color
                    cap_positions.update(caps)
                    placed_runs.extend(((row, start, 2), (row, start + 2, 2)))
                    cluster_done = True
                    continue
            length = min(available, 1 + ((slot_index + index + seed) % 6))
            slot_index += 1
            place_run(row, start, length)

    if not cluster_done:
        raise AssertionError("could not place color-boundary teaching cluster")
    observed_palette = {value for row in grid for value in row if value}
    if observed_palette != set(PALETTE):
        raise AssertionError(f"authored palette drift: {observed_palette}")

    capped = cap_endpoints(grid)
    components = components_of_color(capped, 1)
    by_size = sorted(components, key=len, reverse=True)
    if len(by_size) < 2 or len(by_size[0]) <= len(by_size[1]) or by_size[0] != target_cells:
        raise AssertionError("target is not the unique largest post-cap component")
    by_bbox = sorted(components, key=_bbox_area, reverse=True)
    if by_bbox[0] != distractor_cells or _bbox_area(distractor_cells) <= _bbox_area(target_cells):
        raise AssertionError("bbox counterexample was not preserved")
    return grid


def _pairs(seed: int, domain: str, sizes: list[tuple[int, int]], settings: dict[str, Any]):
    return [
        {"input": grid, "output": transform(grid, settings)}
        for index, (height, width) in enumerate(sizes)
        for grid in [scene(seed, domain, index, height, width)]
    ]


def generate(seed: int, settings: dict[str, Any], demos: int = 2, queries: int = 4) -> dict[str, Any]:
    _finish(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    demo_sizes = [(12, 16), (14, 18), (16, 20), (18, 22), (20, 24), (22, 26)]
    query_sizes = [(14, 17), (18, 22), (24, 27), (30, 30)]
    _rng(seed, "query-size-order", 0).shuffle(query_sizes)
    train = _pairs(seed, "demo", demo_sizes, settings)[:demos]
    test = _pairs(seed, "query", query_sizes, settings)[:queries]
    serialized = {repr(pair["input"]) for pair in train + test}
    if len(serialized) != len(train) + len(test):
        raise AssertionError("all demonstration and query inputs must be distinct")
    return {"train": train, "test": test, "program_solution": program(settings)}


def teaching_check(episode: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    finish = _finish(settings)
    demos = episode.get("train")
    if type(demos) is not list:
        raise ValueError("episode train split must be a list")
    survivors = [
        candidate
        for candidate in SETTINGS
        if all(transform(pair["input"], candidate) == pair["output"] for pair in demos)
    ]
    surviving_rivals = [
        name
        for name in RIVALS_BY_FINISH[finish]
        if all(rival_output(pair["input"], settings, name) == pair["output"] for pair in demos)
    ]
    return {
        "survivors": [deepcopy(candidate) for candidate in survivors],
        "surviving_rivals": surviving_rivals,
        "scope": "Two declared settings and eight setting-aware finite rivals; demonstrations only.",
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select an available query")
    train = deepcopy(episode.get("train"))
    if type(train) is not list:
        raise ValueError("episode train split must be a list")
    return {
        "train": train,
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
