"""Native parametric family for 1ec277b81469.

``canonical`` is the exact selected row-right-packing program.
``fill_largest_bbox`` performs that packing as Step A, then finds the unique
largest same-color four-connected component in the packed intermediate and
fills its bounding box with color 9 as Step B.

Inputs are shared across settings.  The sampler constructs a variable connected
component only after right-packing: its same-color pieces are scattered in the
source, while near-tie and singleton decoys defeat color, first-object, fixed-box,
and whole-component shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "1ec277b81469"
HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"finish": "canonical"},
    {"finish": "fill_largest_bbox"},
)
DEMO_SHAPES = ((8, 13), (10, 17), (12, 21), (15, 24), (18, 27), (21, 29))
QUERY_SHAPES = ((7, 11), (19, 13), (14, 25), (30, 30))


def _integer(value, label, low=None, high=None):
    if type(value) is not int:
        raise ValueError(f"{label} must be an exact integer")
    if (low is not None and value < low) or (high is not None and value > high):
        raise ValueError(f"{label} must be in {low}..{high}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    value = settings["finish"]
    if type(value) is not str or value not in {row["finish"] for row in SETTINGS}:
        raise ValueError("finish must be canonical or fill_largest_bbox")
    return value


def _grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return deepcopy(grid)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def program(settings):
    name = "canonical.rkt" if _setting(settings) == "canonical" else "sequential.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _right_pack(grid):
    source = _grid(grid)
    width = len(source[0])
    output = []
    for row in source:
        values = [value for value in row if value != 0]
        output.append([0] * (width - len(values)) + values)
    return output


def _components(grid):
    source = _grid(grid)
    height, width = len(source), len(source[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            color = source[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and source[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def _largest_component(grid, *, require_unique=True):
    components = _components(grid)
    if not components:
        raise ValueError("grid must contain at least one nonzero component")
    maximum = max(len(component["cells"]) for component in components)
    largest = [component for component in components if len(component["cells"]) == maximum]
    if require_unique and len(largest) != 1:
        raise ValueError("largest component must be unique")
    return largest[0], components


def _bbox(component):
    rows = [row for row, _ in component["cells"]]
    cols = [col for _, col in component["cells"]]
    return min(rows), min(cols), max(rows), max(cols)


def _fill_largest_bbox(grid, *, require_unique=True):
    source = _grid(grid)
    largest, _ = _largest_component(source, require_unique=require_unique)
    r1, c1, r2, c2 = _bbox(largest)
    output = deepcopy(source)
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            output[row][col] = 9
    return output


def stage_summary(grid):
    source = _grid(grid)
    source_largest, source_components = _largest_component(source, require_unique=False)
    intermediate = _right_pack(source)
    largest, components = _largest_component(intermediate)
    r1, c1, r2, c2 = _bbox(largest)
    sr1, sc1, sr2, sc2 = _bbox(source_largest)
    return {
        "intermediate": intermediate,
        "component_count": len(components),
        "largest_size": len(largest["cells"]),
        "largest_color": largest["color"],
        "largest_anchor": [r1, c1],
        "largest_bbox": [r1, c1, r2, c2],
        "source_component_count": len(source_components),
        "source_largest_size": len(source_largest["cells"]),
        "source_largest_bbox": [sr1, sc1, sr2, sc2],
        "skip_a_output": _fill_largest_bbox(source, require_unique=False),
    }


def transform(grid, settings):
    mode = _setting(settings)
    intermediate = _right_pack(grid)
    if mode == "canonical":
        return intermediate
    return _fill_largest_bbox(intermediate)


def _rng(seed, stream, index, height, width, attempt=0):
    payload = json.dumps(
        [seed, stream, index, height, width, attempt], separators=(",", ":")
    ).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _target_height(height, index, rng):
    maximum = min(13, height - 2)
    choices = list(range(5, maximum + 1, 2))
    if not choices:
        raise ValueError("shape must leave two rows outside a five-row target")
    return choices[(index + rng.randrange(len(choices))) % len(choices)]


def _target_span(height, width, index, rng):
    area = height * width
    if area >= 700:
        low, high = 16, min(width - 1, 21)
    elif width >= 24:
        low, high = 10, min(width - 1, 15)
    elif width >= 16:
        low, high = 7, min(width - 1, 11)
    else:
        low, high = 6, min(width - 1, 8)
    return low + ((index + rng.randrange(high - low + 1)) % (high - low + 1))


def _target_cells(top, target_height, left, phase, *, extra):
    """Return a narrow connected component with a four-column holed bbox."""
    starts = (0, 1, 2, 1)
    cells = set()
    row_starts = {}
    for offset in range(target_height):
        start = starts[(phase + offset) % len(starts)]
        row = top + offset
        row_starts[row] = start
        cells.add((row, left + start))
        cells.add((row, left + start + 1))
    if extra:
        row = next(row for row, start in row_starts.items() if start == 0)
        cells.add((row, left + 2))
    return cells


def _spread_positions(rng, width, count, row, index):
    if not 1 <= count <= width - 1:
        raise ValueError("row sequence must fit before the right edge")
    forced = []
    if (row + index) % 3 == 0:
        forced.append(0)
    if count > len(forced) and (row + index) % 4 == 0:
        forced.append(width - 2)
    forced = list(dict.fromkeys(forced))[:count]
    remaining = [col for col in range(width - 1) if col not in forced]
    chosen = forced + rng.sample(remaining, count - len(forced))
    return sorted(chosen)


def _components_8(grid):
    source = _grid(grid)
    height, width = len(source), len(source[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            color = source[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = row + dr, col + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and (nr, nc) not in seen
                            and source[nr][nc] == color
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def _fill_component_bbox(grid, component):
    output = _grid(grid)
    r1, c1, r2, c2 = _bbox(component)
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            output[row][col] = 9
    return output


def _bbox_metrics(component):
    r1, c1, r2, c2 = _bbox(component)
    height = r2 - r1 + 1
    width = c2 - c1 + 1
    return {"height": height, "width": width, "area": height * width}


def _build_candidate(seed, stream, index, height, width, attempt):
    rng = _rng(seed, stream, index, height, width, attempt)
    profile = "frequency_connectivity" if index % 2 == 0 else "rank_geometry"
    target_height = _target_height(height, index, rng)
    span = _target_span(height, width, index, rng)
    if profile == "frequency_connectivity":
        # The first promised lesson always leaves a lower distractor row, so
        # "choose the bottommost object" cannot stand in for the size rule.
        top = rng.randrange(0, height - target_height)
    else:
        top = rng.randrange(0, height - target_height + 1)
    bottom = top + target_height - 1

    colors = list(range(1, 9))
    rng.shuffle(colors)
    target_color, challenge_color = colors[:2]
    fillers = colors[2:]
    salt = rng.randrange(10_000)
    packed = [
        [fillers[(row * 2 + col * 3 + salt) % len(fillers)] for col in range(span)]
        for row in range(height)
    ]

    outside_rows = [row for row in range(height) if not top <= row <= bottom]
    if len(outside_rows) < 2:
        raise ValueError("target must leave two outside rows")

    if profile == "rank_geometry":
        target_left = 1
        target_cells = _target_cells(
            top, target_height, target_left, rng.randrange(4), extra=True
        )
        adjacent = []
        if top > 0:
            adjacent.append(top - 1)
        if bottom + 1 < height:
            adjacent.append(bottom + 1)
        challenge_row = rng.choice(adjacent)
        vertical_rows = range(min(challenge_row, top), max(challenge_row, bottom) + 1)
        challenge_cells = {(row, 0) for row in vertical_rows}
        challenge_cells.update((challenge_row, col) for col in range(5))
        singleton_row = rng.choice([row for row in outside_rows if row != challenge_row])
        singleton = (singleton_row, 0)
        for row, col in challenge_cells:
            packed[row][col] = challenge_color
    else:
        target_left = rng.randrange(0, span - 3)
        target_cells = _target_cells(
            top, target_height, target_left, rng.randrange(4), extra=False
        )
        available = {}
        for parity in (0, 1):
            available[parity] = [
                (row, col)
                for row in range(height)
                for col in range(span)
                if (row + col) % 2 == parity and (row, col) not in target_cells
            ]
        parity = max(available, key=lambda value: (len(available[value]), -value))
        challenge_cells = set(available[parity])
        for row, col in challenge_cells:
            packed[row][col] = challenge_color
        singleton_options = [
            (row, col)
            for row in outside_rows
            for col in range(span)
            if not target_left <= col <= target_left + 3
            and (row + col) % 2 != parity
        ]
        if not singleton_options:
            raise ValueError("no isolated target-color singleton location")
        singleton = rng.choice(singleton_options)

    for row, col in target_cells:
        packed[row][col] = target_color
    packed[singleton[0]][singleton[1]] = target_color

    grid = [[0] * width for _ in range(height)]
    for row, sequence in enumerate(packed):
        positions = _spread_positions(rng, width, span, row, index)
        for col, value in zip(positions, sequence):
            grid[row][col] = value

    packed_start = width - span
    expected_bbox = [
        top,
        packed_start + target_left,
        bottom,
        packed_start + target_left + 3,
    ]
    return grid, target_color, len(target_cells), expected_bbox, profile

def sample_input(seed, stream, index, height, width):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    _integer(height, "height", 7, 30)
    _integer(width, "width", 11, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be nonempty text")

    last_error = None
    for attempt in range(64):
        grid, target_color, target_size, expected_bbox, profile = _build_candidate(
            seed, stream, index, height, width, attempt
        )
        try:
            summary = stage_summary(grid)
            final = transform(grid, {"finish": "fill_largest_bbox"})
            bbox = summary["largest_bbox"]
            bbox_area = (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1)
            if summary["largest_color"] != target_color:
                raise ValueError("wrong largest color after Step A")
            if summary["largest_size"] != target_size:
                raise ValueError("wrong largest size after Step A")
            if bbox != expected_bbox:
                raise ValueError("wrong largest bounding box after Step A")
            if summary["source_largest_size"] >= target_size:
                raise ValueError("target was not created as a strictly larger Step-A component")
            if bbox_area <= target_size:
                raise ValueError("Step-B box has no holes or competing cells")
            if summary["skip_a_output"] == final:
                raise ValueError("Step-A ablation did not change the final output")
            if summary["intermediate"] == final:
                raise ValueError("Step B did not change the intermediate")
            if summary["component_count"] < 3:
                raise ValueError("scene lacks component distractors")

            intermediate = summary["intermediate"]
            components = _components(intermediate)
            target_component = next(
                component
                for component in components
                if component["color"] == target_color
                and len(component["cells"]) == target_size
            )
            target_metrics = _bbox_metrics(target_component)
            all_target_cells = {
                "color": target_color,
                "cells": tuple(
                    (row, col)
                    for row, values in enumerate(intermediate)
                    for col, value in enumerate(values)
                    if value == target_color
                ),
            }
            if _bbox(all_target_cells) == _bbox(target_component):
                raise ValueError("target-color decoy does not change the all-color bbox")
            if _fill_component_bbox(intermediate, all_target_cells) == final:
                raise ValueError("all-cells-of-largest-color shortcut survives")

            if profile == "frequency_connectivity":
                frequencies = {
                    color: sum(value == color for row in intermediate for value in row)
                    for color in range(1, 9)
                }
                modal_color = max(frequencies, key=lambda color: (frequencies[color], -color))
                if modal_color == target_color:
                    raise ValueError("target remains the most frequent color")
                modal_component = max(
                    (component for component in components if component["color"] == modal_color),
                    key=lambda component: len(component["cells"]),
                )
                if _fill_component_bbox(intermediate, modal_component) == final:
                    raise ValueError("most-frequent-color shortcut survives")
                largest_8 = max(_components_8(intermediate), key=lambda component: len(component["cells"]))
                if largest_8["color"] == target_color or len(largest_8["cells"]) <= target_size:
                    raise ValueError("8-connected decoy is not larger than the target")
                if _fill_component_bbox(intermediate, largest_8) == final:
                    raise ValueError("8-connected shortcut survives")
            else:
                rivals = [component for component in components if component is not target_component]
                for metric in ("area", "height", "width"):
                    selected = max(
                        components,
                        key=lambda component: (
                            _bbox_metrics(component)[metric],
                            len(component["cells"]),
                        ),
                    )
                    if selected is target_component:
                        raise ValueError(f"largest-bbox-{metric} shortcut survives")
                    if _bbox_metrics(selected)[metric] <= target_metrics[metric]:
                        raise ValueError(f"rank decoy does not exceed target {metric}")
                    if len(selected["cells"]) >= target_size:
                        raise ValueError("rank decoy is not smaller than the target")
                    if _fill_component_bbox(intermediate, selected) == final:
                        raise ValueError(f"largest-bbox-{metric} output matches target")
            return grid
        except ValueError as error:
            last_error = error
    raise ValueError(f"sampler failed after bounded retries: {last_error}")


def generate(seed, settings, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": dict(settings),
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "prototype": True,
    }
    seen = set()
    for split, shapes in (("train", DEMO_SHAPES[:demos]), ("test", QUERY_SHAPES[:queries])):
        for index, (height, width) in enumerate(shapes):
            grid = sample_input(seed, split, index, height, width)
            key = digest(grid)
            if key in seen:
                raise ValueError("episode inputs must be distinct")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result
