"""Matched-input minimum/maximum room-extreme episodes for 953db766893d.

Python outputs are authoring claims until the protected Racket qualification
worker executes the exact selected program.  Scene sampling is independent of
the private setting and of the requested episode prefix length.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "953db766893d"
SETTINGS = ({"extreme": "minimum"}, {"extreme": "maximum"})
_WALL_COLORS = (1, 2, 5, 6, 7, 8, 9)

# Each profile is (room-row heights, room-column widths, opened separators).
# The first demo is deliberately intact and unequal: large rooms need not be
# merged rooms.  The second retains absolute areas 10 and 20 from demo zero,
# but changes which is extreme, defeating a fixed-area shortcut in two demos.
_DEMOS = (
    ((2, 2, 4), (3, 3, 5), 0),       # 10 x 13, intact
    ((2, 2, 4), (5, 5, 7), 1),       # 10 x 19, one max-expanding door
    ((2, 2, 3, 5), (2, 2, 4, 6), 2), # 15 x 17
    ((3, 3, 5, 6), (2, 2, 4, 5), 3), # 20 x 16
    ((2, 2, 4, 6, 7), (3, 3, 5, 6), 4), # 25 x 20
    ((3, 3, 4, 6, 8), (2, 2, 4, 6, 7), 5), # 28 x 25
)
_QUERIES = (
    ((2, 2, 5), (4, 4, 6), 1),          # 11 x 16
    ((2, 2, 4, 6), (3, 3, 5, 7), 3),    # 17 x 21
    ((2, 2, 4, 5, 7), (3, 3, 5, 5, 7), 5), # 24 x 27
    ((3, 3, 5, 7, 8), (3, 3, 5, 7, 8), 7), # exact 30 x 30
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"extreme"}
        or type(settings["extreme"]) is not str
        or settings["extreme"] not in ("minimum", "maximum")
    ):
        raise ValueError(
            "settings must be exactly {'extreme': 'minimum'|'maximum'}"
        )
    return settings["extreme"]


def program(settings):
    extreme = _setting(settings)
    return (HERE / ("canonical.rkt" if extreme == "minimum" else "maximum.rkt")).read_text()


def _rng(seed, split, index):
    raw = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _ranges(lengths):
    ranges = []
    separators = []
    cursor = 0
    for index, length in enumerate(lengths):
        ranges.append((cursor, cursor + length))
        cursor += length
        if index + 1 < len(lengths):
            separators.append(cursor)
            cursor += 1
    return ranges, separators, cursor


def _adjacency_edges(row_count, col_count):
    edges = []
    for room_row in range(row_count):
        for left_col in range(col_count - 1):
            edges.append(("vertical", room_row, left_col))
    for upper_row in range(row_count - 1):
        for room_col in range(col_count):
            edges.append(("horizontal", upper_row, room_col))
    return edges


def _endpoints(edge):
    orientation, first, second = edge
    if orientation == "vertical":
        return (first, second), (first, second + 1)
    return (first, second), (first + 1, second)


def _choose_openings(row_heights, col_widths, count, rng):
    if count == 0:
        return []
    areas = {
        (room_row, room_col): row_height * col_width
        for room_row, row_height in enumerate(row_heights)
        for room_col, col_width in enumerate(col_widths)
    }
    minimum = min(areas.values())
    minimum_cells = {cell for cell, area in areas.items() if area == minimum}
    edges = _adjacency_edges(len(row_heights), len(col_widths))

    parent = {cell: cell for cell in areas}

    def find(cell):
        while parent[cell] != cell:
            parent[cell] = parent[parent[cell]]
            cell = parent[cell]
        return cell

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root == right_root:
            return False
        parent[right_root] = left_root
        return True

    selected = []
    touched_minimum = set()

    # The first opening joins the unique largest base room to its largest
    # adjacent non-minimum room.  The resulting component is strictly larger
    # than every intact room, while at least one repeated intermediate area
    # remains available for cross-demo role reversal.
    largest = max(areas, key=lambda cell: (areas[cell], cell))
    incident = []
    for edge in edges:
        left, right = _endpoints(edge)
        if largest not in (left, right):
            continue
        other = right if left == largest else left
        if areas[other] > minimum:
            incident.append((areas[other], rng.random(), edge))
    if not incident:
        raise ValueError("profile has no lawful max-expanding opening")
    first = max(incident)[2]
    left, right = _endpoints(first)
    union(left, right)
    selected.append(first)
    touched_minimum |= {cell for cell in (left, right) if cell in minimum_cells}

    candidates = [edge for edge in edges if edge != first]
    rng.shuffle(candidates)
    candidates.sort(
        key=lambda edge: (
            sum(cell in minimum_cells for cell in _endpoints(edge)),
            -sum(areas[cell] for cell in _endpoints(edge)),
        )
    )
    for edge in candidates:
        if len(selected) == count:
            break
        left, right = _endpoints(edge)
        proposed_touched = touched_minimum | {
            cell for cell in (left, right) if cell in minimum_cells
        }
        if len(minimum_cells - proposed_touched) < 2:
            continue
        if not union(left, right):
            continue
        selected.append(edge)
        touched_minimum = proposed_touched
    if len(selected) != count:
        raise ValueError(f"profile supports only {len(selected)} of {count} requested openings")
    return selected


def _door_position(start, end, outer_limit, rng):
    candidates = [position for position in range(start, end) if 0 < position < outer_limit - 1]
    if not candidates:
        raise ValueError("room span cannot host an interior separator opening")
    center = (start + end - 1) / 2
    return min(candidates, key=lambda position: (abs(position - center), rng.random()))


def _build_lattice(row_heights, col_widths, openings, wall_color, rng):
    row_ranges, row_separators, height = _ranges(row_heights)
    col_ranges, col_separators, width = _ranges(col_widths)
    grid = [[0] * width for _ in range(height)]
    for row in row_separators:
        for col in range(width):
            grid[row][col] = wall_color
    for col in col_separators:
        for row in range(height):
            grid[row][col] = wall_color

    door_cells = []
    for orientation, first, second in openings:
        if orientation == "vertical":
            row_start, row_end = row_ranges[first]
            row = _door_position(row_start, row_end, height, rng)
            col = col_separators[second]
        else:
            col_start, col_end = col_ranges[second]
            row = row_separators[first]
            col = _door_position(col_start, col_end, width, rng)
        grid[row][col] = 0
        door_cells.append((row, col))
    return grid, door_cells


def _components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 0}
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _validate_scene(grid, expected_openings):
    components = _components(grid)
    sizes = [len(component) for component in components]
    if len(components) < 3:
        raise ValueError("scene needs at least three zero components")
    if sizes.count(min(sizes)) < 2:
        raise ValueError("scene needs at least two tied minimum rooms")
    if len(set(sizes)) < 3:
        raise ValueError("scene needs at least three room sizes")
    if claimed_output(grid, SETTINGS[0]) == claimed_output(grid, SETTINGS[1]):
        raise ValueError("scene failed to distinguish minimum and maximum settings")
    if expected_openings and all(
        not (
            0 < row < len(grid) - 1
            and 0 < col < len(grid[0]) - 1
            and grid[row][col] == 0
        )
        for row, col in expected_openings
    ):
        raise ValueError("scene lost every requested separator opening")


def sample_input(seed, index, *, split):
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    profiles = _DEMOS if split == "train" else _QUERIES
    _integer(index, 0, len(profiles) - 1, "index")
    row_template, col_template, opening_count = profiles[index]
    rng = _rng(seed, split, index)
    row_heights = list(row_template)
    col_widths = list(col_template)
    rng.shuffle(row_heights)
    rng.shuffle(col_widths)
    openings = _choose_openings(row_heights, col_widths, opening_count, rng)
    grid, door_cells = _build_lattice(
        row_heights, col_widths, openings, rng.choice(_WALL_COLORS), rng
    )
    _validate_scene(grid, door_cells)
    return grid


def claimed_output(grid, settings):
    extreme = _setting(settings)
    components = _components(grid)
    if not components:
        raise ValueError("scene needs at least one zero component")
    sizes = [len(component) for component in components]
    selected = min(sizes) if extreme == "minimum" else max(sizes)
    output = deepcopy(grid)
    for component in components:
        color = 3 if len(component) == selected else 4
        for row, col in component:
            output[row][col] = color
    return output


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, index, split=split)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate input at {split}[{index}]")
            seen.add(key)
            result[split].append({"input": grid, "output": claimed_output(grid, settings)})
    result["sampling"] = {"draws": demos + queries, "duplicate_rejections": 0}
    return result
