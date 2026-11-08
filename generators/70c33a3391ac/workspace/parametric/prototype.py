"""Proposed episode-level occurrence-threshold variant for task 70c33a3391ac.

The selected production generator and canonical authority stay fixed.  This
prototype preserves the original operations—extract exact colored component
crops, count equal crops, and return the first qualifying crop in the canonical
scan order—while choosing one bounded minimum occurrence count once per episode.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "70c33a3391ac"
PROTOTYPE_VERSION = "1.0.0"
STATUS = "proposed task-local prototype; not selected or production-approved"
ROOT = find_root(__file__)
MINIMUM_OCCURRENCES = (2, 3)
DEFAULT_MINIMUM_OCCURRENCES = 2
PARAMETERS = {
    "minimum_occurrences": {
        "allowed": MINIMUM_OCCURRENCES,
        "default": DEFAULT_MINIMUM_OCCURRENCES,
        "selected_once_per_episode": True,
    }
}
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_AUTO = object()

# The final literal is the canonical count threshold: `(> count 1)` means at
# least two occurrences.  Fail closed if canonical formatting/logic changes.
_THRESHOLD_ANCHOR = """                                           obj-grids)
                                 1)"""


def _validate_minimum(value: Any) -> int:
    if type(value) is not int:
        raise TypeError("minimum_occurrences must be an integer (not bool)")
    if value not in MINIMUM_OCCURRENCES:
        raise ValueError(f"minimum_occurrences must be one of {MINIMUM_OCCURRENCES}")
    return value


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return seed


def canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    """Return the unique canonical rule row for the selected task."""
    rows: list[dict[str, Any]] = []
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if not rows:
        raise ValueError(f"missing canonical record for {TASK_ID}")
    programs = {row.get("program_solution") for row in rows}
    if len(programs) != 1:
        raise ValueError(f"canonical variants disagree for {TASK_ID}")
    return next((row for row in rows if row.get("content_hash") == TASK_ID), rows[0])


def program_for(minimum_occurrences: Any = DEFAULT_MINIMUM_OCCURRENCES, *, root: Path | str = ROOT) -> str:
    """Materialize the exact Racket rule for one bounded threshold setting."""
    minimum = _validate_minimum(minimum_occurrences)
    canonical = canonical_record(root=root)["program_solution"]
    if canonical.count(_THRESHOLD_ANCHOR) != 1:
        raise ValueError("canonical occurrence-threshold anchor changed; review required")
    if minimum == DEFAULT_MINIMUM_OCCURRENCES:
        return canonical
    replacement = _THRESHOLD_ANCHOR[:-2] + f"{minimum - 1})"
    return canonical.replace(_THRESHOLD_ANCHOR, replacement, 1)


def choose_minimum_occurrences(seed: Any) -> int:
    """Choose one hidden parameter deterministically exactly once per episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:minimum_occurrences".encode()
    ).digest()
    return MINIMUM_OCCURRENCES[digest[0] % len(MINIMUM_OCCURRENCES)]


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid values must be integer ARC colors 0..9")
    return len(grid), width


def _component_crops(grid: list[list[int]]) -> list[tuple[tuple[int, ...], ...]]:
    """Return exact crops in the canonical row-major discovery order."""
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    crops: list[tuple[tuple[int, ...], ...]] = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in _CARDINAL:
                    rr, cc = row + dr, col + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] != 0
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            top = min(row for row, _ in cells)
            bottom = max(row for row, _ in cells)
            left = min(col for _, col in cells)
            right = max(col for _, col in cells)
            crops.append(
                tuple(
                    tuple(grid[row][left : right + 1])
                    for row in range(top, bottom + 1)
                )
            )
    return crops


def apply_python(grid: list[list[int]], minimum_occurrences: Any) -> list[list[int]]:
    """Independent Python mirror of the two proposed Racket settings.

    The canonical Racket implementation conses each row-major-discovered crop,
    then scans that reversed list.  The retained grammar deliberately places
    the exactly-twice crop later than the exactly-thrice crop so threshold two
    and threshold three make different predictions on every pair.
    """
    minimum = _validate_minimum(minimum_occurrences)
    crops = _component_crops(grid)
    counts = Counter(crops)
    for crop in reversed(crops):
        if counts[crop] >= minimum:
            return [list(row) for row in crop]
    return [[0]]


