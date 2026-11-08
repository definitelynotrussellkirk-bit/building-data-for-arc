"""Proposed episode-fixed odd-row branch policies for seed propagation.

Every input retains the canonical grammar: distinct nonzero seeds appear only
on the top row, at interior columns separated by at least three cells.  The
private setting changes only which diagonal branch is painted on odd rows.
Python outputs remain claims until every label is executed by protected Racket.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "329d82eaaa63"
SETTINGS = (
    {"branches": "both"},
    {"branches": "left"},
    {"branches": "right"},
)

# height, width, number of top-row seeds
_DEMO_PROFILES = (
    (6, 7, 1),
    (6, 12, 3),
    (9, 9, 2),
    (12, 18, 4),
    (18, 24, 5),
    (20, 26, 6),
)
_QUERY_PROFILES = (
    (3, 4, 1),
    (11, 17, 4),
    (24, 29, 7),
    (30, 30, 8),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"branches"}
        or type(settings["branches"]) is not str
        or settings["branches"] not in {"both", "left", "right"}
    ):
        raise ValueError("settings must be exactly {'branches': 'both'|'left'|'right'}")
    return settings["branches"]


def program(settings):
    branches = _setting(settings)
    filename = {"both": "canonical.rkt", "left": "left.rkt", "right": "right.rkt"}[branches]
    return (HERE / filename).read_text()


def _rng(seed, split, index):
    raw = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _seed_columns(width, count, rng):
    """Place separated interior seeds while preserving broad edge coverage."""
    slack = width - 3 * count
    if slack < 0:
        raise ValueError("profile cannot fit separated interior seeds")
    allocation = [0] * (count + 1)
    for _ in range(slack):
        allocation[rng.randrange(count + 1)] += 1
    column = 1 + allocation[0]
    columns = []
    for index in range(count):
        columns.append(column)
        if index + 1 < count:
            column += 3 + allocation[index + 1]
    if columns[-1] > width - 2:
        raise AssertionError("internal seed-column construction escaped the interior")
    return columns


def sample_input(seed, split, index):
    """Deterministic, prefix-stable input independent of the private setting."""
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    _integer(index, 0, len(profiles) - 1, "index")
    height, width, count = profiles[index]
    rng = _rng(seed, split, index)
    columns = _seed_columns(width, count, rng)
    colors = rng.sample(range(1, 10), count)
    grid = [[0] * width for _ in range(height)]
    for column, color in zip(columns, colors):
        grid[0][column] = color
    return grid


def _seeds(grid):
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact ARC integers 0..9")
    if any(cell != 0 for row in grid[1:] for cell in row):
        raise ValueError("only the top row may contain seeds")
    seeds = [(column, color) for column, color in enumerate(grid[0]) if color]
    if not 1 <= len(seeds) <= 9:
        raise ValueError("input must contain 1..9 nonzero top-row seeds")
    columns = [column for column, _ in seeds]
    colors = [color for _, color in seeds]
    if columns[0] == 0 or columns[-1] == width - 1:
        raise ValueError("seed columns must be interior")
    if len(colors) != len(set(colors)):
        raise ValueError("seed colors must be pairwise distinct")
    if any(right - left < 3 for left, right in zip(columns, columns[1:])):
        raise ValueError("seed columns must be separated by at least three")
    return seeds


def transform(grid, settings):
    branches = _setting(settings)
    seeds = _seeds(grid)
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    for column, color in seeds:
        for row in range(height):
            if row % 2 == 0:
                output[row][column] = color
            else:
                if branches in {"both", "left"}:
                    output[row][column - 1] = color
                if branches in {"both", "right"}:
                    output[row][column + 1] = color
    return output


def generate(seed, settings, demos=3, queries=4):
    """Generate 2..6 demonstrations and 1..4 distinct queries independently."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": dict(settings),
        "program_solution": program(settings),
        "train": [],
        "test": [],
    }
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate generated input at {split}[{index}]")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result
