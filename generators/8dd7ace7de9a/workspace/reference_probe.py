"""Independent probes for the 8dd7ace7de9a task-local regression suite.

This module deliberately does not import implementation helpers from generator.py.
It supplies a separately written mirror of the selected rule, canonical/authority
readers that work both in the review tree and in a staged runtime, and a loader
for an explicitly source-bound generator under test.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Iterable

TASK_ID = "8dd7ace7de9a"
RULE_HASH = "0f05e4e27969"
AUTHORITY_PATHS = (
    "shared/data/base/solutions/training/f823c43c__8dd7ace7de9a.json",
    "shared/data/base/solutions/augmented/f823c43c__429a76e684ac.json",
    "data/base/solutions/training/f823c43c__8dd7ace7de9a.json",
    "data/base/solutions/augmented/f823c43c__429a76e684ac.json",
)


def _find_up(*relative_candidates: str) -> Path:
    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        for relative in relative_candidates:
            candidate = parent / relative
            if candidate.is_file():
                return candidate
    raise FileNotFoundError(f"could not locate any of {relative_candidates!r} above {here}")


def canonical_path() -> Path:
    return _find_up(
        "shared/data/canonical/puzzles.jsonl",
        "data/canonical/puzzles.jsonl",
    )


def canonical_rows() -> list[dict]:
    rows: list[dict] = []
    with canonical_path().open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    if not rows:
        raise AssertionError(f"missing canonical row for {TASK_ID}")
    return rows


def canonical_pairs(*, unique: bool = True) -> list[dict]:
    pairs: list[dict] = []
    seen: set[str] = set()
    for row in canonical_rows():
        for split in ("train", "test"):
            raw = row.get(split) or []
            if isinstance(raw, dict):
                raw = [raw]
            for pair in raw:
                if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                    continue
                key = json.dumps(pair, sort_keys=True, separators=(",", ":"))
                if unique and key in seen:
                    continue
                seen.add(key)
                pairs.append(pair)
    return pairs


def canonical_program() -> str:
    for row in canonical_rows():
        if row.get("program_solution"):
            return str(row["program_solution"])
    raise AssertionError("canonical row has no program_solution")


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def authority_files() -> list[Path]:
    found: list[Path] = []
    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        for relative in AUTHORITY_PATHS:
            candidate = parent / relative
            if candidate.is_file() and candidate not in found:
                found.append(candidate)
    # Exactly two source records exist in the review tree; a selected runtime
    # may intentionally stage only the one assigned authority.
    if not found:
        raise AssertionError("no selected authority files found")
    return found


def load_generator(path: str | os.PathLike[str] | None = None) -> ModuleType:
    selected = Path(path or os.environ.get("GENERATOR_UNDER_TEST", "")) if (
        path or os.environ.get("GENERATOR_UNDER_TEST")
    ) else None
    if selected is not None:
        selected = selected.resolve()
        spec = importlib.util.spec_from_file_location(
            f"generator_under_test_{hashlib.sha256(str(selected).encode()).hexdigest()[:12]}",
            selected,
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load generator from {selected}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )


def _validate_grid(grid: object) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty sequences")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors")
    return len(grid), width


def recover_details(
    grid: list[list[int]],
    *,
    noise: int = 6,
    square_only: bool = False,
    max_period: int | None = None,
) -> tuple[list[list[int]], int, int] | None:
    """Independent mirror of the selected lexicographic period search.

    The selected Racket rule tries row periods first, then column periods. It
    ignores color 6 while inferring the tile, requires every residue class to
    retain a clean representative, and reconstructs with the first fitting
    period. This probe keeps that exact ordering.
    """
    h, w = _validate_grid(grid)
    max_pr = min(h // 2, max_period if max_period is not None else h // 2)
    max_pc = min(w // 2, max_period if max_period is not None else w // 2)
    for pr in range(1, max_pr + 1):
        pc_values: Iterable[int] = (pr,) if square_only and pr <= max_pc else (
            () if square_only else range(1, max_pc + 1)
        )
        for pc in pc_values:
            tile: dict[tuple[int, int], int] = {}
            consistent = True
            for r, row in enumerate(grid):
                for c, value in enumerate(row):
                    if value == noise:
                        continue
                    key = (r % pr, c % pc)
                    prior = tile.get(key)
                    if prior is None:
                        tile[key] = value
                    elif prior != value:
                        consistent = False
                        break
                if not consistent:
                    break
            if not consistent or len(tile) != pr * pc:
                continue
            output = [
                [tile[(r % pr, c % pc)] for c in range(w)]
                for r in range(h)
            ]
            return output, pr, pc
    return None


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    details = recover_details(grid)
    if details is None:
        h, w = _validate_grid(grid)
        return [[0 for _ in range(w)] for _ in range(h)]
    return details[0]


def observed(grid: list[list[int]]) -> dict[str, int | bool]:
    details = recover_details(grid)
    if details is None:
        raise ValueError("grid has no recoverable period")
    output, pr, pc = details
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "period_r": pr,
        "period_c": pc,
        "palette_size": len({value for row in output for value in row}),
        "noise_count": sum(value == 6 for row in grid for value in row),
        "clean_anchor": all(
            grid[r][c] != 6 for r in range(pr) for c in range(pc)
        ),
    }


def grid_hash(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode()
    ).hexdigest()
