"""Parametric family for e06cc4c752b2.

The default setting is the selected singleton-to-horizontal-bar rule byte for
byte.  The sequential setting first performs that expansion, then selects the
largest same-color 4-connected component created by the expanded staircase and
fills its bounding box with color 9.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "e06cc4c752b2"
HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"finish": "canonical"},
    {"finish": "fill_largest_bbox"},
)
DEMO_SHAPES = ((9, 13), (11, 17), (13, 15), (16, 20), (19, 17), (22, 26))
QUERY_SHAPES = ((8, 14), (15, 21), (24, 29), (30, 30))


def _integer(value, label, low=None, high=None):
    if type(value) is not int:
        raise ValueError(f"{label} must be an exact integer")
    if low is not None and value < low:
        raise ValueError(f"{label} must be at least {low}")
    if high is not None and value > high:
        raise ValueError(f"{label} must be at most {high}")
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
    if not 3 <= height <= 30 or not 5 <= width <= 30:
        raise ValueError("grid dimensions must be height 3..30 and width 5..30")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    for row in grid:
        for cell in row:
            if type(cell) is not int:
                raise ValueError("grid cells must be exact integer colors")
            if not 0 <= cell <= 9:
                raise ValueError("grid colors must be in 0..9")
            if cell == 9:
                raise ValueError("input color 9 is reserved for stage B")
    markers = [(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0]
    if not markers:
        raise ValueError("grid must contain at least one marker")
    for r, c in markers:
        if c in (0, width - 1):
            raise ValueError("markers must have in-bounds horizontal arms")
        if any(
            0 <= nr < height and 0 <= nc < width and grid[nr][nc] != 0
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        ):
            raise ValueError("every input marker must be cardinally isolated")
    return deepcopy(grid)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def program(settings):
    name = "canonical.rkt" if _setting(settings) == "canonical" else "sequential.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _canonical_expand(grid):
    source = _grid(grid)
    output = deepcopy(source)
    height, width = len(source), len(source[0])
    for r in range(height):
        for c in range(width):
            value = source[r][c]
            if value == 0:
                continue
            isolated = all(
                not (0 <= nr < height and 0 <= nc < width and source[nr][nc] != 0)
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            )
            if not isolated:
                continue
            if c - 1 >= 0 and output[r][c - 1] == 0:
                output[r][c - 1] = value
            if c + 1 < width and output[r][c + 1] == 0:
                output[r][c + 1] = value
    return output


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            result.append({"color": color, "cells": cells})
    return result


def stage_summary(grid):
    source = _grid(grid)
    intermediate = _canonical_expand(source)
    components = _components(intermediate)
    if not components:
        raise ValueError("expanded grid must contain a nonzero component")
    largest = max(components, key=lambda item: len(item["cells"]))
    rows = [r for r, _ in largest["cells"]]
    cols = [c for _, c in largest["cells"]]
    bbox = [min(rows), min(cols), max(rows), max(cols)]
    return {
        "intermediate": intermediate,
        "component_count": len(components),
        "largest_size": len(largest["cells"]),
        "largest_color": largest["color"],
        "largest_anchor": list(min(largest["cells"])),
        "largest_bbox": bbox,
    }


def transform(grid, settings):
    mode = _setting(settings)
    source = _grid(grid)
    intermediate = _canonical_expand(source)
    if mode == "canonical":
        return intermediate
    result = deepcopy(intermediate)
    r1, c1, r2, c2 = stage_summary(source)["largest_bbox"]
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            result[r][c] = 9
    return result


def _rng(seed, stream, index):
    payload = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _expanded(centers):
    return {(r, c + dc) for r, c in centers for dc in (-1, 0, 1)}


def _groups_separate(candidate, occupied):
    cells = _expanded(candidate)
    return all(
        abs(r - rr) + abs(c - cc) > 1
        for r, c in cells
        for rr, cc in occupied
    )


def _original_isolated(candidate, centers):
    all_centers = list(centers) + list(candidate)
    return all(
        (a == b) or abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1
        for i, a in enumerate(all_centers)
        for b in all_centers[i + 1:]
    )


def _chain_candidates(height, width, length):
    rows = range(1, height - length)
    for direction in (1, -1):
        if direction == 1:
            starts = range(2, width - 2 * (length - 1) - 2)
        else:
            starts = range(2 * (length - 1) + 2, width - 2)
        for r0 in rows:
            for c0 in starts:
                yield [(r0 + step, c0 + direction * 2 * step) for step in range(length)]


def _choose_target(rng, height, width, length):
    candidates = list(_chain_candidates(height, width, length))
    if not candidates:
        raise ValueError(f"shape {height}x{width} cannot fit target chain length {length}")
    rng.shuffle(candidates)
    return candidates[0]


def _add_group(groups, centers, occupied, candidate, color, forbidden_bbox):
    if not _original_isolated(candidate, centers):
        return False
    cells = _expanded(candidate)
    r1, c1, r2, c2 = forbidden_bbox
    if any(r1 <= r <= r2 and c1 <= c <= c2 for r, c in cells):
        return False
    if not _groups_separate(candidate, occupied):
        return False
    groups.append((candidate, color))
    centers.extend(candidate)
    occupied.update(cells)
    return True


def sample_input(seed, stream, index, height, width):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    _integer(height, "height", 8, 30)
    _integer(width, "width", 13, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be nonempty text")
    rng = _rng(seed, stream, index)
    desired = 7 if (height, width) == (30, 30) else 3 + (index % 4)
    max_fit = min(height - 2, max(3, (width - 5) // 2 + 1))
    target_length = max(3, min(desired, max_fit))
    target = _choose_target(rng, height, width, target_length)
    target_color = rng.randrange(1, 9)
    groups = [(target, target_color)]
    centers = list(target)
    occupied = _expanded(target)
    target_cells = _expanded(target)
    forbidden_bbox = (
        min(r for r, _ in target_cells), min(c for _, c in target_cells),
        max(r for r, _ in target_cells), max(c for _, c in target_cells),
    )

    colors = [value for value in range(1, 9) if value != target_color]
    rng.shuffle(colors)
    secondary_count = 2 if height * width >= 300 else 1
    chain2 = list(_chain_candidates(height, width, 2))
    rng.shuffle(chain2)
    for group_index in range(secondary_count):
        for candidate in chain2:
            if _add_group(groups, centers, occupied, candidate, colors[group_index], forbidden_bbox):
                break

    singleton_target = min(10, max(2, height * width // 95))
    singles = [(r, c) for r in range(height) for c in range(1, width - 1)]
    rng.shuffle(singles)
    added = 0
    for candidate in singles:
        if _add_group(
            groups, centers, occupied, [candidate],
            colors[(secondary_count + added) % len(colors)], forbidden_bbox,
        ):
            added += 1
            if added >= singleton_target:
                break

    grid = [[0] * width for _ in range(height)]
    for group, color in groups:
        for r, c in group:
            grid[r][c] = color
    _grid(grid)
    summary = stage_summary(grid)
    if summary["largest_size"] != 3 * target_length:
        raise RuntimeError("target staircase was not the unique largest expanded component")
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
