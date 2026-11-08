"""Native parametric adapter for e282a664f807.

``single_box`` is the exact canonical rule. ``largest_completed`` first
completes every two-cell color into its rectangle, then recolors the unique
largest completed rectangle to 9.  Before completion every candidate has the
same raw count, so the second selection genuinely consumes the completed
intermediate.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import hashlib
from itertools import permutations
from pathlib import Path
import random
from typing import Any, Iterable

_HOME = Path(__file__).resolve().parent
_PROGRAMS = {
    "single_box": _HOME / "canonical.rkt",
    "largest_completed": _HOME / "largest_completed.rkt",
}

_DEMO_SPECS = (
    (8, 10, "compact"),
    (9, 12, "negative"),
    (10, 14, "wide"),
    (12, 16, "shifted"),
    (14, 18, "dense"),
    (16, 20, "boundary"),
)
_QUERY_SPECS = (
    (9, 11, "transfer"),
    (15, 17, "boundary"),
    (22, 24, "dense"),
    (30, 30, "stress"),
)
_COLOR_TRIPLES = ((1, 3, 6), (2, 4, 7), (1, 5, 8), (2, 5, 6), (3, 4, 8))
_SIZE_PERMUTATIONS = tuple(permutations((0, 1, 2)))

Grid = list[list[int]]


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _policy(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {"completion_policy"}:
        raise ValueError("settings must contain exactly completion_policy")
    value = settings["completion_policy"]
    if type(value) is not str or value not in _PROGRAMS:
        raise ValueError("completion_policy must be single_box or largest_completed")
    return value


def program(settings: Any) -> str:
    return _PROGRAMS[_policy(settings)].read_text(encoding="utf-8")


def _mix_seed(seed: int, role: str, index: int) -> int:
    raw = f"e282a664f807|{seed}|{role}|{index}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _scan_colors(grid: Grid) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for row in grid:
        for value in row:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
    return result


def _positions(grid: Grid, color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _pair_colors(grid: Grid) -> list[int]:
    counts = Counter(value for row in grid for value in row if value)
    return [color for color in _scan_colors(grid) if counts[color] == 2]


def _fill_bbox(output: Grid, points: list[tuple[int, int]], color: int) -> None:
    if len(points) != 2:
        raise ValueError("a completed color must have exactly two source cells")
    rows = sorted((points[0][0], points[1][0]))
    cols = sorted((points[0][1], points[1][1]))
    if rows[0] == rows[1] or cols[0] == cols[1]:
        raise ValueError("rectangle corners must differ in row and column")
    for r in range(rows[0], rows[1] + 1):
        for c in range(cols[0], cols[1] + 1):
            output[r][c] = color


def intermediate(grid: Grid) -> Grid:
    """Complete every two-cell color into its rectangle on a blank grid."""
    output = [[0 for _ in row] for row in grid]
    colors = _pair_colors(grid)
    if not colors:
        raise ValueError("input has no two-cell color")
    for color in colors:
        _fill_bbox(output, _positions(grid, color), color)
    return output


def completed_areas(stage: Grid) -> list[tuple[int, int]]:
    colors = _scan_colors(stage)
    return [(color, sum(value == color for row in stage for value in row)) for color in colors]


def predict(grid: Grid, completion_policy: str) -> Grid:
    if completion_policy not in _PROGRAMS:
        raise ValueError("unknown completion policy")
    if completion_policy == "single_box":
        colors = _pair_colors(grid)
        if not colors:
            raise ValueError("input has no two-cell color")
        output = [[0 for _ in row] for row in grid]
        color = colors[0]
        _fill_bbox(output, _positions(grid, color), color)
        return output
    stage = intermediate(grid)
    areas = completed_areas(stage)
    peak = max(area for _, area in areas)
    winners = [color for color, area in areas if area == peak]
    if len(winners) != 1:
        raise ValueError("completed rectangles must have a unique largest area")
    selected = winners[0]
    return [[9 if value == selected else value for value in row] for row in stage]


def wrong_order_predict(grid: Grid) -> Grid:
    """Counterfactual: choose the numerically smallest raw pair before filling."""
    colors = _pair_colors(grid)
    if not colors:
        raise ValueError("input has no two-cell color")
    selected = min(colors)
    stage = intermediate(grid)
    return [[9 if value == selected else value for value in row] for row in stage]


def _place_pair(grid: Grid, rect: tuple[int, int, int, int], color: int, negative: bool) -> None:
    r1, c1, r2, c2 = rect
    points = ((r1, c2), (r2, c1)) if negative else ((r1, c1), (r2, c2))
    for r, c in points:
        if grid[r][c] != 0:
            raise RuntimeError("pair corner collision")
        grid[r][c] = color


def _size_classes(height: int, width: int) -> list[tuple[int, int]]:
    small = (max(2, height // 6), max(2, width // 6))
    medium = (
        max(small[0] + 1, height // 4),
        max(small[1] + 1, width // 4),
    )
    large = (
        max(medium[0] + 1, height // 2),
        max(medium[1] + 2, width // 2 + 1),
    )
    return [small, medium, large]


def _slot_rectangles(height: int, width: int, assigned: list[tuple[int, int]]) -> list[tuple[int, int, int, int]]:
    (h0, w0), (h1, w1), (h2, w2) = assigned
    slots = [
        (0, 0, h0 - 1, w0 - 1),
        (0, width - w1, h1 - 1, width - 1),
        (height - h2, (width - w2) // 2, height - 1, (width - w2) // 2 + w2 - 1),
    ]
    cells = []
    for rect in slots:
        r1, c1, r2, c2 = rect
        if not (0 <= r1 < r2 < height and 0 <= c1 < c2 < width):
            raise RuntimeError(f"invalid rectangle slot {rect!r}")
        current = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        if any(current & prior for prior in cells):
            raise RuntimeError("rectangle slots overlap")
        cells.append(current)
    return slots


def _add_distractors(grid: Grid, excluded: set[int], rng: random.Random) -> None:
    palette = [color for color in range(1, 9) if color not in excluded]
    free = [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] == 0]
    rng.shuffle(free)
    count_each = max(3, (len(grid) * len(grid[0])) // max(1, len(palette) * 8))
    needed = count_each * len(palette)
    if needed > len(free):
        count_each = max(3, len(free) // max(1, len(palette)))
    cursor = 0
    for color in palette:
        for r, c in free[cursor : cursor + count_each]:
            grid[r][c] = color
        cursor += count_each


def _build_single(seed: int, role: str, index: int, spec: tuple[int, int, str]) -> Grid:
    height, width, _profile = spec
    rng = random.Random(_mix_seed(seed, role, index))
    grid = [[0 for _ in range(width)] for _ in range(height)]
    target = (2, 3, 4, 5, 6, 7, 8)[(seed + index + (0 if role == "demo" else 3)) % 7]
    box_h = max(2, min(height - 1, 2 + ((seed + 2 * index) % max(2, height // 2))))
    box_w = max(2, min(width - 1, 2 + ((seed * 3 + index) % max(2, width // 2))))
    r1 = rng.randint(0, height - box_h)
    c1 = rng.randint(0, width - box_w)
    rect = (r1, c1, r1 + box_h - 1, c1 + box_w - 1)
    _place_pair(grid, rect, target, negative=(seed + index) % 2 == 1)
    _add_distractors(grid, {target}, rng)
    if _pair_colors(grid) != [target]:
        raise RuntimeError("single-box construction did not preserve a unique pair color")
    return grid


def _build_multiple(seed: int, role: str, index: int, spec: tuple[int, int, str]) -> Grid:
    height, width, _profile = spec
    rng = random.Random(_mix_seed(seed, role, index))
    grid = [[0 for _ in range(width)] for _ in range(height)]
    sizes = _size_classes(height, width)
    permutation = _SIZE_PERMUTATIONS[(seed + index + (0 if role == "demo" else 2)) % len(_SIZE_PERMUTATIONS)]
    assigned = [sizes[rank] for rank in permutation]
    rects = _slot_rectangles(height, width, assigned)
    triple = _COLOR_TRIPLES[(seed + index + (1 if role == "query" else 0)) % len(_COLOR_TRIPLES)]
    rank_to_color = {0: min(triple), 1: sorted(triple)[1], 2: max(triple)}
    colors = [rank_to_color[rank] for rank in permutation]
    for slot, (rect, color) in enumerate(zip(rects, colors)):
        _place_pair(grid, rect, color, negative=(seed + index + slot) % 2 == 1)
    _add_distractors(grid, set(colors), rng)
    if set(_pair_colors(grid)) != set(colors):
        raise RuntimeError("multi-box construction changed the pair-color set")
    areas = completed_areas(intermediate(grid))
    if len({area for _, area in areas}) != len(areas):
        raise RuntimeError("completed rectangle areas are not unique")
    if max(areas, key=lambda item: item[1])[0] == min(colors):
        raise RuntimeError("wrong-order selector accidentally matches the largest rectangle")
    return grid


def _pair(grid: Grid, policy: str) -> dict[str, Grid]:
    return {"input": deepcopy(grid), "output": predict(grid, policy)}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    policy = _policy(settings)
    builder = _build_single if policy == "single_box" else _build_multiple
    demo_inputs = [builder(seed, "demo", index, spec) for index, spec in enumerate(_DEMO_SPECS[:demos])]
    query_bank = [builder(seed, "query", index, spec) for index, spec in enumerate(_QUERY_SPECS)]
    selected_queries = query_bank[:queries]
    all_inputs = demo_inputs + selected_queries
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise RuntimeError("episode inputs must be distinct")
    return {
        "train": [_pair(grid, policy) for grid in demo_inputs],
        "test": [_pair(grid, policy) for grid in selected_queries],
        "program_solution": program(settings),
    }
