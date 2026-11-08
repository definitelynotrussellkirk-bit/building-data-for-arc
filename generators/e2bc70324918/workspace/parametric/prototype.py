#!/usr/bin/env python3
"""Deterministic endpoint-stamp family for e2bc70324918.

The canonical ``copy`` setting extracts the input glyph's normalized cells and
stamps that exact sparse template at the two input-line endpoints.  The
``dilate4`` setting keeps the same stage-A extraction, expands the extracted
template by one orthogonal cell, and then performs the same endpoint-stamp stage
B. Inputs are shared across settings; same-bounding-box source shapes have
distinct dilations, defeating fixed-motif and bounding-box-only shortcuts.
"""
from __future__ import annotations

from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import find_root

TASK_ID = "e2bc70324918"
ALLOWED_MODES = ("copy", "dilate4")
DEFAULT_MODE = "copy"
DEFAULT_DEMOS = 3
DEFAULT_QUERIES = 4
PROTOTYPE_VERSION = "1.1.0"
ROOT = find_root(__file__)

# Symmetric sparse templates ensure the two setting programs differ on every
# generated pair while preserving canonical role semantics.
_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "plus": ((-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)),
    "x": ((-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)),
    "ring": (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1),
    ),
}
_COLORS = (1, 2, 3, 4, 5, 6, 8, 9)
_BG = 7


def _validate_mode(stamp_mode: str) -> None:
    if type(stamp_mode) is not str or stamp_mode not in ALLOWED_MODES:
        raise ValueError(f"stamp_mode must be one of {ALLOWED_MODES}, got {stamp_mode!r}")


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
    source = _source_path("canonical.rkt", root=root).read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError("canonical Racket source is empty")
    return source


def program_for(stamp_mode: str = DEFAULT_MODE, *, root: Path = ROOT) -> str:
    _validate_mode(stamp_mode)
    name = "canonical.rkt" if stamp_mode == "copy" else "dilate4.rkt"
    source = _source_path(name, root=root).read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError(f"Racket source is empty: {name}")
    return source


def _stable_rng(seed: int, slot: int, purpose: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{slot}:{purpose}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _line_cells(orientation: str, h: int, w: int, length: int) -> list[tuple[int, int]]:
    mid_r, mid_c = h // 2, w // 2
    if orientation == "horizontal":
        start = mid_c - length // 2
        return [(mid_r, start + i) for i in range(length)]
    if orientation == "vertical":
        start = mid_r - length // 2
        return [(start + i, mid_c) for i in range(length)]
    start_r = mid_r - length // 2
    if orientation == "diagonal":
        start_c = mid_c - length // 2
        return [(start_r + i, start_c + i) for i in range(length)]
    if orientation == "anti-diagonal":
        start_c = mid_c + length // 2
        return [(start_r + i, start_c - i) for i in range(length)]
    raise ValueError(f"unsupported orientation: {orientation}")


def _shape_cells(center: tuple[int, int], offsets) -> list[tuple[int, int]]:
    r, c = center
    return [(r + dr, c + dc) for dr, dc in offsets]


def _halo(cells, radius: int = 1) -> set[tuple[int, int]]:
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in range(-radius, radius + 1)
        for dc in range(-radius, radius + 1)
    }


def _dimensions(seed: int, slot: int, *, stress: bool, difficulty: str | None) -> tuple[int, int]:
    if stress:
        return 30, 30
    band = {None: 0, "easy": 0, "medium": 2, "hard": 4}[difficulty]
    h = 13 + band + ((seed + 3 * slot) % 4)
    w = 14 + band + ((2 * seed + 5 * slot) % 5)
    return min(h, 24), min(w, 25)


def _build_input(seed: int, slot: int, *, difficulty: str | None, stress: bool = False):
    h, w = _dimensions(seed, slot, stress=stress, difficulty=difficulty)
    rng = _stable_rng(seed, slot, "layout")
    shape_name = ("plus", "x", "ring")[(seed + slot) % 3]
    offsets = _SHAPES[shape_name]
    n_glyphs = 4 if stress else 2 + ((seed + 2 * slot) % 3)
    orientations = ("horizontal", "vertical", "diagonal", "anti-diagonal")
    orientation = orientations[(seed + slot) % len(orientations)]
    max_length = min(h, w) - 8
    length = min(max_length, 6 + ((seed + slot) % 3))
    length = max(length, 5)
    line = _line_cells(orientation, h, w, length)
    line_set = set(line)

    if stress:
        candidates = [(3, 3), (3, w - 4), (h - 4, 3), (h - 4, w - 4)]
    else:
        candidates = [
            (2, 2), (2, w - 3), (h - 3, 2), (h - 3, w - 3),
            (2, w // 2), (h - 3, w // 2), (h // 2, 2), (h // 2, w - 3),
        ]
        rng.shuffle(candidates)

    selected: list[tuple[int, int]] = []
    occupied: set[tuple[int, int]] = set()
    for center in candidates:
        cells = _shape_cells(center, offsets)
        if any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
            continue
        if set(cells) & line_set:
            continue
        if set(cells) & _halo(occupied):
            continue
        selected.append(center)
        occupied.update(cells)
        if len(selected) == n_glyphs:
            break
    if len(selected) != n_glyphs:
        raise AssertionError("could not place the requested separated glyphs")

    palette = list(_COLORS)
    rng.shuffle(palette)
    line_color, stamp_color = palette[:2]
    grid = [[_BG for _ in range(w)] for _ in range(h)]
    for r, c in line:
        grid[r][c] = line_color
    for center in selected:
        for r, c in _shape_cells(center, offsets):
            grid[r][c] = stamp_color

    # Validate the grammar through the same independent role parser used by the mirror.
    parsed = _parse_roles(grid)
    if len(parsed["stamp_objects"]) != n_glyphs:
        raise AssertionError("constructed glyphs merged or disappeared")
    outputs = {mode: python_mirror(grid, stamp_mode=mode) for mode in ALLOWED_MODES}
    if outputs["copy"] == outputs["dilate4"]:
        raise AssertionError("constructed input does not distinguish stamp modes")
    return grid


def _components8(grid, bg: int):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == bg:
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if not (dr or dc):
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < h and 0 <= nc < w
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color
                        ):
                            seen.add((nr, nc))
                            queue.append((nr, nc))
            objects.append({"color": color, "cells": cells})
    return objects


