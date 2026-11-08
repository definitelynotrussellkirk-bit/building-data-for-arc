"""Native parametric family for 85305305afdf.

``canonical`` is the exact selected ARC rule.  ``fill_largest_bbox`` first
executes that right-shift rule, then discovers the largest same-color component
in the resulting grid and fills its input-dependent bounding box with color 9.
The sampler constructs a teaching motif whose largest intermediate component is
created by Step A from many disconnected input pieces, so Step B cannot be
selected correctly from the original grid.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "85305305afdf"
HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"finish": "canonical"},
    {"finish": "fill_largest_bbox"},
)
DEMO_SHAPES = ((9, 13), (11, 17), (13, 19), (15, 21), (17, 25), (19, 27))
QUERY_SHAPES = ((7, 11), (16, 20), (23, 29), (30, 30))


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


def _intermediate(grid):
    source = _grid(grid)
    height, width = len(source), len(source[0])
    out = [[0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            value = source[row][col]
            if value == 0:
                continue
            if col + 1 < width and source[row][col + 1] == 0:
                if out[row][col + 1] == 0:
                    out[row][col + 1] = value
            elif out[row][col] == 0:
                out[row][col] = value
    return out


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
    out = deepcopy(source)
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            out[row][col] = 9
    return out


def stage_summary(grid):
    source = _grid(grid)
    intermediate = _intermediate(source)
    largest, components = _largest_component(intermediate)
    r1, c1, r2, c2 = _bbox(largest)
    return {
        "intermediate": intermediate,
        "component_count": len(components),
        "largest_size": len(largest["cells"]),
        "largest_color": largest["color"],
        "largest_anchor": [r1, c1],
        "largest_bbox": [r1, c1, r2, c2],
        "skip_a_output": _fill_largest_bbox(source, require_unique=False),
    }


def transform(grid, settings):
    mode = _setting(settings)
    intermediate = _intermediate(grid)
    if mode == "canonical":
        return intermediate
    return _fill_largest_bbox(intermediate)


def _rng(seed, stream, index, height, width):
    payload = json.dumps([seed, stream, index, height, width], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _target_geometry(rng, height, width, index):
    max_height = max(5, min(height, 21))
    choices = [value for value in range(5, max_height + 1) if value % 2 == 1]
    if height >= 25:
        target_height = choices[-1]
    elif height >= 20:
        target_height = choices[-min(2, len(choices))]
    else:
        target_height = choices[(index + rng.randrange(len(choices))) % len(choices)]
    top = rng.randrange(0, height - target_height + 1)
    left = rng.randrange(0, width - 4)
    return top, left, target_height


def sample_input(seed, stream, index, height, width):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    _integer(height, "height", 7, 30)
    _integer(width, "width", 9, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be nonempty text")
    rng = _rng(seed, stream, index, height, width)
    grid = [[0] * width for _ in range(height)]
    target_color = (2, 3, 4, 5, 6, 7)[rng.randrange(6)]
    top, left, target_height = _target_geometry(rng, height, width, index)

    # Step A merges alternating disconnected pieces into a unique vertical,
    # hole-bearing component.  Even rows are isolated movers; odd rows are
    # three-cell runs whose two-cell prefix stays and whose terminal detaches.
    reserved = set()
    for offset in range(target_height):
        row = top + offset
        if offset % 2 == 0:
            grid[row][left] = target_color
            reserved.update({(row, left), (row, left + 1)})
        else:
            grid[row][left + 1] = target_color
            grid[row][left + 2] = target_color
            grid[row][left + 3] = target_color
            reserved.update((row, col) for col in range(left + 1, left + 5))

    distractor_colors = [color for color in range(1, 9) if color != target_color]
    # Dense but bounded short-run distractors provide geometry/color spread and
    # substantive large-canvas stress without challenging the unique target.
    for row in range(height):
        segment = 0
        for start in range(0, width - 3, 5):
            footprint = range(start, start + 4)
            if any((row, col) in reserved or grid[row][col] != 0 for col in footprint):
                segment += 1
                continue
            # Keep some zero structure on small scenes; fill more of large ones.
            draw = (row * 17 + segment * 11 + index + seed) % 5
            if draw == 0 and height * width < 400:
                segment += 1
                continue
            length = 2 + ((row + segment + index) % 2)
            color = distractor_colors[(row * 3 + segment * 5 + index) % len(distractor_colors)]
            for col in range(start, start + length):
                grid[row][col] = color
            segment += 1

    summary = stage_summary(grid)
    expected_size = target_height + target_height // 2
    if summary["largest_color"] != target_color or summary["largest_size"] != expected_size:
        raise ValueError("sampler failed to create its unique Step-A component")
    if summary["skip_a_output"] == transform(grid, {"finish": "fill_largest_bbox"}):
        raise ValueError("Step-A ablation did not change the final output")
    return grid


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
