#!/usr/bin/env python3
"""Proposed episode-level synchronous-pass budget for ARC task 135219aecdb4.

The selected production task remains the canonical three-pass rule.  This
separate prototype chooses one exact pass count for a whole episode and uses
only inputs whose first, second, and third synchronous states are all distinct,
so demonstrations identify the hidden setting before any query is answered.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_id,
)

TASK_ID = "135219aecdb4"
ALLOWED_PASS_COUNTS = (1, 2, 3)
DEFAULT_PASS_COUNT = 3
PARAMETERS = {
    "pass_count": {
        "allowed": ALLOWED_PASS_COUNTS,
        "default": DEFAULT_PASS_COUNT,
        "selected_once_per_episode": True,
    }
}
MAX_AUTHORING_COUNT = 64
_CANONICAL_TAIL = "(fill (fill (fill g)))"
_SYMBOLS = (1, 2, 3, 4)


def _root(root: Path | str | None = None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


def canonical_record(*, root: Path | str | None = None) -> dict[str, Any]:
    """Load the exact source-bound canonical record for this task."""
    with canonical_path(_root(root)).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise FileNotFoundError(f"missing canonical row {TASK_ID}")


def _validate_pass_count(pass_count: int) -> int:
    if type(pass_count) is not int or pass_count not in ALLOWED_PASS_COUNTS:
        raise ValueError(
            f"pass_count must be one of the exact integers {ALLOWED_PASS_COUNTS}, "
            f"got {pass_count!r}"
        )
    return pass_count


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    return seed


def _validate_count(name: str, value: int) -> int:
    if type(value) is not int or not 1 <= value <= MAX_AUTHORING_COUNT:
        raise ValueError(
            f"{name} must be an exact integer in 1..{MAX_AUTHORING_COUNT}, "
            f"got {value!r}"
        )
    return value


def racket_program(
    pass_count: int = DEFAULT_PASS_COUNT,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize exact canonical Racket or its one-site pass-depth variant."""
    count = _validate_pass_count(pass_count)
    canonical = canonical_record(root=root)["program_solution"]
    if canonical.count(_CANONICAL_TAIL) != 1:
        raise ValueError("canonical rule no longer has one recognized three-pass tail")
    if count == DEFAULT_PASS_COUNT:
        return canonical
    replacement = "(fill g)" if count == 1 else "(fill (fill g))"
    return canonical.replace(_CANONICAL_TAIL, replacement, 1)


def _fill_pass(grid: list[list[int]]) -> list[list[int]]:
    """One synchronous row/column single-candidate pass."""
    out = [list(row) for row in grid]
    for row in range(4):
        for col in range(4):
            if grid[row][col] != 0:
                continue
            row_values = {
                grid[row][other_col]
                for other_col in range(4)
                if grid[row][other_col] != 0
            }
            col_values = {
                grid[other_row][col]
                for other_row in range(4)
                if grid[other_row][col] != 0
            }
            candidates = [
                value
                for value in _SYMBOLS
                if value not in row_values and value not in col_values
            ]
            if len(candidates) == 1:
                out[row][col] = candidates[0]
    return out


def apply_python(grid: list[list[int]], pass_count: int = DEFAULT_PASS_COUNT):
    """Independent mirror for parity checks; retained labels come from Racket."""
    count = _validate_pass_count(pass_count)
    out = [list(row) for row in grid]
    for _ in range(count):
        out = _fill_pass(out)
    return out


def select_pass_count(seed: int) -> int:
    """Select one setting deterministically, exactly once per episode."""
    seed = _validate_seed(seed)
    return ALLOWED_PASS_COUNTS[seed % len(ALLOWED_PASS_COUNTS)]


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"), ensure_ascii=False)


def _candidate_stream(
    seed: int,
    *,
    root: Path,
    max_draws: int,
) -> Any:
    """Yield lawful true-three-pass inputs within a bounded number of draws."""
    if type(max_draws) is not int or max_draws < 1:
        raise ValueError("max_draws must be a positive exact integer")
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    for attempt in range(max_draws):
        generator_seed = (
            (seed + 1) * 1_000_003 + attempt * 104_729 + 13_521_901
        ) & 0x7FFFFFFF
        sample_index = 3 * (seed * 257 + attempt) + 1
        n_erased = 5 + (attempt % 3)
        grid = generator.generate(
            generator_seed,
            sample_index,
            n_erased=n_erased,
        )
        facts = generator.semantic_observables(grid)
        if not facts.get("errors") and facts.get("passes_to_complete") == 3:
            yield {
                "input": grid,
                "generator_seed": generator_seed,
                "sample_index": sample_index,
                "n_erased": n_erased,
            }


def generate_episode(
    seed: int,
    *,
    pass_count: int | None = None,
    demo_count: int = 3,
    query_count: int = 4,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Build one deterministic fixed-setting episode with independent counts."""
    seed = _validate_seed(seed)
    demo_count = _validate_count("demo_count", demo_count)
    query_count = _validate_count("query_count", query_count)
    selected = select_pass_count(seed) if pass_count is None else _validate_pass_count(pass_count)
    source_root = _root(root)
    needed = demo_count + query_count
    max_draws = max(256, needed * 64)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for candidate in _candidate_stream(
        seed, root=source_root, max_draws=max_draws
    ):
        key = _grid_key(candidate["input"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                **candidate,
                "output": apply_python(candidate["input"], selected),
            }
        )
        if len(rows) == needed:
            break
    if len(rows) != needed:
        raise RuntimeError(
            f"could not sample {needed} distinct true-three-pass inputs in "
            f"{max_draws} draws"
        )

    return {
        "schema": "135219aecdb4-pass-budget-episode-v1",
        "status": "proposed_not_selected",
        "task_id": TASK_ID,
        "seed": seed,
        "parameter_draw_count": 1,
        "parameter": {"pass_count": selected},
        "program": racket_program(selected, root=source_root),
        "train": rows[:demo_count],
        "test": rows[demo_count:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only visible demonstrations and unlabeled query inputs."""
    return {
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def public_filename(episode: dict[str, Any]) -> str:
    """Opaque content name based only on exactly visible public bytes."""
    return f"challenge-{public_challenge_id(public_challenge(episode))}.json"
