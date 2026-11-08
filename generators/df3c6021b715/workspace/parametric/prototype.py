#!/usr/bin/env python3
"""Proposed episode-level partition-axis parameter for df3c6021b715.

This module is deliberately separate from the selected canonical execution
path.  The hidden ``partition_axis`` is chosen once per episode:

``horizontal`` (canonical/default)
    Sort the dots by row.  The upper and lower dots seed rectangular frames in
    the upper and lower halves of the canvas.

``vertical`` (proposed alternative)
    Sort the dots by column.  The left and right dots seed rectangular frames
    in the left and right halves of the canvas.

Inputs are constructed with one dot in each horizontal half *and* one dot in
each vertical half, so the same input is lawful under both settings.  Every
retained demonstration is required to distinguish the two executed rules.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

TASK_ID = "df3c6021b715"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "partition_axis"
ALLOWED_AXES = ("horizontal", "vertical")
DEFAULT_AXIS = "horizontal"

CANONICAL_HORIZONTAL_PROGRAM = '(rule! (lambda (g)\n         (let* ((h (rows g))\n                (w (cols g)))\n           (let* ((mid (/ h 2))\n                  (dots (filter (lambda (p) (!= (at g (fst p) (snd p)) 0))\n                                (flatmap (lambda (r)\n                                           (map (lambda (c) (cons r c)) (range 0 w)))\n                                         (range 0 h))))\n                  (d1 (pick-min dots fst))\n                  (d2 (second (sort-by dots (lambda (p) (fst p)))))\n                  (c1 (at g (fst d1) (snd d1)))\n                  (c2 (at g (fst d2) (snd d2)))\n                  (r1 (fst d1))\n                  (r2 (fst d2)))\n             (cellmap g\n                      (r c v)\n                      (if (< r mid)\n                          (cond\n                            ((= r r1) c1)\n                            ((zero? r) c1)\n                            ((or (zero? c) (= c (- w 1))) c1)\n                            (else 0))\n                          (cond\n                            ((= r r2) c2)\n                            ((= r (- h 1)) c2)\n                            ((or (zero? c) (= c (- w 1))) c2)\n                            (else 0))))))))'

VERTICAL_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((mid (/ w 2))
                  (dots (filter (lambda (p) (!= (at g (fst p) (snd p)) 0))
                                (flatmap (lambda (r)
                                           (map (lambda (c) (cons r c)) (range 0 w)))
                                         (range 0 h))))
                  (d1 (pick-min dots snd))
                  (d2 (second (sort-by dots (lambda (p) (snd p)))))
                  (c1 (at g (fst d1) (snd d1)))
                  (c2 (at g (fst d2) (snd d2)))
                  (x1 (snd d1))
                  (x2 (snd d2)))
             (cellmap g
                      (r c v)
                      (if (< c mid)
                          (cond
                            ((= c x1) c1)
                            ((zero? c) c1)
                            ((or (zero? r) (= r (- h 1))) c1)
                            (else 0))
                          (cond
                            ((= c x2) c2)
                            ((= c (- w 1)) c2)
                            ((or (zero? r) (= r (- h 1))) c2)
                            (else 0))))))))"""

_PROGRAMS = {
    "horizontal": CANONICAL_HORIZONTAL_PROGRAM,
    "vertical": VERTICAL_PROGRAM,
}


def _validate_axis(axis: Any) -> str:
    if type(axis) is not str or axis not in ALLOWED_AXES:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_AXES} as an exact string, "
            f"found {axis!r}"
        )
    return axis


