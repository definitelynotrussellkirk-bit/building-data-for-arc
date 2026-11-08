"""Reference Python implementation and setting-independent scene sampler.

The finite family keeps the original topology rule as its default and adds a
composed alternative:

1. find the unique component with the largest enclosed-hole count;
2. use that component's occupied-cell count as a threshold;
3. recolor every component 8 iff its size meets that threshold, else 2.

Inputs are sampled without consulting the selected setting.  Every generated
scene contains a unique two-hole anchor, one one-hole object, a large solid, a
small solid, and a leaky bbox-gap distractor.  The one-hole and leaky objects
alternate between below- and above-threshold sizes, so visible demonstrations
reject fixed size-rank and bbox-gap shortcuts while preserving the topology-led
intermediate.
"""
from __future__ import annotations

import hashlib
import random
from collections import deque
from typing import Any

DEFAULT_SETTINGS = {"rule_mode": "hole_presence"}
ALTERNATE_SETTINGS = {"rule_mode": "most_holed_size_threshold"}
SUPPORTED_SETTINGS = (DEFAULT_SETTINGS, ALTERNATE_SETTINGS)

_DEMO_DIMS = ((12, 16), (14, 18), (18, 20), (16, 24), (20, 22), (24, 26))
_QUERY_DIMS = ((13, 17), (21, 23), (26, 27), (30, 30))
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def validate_settings(settings: Any) -> dict[str, str]:
    if not isinstance(settings, dict) or set(settings) != {"rule_mode"}:
        raise ValueError("settings must contain exactly rule_mode")
    value = settings["rule_mode"]
    if value not in {item["rule_mode"] for item in SUPPORTED_SETTINGS}:
        raise ValueError("settings rule_mode is undeclared")
    return {"rule_mode": value}


def _validate_grid(grid: Any) -> str | None:
    if not isinstance(grid, list) or not 1 <= len(grid) <= 30:
        return "grid must have 1..30 rows"
    if not grid or not isinstance(grid[0], list) or not 1 <= len(grid[0]) <= 30:
        return "grid must have 1..30 columns"
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            return "grid must be rectangular"
        for cell in row:
            if isinstance(cell, bool) or not isinstance(cell, int) or cell not in (0, 6):
                return "input cells must be exact integers 0 or 6"
    return None


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _hole_count(cells: set[tuple[int, int]]) -> int:
    r0, c0, r1, c1 = _bbox(cells)
    background = {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if (row, col) not in cells
    }
    seen: set[tuple[int, int]] = set()
    holes = 0
    for start in sorted(background):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        touches_edge = False
        while queue:
            row, col = queue.popleft()
            if row in (r0, r1) or col in (c0, c1):
                touches_edge = True
            for dr, dc in _DIR4:
                neighbor = (row + dr, col + dc)
                if neighbor in background and neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        if not touches_edge:
            holes += 1
    return holes


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    answer: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if grid[start_row][start_col] != 6 or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells: set[tuple[int, int]] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in _DIR4:
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == 6
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0, c0, r1, c1 = _bbox(cells)
            answer.append(
                {
                    "index": len(answer),
                    "cells": cells,
                    "size": len(cells),
                    "hole_count": _hole_count(cells),
                    "bbox": (r0, c0, r1, c1),
                    "touches_outer_boundary": any(
                        row in (0, height - 1) or col in (0, width - 1)
                        for row, col in cells
                    ),
                }
            )
    return answer


