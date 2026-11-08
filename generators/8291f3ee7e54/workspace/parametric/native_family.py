"""Deterministic native episode family for the ring-order parameter.

The first six slots are production-shaped inputs from the reviewed generator.
The four query slots are fixed independently of the requested demonstration
count; the first query is a substantive 30x30 extension with a detached
same-color distractor.  Inputs never depend on the hidden ring-order setting.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

RING_ORDERS = ("largest_outside", "smallest_outside")
MAX_DEMOS = 6
MAX_QUERIES = 4
QUERY_OFFSET = MAX_DEMOS
TOTAL_SLOTS = MAX_DEMOS + MAX_QUERIES

_HOME = Path(__file__).resolve().parent
_ROOT = _HOME.parents[3]
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Colors are assigned in descending selected-span order.  The first two rows
# are intentionally non-monotone so neither numeric ascending nor descending
# ring assignment can explain the minimum visible lesson.
_PALETTES: tuple[tuple[int, ...], ...] = (
    (5, 1, 9, 3, 7),
    (4, 9, 2, 8, 1),
    (8, 3, 6, 1, 9),
    (6, 2, 9, 4, 7),
    (3, 8, 1, 7, 5),
    (9, 4, 7, 2, 6),
    (6, 2, 9, 4, 1),
    (7, 1, 5, 9, 3),
    (2, 8, 4, 9, 1),
    (5, 9, 2, 7, 4),
)


def _load_adjacent(filename: str) -> ModuleType:
    path = (_HOME / filename).resolve()
    if path.parent != _HOME or not path.is_file():
        raise ValueError(f"missing adjacent native-family resource: {filename}")
    name = "_arc_8291f3ee7e54_family_" + path.stem + "_" + hashlib.sha256(str(path).encode()).hexdigest()
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adjacent native-family resource: {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load_adjacent("prototype.py")


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative integer; bool is forbidden")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_ring_order(ring_order: Any) -> str:
    if type(ring_order) is not str or ring_order not in RING_ORDERS:
        raise ValueError("ring_order must be exactly 'largest_outside' or 'smallest_outside'")
    return ring_order


def _validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return deepcopy(grid)


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _span(bbox: tuple[int, int, int, int]) -> int:
    r0, c0, r1, c1 = bbox
    return max(r1 - r0 + 1, c1 - c0 + 1)


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(h)
        for col in range(w)
        if grid[row][col] == color
    }
    result: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells: list[tuple[int, int]] = []
        while stack:
            row, col = stack.pop()
            cells.append((row, col))
            for dr, dc in _DIRS4:
                nxt = (row + dr, col + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
        result.append(cells)
    return result


def analyze_input(grid: Any) -> dict[str, Any]:
    """Return the exact component/span intermediate consumed by ring painting."""
    source = _validate_grid(grid)
    colors = sorted({cell for row in source for cell in row if cell != 0})
    if not colors:
        raise ValueError("input needs at least one nonzero color")
    layers: list[dict[str, Any]] = []
    for color in colors:
        components = _components(source, color)
        component_rows = [
            {"cells": cells, "bbox": _bbox(cells), "span": _span(_bbox(cells))}
            for cells in components
        ]
        selected = max(
            component_rows,
            key=lambda row: (
                row["span"],
                len(row["cells"]),
                -row["bbox"][0],
                -row["bbox"][1],
            ),
        )
        all_cells = [cell for component in component_rows for cell in component["cells"]]
        union_bbox = _bbox(all_cells)
        layers.append(
            {
                "color": color,
                "selected_span": selected["span"],
                "selected_bbox": list(selected["bbox"]),
                "selected_cell_count": len(selected["cells"]),
                "component_count": len(component_rows),
                "union_bbox": list(union_bbox),
                "union_span": _span(union_bbox),
            }
        )
    layers.sort(key=lambda layer: (-layer["selected_span"], layer["color"]))
    spans = [layer["selected_span"] for layer in layers]
    if len(spans) != len(set(spans)):
        raise ValueError(f"selected component spans must be unique: {spans}")
    return {"layers": layers, "spans": spans}


def _recolor_by_span(grid: list[list[int]], slot: int) -> list[list[int]]:
    facts = analyze_input(grid)
    palette = _PALETTES[slot]
    if len(facts["layers"]) > len(palette):
        raise ValueError("palette is too small for generated layer count")
    mapping = {
        layer["color"]: palette[index]
        for index, layer in enumerate(facts["layers"])
    }
    return [[mapping.get(cell, cell) for cell in row] for row in grid]


def _paint_frame(
    grid: list[list[int]],
    top: int,
    left: int,
    side: int,
    color: int,
) -> None:
    for row in range(top, top + side):
        for col in range(left, left + side):
            if row in (top, top + side - 1) or col in (left, left + side - 1):
                if grid[row][col] != 0:
                    raise AssertionError("30x30 frame construction overlapped")
                grid[row][col] = color


def _build_30x30(seed: int) -> list[list[int]]:
    """Build a boundary-rich five-layer query with a largest-color distractor."""
    seed = _validate_seed(seed)
    grid = [[0 for _ in range(30)] for _ in range(30)]
    colors = _PALETTES[QUERY_OFFSET]
    placements = (
        (0, 0, 11),
        (0, 21, 9),
        (23, 0, 7),
        (25, 25, 5),
        (12 + seed % 3, 12 + (seed // 3) % 3, 3),
    )
    for color, (top, left, side) in zip(colors, placements, strict=True):
        _paint_frame(grid, top, left, side, color)
    distractor_col = 10 + seed % 9
    if grid[29][distractor_col] != 0:
        raise AssertionError("30x30 distractor collided")
    grid[29][distractor_col] = colors[0]
    return grid


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _thaw(grid: tuple[tuple[int, ...], ...]) -> list[list[int]]:
    return [list(row) for row in grid]


@lru_cache(maxsize=64)
def _base_inputs(seed: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    seed = _validate_seed(seed)
    rows, _, _ = _PROTOTYPE._input_rows(seed, TOTAL_SLOTS, root=_ROOT)
    inputs = [_recolor_by_span(row["input"], slot) for slot, row in enumerate(rows)]
    inputs[QUERY_OFFSET] = _build_30x30(seed)
    payloads = [repr(grid) for grid in inputs]
    if len(payloads) != len(set(payloads)):
        raise AssertionError("native family produced duplicate inputs")
    for slot, grid in enumerate(inputs):
        facts = analyze_input(grid)
        if slot == QUERY_OFFSET and facts["spans"] != [11, 9, 7, 5, 3]:
            raise AssertionError("30x30 query lost its intended span sequence")
    return tuple(_freeze(grid) for grid in inputs)


def build_input(seed: int, slot: int) -> list[list[int]]:
    seed = _validate_seed(seed)
    if type(slot) is not int or not 0 <= slot < TOTAL_SLOTS:
        raise ValueError(f"slot must be an integer in 0..{TOTAL_SLOTS - 1}")
    return _thaw(_base_inputs(seed)[slot])


def apply_rule(grid: Any, ring_order: str) -> list[list[int]]:
    """Python label claim for the exact selected Racket ring semantics."""
    source = _validate_grid(grid)
    ring_order = _validate_ring_order(ring_order)
    layers = analyze_input(source)["layers"]
    n = layers[0]["selected_span"]
    colors = [layer["color"] for layer in layers]
    if ring_order == "smallest_outside":
        colors.reverse()
    output = [[0 for _ in range(n)] for _ in range(n)]
    for layer, color in zip(layers, colors, strict=True):
        side = layer["selected_span"]
        offset = (n - side) // 2
        for row in range(offset, offset + side):
            for col in range(offset, offset + side):
                if (
                    row in (offset, offset + side - 1)
                    or col in (offset, offset + side - 1)
                ):
                    output[row][col] = color
    return output


def generate_episode(
    seed: int,
    ring_order: str,
    demos: int,
    queries: int,
    program_solution: str,
) -> dict[str, Any]:
    """Return the worker-facing train/test/program payload."""
    seed = _validate_seed(seed)
    ring_order = _validate_ring_order(ring_order)
    if type(demos) is not int or not 2 <= demos <= MAX_DEMOS:
        raise ValueError("demos must be an integer in 2..6; bool is forbidden")
    if type(queries) is not int or not 1 <= queries <= MAX_QUERIES:
        raise ValueError("queries must be an integer in 1..4; bool is forbidden")
    if type(program_solution) is not str or not program_solution.strip():
        raise ValueError("program_solution must be nonempty Racket source")

    def pair(slot: int) -> dict[str, list[list[int]]]:
        input_grid = build_input(seed, slot)
        return {"input": input_grid, "output": apply_rule(input_grid, ring_order)}

    return {
        "train": [pair(slot) for slot in range(demos)],
        "test": [pair(QUERY_OFFSET + index) for index in range(queries)],
        "program_solution": program_solution,
    }
