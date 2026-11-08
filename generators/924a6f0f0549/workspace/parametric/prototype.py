#!/usr/bin/env python3
"""Episode-fixed outline-versus-silhouette family for ``924a6f0f0549``.

Stage A counts the marker row and selects the unique body object with that
area.  Stage B consumes that selected object's cells and either renders only
its 4-neighbor outline (the exact canonical default) or its full silhouette.
Inputs are shared across settings and every sampled selected object has a real
interior, so two demonstrations identify the finite setting without relying on
query labels.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK_ID = "924a6f0f0549"
ALLOWED_MODES = ("outline", "silhouette")
DEFAULT_MODE = "outline"
DEFAULT_DEMOS = 2
DEFAULT_QUERIES = 4
ROOT = find_root(__file__)
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SELECTED_DIMS = (
    (3, 3), (3, 4), (3, 5), (4, 4), (4, 5),
    (4, 6), (5, 3), (5, 4), (5, 5), (3, 6),
)


def _validate_mode(render_mode: str) -> None:
    if type(render_mode) is not str or render_mode not in ALLOWED_MODES:
        raise ValueError(f"render_mode must be one of {ALLOWED_MODES}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def _validate_difficulty(difficulty: str) -> None:
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be easy, medium, or hard")


def canonical_source(*, root: Path = ROOT) -> str:
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if type(source) is not str or not source.strip():
                    raise ValueError("canonical record has no program_solution")
                sources.add(source)
    if len(sources) != 1:
        raise ValueError(f"expected one canonical program, found {len(sources)}")
    return next(iter(sources))


def program_for(render_mode: str = DEFAULT_MODE, *, root: Path = ROOT) -> str:
    _validate_mode(render_mode)
    source = canonical_source(root=root)
    if render_mode == DEFAULT_MODE:
        return source
    needle = "(outline (e5-outline-cells cells))"
    if source.count(needle) != 1:
        raise ValueError("canonical source no longer matches guarded outline patch")
    return source.replace(needle, "(outline cells)")


def execute_rule(program: str, grid, *, bridge: RacketBridge | None = None):
    owns_bridge = bridge is None
    active = RacketBridge() if owns_bridge else bridge
    try:
        active.define_grid("parametric_input", grid)
        return active.eval_text(f"({wrap_rule(program)} parametric_input)")
    finally:
        if owns_bridge:
            active.shutdown()


def _validate_grid(grid) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if (len(grid) > 30 or width > 30
            or any(type(row) is not list or len(row) != width
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular exact colors 0..9 within 30x30")
    return len(grid), width


def _components(grid, *, start_row: int = 1):
    h, w = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    out: list[tuple[int, list[tuple[int, int]]]] = []
    for row in range(start_row, h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                cell = stack.pop()
                cells.append(cell)
                for dr, dc in _DIRS4:
                    nxt = (cell[0] + dr, cell[1] + dc)
                    if (start_row <= nxt[0] < h and 0 <= nxt[1] < w
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        stack.append(nxt)
            out.append((color, cells))
    return out


def python_mirror(grid, *, render_mode: str = DEFAULT_MODE):
    _validate_mode(render_mode)
    _validate_grid(grid)
    marker_count = sum(value == 1 for value in grid[0])
    matches = [item for item in _components(grid) if len(item[1]) == marker_count]
    if len(matches) != 1:
        raise ValueError("input needs one unique marker-count body object")
    color, cells = matches[0]
    selected = set(cells)
    rendered = selected if render_mode == "silhouette" else {
        cell for cell in selected
        if any((cell[0] + dr, cell[1] + dc) not in selected for dr, dc in _DIRS4)
    }
    r0 = min(row for row, _ in rendered)
    r1 = max(row for row, _ in rendered)
    c0 = min(col for _, col in rendered)
    c1 = max(col for _, col in rendered)
    output = [[0 for _ in range(c1 - c0 + 1)] for _ in range(r1 - r0 + 1)]
    for row, col in rendered:
        output[row - r0][col - c0] = color
    return output


def _paint(grid, top: int, left: int, cells, color: int) -> None:
    for dr, dc in cells:
        if grid[top + dr][left + dc] != 0:
            raise AssertionError("sampler object collision")
        grid[top + dr][left + dc] = color


def _rectangle(height: int, width: int):
    return [(row, col) for row in range(height) for col in range(width)]


def _stable_rng(seed: int, sample_index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{sample_index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def build_input(seed: int, sample_index: int, total: int, difficulty: str = "medium"):
    _validate_seed(seed)
    _validate_difficulty(difficulty)
    if type(sample_index) is not int or type(total) is not int or not 0 <= sample_index < total:
        raise ValueError("sample_index must be inside a positive total")

    if sample_index == total - 1:
        h = w = 30
        selected_h, selected_w = 5, 5
    else:
        selected_h, selected_w = _SELECTED_DIMS[sample_index % len(_SELECTED_DIMS)]
        marker_count = selected_h * selected_w
        h = 14 + sample_index % 6
        w = min(29, max(marker_count + 1, 18 + sample_index % 7))
    marker_count = selected_h * selected_w
    if marker_count > w:
        raise AssertionError("marker row cannot encode selected area")

    grid = [[0 for _ in range(w)] for _ in range(h)]
    rng = _stable_rng(seed, sample_index)
    for col in rng.sample(range(w), marker_count):
        grid[0][col] = 1

    # A row-major distractor deliberately appears before the selected object;
    # this also supports a strong causal counterfactual for the A stage.
    _paint(grid, 2, 1, [(0, 0), (1, 0), (1, 1)], 2)                 # area 3
    _paint(grid, 2, 6, _rectangle(2, 2), 3)                         # area 4
    _paint(grid, 5, 1, [(0, 0), (1, 0), (2, 0), (2, 1),
                        (2, 2), (1, 2), (0, 2)], 7)                 # area 7
    _paint(grid, h - 2, 1, [(0, col) for col in range(5)], 6)       # area 5
    selected_top = h - selected_h - 2
    selected_left = w - selected_w - 2
    _paint(grid, selected_top, selected_left,
           _rectangle(selected_h, selected_w), 4)

    sizes = sorted(len(cells) for _, cells in _components(grid))
    if sizes != sorted([3, 4, 5, 7, marker_count]):
        raise AssertionError(f"sampler component drift: {sizes}")
    outline = python_mirror(grid, render_mode="outline")
    silhouette = python_mirror(grid, render_mode="silhouette")
    if outline == silhouette:
        raise AssertionError("sample does not distinguish render modes")
    return grid


def grid_sha256(grid) -> str:
    _validate_grid(grid)
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    ).hexdigest()


def generate_claims(seed: int, *, render_mode: str, difficulty: str = "medium",
                    demos: int = DEFAULT_DEMOS, queries: int = DEFAULT_QUERIES,
                    root: Path = ROOT) -> dict[str, Any]:
    _validate_seed(seed)
    _validate_mode(render_mode)
    _validate_counts(demos, queries)
    _validate_difficulty(difficulty)
    total = demos + queries
    inputs = [build_input(seed, index, total, difficulty) for index in range(total)]
    if len({grid_sha256(grid) for grid in inputs}) != total:
        raise AssertionError("sampler emitted duplicate visible inputs")
    pairs = [
        {"input": grid, "output": python_mirror(grid, render_mode=render_mode)}
        for grid in inputs
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(render_mode, root=root),
    }