def analyze_input(grid: Any) -> dict[str, Any]:
    error = _validate_grid(grid)
    if error:
        return {"errors": [error], "components": []}

    components = _components(grid)
    errors: list[str] = []
    if len(components) not in (4, 5):
        errors.append(f"expected four or five color-6 components, got {len(components)}")

    two_hole = [component for component in components if component["hole_count"] == 2]
    one_hole = [component for component in components if component["hole_count"] == 1]
    unexpected = [component for component in components if component["hole_count"] not in (0, 1, 2)]
    if len(two_hole) != 1 or len(one_hole) != 1 or unexpected:
        holes = sorted(component["hole_count"] for component in components)
        errors.append(
            "expected exactly one two-hole anchor, one one-hole object, and all remaining objects solid; "
            f"got {holes}"
        )

    anchor = two_hole[0] if len(two_hole) == 1 else None
    anchor_size = anchor["size"] if anchor else None
    if anchor_size is not None:
        others = [component for component in components if component is not anchor]
        if not any(component["size"] > anchor_size for component in others):
            errors.append("at least one non-anchor object must be larger than the anchor")
        if not any(component["size"] < anchor_size for component in others):
            errors.append("at least one non-anchor object must be smaller than the anchor")

    return {
        "errors": errors,
        "components": components,
        "anchor": anchor,
        "anchor_size": anchor_size,
        "nonzero_cells": sum(component["size"] for component in components),
        "outer_boundary_components": sum(
            bool(component["touches_outer_boundary"]) for component in components
        ),
    }


def solve(grid: list[list[int]], settings: Any) -> list[list[int]]:
    normalized = validate_settings(settings)
    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise ValueError("input violates parametric grammar: " + "; ".join(analysis["errors"]))
    output = [[0 for _ in row] for row in grid]
    threshold = analysis["anchor_size"]
    for component in analysis["components"]:
        if normalized["rule_mode"] == "hole_presence":
            color = 8 if component["hole_count"] >= 1 else 2
        else:
            color = 8 if component["size"] >= threshold else 2
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def _rect_perimeter(height: int, width: int) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }


def _anchor_shape(height: int, width: int) -> set[tuple[int, int]]:
    cells = _rect_perimeter(height, width)
    divider = width // 2
    cells.update((row, divider) for row in range(1, height - 1))
    return cells


