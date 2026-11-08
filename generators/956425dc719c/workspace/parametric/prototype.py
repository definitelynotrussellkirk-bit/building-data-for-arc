#!/usr/bin/env python3
"""Post-filter selector family for 956425dc719c.

Stage A is always the canonical operation: recolor orange components touching
exactly one border gray.  ``largest`` and ``smallest`` then recompute orange
components on that stage-A grid and paint the unique size-ranked survivor blue.
The sampler makes the removed component the original unique largest, so ranking
before stage A is an observable wrong-order rival.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root

TASK_ID = "956425dc719c"
ALLOWED_MODES = ("none", "largest", "smallest")
DEFAULT_MODE = "none"
DEFAULT_DEMOS = 3
DEFAULT_QUERIES = 4
PROTOTYPE_VERSION = "1.1.0"
ROOT = find_root(__file__)

# (smallest survivor, middle survivor, largest survivor, removed one-border)
# Slot-indexed so the minimum two-demo lesson already changes both selected sizes.
_RANK_PROFILES = (
    (2, 4, 7, 10),
    (3, 6, 9, 12),
    (1, 5, 8, 11),
    (4, 7, 10, 13),
)


def _validate_mode(post_select: str) -> None:
    if type(post_select) is not str or post_select not in ALLOWED_MODES:
        raise ValueError(f"post_select must be one of {ALLOWED_MODES}, got {post_select!r}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def _validate_difficulty(difficulty: str | None) -> None:
    if difficulty not in {None, "easy", "medium", "hard"}:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _source_path(name: str, *, root: Path = ROOT) -> Path:
    return Path(root) / "generators" / TASK_ID / "workspace" / "parametric" / name


def canonical_source(*, root: Path = ROOT) -> str:
    return _source_path("canonical.rkt", root=root).read_text(encoding="utf-8")


def program_for(post_select: str = DEFAULT_MODE, *, root: Path = ROOT) -> str:
    _validate_mode(post_select)
    names = {"none": "canonical.rkt", "largest": "largest.rkt", "smallest": "smallest.rkt"}
    source = _source_path(names[post_select], root=root).read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError(f"empty Racket program for {post_select}")
    return source


def wrong_order_program(*, root: Path = ROOT) -> str:
    source = _source_path("wrong_order_largest.rkt", root=root).read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError("empty wrong-order Racket program")
    return source



def _episode_index(slot: int) -> int:
    """Map the six train and four query slots to disjoint visible indices."""
    if 0 <= slot < 6:
        return slot
    if 100 <= slot < 104:
        return 6 + slot - 100
    return slot % 10


def _rotate90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _reflect(grid):
    return [row[::-1] for row in grid]


def _transform(grid, index: int):
    result = [row[:] for row in grid]
    rotations = index // 2
    for _ in range(rotations):
        result = _rotate90(result)
    if index % 2:
        result = _reflect(result)
    return result


def _paint(grid, cells, color: int) -> None:
    for r, c in cells:
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            raise AssertionError("component escaped grid")
        if grid[r][c] != 0:
            raise AssertionError("component overlap")
        grid[r][c] = color


def _halo(cells):
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))
    }


def _dimensions(seed: int, slot: int, *, stress: bool, difficulty: str | None):
    if stress:
        return 30, 30
    band = {None: 0, "easy": 0, "medium": 2, "hard": 4}[difficulty]
    return 14 + band + ((seed + slot) % 3), 15 + band + ((2 * seed + 3 * slot) % 4)


def _compact_cells(anchor_r: int, anchor_c: int, size: int, width: int):
    return [(anchor_r + index // width, anchor_c + index % width) for index in range(size)]


def _corner_cells(h: int, size: int, width: int = 3):
    # Row-major upward from the bottom-left corner; touches exactly two borders.
    return [(h - 1 - index // width, index % width) for index in range(size)]


def _build_input(seed: int, slot: int, *, difficulty: str | None, stress: bool = False):
    h, w = _dimensions(seed, slot, stress=stress, difficulty=difficulty)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    small_size, middle_size, large_size, border_size = _RANK_PROFILES[slot % len(_RANK_PROFILES)]

    # Original unique largest touches only the top border and is removed by A.
    target_width = 5
    start_c = w // 2 - target_width // 2
    target = _compact_cells(0, start_c, border_size, target_width)
    # Three survivors have unique sizes, but those sizes vary by episode.
    corner = _corner_cells(h, small_size)
    middle = _compact_cells(3, 2, middle_size, 3)
    large = _compact_cells(h - 7, w - 7, large_size, 4)

    orange = [target, corner, middle, large]
    occupied = set()
    for cells in orange:
        if set(cells) & _halo(occupied):
            raise AssertionError("orange components are not separated")
        _paint(grid, cells, 7)
        occupied.update(cells)

    # Add a source-role distractor with eight cells, placed deterministically in
    # a clear interior location. Its color varies without colliding with blue/gray.
    ring_offsets = (
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 2),
    )
    candidates = [(r, c) for r in range(2, h - 4) for c in range(2, w - 4)]
    clear_candidates = []
    for ar, ac in candidates:
        cells = [(ar + dr, ac + dc) for dr, dc in ring_offsets]
        if not (set(cells) & _halo(occupied)):
            clear_candidates.append((ar, ac, cells))
    if len(clear_candidates) < 10:
        raise AssertionError("could not reserve ten distinct distractor positions")

    visible_index = _episode_index(slot)
    offset_digest = hashlib.sha256(
        f"{TASK_ID}:{seed}:{h}:{w}:distractor".encode()
    ).digest()
    offset = int.from_bytes(offset_digest[:8], "big") % len(clear_candidates)
    _, _, cells = clear_candidates[(offset + visible_index) % len(clear_candidates)]
    distractor_color = (2, 3, 4, 6, 8, 9)[(seed + visible_index) % 6]
    _paint(grid, cells, distractor_color)
    occupied.update(cells)

    transformed = _transform(grid, 0 if stress else (seed + slot) % 8)
    analysis = analyze_input(transformed)
    expected_remaining = sorted((small_size, middle_size, large_size))
    if analysis["one_border_sizes"] != [border_size] or analysis["remaining_sizes"] != expected_remaining:
        raise AssertionError(f"constructed scene lost rank grammar: {analysis}")
    outputs = {mode: python_mirror(transformed, post_select=mode) for mode in ALLOWED_MODES}
    if len({_grid_key(value) for value in outputs.values()}) != 3:
        raise AssertionError("constructed scene does not distinguish all settings")
    if python_wrong_order_largest(transformed) == outputs["largest"]:
        raise AssertionError("constructed scene does not expose wrong ordering")
    return transformed


def _components4(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            objects.append({"color": color, "cells": sorted(cells)})
    return objects


def _side_count(cells, h: int, w: int) -> int:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return int(min(rows) == 0) + int(max(rows) == h - 1) + int(min(cols) == 0) + int(max(cols) == w - 1)


def analyze_input(grid):
    h, w = len(grid), len(grid[0])
    orange = [obj for obj in _components4(grid) if obj["color"] == 7]
    one = sorted(len(obj["cells"]) for obj in orange if _side_count(obj["cells"], h, w) == 1)
    remaining = sorted(len(obj["cells"]) for obj in orange if _side_count(obj["cells"], h, w) != 1)
    return {
        "one_border_sizes": one,
        "remaining_sizes": remaining,
        "orange_component_count": len(orange),
    }


def _paint_copy(grid, cells, color):
    out = [row[:] for row in grid]
    for r, c in cells:
        out[r][c] = color
    return out


def _stage_a(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for obj in _components4(grid):
        if obj["color"] == 7 and _side_count(obj["cells"], h, w) == 1:
            for r, c in obj["cells"]:
                out[r][c] = 5
    return out


def extracted_intermediate(grid):
    """Return stage A's remaining orange rank pool consumed by stage B."""
    stage_a = _stage_a(grid)
    remaining = [obj for obj in _components4(stage_a) if obj["color"] == 7]
    return [
        {"size": len(obj["cells"]), "cells": [list(cell) for cell in obj["cells"]]}
        for obj in remaining
    ]


def python_mirror(grid, *, post_select: str = DEFAULT_MODE):
    _validate_mode(post_select)
    stage_a = _stage_a(grid)
    if post_select == "none":
        return stage_a
    remaining = [obj for obj in _components4(stage_a) if obj["color"] == 7]
    sizes = [len(obj["cells"]) for obj in remaining]
    if len(sizes) < 2 or len(set(sizes)) != len(sizes):
        raise ValueError("post-selection requires at least two uniquely sized remaining orange components")
    selected = max(remaining, key=lambda obj: len(obj["cells"])) if post_select == "largest" else min(
        remaining, key=lambda obj: len(obj["cells"])
    )
    return _paint_copy(stage_a, selected["cells"], 1)


def python_wrong_order_largest(grid):
    """Counterfactual: rank original orange components before canonical filtering."""
    orange = [obj for obj in _components4(grid) if obj["color"] == 7]
    sizes = [len(obj["cells"]) for obj in orange]
    if len(set(sizes)) != len(sizes):
        raise ValueError("wrong-order counterfactual expects unique original sizes")
    selected = max(orange, key=lambda obj: len(obj["cells"]))
    return _stage_a(_paint_copy(grid, selected["cells"], 1))


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def grid_sha256(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _sample_inputs(seed: int, demos: int, *, difficulty: str | None):
    train = [_build_input(seed, index, difficulty=difficulty) for index in range(demos)]
    test = [
        _build_input(seed, 100 + index, difficulty=difficulty, stress=index == 3)
        for index in range(DEFAULT_QUERIES)
    ]
    hashes = [grid_sha256(grid) for grid in train + test]
    if len(hashes) != len(set(hashes)):
        raise AssertionError("parametric sampler emitted duplicate visible inputs")
    return train, test


def generate_claims(
    seed: int,
    *,
    post_select: str,
    difficulty: str | None = "medium",
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
) -> dict[str, Any]:
    _validate_seed(seed)
    _validate_mode(post_select)
    _validate_counts(demos, queries)
    _validate_difficulty(difficulty)
    train_inputs, test_inputs = _sample_inputs(seed, demos, difficulty=difficulty)
    def pair(grid):
        return {"input": grid, "output": python_mirror(grid, post_select=post_select)}
    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program_for(post_select, root=root),
    }