def _ordered_colors(seed: int, pair_index: int) -> tuple[int, ...]:
    colors = list(range(1, 10))
    return tuple(
        sorted(
            colors,
            key=lambda color: hashlib.sha256(
                f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:{pair_index}:color:{color}".encode()
            ).digest(),
        )
    )


def _place(grid: list[list[int]], top: int, left: int, crop: tuple[tuple[int, ...], ...]) -> None:
    for dr, row in enumerate(crop):
        for dc, value in enumerate(row):
            if value:
                if grid[top + dr][left + dc] != 0:
                    raise ValueError("prototype placement collision")
                grid[top + dr][left + dc] = value


def input_for(seed: Any, pair_index: Any) -> list[list[int]]:
    """Build one lawful threshold-distinguishing component scene."""
    _validate_seed(seed)
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer")
    colors = _ordered_colors(seed, pair_index)
    a, b, c, d, e, f, g, h, _unused = colors
    pair_crop = ((a, b, b), (a, a, 0))
    triple_crop = ((c, c), (0, d), (d, d))
    unique_wide = ((e, e, 0), (e, f, f))
    unique_tall = ((g, 0), (g, h), (h, h))

    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:{pair_index}:layout".encode()
    ).digest()
    shift = digest[0] % 3
    grid = [[0] * 22 for _ in range(25)]

    # Three copies first in row-major order.
    for top, left in ((1, 1 + shift), (5, 9 - shift), (9, 16 - shift)):
        _place(grid, top, left, triple_crop)
    # Unique components prevent a pure two-class counting scene.
    _place(grid, 13, 2 + shift, unique_wide)
    _place(grid, 13, 14 - shift, unique_tall)
    # Two copies last in row-major order. Reversed canonical scan therefore
    # selects this crop at threshold 2, while threshold 3 skips it.
    _place(grid, 18, 4 + shift, pair_crop)
    _place(grid, 22, 13 - shift, pair_crop)
    return grid


def build_episode(
    seed: Any,
    *,
    minimum_occurrences: int | object = _AUTO,
    n_train: int = 3,
    n_test: int = 1,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    """Build a complete private episode with one fixed hidden rule setting."""
    _validate_seed(seed)
    if minimum_occurrences is _AUTO:
        selected = choose_minimum_occurrences(seed)
    else:
        selected = _validate_minimum(minimum_occurrences)
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive integer")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive integer")

    pairs = []
    for pair_index in range(n_train + n_test):
        grid = input_for(seed, pair_index)
        pairs.append(
            {
                "input": grid,
                "output": apply_python(grid, selected),
                "pair_index": pair_index,
            }
        )
    return {
        "schema": "70c33a3391ac-minimum-occurrences-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter_draw_count": 1,
        "parameter": {"minimum_occurrences": selected},
        "program": program_for(selected, root=root),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Mask the hidden parameter, Racket program, metadata, and query labels."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def episode_errors(episode: Any) -> list[str]:
    """Check the bounded episode contract and declared parameter rivals."""
    errors: list[str] = []
    if not isinstance(episode, dict):
        return ["episode must be a dictionary"]
    parameter = episode.get("parameter", {})
    try:
        selected = _validate_minimum(parameter.get("minimum_occurrences"))
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if episode.get("parameter_draw_count") != 1:
        errors.append("parameter must be selected exactly once per episode")
    try:
        if episode.get("program") != program_for(selected):
            errors.append("episode program does not match the selected parameter")
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not train:
        errors.append("episode needs at least one demonstration")
        train = []
    if not isinstance(test, list) or not test:
        errors.append("episode needs at least one query")
        test = []
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            try:
                outputs = {
                    candidate: apply_python(pair["input"], candidate)
                    for candidate in MINIMUM_OCCURRENCES
                }
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"{split}[{index}] invalid: {exc}")
                continue
            if pair.get("output") != outputs[selected]:
                errors.append(f"{split}[{index}] selected label mismatch")
            if split == "train" and outputs[2] == outputs[3]:
                errors.append(f"{split}[{index}] does not distinguish both settings")
    return errors
