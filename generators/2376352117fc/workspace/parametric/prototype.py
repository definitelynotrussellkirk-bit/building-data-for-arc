"""Matched-input vector-direction episodes for 2376352117fc.

The canonical setting translates every green cell by the blue-to-red marker
vector.  The alternate setting uses the reverse marker vector.  Both rules
paint only in-bounds translated cells cyan on a fresh zero grid.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "2376352117fc"
HERE = Path(__file__).resolve().parent
SETTING_NAMES = ("blue_to_red", "red_to_blue")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Dimensions, shape box, size, marker vector and placement requirement.  The
# first two are constructive teaching examples: self-overlap and bilateral
# clipping respectively.  Prefixes never depend on requested totals.
DEMO_PROFILES = (
    ((9, 11), (4, 5), 14, (0, 2), "full_overlap"),
    ((10, 13), (4, 8), 22, (0, 6), "both_partial"),
    ((12, 15), (5, 6), 20, (3, -4), "full_clear"),
    ((14, 16), (6, 6), 25, (-4, 0), "mixed"),
    ((16, 18), (7, 8), 34, (2, 3), "full_overlap"),
    ((18, 20), (8, 9), 44, (-5, 4), "mixed"),
)
QUERY_PROFILES = (
    ((12, 15), (5, 7), 24, (3, -3), "full_overlap"),
    ((18, 20), (8, 9), 40, (-6, 0), "both_partial"),
    ((24, 27), (9, 11), 62, (0, 7), "mixed"),
    ((30, 30), (12, 12), 90, (-8, -7), "bottom_right"),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _direction(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"vector_direction"}:
        raise ValueError("settings must contain exactly vector_direction")
    value = settings["vector_direction"]
    if type(value) is not str or value not in SETTING_NAMES:
        raise ValueError(f"vector_direction must be one of {SETTING_NAMES}")
    return value


def program_for(direction: str) -> str:
    if direction == "blue_to_red":
        path = HERE / "canonical.rkt"
    elif direction == "red_to_blue":
        path = HERE / "red_to_blue.rkt"
    else:
        raise ValueError(f"unknown vector direction {direction!r}")
    return path.read_text()


def program(settings: dict[str, Any]) -> str:
    return program_for(_direction(settings))


def _validate_grid(grid: Any) -> tuple[list[list[int]], int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    clean: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or value not in (0, 1, 2, 3) for value in row):
            raise ValueError("input cells must be exact integer colors 0,1,2,3")
        clean.append(list(row))
    for color in (1, 2):
        if sum(value == color for row in clean for value in row) != 1:
            raise ValueError(f"grid must contain exactly one color-{color} marker")
    green = {(r, c) for r, row in enumerate(clean) for c, value in enumerate(row) if value == 3}
    if len(green) < 3 or not _connected(green):
        raise ValueError("grid must contain one 4-connected green motif of at least three cells")
    return clean, len(clean), width


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {min(cells)}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in CARDINAL:
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def analyze(grid: Any, direction: str) -> dict[str, Any]:
    if direction not in SETTING_NAMES:
        raise ValueError(f"direction must be one of {SETTING_NAMES}")
    values, height, width = _validate_grid(grid)
    blue = next((r, c) for r, row in enumerate(values) for c, value in enumerate(row) if value == 1)
    red = next((r, c) for r, row in enumerate(values) for c, value in enumerate(row) if value == 2)
    base = (red[0] - blue[0], red[1] - blue[1])
    vector = base if direction == "blue_to_red" else (-base[0], -base[1])
    source = sorted((r, c) for r, row in enumerate(values) for c, value in enumerate(row) if value == 3)
    raw_targets = [(r + vector[0], c + vector[1]) for r, c in source]
    visible = sorted((r, c) for r, c in raw_targets if 0 <= r < height and 0 <= c < width)
    source_set = set(source)
    return {
        "blue": blue,
        "red": red,
        "base_vector": base,
        "applied_vector": vector,
        "source_cells": source,
        "raw_targets": raw_targets,
        "visible_targets": visible,
        "target_source_overlap": bool(source_set & set(visible)),
    }


def _render(grid: Any, direction: str, *, all_or_nothing: bool = False,
            background_only: bool = False, preserve_input: bool = False,
            unit_vector: bool = False, same_color: bool = False,
            swap_axes: bool = False) -> list[list[int]]:
    values, height, width = _validate_grid(grid)
    info = analyze(values, direction)
    dr, dc = info["applied_vector"]
    if unit_vector:
        dr, dc = (dr > 0) - (dr < 0), (dc > 0) - (dc < 0)
    if swap_axes:
        dr, dc = dc, dr
    raw = [(r + dr, c + dc) for r, c in info["source_cells"]]
    visible = [(r, c) for r, c in raw if 0 <= r < height and 0 <= c < width]
    out = copy.deepcopy(values) if preserve_input else [[0] * width for _ in range(height)]
    if all_or_nothing and len(visible) != len(raw):
        return out
    color = 3 if same_color else 8
    for row, col in visible:
        if not background_only or values[row][col] == 0:
            out[row][col] = color
    return out


def solve(grid: Any, rule: str) -> list[list[int]]:
    if rule in SETTING_NAMES:
        return _render(grid, rule)
    for suffix, options in (
        ("_all_or_nothing", {"all_or_nothing": True}),
        ("_background_only", {"background_only": True}),
        ("_preserve_input", {"preserve_input": True}),
        ("_unit", {"unit_vector": True}),
        ("_same_color", {"same_color": True}),
        ("_swap_axes", {"swap_axes": True}),
    ):
        if rule.endswith(suffix):
            direction = rule.removesuffix(suffix)
            if direction in SETTING_NAMES:
                return _render(grid, direction, **options)
    raise ValueError(f"unknown rule {rule!r}")


CANDIDATE_NAMES = tuple(
    ["blue_to_red", "red_to_blue"]
    + [f"{direction}{suffix}" for direction in SETTING_NAMES for suffix in (
        "_all_or_nothing", "_background_only", "_preserve_input",
        "_unit", "_same_color", "_swap_axes")]
)


def teaching_survivors(demos: list[dict[str, Any]]) -> list[str]:
    survivors = []
    for candidate in CANDIDATE_NAMES:
        if all(solve(pair["input"], candidate) == pair["output"] for pair in demos):
            survivors.append(candidate)
    return survivors


def _rng(seed: int, split: str, index: int, attempt: int = 0) -> random.Random:
    payload = json.dumps([TASK_ID, "vector-direction-v1", seed, split, index, attempt],
                         separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _shape_in_box(rng: random.Random, height: int, width: int, size: int) -> set[tuple[int, int]]:
    if not height >= 2 or not width >= 2 or not height + width - 1 <= size <= height * width:
        raise ValueError("invalid shape profile")
    top = 0 if rng.randrange(2) == 0 else height - 1
    left = 0 if rng.randrange(2) == 0 else width - 1
    cells = {(top, col) for col in range(width)} | {(row, left) for row in range(height)}
    while len(cells) < size:
        frontier = sorted({(row + dr, col + dc) for row, col in cells for dr, dc in CARDINAL
                           if 0 <= row + dr < height and 0 <= col + dc < width
                           and (row + dr, col + dc) not in cells})
        if not frontier:
            raise RuntimeError("shape frontier exhausted")
        cells.add(rng.choice(frontier))
    assert _connected(cells)
    return cells


def _placement_ok(mode: str, source: set[tuple[int, int]], vector: tuple[int, int],
                  height: int, width: int) -> bool:
    counts = []
    overlaps = []
    for sign in (1, -1):
        dr, dc = sign * vector[0], sign * vector[1]
        visible = {(r + dr, c + dc) for r, c in source
                   if 0 <= r + dr < height and 0 <= c + dc < width}
        counts.append(len(visible))
        overlaps.append(bool(source & visible))
    if len(set((r + vector[0], c + vector[1]) for r, c in source)
           ^ set((r - vector[0], c - vector[1]) for r, c in source)) == 0:
        return False
    if mode == "full_overlap":
        return counts == [len(source), len(source)] and all(overlaps)
    if mode == "both_partial":
        return all(0 < count < len(source) for count in counts)
    if mode == "full_clear":
        return counts == [len(source), len(source)] and not any(overlaps)
    if mode == "mixed":
        return all(count > 0 for count in counts) and counts[0] != counts[1]
    if mode == "bottom_right":
        touches = any(r == height - 1 for r, _ in source) and any(c == width - 1 for _, c in source)
        return touches and all(count > 0 for count in counts) and counts[0] != counts[1]
    raise ValueError(f"unknown placement mode {mode}")


def _build_input(seed: int, split: str, index: int, profile) -> list[list[int]]:
    (height, width), (shape_h, shape_w), size, vector, mode = profile
    for attempt in range(128):
        rng = _rng(seed, split, index, attempt)
        relative = _shape_in_box(rng, shape_h, shape_w, size)
        origins = [(row, col) for row in range(height - shape_h + 1)
                   for col in range(width - shape_w + 1)]
        if mode == "bottom_right":
            origins = [(height - shape_h, width - shape_w)]
        else:
            rng.shuffle(origins)
        for row0, col0 in origins:
            source = {(row0 + row, col0 + col) for row, col in relative}
            if not _placement_ok(mode, source, vector, height, width):
                continue
            marker_sites = []
            for row in range(height):
                for col in range(width):
                    red = (row + vector[0], col + vector[1])
                    if (0 <= red[0] < height and 0 <= red[1] < width
                            and (row, col) not in source and red not in source):
                        marker_sites.append((row, col))
            rng.shuffle(marker_sites)
            if not marker_sites:
                continue
            blue = marker_sites[0]
            red = (blue[0] + vector[0], blue[1] + vector[1])
            grid = [[0] * width for _ in range(height)]
            for row, col in source:
                grid[row][col] = 3
            grid[blue[0]][blue[1]] = 1
            grid[red[0]][red[1]] = 2
            _validate_grid(grid)
            return grid
    raise RuntimeError(f"bounded sampler exhausted for {split}[{index}] mode={mode}")


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split == "demo":
        profiles = DEMO_PROFILES
    elif split == "query":
        profiles = QUERY_PROFILES
    else:
        raise ValueError("split must be demo or query")
    _integer(index, 0, len(profiles) - 1, "index")
    return _build_input(seed, split, index, profiles[index])


def generate_episode(seed: int, direction: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if type(direction) is not str or direction not in SETTING_NAMES:
        raise ValueError(f"vector_direction must be one of {SETTING_NAMES}")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train = []
    test = []
    for index in range(demos):
        grid = sample_input(seed, "demo", index)
        train.append({"input": grid, "output": solve(grid, direction)})
    for index in range(queries):
        grid = sample_input(seed, "query", index)
        test.append({"input": grid, "output": solve(grid, direction)})
    return {"train": train, "test": test, "program_solution": program_for(direction)}


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    return generate_episode(seed, _direction(settings), demos=demos, queries=queries)
