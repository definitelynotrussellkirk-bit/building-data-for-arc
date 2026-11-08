#!/usr/bin/env python3
"""Proposed episode-level run-axis parameter for ARC task 0a9ee3cbb232.

The canonical/default setting counts maximal horizontal runs of colors 3 and 2.
The proposed nearby setting counts maximal vertical runs instead.  Both settings
write the counts into the same 2x3 row-major tally (3 cells first, then 2 cells,
with natural six-cell truncation).  The setting is chosen once per episode and
never exposed in the public challenge.

This module is task-local prototype evidence.  It does not alter the selected
canonical Racket authority or production generator interface.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

TASK_ID = "0a9ee3cbb232"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "run_axis"
ALLOWED_AXES = ("horizontal", "vertical")
DEFAULT_AXIS = "horizontal"

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
ROOT = HERE.parents[3]


def _sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _validate_axis(axis: Any) -> str:
    if type(axis) is not str:
        raise TypeError("run_axis must be an exact string")
    if axis not in ALLOWED_AXES:
        raise ValueError(f"run_axis must be one of {ALLOWED_AXES}, got {axis!r}")
    return axis


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool or coercible)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def canonical_record() -> dict[str, Any]:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical task {TASK_ID} is absent from {path}")


def canonical_program() -> str:
    source = canonical_record().get("program_solution")
    if not isinstance(source, str) or not source.strip().startswith("(rule!"):
        raise RuntimeError("canonical program_solution is missing or malformed")
    return source


_VERTICAL_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((count-segments (lambda (color)
                                    (let loop-c
                                         ((c 0) (count 0))
                                         (cond
                                           ((>= c w) count)
                                           (else (let loop-r
                                                      ((r 0) (in-seg? #f) (cnt count))
                                                      (cond
                                                        ((>= r h) (loop-c (+ c 1) cnt))
                                                        ((= (at g r c) color) (cond
                                                            ((not in-seg?) (loop-r (+ r 1)
                                                                      #t
                                                                      (+ cnt 1)))
                                                            (else (loop-r (+ r 1)
                                                                          #t
                                                                          cnt))))
                                                        (else (loop-r (+ r 1) #f cnt)))))))))
                  (n3 (count-segments 3))
                  (n2 (count-segments 2)))
             (build-grid 2
                         3
                         (r c)
                         (let ((i (+ (* r 3) c)))
                           (cond ((< i n3) 3) ((< i (+ n3 n2)) 2) (else 0))))))))"""


def program_for(run_axis: Any) -> str:
    axis = _validate_axis(run_axis)
    return canonical_program() if axis == "horizontal" else _VERTICAL_PROGRAM


def program_sha256(run_axis: Any) -> str:
    return _sha256(program_for(run_axis))


def choose_axis(seed: Any) -> str:
    seed = _validate_seed(seed)
    return ALLOWED_AXES[seed % len(ALLOWED_AXES)]


def other_axis(run_axis: Any) -> str:
    return "vertical" if _validate_axis(run_axis) == "horizontal" else "horizontal"


def input_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty rectangular list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact ARC colors 0..9"]
    palette = {value for row in grid for value in row}
    errors = []
    if 2 not in palette or 3 not in palette:
        errors.append("both counted colors 2 and 3 must occur")
    return errors


def run_counts(grid: list[list[int]], run_axis: Any) -> tuple[int, int]:
    axis = _validate_axis(run_axis)
    errors = input_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    lines = grid if axis == "horizontal" else [list(column) for column in zip(*grid)]
    counts = []
    for color in (3, 2):
        total = 0
        for line in lines:
            active = False
            for value in line:
                if value == color:
                    if not active:
                        total += 1
                    active = True
                else:
                    active = False
        counts.append(total)
    return counts[0], counts[1]


def tally(n3: int, n2: int) -> list[list[int]]:
    output = [[0] * 3 for _ in range(2)]
    for index in range(6):
        if index < n3:
            output[index // 3][index % 3] = 3
        elif index < n3 + n2:
            output[index // 3][index % 3] = 2
    return output


def apply_python(grid: list[list[int]], run_axis: Any) -> list[list[int]]:
    """Independent authoring mirror; retained labels are also executed in Racket."""
    return tally(*run_counts(grid, run_axis))


def _load_selected_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("parametric_selected_generator", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load selected generator from {path}")
    spec.loader.exec_module(module)
    return module, path


def build_episode(
    seed: Any,
    *,
    run_axis: str | None = None,
    n_train: int = 3,
    n_test: int = 1,
) -> dict[str, Any]:
    """Build one complete episode with one fixed hidden run-axis setting."""
    seed = _validate_seed(seed)
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive exact integer")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive exact integer")
    selected = choose_axis(seed) if run_axis is None else _validate_axis(run_axis)
    alternative = other_axis(selected)
    generator, generator_path = _load_selected_generator()

    pairs: list[dict[str, Any]] = []
    bands = ("easy", "medium", "hard")
    for pair_index in range(n_train + n_test):
        # The selected canonical sampler already preserves the original object
        # roles and makes horizontal/vertical counts disagree on its structured
        # runs.  Keep a bounded deterministic search as an explicit safeguard.
        for attempt in range(64):
            draw_seed = seed * 1009 + pair_index * 131 + attempt
            sample_index = pair_index * 2 + attempt
            difficulty = bands[pair_index % len(bands)]
            grid = generator.generate(
                draw_seed, sample_index, difficulty=difficulty
            )
            if apply_python(grid, selected) != apply_python(grid, alternative):
                break
        else:
            raise RuntimeError(
                f"could not materialize an axis-distinguishing pair {pair_index}"
            )
        pairs.append(
            {
                "input": grid,
                "output": apply_python(grid, selected),
                "sampling": {
                    "pair_index": pair_index,
                    "draw_seed": draw_seed,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "attempt": attempt,
                    "horizontal_counts": list(run_counts(grid, "horizontal")),
                    "vertical_counts": list(run_counts(grid, "vertical")),
                },
            }
        )

    generator_sha256 = _sha256(generator_path.read_bytes())
    return {
        "schema": "0a9ee3cbb232-parametric-run-axis-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter": {PARAMETER_NAME: selected},
        "program_sha256": program_sha256(selected),
        "generator_sha256": generator_sha256,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a challenge with demonstrations but no hidden rule/query labels."""
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def episode_errors(episode: Any) -> list[str]:
    if not isinstance(episode, dict):
        return ["episode must be a dictionary"]
    try:
        axis = _validate_axis(episode["parameter"][PARAMETER_NAME])
    except (KeyError, TypeError, ValueError) as exc:
        return [f"invalid parameter: {exc}"]
    errors = []
    alternative = other_axis(axis)
    for split in ("train", "test"):
        pairs = episode.get(split)
        if not isinstance(pairs, list) or not pairs:
            errors.append(f"{split} must contain at least one pair")
            continue
        for index, pair in enumerate(pairs):
            try:
                expected = apply_python(pair["input"], axis)
                rival = apply_python(pair["input"], alternative)
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"{split}[{index}] invalid: {exc}")
                continue
            if pair.get("output") != expected:
                errors.append(f"{split}[{index}] output disagrees with selected setting")
            if expected == rival:
                errors.append(f"{split}[{index}] does not distinguish the two settings")
    return errors
