"""Proposed orthogonal/diagonal seed-neighborhood family for cc74d7392ecd.

The production generator and canonical authority stay unchanged.  This module is
an opt-in task-local prototype for the native parametric qualification worker.
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Any

TASK_ID = "cc74d7392ecd"
PARAMETER = "neighborhood"
SETTINGS = ("orthogonal", "diagonal")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "orthogonal": _HOME / "canonical.rkt",
    "diagonal": _HOME / "diagonal.rkt",
}

# The first four query shapes are fixed so count prefixes are stable and the
# final query provides substantive exact-30x30 stress rather than empty padding.
_TRAIN_PROFILES = (
    (5, 5, 2),
    (6, 8, 3),
    (9, 7, 4),
    (13, 17, 8),
    (18, 21, 12),
    (24, 26, 16),
)
_QUERY_PROFILES = (
    (7, 7, 4),
    (16, 20, 10),
    (23, 29, 18),
    (30, 30, 24),
)


def _validate_settings(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def program(settings: dict[str, str]) -> str:
    """Return exact Racket source for one declared setting."""
    value = _validate_settings(settings)
    return _PROGRAM_FILES[value].read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|inputs-v1|{seed}|{split}|{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _far_enough(candidate: tuple[int, int], placed: list[tuple[int, int]]) -> bool:
    # Chebyshev distance >=3 keeps both radius-one crosses and Xs disjoint.
    return all(max(abs(candidate[0] - r), abs(candidate[1] - c)) >= 3 for r, c in placed)


def _candidate_cells(height: int, width: int, rng: random.Random) -> list[tuple[int, int]]:
    rows = sorted(set([0, height - 1, *range(1, height - 1, 3), *range(3, height - 1, 3)]))
    cols = sorted(set([0, width - 1, *range(1, width - 1, 3), *range(3, width - 1, 3)]))
    lattice = [(r, c) for r in rows for c in cols]
    rng.shuffle(lattice)
    return lattice


def _anchors(height: int, width: int, count: int) -> list[tuple[int, int]]:
    if count == 2:
        return [(0, 0), (height - 1, width - 1)]
    candidates = [
        (0, 0),
        (height - 1, width - 1),
        (0, width - 1),
        (height - 1, 0),
        (0, width // 2),
        (height - 1, width // 2),
        (height // 2, 0),
        (height // 2, width - 1),
        (height // 2, width // 2),
    ]
    placed: list[tuple[int, int]] = []
    for cell in candidates:
        if cell not in placed and _far_enough(cell, placed):
            placed.append(cell)
        if len(placed) == min(count, 8):
            break
    return placed


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, count = profiles[index]
    rng = _rng(seed, split, index)
    placed = _anchors(height, width, count)
    for cell in _candidate_cells(height, width, rng):
        if len(placed) >= count:
            break
        if cell not in placed and _far_enough(cell, placed):
            placed.append(cell)
    if len(placed) != count:
        raise RuntimeError(
            f"could not place {count} separated seeds on {height}x{width}; got {len(placed)}"
        )

    palette = list(range(1, 10))
    rng.shuffle(palette)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for i, (row, col) in enumerate(placed):
        grid[row][col] = palette[i % len(palette)]
    return grid


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact ARC colors")
    return len(grid), width


def apply_rule(grid: list[list[int]], neighborhood: str) -> list[list[int]]:
    """Independent Python label claim; protected Racket remains authoritative."""
    if type(neighborhood) is not str or neighborhood not in SETTINGS:
        raise ValueError(f"neighborhood must be one of {SETTINGS!r}")
    height, width = _validate_grid(grid)
    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r in range(height):
        for c in range(width):
            for sr, sc, color in seeds:
                dr, dc = abs(sr - r), abs(sc - c)
                hit = (dr == 0 and dc == 0)
                if neighborhood == "orthogonal":
                    hit = hit or dr + dc == 1
                else:
                    hit = hit or (dr == 1 and dc == 1)
                if hit:
                    output[r][c] = color
                    break
    return output


def generate(
    seed: int,
    settings: dict[str, str],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    """Generate one setting-fixed episode with independent demo/query counts."""
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    selected = _validate_settings(settings)

    train = []
    for index in range(demos):
        grid = _sample_input(seed, "train", index)
        train.append({"input": grid, "output": apply_rule(grid, selected)})
    test = []
    for index in range(queries):
        grid = _sample_input(seed, "test", index)
        test.append({"input": grid, "output": apply_rule(grid, selected)})

    serialized = [repr(pair["input"]) for pair in [*train, *test]]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    return {"train": train, "test": test, "program_solution": program(settings)}