def _one_hole_shape(height: int, width: int, *, dense: bool) -> set[tuple[int, int]]:
    if not dense:
        return _rect_perimeter(height, width)
    cells = _solid_shape(height, width)
    cells.remove((height // 2, width // 2))
    return cells


def _solid_shape(height: int, width: int) -> set[tuple[int, int]]:
    return {(row, col) for row in range(height) for col in range(width)}


def _small_shape() -> set[tuple[int, int]]:
    return {(0, 0), (0, 1), (1, 0), (1, 1)}


def _leaky_shape(height: int, width: int, *, dense: bool) -> set[tuple[int, int]]:
    middle = width // 2
    if dense:
        cells = _solid_shape(height, width)
        cells.remove((0, middle))
        cells.remove((1, middle))
        return cells
    cells = _rect_perimeter(height, width)
    cells.remove((0, middle))
    return cells


def _rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"14dacb3b518f:{seed}:{role}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _slots(height: int, width: int) -> list[tuple[int, int, int, int]]:
    separator_row = height // 2
    row_specs = ((0, separator_row), (separator_row + 1, height - separator_row - 1))
    usable_width = width - 2
    base, remainder = divmod(usable_width, 3)
    widths = [base + (1 if index < remainder else 0) for index in range(3)]
    column_specs = []
    start = 0
    for slot_width in widths:
        column_specs.append((start, slot_width))
        start += slot_width + 1
    return [
        (row_start, col_start, slot_h, slot_w)
        for row_start, slot_h in row_specs
        for col_start, slot_w in column_specs
    ]


def _role_shape(role: str, slot_h: int, slot_w: int) -> set[tuple[int, int]]:
    shape_h = min(slot_h, 9)
    shape_w = min(slot_w, 9)
    if role in {"anchor", "one_hole_small", "one_hole_large"}:
        if shape_h < 5 or shape_w < 5:
            raise ValueError("profile slot is too small for enclosed-hole grammar")
    if role in {"leaky_small", "leaky_large"}:
        if shape_h < 3 or shape_w < 3:
            raise ValueError("profile slot is too small for leaky distractor grammar")
    if role == "anchor":
        return _anchor_shape(shape_h, shape_w)
    if role == "one_hole_small":
        return _one_hole_shape(shape_h, shape_w, dense=False)
    if role == "one_hole_large":
        return _one_hole_shape(shape_h, shape_w, dense=True)
    if role == "large_solid":
        return _solid_shape(slot_h, slot_w)
    if role == "small_solid":
        return _small_shape()
    if role == "leaky_small":
        return _leaky_shape(shape_h, shape_w, dense=False)
    if role == "leaky_large":
        return _leaky_shape(shape_h, shape_w, dense=True)
    raise AssertionError(role)


def _profile(role: str, index: int) -> tuple[bool, bool]:
    profiles = (
        (False, False),
        (True, False),
        (False, True),
        (True, True),
        (False, True),
        (True, False),
    ) if role == "demo" else (
        (True, True),
        (False, True),
        (True, False),
        (False, False),
    )
    return profiles[index]


def _place(
    grid: list[list[int]],
    cells: set[tuple[int, int]],
    slot: tuple[int, int, int, int],
    rng: random.Random,
    corner_lock: bool,
) -> None:
    slot_r, slot_c, slot_h, slot_w = slot
    shape_h = max(row for row, _ in cells) + 1
    shape_w = max(col for _, col in cells) + 1
    row_slack, col_slack = slot_h - shape_h, slot_w - shape_w
    if corner_lock:
        # The slot's location determines the outward corner.  This makes the
        # 30x30 stress case exercise clipping-adjacent topology without
        # clipping any component.
        top = slot_r == 0
        left = slot_c == 0
        row_offset = 0 if top else row_slack
        col_offset = 0 if left else col_slack
    else:
        row_offset = rng.randint(0, row_slack)
        col_offset = rng.randint(0, col_slack)
    for row, col in cells:
        grid[slot_r + row_offset + row][slot_c + col_offset + col] = 6


def make_scene(seed: int, role: str, index: int) -> list[list[int]]:
    dims = _DEMO_DIMS if role == "demo" else _QUERY_DIMS
    height, width = dims[index]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    slots = _slots(height, width)
    rng = _rng(seed, role, index)
    one_hole_large, leaky_large = _profile(role, index)

    wide = [slot_index for slot_index, slot in enumerate(slots) if slot[2] >= 5 and slot[3] >= 5]
    rng.shuffle(wide)
    if len(wide) < 4:
        raise AssertionError("profile needs four topology-capable slots")
    assignments = {
        "anchor": wide.pop(),
        "one_hole_large" if one_hole_large else "one_hole_small": wide.pop(),
        "large_solid": wide.pop(),
    }
    remaining = [slot_index for slot_index in range(len(slots)) if slot_index not in assignments.values()]
    if leaky_large:
        leaky_candidates = [slot_index for slot_index in wide if slot_index in remaining]
        if not leaky_candidates:
            raise AssertionError("profile needs a fourth topology-capable slot")
        leaky_slot = rng.choice(leaky_candidates)
    else:
        leaky_slot = rng.choice(remaining)
    assignments["leaky_large" if leaky_large else "leaky_small"] = leaky_slot
    remaining.remove(leaky_slot)
    small_slot = rng.choice(remaining)
    assignments["small_solid"] = small_slot

    corner_lock = role == "query" and index == len(_QUERY_DIMS) - 1
    for object_role, slot_index in assignments.items():
        slot = slots[slot_index]
        cells = _role_shape(object_role, slot[2], slot[3])
        _place(grid, cells, slot, rng, corner_lock)
    analysis = analyze_input(grid)
    if analysis["errors"]:
        raise AssertionError(f"internal scene grammar failure: {analysis['errors']}")
    return grid


def generate_inputs(seed: int, demos: int, queries: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    return (
        [make_scene(seed, "demo", index) for index in range(demos)],
        [make_scene(seed, "query", index) for index in range(queries)],
    )
