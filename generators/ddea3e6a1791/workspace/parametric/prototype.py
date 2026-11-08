"""Proposed episode-level background-color parameter for ddea3e6a1791.

This module is intentionally separate from the selected canonical execution
path.  The transformation remains "crop to the tight bounding box of all
foreground cells", while ``background_color`` is chosen once per episode:

``0`` (canonical/default)
    Foreground means every nonzero cell.  The emitted program is byte-for-byte
    the selected canonical Racket source.

``9`` (proposed alternative)
    Foreground means every cell whose value is not 9.  Inputs use 9 as their
    canvas color, including possible color-0 foreground cells.

Every retained demonstration distinguishes the two settings: applying the
wrong background treats the full canvas as foreground and returns the full
input instead of the compact crop.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "ddea3e6a1791"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "background_color"
ALLOWED_VALUES = (0, 9)
DEFAULT_VALUE = 0

CANONICAL_PROGRAM = """(rule! (let ((dummy 0)) (define (nonzero-cells grid) (filter (lambda (p) (not (= (at grid (first p) (second p)) 0))) (grid-positions grid))) (define (crop-nonzero grid) (let ((cells (nonzero-cells grid))) (if (empty? cells) (list (list 0)) (let* ((bb (bbox-of-cells cells))) (subgrid grid (first bb) (second bb) (third bb) (fourth bb)))))) (crop-nonzero g)))"""

BACKGROUND_9_PROGRAM = """(rule! (let ((background 9)) (define (foreground-cells grid) (filter (lambda (p) (not (= (at grid (first p) (second p)) background))) (grid-positions grid))) (define (crop-foreground grid) (let ((cells (foreground-cells grid))) (if (empty? cells) (list (list background)) (let* ((bb (bbox-of-cells cells))) (subgrid grid (first bb) (second bb) (third bb) (fourth bb)))))) (crop-foreground g)))"""

_PROGRAMS = {
    0: CANONICAL_PROGRAM,
    9: BACKGROUND_9_PROGRAM,
}
_BANDS = ("easy", "medium", "hard", None)


def _validate_background(value: Any) -> int:
    if type(value) is not int or value not in ALLOWED_VALUES:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_VALUES} as an exact integer, "
            f"found {value!r}"
        )
    return value


def choose_value(seed: int) -> int:
    """Choose one hidden setting deterministically, once for an episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool or a coercible value)")
    return ALLOWED_VALUES[seed % len(ALLOWED_VALUES)]


def other_value(value: int) -> int:
    value = _validate_background(value)
    return 9 if value == 0 else 0


def program_for(value: int) -> str:
    return _PROGRAMS[_validate_background(value)]


def apply_python(grid: list[list[int]], background_color: int) -> list[list[int]]:
    """Independent Python mirror used only for prototype authoring checks."""
    background = _validate_background(background_color)
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid values must be exact ARC colors 0..9")

    active = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != background
    ]
    if not active:
        return [[background]]
    row0 = min(row for row, _ in active)
    row1 = max(row for row, _ in active)
    col0 = min(col for _, col in active)
    col1 = max(col for _, col in active)
    return [values[col0 : col1 + 1] for values in grid[row0 : row1 + 1]]


def _with_background(grid: list[list[int]], background_color: int) -> list[list[int]]:
    """Map a canonical zero-background input into the selected color role.

    For background 9, swapping colors 0 and 9 preserves every shape while
    allowing 0 to act as an ordinary foreground color when it was present.
    """
    background = _validate_background(background_color)
    if background == 0:
        return [row[:] for row in grid]
    return [
        [9 if value == 0 else 0 if value == 9 else value for value in row]
        for row in grid
    ]


def build_episode(
    seed: int,
    *,
    background_color: int | None = None,
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
    selected = choose_value(seed) if background_color is None else _validate_background(background_color)

    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    pairs: list[dict[str, Any]] = []
    for pair_index in range(n_train + n_test):
        difficulty = _BANDS[pair_index % len(_BANDS)]
        canonical_input = generator.generate(seed, pair_index, difficulty=difficulty)
        grid = _with_background(canonical_input, selected)
        pairs.append(
            {
                "input": grid,
                "output": apply_python(grid, selected),
                "sampling": {
                    "seed": seed,
                    "sample_index": pair_index,
                    "difficulty": difficulty,
                },
            }
        )

    return {
        "schema": "ddea3e6a1791-parametric-episode-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "parameter": {PARAMETER_NAME: selected},
        "program": program_for(selected),
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "input_constraints": {
            "canvas_color": selected,
            "foreground_definition": f"cell value != {selected}",
            "wrong_setting_returns_full_canvas": True,
        },
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }


def episode_errors(episode: Any) -> list[str]:
    """Check episode constancy, labels, and declared-setting identifiability."""
    if not isinstance(episode, dict):
        return ["episode must be a mapping"]
    parameter = episode.get("parameter")
    if not isinstance(parameter, dict) or PARAMETER_NAME not in parameter:
        return [f"episode must declare parameter {PARAMETER_NAME!r}"]
    try:
        selected = _validate_background(parameter[PARAMETER_NAME])
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
    alternative = other_value(selected)
    distinguishing_demos = 0
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                errors.append(f"{split_name}[{index}] must contain input and output")
                continue
            try:
                expected = apply_python(pair["input"], selected)
                rival = apply_python(pair["input"], alternative)
            except (TypeError, ValueError) as exc:
                errors.append(f"{split_name}[{index}] invalid: {exc}")
                continue
            if pair["output"] != expected:
                errors.append(f"{split_name}[{index}] output disagrees with selected setting")
            if split_name == "train" and rival != expected:
                distinguishing_demos += 1
    if distinguishing_demos != len(train):
        errors.append(
            "every training demonstration must distinguish the alternative setting"
        )
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden parameter, source program, and query answers."""
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
