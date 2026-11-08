"""Shared canonical ARC pair loading and grid normalization helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANONICAL = ROOT / "data" / "canonical" / "puzzles.jsonl"


def normalize_pair_container(raw: Any) -> list[dict[str, Any]]:
    """Return a uniform pair list from singleton-dict or list containers."""
    if raw is None:
        return []
    candidates = [raw] if isinstance(raw, dict) else raw
    if not isinstance(candidates, list):
        return []
    return [pair for pair in candidates if isinstance(pair, dict)]


def normalize_grid(grid: Any) -> list[list[int]] | None:
    """Normalize nested integer grids and canonical digit-string rows."""
    if (
        isinstance(grid, list)
        and grid
        and all(isinstance(row, list) for row in grid)
    ):
        if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
            return None
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 9
            for row in grid
            for value in row
        ):
            return None
        return [list(row) for row in grid]
    if (
        isinstance(grid, list)
        and grid
        and all(isinstance(row, str) and row for row in grid)
    ):
        if any(len(row) != len(grid[0]) for row in grid):
            return None
        try:
            return [[int(value) for value in row] for row in grid]
        except ValueError:
            return None
    return None


def iter_task_rows(
    task_id: str,
    canonical: Path = DEFAULT_CANONICAL,
) -> Iterator[dict[str, Any]]:
    """Yield every canonical source row for ``task_id`` in file order."""
    with canonical.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{canonical}:{line_number}: expected object")
            if row.get("task_id") == task_id:
                yield row


def load_task_pairs(
    task_id: str,
    canonical: Path = DEFAULT_CANONICAL,
    *,
    splits: tuple[str, ...] = ("train", "test"),
) -> list[dict[str, Any]]:
    """Load normalized canonical pairs across all rows for one task.

    Both the historical singleton-dict ``test`` form and the usual pair list
    are accepted. Invalid grids are rejected loudly instead of disappearing
    from a review gate.
    """
    pairs: list[dict[str, Any]] = []
    for row_index, row in enumerate(iter_task_rows(task_id, canonical)):
        for split in splits:
            for pair_index, pair in enumerate(
                normalize_pair_container(row.get(split))
            ):
                source = normalize_grid(pair.get("input"))
                target = (
                    normalize_grid(pair.get("output"))
                    if pair.get("output") is not None
                    else None
                )
                if source is None:
                    raise ValueError(
                        f"{task_id} row {row_index} {split}[{pair_index}] "
                        "has an invalid input grid"
                    )
                if pair.get("output") is not None and target is None:
                    raise ValueError(
                        f"{task_id} row {row_index} {split}[{pair_index}] "
                        "has an invalid output grid"
                    )
                pairs.append(
                    {
                        "input": source,
                        "output": target,
                        "split": split,
                        "row_index": row_index,
                        "pair_index": pair_index,
                    }
                )
    return pairs
