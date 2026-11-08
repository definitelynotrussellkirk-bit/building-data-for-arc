"""Parametric prototype for 3194379886a5.

The default ``matched_prototype`` rule is the exact canonical program.
``matched_color_pointer`` first identifies the prototype that is D4-equivalent
to the query (Stage A), reads that matched panel's color as a 1-based pointer,
then emits the pointed-to prototype in its stored pose recolored by the query
(Stage B).  The pointer palette is an input-dependent derangement of 1,2,3, so
Stage B cannot be selected before Stage A.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "3194379886a5"
HERE = Path(__file__).resolve().parent
SELECTION_RULES = ("matched_prototype", "matched_color_pointer")
_DEMO_SIZES = (4, 5, 6, 4, 5, 6)
_QUERY_SIZES = (4, 5, 6, 6)
_DERANGEMENTS = ((2, 3, 1), (3, 1, 2))
_QUERY_COLORS = (6, 7, 8, 9)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def normalize_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"selection_rule"}:
        raise ValueError("settings must contain exactly selection_rule")
    value = settings["selection_rule"]
    if type(value) is not str or value not in SELECTION_RULES:
        raise ValueError(f"selection_rule must be one of {SELECTION_RULES}")
    return {"selection_rule": value}


def program(settings: Any) -> str:
    rule = normalize_settings(settings)["selection_rule"]
    name = "canonical.rkt" if rule == "matched_prototype" else "matched_color_pointer.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = frozenset(cells)
    if not cells:
        raise ValueError("shape cannot be empty")
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def _transforms(cells: Iterable[tuple[int, int]]) -> tuple[frozenset[tuple[int, int]], ...]:
    current = _normalize(cells)
    forms: set[frozenset[tuple[int, int]]] = set()
    for _ in range(4):
        forms.add(_normalize(current))
        forms.add(_normalize((row, -col) for row, col in current))
        current = _normalize((col, -row) for row, col in current)
    return tuple(sorted(forms, key=lambda form: tuple(sorted(form))))


def _key(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(tuple(sorted(form)) for form in _transforms(cells))


def projection_signature(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    cells = tuple(cells)
    rows = tuple(sorted(Counter(row for row, _ in cells).values()))
    cols = tuple(sorted(Counter(col for _, col in cells).values()))
    return tuple(sorted((rows, cols)))  # type: ignore[return-value]


_COLLISION_A = _normalize(((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)))
_COLLISION_B = _normalize(((0, 0), (1, 0), (2, 0), (2, 1), (3, 0)))
assert _key(_COLLISION_A) != _key(_COLLISION_B)
assert projection_signature(_COLLISION_A) == projection_signature(_COLLISION_B)


def _components(cells: Iterable[tuple[int, int]]) -> list[frozenset[tuple[int, int]]]:
    remaining = set(cells)
    result: list[frozenset[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        pending = [start]
        component = {start}
        while pending:
            row, col = pending.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    pending.append(point)
        result.append(frozenset(component))
    return result


def analyze(grid: Any) -> dict[str, Any]:
    if (
        type(grid) is not list
        or not 3 <= len(grid) <= 6
        or type(grid[0]) is not list
        or len(grid[0]) != 4 * len(grid) + 3
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("grid must encode four square panels of size 3..6")
    size = len(grid)
    separators = tuple(panel * (size + 1) + size for panel in range(3))
    full_fives = tuple(
        col for col in range(len(grid[0])) if all(grid[row][col] == 5 for row in range(size))
    )
    if full_fives != separators:
        raise ValueError("expected exactly three full-height gray separators")

    panel_cells: list[frozenset[tuple[int, int]]] = []
    panel_colors: list[int] = []
    for panel in range(4):
        left = panel * (size + 1)
        values = {
            grid[row][left + col]
            for row in range(size)
            for col in range(size)
            if grid[row][left + col] != 0
        }
        if len(values) != 1 or 5 in values:
            raise ValueError(f"panel {panel} must have one non-divider foreground color")
        color = next(iter(values))
        cells = frozenset(
            (row, col)
            for row in range(size)
            for col in range(size)
            if grid[row][left + col] == color
        )
        if len(cells) < 3 or len(_components(cells)) != 1:
            raise ValueError(f"panel {panel} must contain one connected shape")
        panel_colors.append(color)
        panel_cells.append(cells)

    if tuple(sorted(panel_colors[:3])) != (1, 2, 3):
        raise ValueError("prototype colors must be a permutation of 1,2,3")
    if panel_colors[3] not in _QUERY_COLORS:
        raise ValueError("query color must be one of 6,7,8,9")
    prototype_keys = tuple(_key(cells) for cells in panel_cells[:3])
    if len(set(prototype_keys)) != 3:
        raise ValueError("prototype D4 classes must be distinct")
    query_key = _key(panel_cells[3])
    matches = [index for index, key in enumerate(prototype_keys) if key == query_key]
    if len(matches) != 1:
        raise ValueError("query must match exactly one prototype")
    match_index = matches[0]
    pointer_color = panel_colors[match_index]
    pointer_index = pointer_color - 1
    return {
        "panel_size": size,
        "prototype_cells": tuple(panel_cells[:3]),
        "query_cells": panel_cells[3],
        "prototype_colors": tuple(panel_colors[:3]),
        "query_color": panel_colors[3],
        "match_index": match_index,
        "pointer_color": pointer_color,
        "pointer_index": pointer_index,
        "projection_matches": tuple(
            index
            for index, cells in enumerate(panel_cells[:3])
            if projection_signature(cells) == projection_signature(panel_cells[3])
        ),
    }


def _paint(cells: Iterable[tuple[int, int]], size: int, color: int) -> list[list[int]]:
    result = [[0 for _ in range(size)] for _ in range(size)]
    for row, col in cells:
        result[row][col] = color
    return result


def finish_python(grid: Any, settings: Any) -> list[list[int]]:
    rule = normalize_settings(settings)["selection_rule"]
    facts = analyze(grid)
    selected = facts["match_index"] if rule == "matched_prototype" else facts["pointer_index"]
    return _paint(facts["prototype_cells"][selected], facts["panel_size"], facts["query_color"])


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:color-pointer-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _random_connected_shape(rng: random.Random, size: int, cell_count: int) -> frozenset[tuple[int, int]]:
    cells = {(0, 0)}
    while len(cells) < cell_count:
        frontier = {
            point
            for row, col in cells
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
            if 0 <= point[0] < size and 0 <= point[1] < size and point not in cells
        }
        if not frontier:
            raise RuntimeError("shape frontier exhausted")
        cells.add(rng.choice(sorted(frontier)))
    return _normalize(cells)


def _shift(rng: random.Random, cells: Iterable[tuple[int, int]], size: int) -> frozenset[tuple[int, int]]:
    cells = _normalize(cells)
    height = max(row for row, _ in cells) + 1
    width = max(col for _, col in cells) + 1
    top = rng.randint(0, size - height)
    left = rng.randint(0, size - width)
    return frozenset((top + row, left + col) for row, col in cells)


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    sizes = _DEMO_SIZES if split == "train" else _QUERY_SIZES
    size = sizes[index]
    rng = _rng(seed, split, index)
    match_index = (index + (0 if split == "train" else 2) + seed) % 3
    decoy_index = 1 if match_index == 0 else 0
    target = rng.choice(_transforms(_COLLISION_B))
    decoy = rng.choice(_transforms(_COLLISION_A))
    prototypes: list[frozenset[tuple[int, int]] | None] = [None, None, None]
    prototypes[match_index] = target
    prototypes[decoy_index] = decoy
    remaining_index = next(i for i, value in enumerate(prototypes) if value is None)
    forbidden = {_key(target), _key(decoy)}
    for _ in range(400):
        candidate = _random_connected_shape(rng, size, rng.randint(3, min(11, size * size // 2)))
        if _key(candidate) not in forbidden:
            prototypes[remaining_index] = candidate
            break
    if prototypes[remaining_index] is None:
        raise RuntimeError("could not construct third prototype")
    concrete = tuple(value for value in prototypes if value is not None)
    if len(concrete) != 3:
        raise AssertionError("prototype construction incomplete")
    placed = tuple(_shift(rng, rng.choice(_transforms(value)), size) for value in concrete)
    query = _shift(rng, rng.choice(_transforms(target)), size)
    # The first two demonstrations deliberately use opposite pointer directions.
    # This keeps the two-demo minimum identifiable against fixed-panel and
    # cyclic-next/previous shortcuts instead of relying on a lucky seed.
    if split == "train" and index < 2:
        colors = _DERANGEMENTS[index]
    else:
        colors = _DERANGEMENTS[rng.randrange(len(_DERANGEMENTS))]
    query_color = _QUERY_COLORS[(index + seed + (0 if split == "train" else 1)) % len(_QUERY_COLORS)]

    grid = [[0 for _ in range(4 * size + 3)] for _ in range(size)]
    for panel, cells in enumerate(placed):
        left = panel * (size + 1)
        for row, col in cells:
            grid[row][left + col] = colors[panel]
    query_left = 3 * (size + 1)
    for row, col in query:
        grid[row][query_left + col] = query_color
    for panel in range(3):
        separator = panel * (size + 1) + size
        for row in range(size):
            grid[row][separator] = 5

    facts = analyze(grid)
    if facts["match_index"] != match_index or facts["pointer_index"] == match_index:
        raise AssertionError(f"scene lost dependency: {facts}")
    return grid


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _exact_int(seed, "seed", 0, 2**63 - 1)
    demos = _exact_int(demos, "demos", 2, 6)
    queries = _exact_int(queries, "queries", 1, 4)
    normalized = normalize_settings(settings)
    train_inputs = [_scene(seed, "train", index) for index in range(demos)]
    test_inputs = [_scene(seed, "test", index) for index in range(queries)]
    all_inputs = train_inputs + test_inputs
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise RuntimeError("episode inputs must be distinct")

    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {"input": copy.deepcopy(grid), "output": finish_python(grid, normalized)}

    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program(normalized),
        "settings": copy.deepcopy(normalized),
        "metadata": {
            "schema": "3194379886a5-color-pointer-v1",
            "seed": seed,
            "max_lawful_canvas": [6, 27],
            "sequential_dependency": {
                "step_a": "match the query's normalized D4 class to one prototype",
                "intermediate": "matched prototype index and its input color pointer",
                "step_b": "select the pointed-to prototype and repaint it with the query color",
            },
        },
    }
