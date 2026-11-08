"""Task-local episode-level tie-policy prototype for ARC task ec9cf2c80d58.

The production generator and canonical authority remain pinned to
``tie_policy='column'``: row/column extent ties erase the matching column.
The sole proposed alternative is ``tie_policy='row'``, which erases the
matching row on a tie.  The selected policy is fixed for an entire episode.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "ec9cf2c80d58"
PROTOTYPE_VERSION = "1.0.0"
STATUS = "proposed task-local prototype; not production-approved"
ROOT = find_root(__file__)
PARAMETERS = {
    "tie_policy": {
        "allowed": ("column", "row"),
        "default": "column",
        "selected_once_per_episode": True,
    }
}
_AUTO = object()
_COLUMN_TIE_ANCHOR = "(if (>= row-ext col-ext)"
_ROW_TIE_ANCHOR = "(if (> row-ext col-ext)"
_DIFFICULTIES = ("easy", "medium", "hard")


def _validate_policy(tie_policy: str) -> None:
    if type(tie_policy) is not str or tie_policy not in PARAMETERS["tie_policy"]["allowed"]:
        raise ValueError("tie_policy must be exactly 'column' or 'row'")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be a Python int")


def canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    """Return the unique canonical ledger authority for this task."""
    matches = []
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                matches.append(record)
    if not matches:
        raise ValueError(f"missing canonical record for {TASK_ID}")
    programs = {record.get("program_solution") for record in matches}
    if len(programs) != 1:
        raise ValueError(f"canonical variants disagree on program authority for {TASK_ID}")
    return next(
        (record for record in matches if record.get("content_hash") == TASK_ID),
        matches[0],
    )


def racket_program(tie_policy: str = "column", *, root: Path | str = ROOT) -> str:
    """Materialize the exact Racket program for one declared setting."""
    _validate_policy(tie_policy)
    canonical = canonical_record(root=root)["program_solution"]
    if canonical.count(_COLUMN_TIE_ANCHOR) != 1:
        raise ValueError("canonical tie anchor changed; prototype requires review")
    if tie_policy == "column":
        return canonical
    return canonical.replace(_COLUMN_TIE_ANCHOR, _ROW_TIE_ANCHOR, 1)


def choose_tie_policy(seed: int) -> str:
    """Choose one hidden policy deterministically, exactly once per episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:tie_policy".encode()
    ).digest()
    allowed = PARAMETERS["tie_policy"]["allowed"]
    return allowed[digest[0] % len(allowed)]


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty rectangular list of lists")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid must be a nonempty rectangular list of lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int for row in grid for value in row):
        raise ValueError("grid cells must be Python integers")
    return len(grid), width


def _neighbor(grid: list[list[int]], row: int, col: int) -> int | None:
    height, width = len(grid), len(grid[0])
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = row + dr, col + dc
        if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] != 0:
            return grid[nr][nc]
    return None


def apply_python(grid: list[list[int]], tie_policy: str = "column") -> list[list[int]]:
    """Independent mirror of the two-setting rule family.

    All neighbor and extent decisions read the original grid.  Only the tie
    comparator varies: ``>=`` for the canonical column-on-tie policy and ``>``
    for the proposed row-on-tie policy.
    """
    _validate_policy(tie_policy)
    height, width = _validate_grid(grid)
    output = [row[:] for row in grid]
    holes = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
    ]
    for row, col in holes:
        color = _neighbor(grid, row, col)
        if color is None:
            continue
        row_extent = sum(grid[row][c] in (0, color) for c in range(width))
        col_extent = sum(grid[r][col] in (0, color) for r in range(height))
        clear_column = (
            row_extent >= col_extent
            if tie_policy == "column"
            else row_extent > col_extent
        )
        cells = (
            ((r, col) for r in range(height))
            if clear_column
            else ((row, c) for c in range(width))
        )
        for r, c in cells:
            if grid[r][c] in (0, color):
                output[r][c] = 0
    return output


def _episode_specs(seed: int, count: int) -> tuple[tuple[int, int, str], ...]:
    """Return distinct generated teaching slots for one episode."""
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:episode_inputs".encode()
    ).digest()
    generator_seed = int.from_bytes(digest[:8], "big") % (2**31)
    offset = int.from_bytes(digest[8:16], "big") % 64
    difficulty_offset = digest[16] % len(_DIFFICULTIES)
    return tuple(
        (
            generator_seed,
            2 * ((offset + index) % 64) + 1,
            _DIFFICULTIES[(difficulty_offset + index) % len(_DIFFICULTIES)],
        )
        for index in range(count)
    )


def generate_episode(
    seed: int,
    *,
    tie_policy: str | object = _AUTO,
    root: Path | str = ROOT,
    train_count: int = 3,
    query_count: int = 1,
) -> dict[str, Any]:
    """Build one complete private episode with one fixed hidden policy."""
    _validate_seed(seed)
    if tie_policy is _AUTO:
        selected = choose_tie_policy(seed)
    else:
        _validate_policy(tie_policy)
        selected = tie_policy
    if type(train_count) is not int or train_count < 1:
        raise ValueError("train_count must be a positive integer")
    if type(query_count) is not int or query_count < 1:
        raise ValueError("query_count must be a positive integer")

    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    rows = []
    opposite = "row" if selected == "column" else "column"
    for generator_seed, sample_index, difficulty in _episode_specs(
        seed, train_count + query_count
    ):
        grid = generator.generate(
            generator_seed,
            sample_index,
            difficulty=difficulty,
        )
        if generator.schedule_profile(generator_seed, sample_index, difficulty) != "teaching":
            raise AssertionError("prototype input schedule lost its teaching slot")
        if generator.self_check(grid):
            raise AssertionError("prototype input escaped the production grammar")
        output = apply_python(grid, selected)
        if apply_python(grid, opposite) == output:
            raise AssertionError("prototype emitted a non-distinguishing tie witness")
        rows.append({
            "input": grid,
            "output": output,
            "generator_seed": generator_seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
        })

    return {
        "schema": "ec9cf2c80d58-tie-policy-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter_draw_count": 1,
        "parameter": {"tie_policy": selected},
        "program": racket_program(selected, root=root),
        "train": rows[:train_count],
        "test": rows[train_count:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Mask the setting, source metadata, program, and all query labels."""
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
