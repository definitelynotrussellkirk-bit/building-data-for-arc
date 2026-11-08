#!/usr/bin/env python3
"""Native object/cell-count × chart-alignment family for 99d71aabd753.

The visible input sampler is independent of the private episode setting.  Every
scene contains three colors with distinct, nonconsecutive object counts and
distinct cell totals whose ranking conflicts with object-count ranking.  Thus
both rule axes are demonstrated rather than encoded by dimensions or positions.
"""
from __future__ import annotations

from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable

from reviewer_support import canonical_path, find_root

TASK_ID = "99d71aabd753"
ROOT = find_root(__file__)
ALLOWED_MEASURES = ("objects", "cells")
ALLOWED_ALIGNMENTS = ("right", "left")
DEFAULT_MEASURE = "objects"
DEFAULT_ALIGNMENT = "right"
DEFAULT_DEMOS = 2
DEFAULT_QUERIES = 4
PROTOTYPE_VERSION = "1.0.0"

# Roles are ordered by decreasing object count.  Cell totals are distinct and
# deliberately reorder those roles.  Each tuple is one rectangle (height,width).
_PROFILE_SPECS: tuple[tuple[tuple[tuple[int, int], ...], ...], ...] = (
    (((1, 1),) * 6, ((2, 2),) * 4, ((3, 4),)),                 # objects 6,4,1; cells 6,16,12
    (((1, 1),) * 5, ((2, 3),) * 3, ((4, 4),)),                 # 5,3,1; 5,18,16
    (((1, 1),) * 6, ((2, 3),) * 3, ((3, 3), (2, 3))),          # 6,3,2; 6,18,15
    (((1, 1),) * 5, ((3, 3),) * 2, ((4, 4),)),                 # 5,2,1; 5,18,16
    (((1, 1),) * 6, ((2, 2),) * 4, ((2, 3),) * 2),             # 6,4,2; 6,16,12
    (((1, 1),) * 5, ((2, 3),) * 3, ((2, 4), (2, 3))),          # 5,3,2; 5,18,14
    (((1, 1),) * 6, ((3, 3),) * 2, ((4, 4),)),                 # 6,2,1; 6,18,16
)

_OBJECT_SCORE_BLOCK = """(let* ((mask (cellmap g (r c v) (if (= v col) 1 0)))
                                        (objs (objects mask 0)))
                                   (list col (length objs)))"""
_CELL_SCORE_BLOCK = "(list col (length (find-color g col)))"
_RIGHT_RENDER = "(if (>= c (- max-w cnt)) col 0)"
_LEFT_RENDER = "(if (< c cnt) col 0)"


def _validate_measure(value: str) -> None:
    if type(value) is not str or value not in ALLOWED_MEASURES:
        raise ValueError(f"measure must be one of {ALLOWED_MEASURES}, got {value!r}")


def _validate_alignment(value: str) -> None:
    if type(value) is not str or value not in ALLOWED_ALIGNMENTS:
        raise ValueError(
            f"alignment must be one of {ALLOWED_ALIGNMENTS}, got {value!r}"
        )


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def canonical_source(*, root: Path = ROOT) -> str:
    sources: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise ValueError(f"canonical record for {TASK_ID} has no program_solution")
                sources.append(source)
    if not sources:
        raise ValueError(f"no canonical record found for {TASK_ID}")
    if len(set(sources)) != 1:
        raise ValueError(f"canonical variants for {TASK_ID} disagree")
    return sources[0]


def program_for(
    measure: str = DEFAULT_MEASURE,
    alignment: str = DEFAULT_ALIGNMENT,
    *,
    root: Path = ROOT,
) -> str:
    """Materialize one exact rule; the default is untouched canonical bytes."""
    _validate_measure(measure)
    _validate_alignment(alignment)
    source = canonical_source(root=root)
    if measure == DEFAULT_MEASURE and alignment == DEFAULT_ALIGNMENT:
        return source
    if source.count(_OBJECT_SCORE_BLOCK) != 1:
        raise ValueError("canonical source no longer matches the guarded score template")
    if source.count(_RIGHT_RENDER) != 1:
        raise ValueError("canonical source no longer matches the guarded render template")
    if measure == "cells":
        source = source.replace(_OBJECT_SCORE_BLOCK, _CELL_SCORE_BLOCK)
    if alignment == "left":
        source = source.replace(_RIGHT_RENDER, _LEFT_RENDER)
    return source


def _rng(seed: int, sample_index: int, attempt: int = 0) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:scene:{seed}:{sample_index}:{attempt}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _dimensions(sample_index: int, total: int) -> tuple[int, int]:
    if sample_index == total - 1:
        return 30, 30
    return 18 + (sample_index % 5), 19 + ((2 * sample_index + 1) % 5)


def _rotated_dims(rect: tuple[int, int], rng: random.Random) -> tuple[int, int]:
    h, w = rect
    return (w, h) if h != w and rng.randrange(2) else (h, w)


def _cells(row: int, col: int, height: int, width: int) -> set[tuple[int, int]]:
    return {
        (row + dr, col + dc)
        for dr in range(height)
        for dc in range(width)
    }


