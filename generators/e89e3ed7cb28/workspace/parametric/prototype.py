#!/usr/bin/env python3
"""Episode-level bottom-survivor / modal-survivor-colour family.

The canonical setting keeps one bottommost non-zero cell in every active
column.  The alternative is deliberately sequential:

A. build that canonical survivor grid;
I. take the unique modal colour among the survivor cells;
B. filter the *original* input to the intermediate colour.

The episode constructor makes the whole-grid modal colour a different decoy and
places the selected colour above a column survivor, so neither raw frequency nor
"just return stage A" fits the alternative demonstrations.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK_ID = "e89e3ed7cb28"
ALLOWED_MODES = ("bottommost", "modal_survivor_color")
DEFAULT_MODE = "bottommost"
ROOT = find_root(__file__)

_MODAL_PROGRAM = r'''(rule! (let ((dummy 0))
  (let* ((stage-a
          (for/fold ((out (empty-grid (rows g) (cols g) 0)))
                    ((c (in-range (cols g))))
            (let ((hits (filter (lambda (r) (not (= (at g r c) 0)))
                                (reverse (range 0 (rows g))))))
              (if (empty? hits)
                  out
                  (let ((r (first hits)))
                    (set-cell out r c (at g r c)))))))
         (survivor-colors
          (filter (lambda (color) (not (= color 0))) (grid-colors stage-a)))
         (key-color
          (first
           (sort survivor-colors
                 (lambda (a b)
                   (let ((ca (count-color stage-a a))
                         (cb (count-color stage-a b)))
                     (or (> ca cb) (and (= ca cb) (< a b)))))))))
    (grid-from-fn (rows g) (cols g)
                  (lambda (r c)
                    (if (= (at g r c) key-color) key-color 0))))))'''


def _validate_mode(output_mode: str) -> None:
    if type(output_mode) is not str or output_mode not in ALLOWED_MODES:
        raise ValueError(f"output_mode must be one of {ALLOWED_MODES}, got {output_mode!r}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def canonical_source(*, root: Path = ROOT) -> str:
    sources: set[str] = set()
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            source = row.get("program_solution")
            if isinstance(source, str) and source.strip():
                sources.add(source)
    if len(sources) != 1:
        raise ValueError(f"expected one canonical source for {TASK_ID}, found {len(sources)}")
    return next(iter(sources))


def program_for(output_mode: str, *, root: Path = ROOT) -> str:
    _validate_mode(output_mode)
    return canonical_source(root=root) if output_mode == DEFAULT_MODE else _MODAL_PROGRAM


def _rng(seed: int, index: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{index}:{label}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _dimensions(seed: int, index: int) -> tuple[int, int]:
    return 9 + ((seed + 2 * index) % 7), 10 + ((3 * seed + 5 * index) % 8)


def make_input(
    seed: int,
    index: int,
    *,
    height: int | None = None,
    width: int | None = None,
) -> list[list[int]]:
    """Construct a lawful scene with a unique survivor-mode and decoy raw mode."""
    _validate_seed(seed)
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")
    if height is None or width is None:
        default_h, default_w = _dimensions(seed, index)
        height = default_h if height is None else height
        width = default_w if width is None else width
    if type(height) is not int or type(width) is not int or not 8 <= height <= 30 or not 8 <= width <= 30:
        raise ValueError("height and width must be exact integers in 8..30")

    rng = _rng(seed, index, "layout")
    stress = height == 30 and width == 30
    active_count = min(width, 18 if stress else max(6, min(10, width - 1)))
    if stress:
        interior = list(range(1, width - 1))
        rng.shuffle(interior)
        columns = [0, width - 1, *interior[: active_count - 2]]
    else:
        columns = rng.sample(range(width), active_count)
    columns = sorted(columns)

    key_color = 1 + ((seed * 5 + index * 3) % 9)
    decoy_color = 1 + (key_color % 9)
    other_colors = [c for c in range(1, 10) if c not in {key_color, decoy_color}]
    rng.shuffle(other_colors)
    key_count = max(2, active_count // 3)
    bottom_colors = [key_color] * key_count
    while len(bottom_colors) < active_count:
        bottom_colors.append(other_colors[(len(bottom_colors) - key_count) % len(other_colors)])
    rng.shuffle(bottom_colors)

    grid = [[0 for _ in range(width)] for _ in range(height)]
    non_key_column: int | None = None
    for position, (column, bottom_color) in enumerate(zip(columns, bottom_colors)):
        if stress and position in {0, 1, 2}:
            bottom_row = height - 1 - position
        else:
            bottom_row = rng.randint(max(5, height // 2), height - 1)
        grid[bottom_row][column] = bottom_color
        if bottom_color != key_color and non_key_column is None:
            non_key_column = column

        available = list(range(bottom_row))
        rng.shuffle(available)
        decoy_slots = available[: min(4 if stress else 3, len(available))]
        for row in decoy_slots:
            grid[row][column] = decoy_color
        remaining = [row for row in available if row not in decoy_slots]
        if remaining:
            filler = other_colors[(position + index) % len(other_colors)]
            grid[remaining[0]][column] = filler

    # B must visibly reuse the original, not merely recolour stage A.
    assert non_key_column is not None
    candidate_rows = [r for r in range(height) if grid[r][non_key_column] == 0]
    key_row = min(candidate_rows)
    grid[key_row][non_key_column] = key_color

    if stress:
        # Force all four canvas boundaries to carry content without changing the
        # unique survivor mode or the raw decoy mode.
        left_bottom = max(r for r in range(height) if grid[r][0] != 0)
        right_bottom = max(r for r in range(height) if grid[r][width - 1] != 0)
        grid[0][0] = decoy_color
        grid[0][width - 1] = decoy_color
        grid[height - 1][0] = grid[left_bottom][0]
        grid[height - 1][width - 1] = grid[right_bottom][width - 1]

    stage = bottommost_grid(grid)
    if modal_survivor_color(stage) != key_color:
        raise AssertionError("construction lost the unique survivor mode")
    if whole_grid_modal_color(grid) != decoy_color:
        raise AssertionError("construction lost the whole-grid frequency decoy")
    if python_mirror(grid, output_mode=DEFAULT_MODE) == python_mirror(
        grid, output_mode="modal_survivor_color"
    ):
        raise AssertionError("declared settings do not disagree")
    return grid


def bottommost_grid(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for column in range(width):
        for row in range(height - 1, -1, -1):
            if grid[row][column] != 0:
                output[row][column] = grid[row][column]
                break
    return output


def _modal_color(values: list[int]) -> int:
    counts = Counter(value for value in values if value != 0)
    if not counts:
        raise ValueError("a non-zero colour is required")
    return min(counts, key=lambda color: (-counts[color], color))


def modal_survivor_color(stage_a: list[list[int]]) -> int:
    return _modal_color([value for row in stage_a for value in row])


def whole_grid_modal_color(grid: list[list[int]]) -> int:
    return _modal_color([value for row in grid for value in row])


def filter_to_color(grid: list[list[int]], color: int) -> list[list[int]]:
    return [[value if value == color else 0 for value in row] for row in grid]


def python_mirror(grid: list[list[int]], *, output_mode: str) -> list[list[int]]:
    _validate_mode(output_mode)
    stage_a = bottommost_grid(grid)
    if output_mode == DEFAULT_MODE:
        return stage_a
    return filter_to_color(grid, modal_survivor_color(stage_a))


def execute_rule(program: str, grid: list[list[int]], *, bridge: RacketBridge) -> list[list[int]]:
    wrapped = wrap_rule(program)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrapped} {literal})")


def make_episode(
    seed: int,
    *,
    output_mode: str,
    demos: int = 2,
    queries: int = 4,
    root: Path = ROOT,
) -> dict[str, Any]:
    _validate_seed(seed)
    _validate_mode(output_mode)
    _validate_counts(demos, queries)
    pairs: list[dict[str, list[list[int]]]] = []
    total = demos + queries
    for index in range(total):
        is_stress = index == total - 1
        if is_stress:
            grid = make_input(seed, index, height=30, width=30)
        else:
            height, width = _dimensions(seed, index)
            grid = make_input(seed, index, height=height, width=width)
        pairs.append({"input": grid, "output": python_mirror(grid, output_mode=output_mode)})
    return {
        "task_id": TASK_ID,
        "parameters": {"output_mode": output_mode},
        "selection_scope": "once_per_episode",
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program": program_for(output_mode, root=root),
    }


def generate_claims(
    seed: int,
    *,
    output_mode: str,
    demos: int = 2,
    queries: int = 4,
    root: Path = ROOT,
) -> dict[str, Any]:
    episode = make_episode(
        seed,
        output_mode=output_mode,
        demos=demos,
        queries=queries,
        root=root,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program"],
    }