def choose_axis(seed: int) -> str:
    """Choose one hidden setting deterministically, once for an episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool or a coercible value)")
    return ALLOWED_AXES[seed % len(ALLOWED_AXES)]


def other_axis(axis: str) -> str:
    return "vertical" if _validate_axis(axis) == "horizontal" else "horizontal"


def program_for(axis: str) -> str:
    return _PROGRAMS[_validate_axis(axis)]


def ordered_dots(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    """Return the two nonzero cells sorted by row, then column."""
    return sorted(
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    )


def input_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty rectangular list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty rectangular list"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be exact ARC colors 0..9"]

    height = len(grid)
    errors: list[str] = []
    if not 8 <= height <= 18 or not 8 <= width <= 18:
        errors.append("grid dimensions must each be in 8..18")
    dots = ordered_dots(grid)
    if len(dots) != 2:
        errors.append(f"expected exactly two nonzero dots, found {len(dots)}")
        return errors
    if dots[0][2] == dots[1][2]:
        errors.append("the two dots must have distinct colors")
    if any(row in (0, height - 1) or col in (0, width - 1) for row, col, _ in dots):
        errors.append("both dots must be interior")
    row_mid = height // 2
    col_mid = width // 2
    if sum(row < row_mid for row, _, _ in dots) != 1:
        errors.append("expected one dot in each horizontal half")
    if sum(col < col_mid for _, col, _ in dots) != 1:
        errors.append("expected one dot in each vertical half")
    return errors


def _render_horizontal(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    dots = ordered_dots(grid)
    upper = min(dots, key=lambda dot: dot[0])
    lower = max(dots, key=lambda dot: dot[0])
    row_mid = height // 2
    output = [[0] * width for _ in range(height)]
    for row in range(height):
        color = upper[2] if row < row_mid else lower[2]
        marker_row = upper[0] if row < row_mid else lower[0]
        outer_row = 0 if row < row_mid else height - 1
        for col in range(width):
            if row in (marker_row, outer_row) or col in (0, width - 1):
                output[row][col] = color
    return output


def _render_vertical(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    dots = ordered_dots(grid)
    left = min(dots, key=lambda dot: dot[1])
    right = max(dots, key=lambda dot: dot[1])
    col_mid = width // 2
    output = [[0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            color = left[2] if col < col_mid else right[2]
            marker_col = left[1] if col < col_mid else right[1]
            outer_col = 0 if col < col_mid else width - 1
            if col in (marker_col, outer_col) or row in (0, height - 1):
                output[row][col] = color
    return output


def apply_python(grid: list[list[int]], partition_axis: str) -> list[list[int]]:
    """Independent Python mirror used only for prototype authoring checks."""
    axis = _validate_axis(partition_axis)
    errors = input_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if axis == "horizontal":
        return _render_horizontal(grid)
    return _render_vertical(grid)


def _episode_input(seed: int, pair_index: int) -> tuple[list[list[int]], dict[str, Any]]:
    rng = random.Random(seed * 1_000_003 + pair_index * 97_409 + 0xD3F3C6)
    height = rng.choice((8, 9, 10, 11, 12, 13, 14))
    width = rng.choice((8, 9, 10, 11, 12, 13, 14))
    upper_row = rng.randint(1, height // 2 - 1)
    lower_row = rng.randint(height // 2, height - 2)
    left_col = rng.randint(1, width // 2 - 1)
    right_col = rng.randint(width // 2, width - 2)
    upper_color, lower_color = rng.sample(range(1, 10), 2)

    # Alternate diagonals so row order and column order do not always assign the
    # same color to the first region.
    if (seed + pair_index) % 2 == 0:
        upper_col, lower_col = left_col, right_col
        diagonal = "upper_left_to_lower_right"
    else:
        upper_col, lower_col = right_col, left_col
        diagonal = "upper_right_to_lower_left"

    grid = [[0] * width for _ in range(height)]
    grid[upper_row][upper_col] = upper_color
    grid[lower_row][lower_col] = lower_color
    sampling = {
        "seed": seed,
        "pair_index": pair_index,
        "height": height,
        "width": width,
        "diagonal": diagonal,
        "upper_dot": [upper_row, upper_col, upper_color],
        "lower_dot": [lower_row, lower_col, lower_color],
    }
    return grid, sampling


def build_episode(
    seed: int,
    *,
    partition_axis: str | None = None,
    n_train: int = 3,
    n_test: int = 1,
) -> dict[str, Any]:
    """Build one complete episode with one fixed hidden rule setting."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool or a coercible value)")
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive integer")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive integer")
    selected = choose_axis(seed) if partition_axis is None else _validate_axis(partition_axis)

    pairs: list[dict[str, Any]] = []
    for pair_index in range(n_train + n_test):
        grid, sampling = _episode_input(seed, pair_index)
        pairs.append(
            {
                "input": grid,
                "output": apply_python(grid, selected),
                "sampling": sampling,
            }
        )

    task_home = Path(__file__).resolve().parents[2]
    generator_path = task_home / "generator.py"
    return {
        "schema": "df3c6021b715-parametric-axis-episode-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "parameter": {PARAMETER_NAME: selected},
        "program": program_for(selected),
        "generator_source": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "input_constraints": {
            "exact_nonzero_dots": 2,
            "distinct_dot_colors": True,
            "one_dot_per_horizontal_half": True,
            "one_dot_per_vertical_half": True,
        },
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }


def episode_errors(episode: Any) -> list[str]:
    """Check setting constancy, labels, and declared-axis identifiability."""
    if not isinstance(episode, dict):
        return ["episode must be a mapping"]
    parameter = episode.get("parameter")
    if not isinstance(parameter, dict) or PARAMETER_NAME not in parameter:
        return [f"episode must declare parameter {PARAMETER_NAME!r}"]
    try:
        selected = _validate_axis(parameter[PARAMETER_NAME])
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if episode.get("program") != program_for(selected):
        return ["episode program does not match its selected parameter"]

    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not train:
        return ["episode needs at least one training pair"]
    if not isinstance(test, list) or not test:
        return ["episode needs at least one test pair"]

    errors: list[str] = []
    alternative = other_axis(selected)
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                errors.append(f"{split_name}[{index}] must contain input and output")
                continue
            visible_errors = input_errors(pair["input"])
            if visible_errors:
                errors.append(f"{split_name}[{index}] invalid: {'; '.join(visible_errors)}")
                continue
            expected = apply_python(pair["input"], selected)
            rival = apply_python(pair["input"], alternative)
            if pair["output"] != expected:
                errors.append(f"{split_name}[{index}] output disagrees with selected setting")
            if split_name == "train" and rival == expected:
                errors.append(f"{split_name}[{index}] does not distinguish the alternative axis")
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden parameter, source program, metadata, and query answers."""
    errors = episode_errors(episode)
    if errors:
        raise ValueError("invalid episode: " + "; ".join(errors))
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }
