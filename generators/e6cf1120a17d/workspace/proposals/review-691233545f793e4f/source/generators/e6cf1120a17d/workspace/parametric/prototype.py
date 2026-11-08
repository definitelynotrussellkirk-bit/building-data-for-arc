#!/usr/bin/env python3
"""Native routing family for e6cf1120a17d.

Both settings share the same rectangle-and-four-markers input grammar.  The
canonical setting clears the inset markers and routes each to the diagonally
opposite outside corner.  The alternative first finds the largest marker in
clockwise order, then rotates that entire clockwise marker sequence so the
largest marker lands at the outside top-left corner.
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Any

TASK_ID = "e6cf1120a17d"
ROUTINGS = ("diagonal_opposite", "max_to_topleft")
DEFAULT_SETTINGS = {"routing": "diagonal_opposite"}
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)

_HOME = Path(__file__).resolve().parent
_CANONICAL_PATH = _HOME / "canonical.rkt"
_MAX_PATH = _HOME / "max_to_topleft.rkt"

_DEMO_PROFILES: tuple[tuple[int, int], ...] = (
    (9, 10),
    (11, 13),
    (14, 15),
    (18, 17),
    (22, 24),
    (26, 25),
)
_QUERY_PROFILES: tuple[tuple[int, int], ...] = (
    (10, 12),
    (16, 19),
    (24, 27),
    (30, 30),
)
# Clockwise marker indices: TL=0, TR=1, BR=2, BL=3.  The first two demo
# positions differ, so no fixed cyclic rotation can mimic max-driven routing.
_DEMO_MAX_POSITIONS = (0, 1, 3, 2, 0, 1)
_QUERY_MAX_POSITIONS = (1, 3, 2, 0)
# Rank schedules also prevent a "minimum marker to top-left" explanation from
# coinciding with the canonical two-step diagonal route in both demonstrations.
_DEMO_MIN_POSITIONS = (1, 3, 0, 1, 2, 3)
_QUERY_MIN_POSITIONS = (3, 0, 1, 2)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"routing"}:
        raise ValueError("settings must name exactly routing")
    routing = value["routing"]
    if routing not in ROUTINGS:
        raise ValueError("routing must be diagonal_opposite or max_to_topleft")
    return {"routing": routing}


def _rng(seed: int, domain: str, index: int) -> random.Random:
    payload = f"{TASK_ID}|v1|{seed}|{domain}|{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def program(settings: dict[str, Any]) -> str:
    selected = _settings(settings)
    path = _CANONICAL_PATH if selected["routing"] == "diagonal_opposite" else _MAX_PATH
    return path.read_text(encoding="utf-8")


def _strict_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not grid[0] or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integers 0..9")
    return grid


def _geometry(grid: list[list[int]]) -> dict[str, Any]:
    source = _strict_grid(grid)
    rows, cols = len(source), len(source[0])
    counts: dict[int, int] = {}
    for row in source:
        for value in row:
            if value != 0:
                counts[value] = counts.get(value, 0) + 1
    if not counts:
        raise ValueError("input requires a nonzero rectangle")
    rect_color = max(counts, key=counts.get)
    rect_cells = [
        (r, c)
        for r, row in enumerate(source)
        for c, value in enumerate(row)
        if value == rect_color
    ]
    r0 = min(r for r, _ in rect_cells)
    r1 = max(r for r, _ in rect_cells)
    c0 = min(c for _, c in rect_cells)
    c1 = max(c for _, c in rect_cells)
    if r1 - r0 + 1 < 5 or c1 - c0 + 1 < 5:
        raise ValueError("rectangle must be at least 5x5")
    if r0 < 1 or c0 < 1 or r1 >= rows - 1 or c1 >= cols - 1:
        raise ValueError("rectangle requires a one-cell outside-corner margin")

    # Clockwise order is the common representation used by both routings.
    inside = (
        (r0 + 1, c0 + 1),
        (r0 + 1, c1 - 1),
        (r1 - 1, c1 - 1),
        (r1 - 1, c0 + 1),
    )
    outside = (
        (r0 - 1, c0 - 1),
        (r0 - 1, c1 + 1),
        (r1 + 1, c1 + 1),
        (r1 + 1, c0 - 1),
    )
    markers = tuple(source[r][c] for r, c in inside)
    if any(value in (0, rect_color) for value in markers) or len(set(markers)) != 4:
        raise ValueError("inset markers must be four distinct nonzero non-rectangle colors")
    marker_cells = set(inside)
    for r in range(rows):
        for c in range(cols):
            in_box = r0 <= r <= r1 and c0 <= c <= c1
            if in_box:
                expected = markers[inside.index((r, c))] if (r, c) in marker_cells else rect_color
                if source[r][c] != expected:
                    raise ValueError("rectangle body must be solid except its four inset markers")
            elif source[r][c] != 0:
                raise ValueError("all cells outside the input rectangle must be background 0")
    return {
        "rect_color": rect_color,
        "bbox": (r0, c0, r1, c1),
        "inside": inside,
        "outside": outside,
        "markers": markers,
    }


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    source = _strict_grid(grid)
    selected = _settings(settings)
    geometry = _geometry(source)
    markers = geometry["markers"]
    if selected["routing"] == "diagonal_opposite":
        routed = markers[2:] + markers[:2]
    else:
        max_index = markers.index(max(markers))
        routed = markers[max_index:] + markers[:max_index]

    output = [row[:] for row in source]
    for r, c in geometry["inside"]:
        output[r][c] = 0
    for (r, c), value in zip(geometry["outside"], routed):
        output[r][c] = value
    return output


def _sample_input(seed: int, domain: str, index: int) -> list[list[int]]:
    if domain == "demo":
        rows, cols = _DEMO_PROFILES[index]
        max_position = _DEMO_MAX_POSITIONS[index]
        min_position = _DEMO_MIN_POSITIONS[index]
    elif domain == "query":
        rows, cols = _QUERY_PROFILES[index]
        max_position = _QUERY_MAX_POSITIONS[index]
        min_position = _QUERY_MIN_POSITIONS[index]
    else:
        raise ValueError("domain must be demo or query")
    rng = _rng(seed, domain, index)

    if rows >= 24:
        rect_h = rows - rng.randint(3, 5)
        rect_w = cols - rng.randint(3, 5)
    else:
        rect_h = rng.randint(5, max(5, rows - 3))
        rect_w = rng.randint(5, max(5, cols - 3))
    rect_r = rng.randint(1, rows - rect_h - 1)
    rect_c = rng.randint(1, cols - rect_w - 1)

    palette = rng.sample(range(1, 10), 5)
    rect_color = palette[0]
    marker_values = sorted(palette[1:])
    minimum = marker_values.pop(0)
    maximum = marker_values.pop()
    rng.shuffle(marker_values)
    markers = [0, 0, 0, 0]
    markers[min_position] = minimum
    markers[max_position] = maximum
    remaining_positions = [
        position for position in range(4) if position not in (min_position, max_position)
    ]
    for position, value in zip(remaining_positions, marker_values):
        markers[position] = value

    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    for r in range(rect_r, rect_r + rect_h):
        for c in range(rect_c, rect_c + rect_w):
            grid[r][c] = rect_color
    r0, c0 = rect_r, rect_c
    r1, c1 = rect_r + rect_h - 1, rect_c + rect_w - 1
    inside = (
        (r0 + 1, c0 + 1),
        (r0 + 1, c1 - 1),
        (r1 - 1, c1 - 1),
        (r1 - 1, c0 + 1),
    )
    for (r, c), value in zip(inside, markers):
        grid[r][c] = value
    _geometry(grid)
    return grid


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int,
    queries: int,
) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    selected = _settings(settings)
    _exact_int(demos, "demos", *DEMO_LIMITS)
    _exact_int(queries, "queries", *QUERY_LIMITS)

    train = []
    for index in range(demos):
        grid = _sample_input(seed, "demo", index)
        train.append({"input": grid, "output": transform(grid, selected)})
    test = []
    for index in range(queries):
        grid = _sample_input(seed, "query", index)
        test.append({"input": grid, "output": transform(grid, selected)})
    return {"train": train, "test": test, "program_solution": program(selected)}