def _endpoints(cells):
    cell_set = set(cells)
    return [
        (r, c)
        for r, c in cells
        if sum(
            (r + dr, c + dc) in cell_set
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if dr or dc
        ) == 1
    ]


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _normalize(cells):
    r1, c1, _, _ = _bbox(cells)
    return sorted((r - r1, c - c1) for r, c in cells)


def _parse_roles(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    bg = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    objects = _components8(grid, bg)
    line_candidates = [
        obj for obj in objects if len(obj["cells"]) > 1 and len(_endpoints(obj["cells"])) == 2
    ]
    if len(line_candidates) != 1:
        raise ValueError(f"expected one line object, found {len(line_candidates)}")
    line = line_candidates[0]
    colors = []
    for row in grid:
        for value in row:
            if value != bg and value not in colors:
                colors.append(value)
    stamp_colors = [color for color in colors if color != line["color"]]
    if len(stamp_colors) != 1:
        raise ValueError("expected exactly one stamp color")
    stamps = [obj for obj in objects if obj["color"] == stamp_colors[0]]
    if not stamps:
        raise ValueError("expected at least one stamp object")
    return {
        "bg": bg,
        "line_color": line["color"],
        "line_cells": line["cells"],
        "stamp_color": stamp_colors[0],
        "stamp_objects": stamps,
    }


def _draw_line(grid, a: tuple[int, int], b: tuple[int, int], color: int) -> None:
    r, c = a
    r2, c2 = b
    dr, dc = abs(r2 - r), abs(c2 - c)
    sr, sc = (1 if r < r2 else -1), (1 if c < c2 else -1)
    err = dr - dc
    while True:
        if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
            grid[r][c] = color
        if (r, c) == (r2, c2):
            return
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            r += sr
        if e2 < dr:
            err += dr
            c += sc


def extracted_intermediate(grid, *, stamp_mode: str):
    """Return stage A's input-dependent normalized template consumed by stage B."""
    _validate_mode(stamp_mode)
    parsed = _parse_roles(grid)
    source = _normalize(parsed["stamp_objects"][0]["cells"])
    if stamp_mode == "copy":
        return source
    expanded = {
        (r + dr, c + dc)
        for r, c in source
        for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))
    }
    return _normalize(expanded)


def python_mirror(grid, *, stamp_mode: str = DEFAULT_MODE):
    """Independent Python mirror; protected Racket remains label authority."""
    _validate_mode(stamp_mode)
    parsed = _parse_roles(grid)
    h, w = len(grid), len(grid[0])
    stamp_cells = extracted_intermediate(grid, stamp_mode=stamp_mode)
    stamp_r1, stamp_c1, stamp_r2, stamp_c2 = _bbox(stamp_cells)
    stamp_cr = (stamp_r1 + stamp_r2) // 2
    stamp_cc = (stamp_c1 + stamp_c2) // 2
    centers = []
    for obj in parsed["stamp_objects"]:
        r1, c1, r2, c2 = _bbox(obj["cells"])
        centers.append(((r1 + r2) // 2, (c1 + c2) // 2))
    output = [[parsed["bg"] for _ in range(w)] for _ in range(h)]
    for i, a in enumerate(centers):
        for b in centers[i + 1 :]:
            _draw_line(output, a, b, parsed["line_color"])
    for endpoint_r, endpoint_c in _endpoints(parsed["line_cells"]):
        for r, c in stamp_cells:
            nr = endpoint_r + r - stamp_cr
            nc = endpoint_c + c - stamp_cc
            if 0 <= nr < h and 0 <= nc < w:
                output[nr][nc] = parsed["stamp_color"]
    return output


def grid_sha256(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _sample_inputs(seed: int, demos: int, *, difficulty: str | None):
    train = [
        _build_input(seed, index, difficulty=difficulty)
        for index in range(demos)
    ]
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
    stamp_mode: str,
    difficulty: str | None = "medium",
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
) -> dict[str, Any]:
    _validate_seed(seed)
    _validate_mode(stamp_mode)
    _validate_counts(demos, queries)
    _validate_difficulty(difficulty)
    train_inputs, test_inputs = _sample_inputs(seed, demos, difficulty=difficulty)
    pair = lambda grid: {
        "input": grid,
        "output": python_mirror(grid, stamp_mode=stamp_mode),
    }
    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program_for(stamp_mode, root=root),
    }