def _add_moat(
    forbidden: set[tuple[int, int]],
    cells: Iterable[tuple[int, int]],
    height: int,
    width: int,
) -> None:
    for row, col in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = row + dr, col + dc
                if 0 <= rr < height and 0 <= cc < width:
                    forbidden.add((rr, cc))


def _place_scene(
    height: int,
    width: int,
    entries: list[tuple[int, int, int]],
    rng: random.Random,
    *,
    span_edges: bool,
) -> list[list[int]] | None:
    grid = [[0 for _ in range(width)] for _ in range(height)]
    forbidden: set[tuple[int, int]] = set()
    ordered = sorted(entries, key=lambda item: item[1] * item[2], reverse=True)

    anchored = 4 if span_edges else 0
    for index, (color, rh, rw) in enumerate(ordered):
        if index < anchored:
            anchors = (
                (0, 0),
                (0, width - rw),
                (height - rh, 0),
                (height - rh, width - rw),
            )
            positions = [anchors[index]]
        else:
            positions = [
                (row, col)
                for row in range(height - rh + 1)
                for col in range(width - rw + 1)
            ]
            rng.shuffle(positions)
        placed = False
        for row, col in positions:
            cells = _cells(row, col, rh, rw)
            if cells & forbidden:
                continue
            for rr, cc in cells:
                grid[rr][cc] = color
            _add_moat(forbidden, cells, height, width)
            placed = True
            break
        if not placed:
            return None
    return grid


def build_input(seed: int, sample_index: int, total: int) -> list[list[int]]:
    _validate_seed(seed)
    if type(sample_index) is not int or type(total) is not int or not 0 <= sample_index < total:
        raise ValueError("sample_index must be an exact integer inside total")
    height, width = _dimensions(sample_index, total)
    profile = _PROFILE_SPECS[(seed + 3 * sample_index) % len(_PROFILE_SPECS)]
    for attempt in range(80):
        rng = _rng(seed, sample_index, attempt)
        colors = list(range(1, 10))
        rng.shuffle(colors)
        role_colors = colors[:3]
        entries: list[tuple[int, int, int]] = []
        for color, rectangles in zip(role_colors, profile):
            for rectangle in rectangles:
                rh, rw = _rotated_dims(rectangle, rng)
                entries.append((color, rh, rw))
        rng.shuffle(entries)
        scene = _place_scene(
            height,
            width,
            entries,
            rng,
            span_edges=(sample_index == total - 1),
        )
        if scene is not None:
            return scene
    raise RuntimeError("could not place deterministic parametric scene")


def sample_inputs(seed: int, total: int) -> list[list[list[int]]]:
    _validate_seed(seed)
    if type(total) is not int or not 6 <= total <= 10:
        raise ValueError("total must be an exact integer in 6..10")
    grids = [build_input(seed, index, total) for index in range(total)]
    keys = [json.dumps(grid, separators=(",", ":")) for grid in grids]
    if len(set(keys)) != len(keys):
        raise AssertionError("parametric sampler emitted duplicate visible inputs")
    return grids


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(grid), width


def component_counts(grid: list[list[int]]) -> dict[int, int]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    counts: dict[int, int] = defaultdict(int)
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            counts[color] += 1
            seen.add((row, col))
            queue = deque([(row, col)])
            while queue:
                rr, cc = queue.popleft()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
    return dict(counts)


def cell_counts(grid: list[list[int]]) -> dict[int, int]:
    _validate_grid(grid)
    counts: dict[int, int] = defaultdict(int)
    for row in grid:
        for value in row:
            if value != 0:
                counts[value] += 1
    return dict(counts)


def python_output(
    grid: list[list[int]],
    *,
    measure: str = DEFAULT_MEASURE,
    alignment: str = DEFAULT_ALIGNMENT,
) -> list[list[int]]:
    _validate_measure(measure)
    _validate_alignment(alignment)
    values = component_counts(grid) if measure == "objects" else cell_counts(grid)
    if len(values) != 3 or len(set(values.values())) != 3:
        raise ValueError("scene must expose three colors with distinct selected scores")
    colors = sorted(values, key=values.get, reverse=True)
    width = max(values.values())
    if width > 30:
        raise ValueError("chart width exceeds ARC limit")
    output = []
    for color in colors:
        score = values[color]
        if alignment == "right":
            output.append([0] * (width - score) + [color] * score)
        else:
            output.append([color] * score + [0] * (width - score))
    return output


def rank_step_output(grid: list[list[int]]) -> list[list[int]]:
    values = component_counts(grid)
    colors = sorted(values, key=values.get, reverse=True)
    width = max(values.values())
    return [
        [0] * rank + [color] * (width - rank)
        for rank, color in enumerate(colors)
    ]


def generate_claims(
    seed: int,
    *,
    measure: str,
    alignment: str,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
) -> dict:
    _validate_seed(seed)
    _validate_measure(measure)
    _validate_alignment(alignment)
    _validate_counts(demos, queries)
    grids = sample_inputs(seed, demos + queries)
    pairs = [
        {
            "input": grid,
            "output": python_output(grid, measure=measure, alignment=alignment),
        }
        for grid in grids
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(measure, alignment, root=root),
    }
