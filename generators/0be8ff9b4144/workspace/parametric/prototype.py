"""Parametric intersection-policy family for 0be8ff9b4144.

The input grammar is shared by all settings. Step A decodes the ordered active
row and column lists from exact header colors. Step B consumes those ordered
lists: the canonical setting paints their full Cartesian product, while the two
alternatives paint intersections whose *ranks* have equal or unequal parity.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Callable

TASK_ID = "0be8ff9b4144"
POLICIES = ("all", "same_parity", "opposite_parity")
DEFAULT_POLICY = "all"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

_HERE = Path(__file__).resolve().parent
_RULES = {
    "all": _HERE / "rules" / "canonical.rkt",
    "same_parity": _HERE / "rules" / "same_parity.rkt",
    "opposite_parity": _HERE / "rules" / "opposite_parity.rkt",
}

# Every profile has at least three active rows and columns. That makes parity
# patterns structural rather than a disguised single diagonal.
_DEMO_PROFILES = (
    (9, 11, 3, 4, 0.07, False),
    (11, 13, 4, 3, 0.08, False),
    (13, 16, 5, 4, 0.08, False),
    (16, 18, 4, 5, 0.09, True),
    (20, 22, 5, 6, 0.09, False),
    (24, 27, 6, 5, 0.10, True),
)
_QUERY_PROFILES = (
    (12, 14, 3, 5, 0.08, False),
    (18, 25, 4, 6, 0.09, True),
    (25, 18, 6, 4, 0.09, True),
    (30, 30, 6, 6, 0.11, True),
)
_BACKGROUND_COLORS = (0, 1, 4, 6, 7, 9)
_CONTENT_COLORS = (1, 4, 6, 7, 8, 9)


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in [{low}, {high}]")
    return value


def _policy(value: str) -> str:
    if type(value) is not str or value not in POLICIES:
        raise ValueError(f"intersection_policy must be one of {POLICIES}")
    return value


def rule_text(intersection_policy: str) -> str:
    return _RULES[_policy(intersection_policy)].read_text()


def active_axes(grid: list[list[int]]) -> tuple[list[int], list[int]]:
    rows = [index for index in range(1, len(grid)) if grid[index][0] == 3]
    cols = [index for index in range(1, len(grid[0])) if grid[0][index] == 2]
    return rows, cols


def _selected(row_rank: int, col_rank: int, policy: str) -> bool:
    if policy == "all":
        return True
    same = (row_rank + col_rank) % 2 == 0
    return same if policy == "same_parity" else not same


def apply_policy(grid: list[list[int]], intersection_policy: str) -> list[list[int]]:
    policy = _policy(intersection_policy)
    rows, cols = active_axes(grid)
    out = copy.deepcopy(grid)
    for row_rank, row in enumerate(rows):
        for col_rank, col in enumerate(cols):
            if _selected(row_rank, col_rank, policy):
                out[row][col] = 5
    return out


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"{TASK_ID}:intersection-policy-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _mixed_rank_positions(
    rng: random.Random, maximum: int, count: int, boundary: bool
) -> list[int]:
    pool = list(range(1, maximum + 1))
    forced = {1, maximum} if boundary else set()
    if len(forced) > count:
        raise ValueError("profile has too few markers for required boundaries")
    for _ in range(512):
        remaining = [value for value in pool if value not in forced]
        chosen = sorted(forced | set(rng.sample(remaining, count - len(forced))))
        # Neither raw coordinate parity nor its complement can globally stand in
        # for marker rank parity when both offsets occur.
        if len({(position - rank) % 2 for rank, position in enumerate(chosen)}) == 2:
            return chosen
    raise RuntimeError("could not construct an irregular rank/coordinate mapping")


def _different_color(rng: random.Random, forbidden: set[int]) -> int:
    options = [color for color in _CONTENT_COLORS if color not in forbidden]
    if not options:
        raise RuntimeError("no contrast color available")
    return rng.choice(options)


def _make_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, row_count, col_count, density, boundary = profiles[index]
    rng = _rng(seed, split, index)
    background = rng.choice(_BACKGROUND_COLORS)
    grid = [[background for _ in range(width)] for _ in range(height)]

    rows = _mixed_rank_positions(rng, height - 1, row_count, boundary)
    cols = _mixed_rank_positions(rng, width - 1, col_count, boundary)
    grid[0][0] = _different_color(rng, {background, 2, 3, 5})
    for row in rows:
        grid[row][0] = 3
    for col in cols:
        grid[0][col] = 2

    inactive_rows = [row for row in range(1, height) if row not in rows]
    inactive_cols = [col for col in range(1, width) if col not in cols]
    for row in rng.sample(inactive_rows, min(3, len(inactive_rows))):
        grid[row][0] = _different_color(rng, {background, 3, 5})
    for col in rng.sample(inactive_cols, min(3, len(inactive_cols))):
        grid[0][col] = _different_color(rng, {background, 2, 5})

    # Occupied active intersections force the learner to infer both which cells
    # are selected and that selected cells are overwritten rather than skipped.
    for row in rows:
        for col in cols:
            grid[row][col] = _different_color(rng, {background, 5})

    occupied = {(row, col) for row in rows for col in cols}
    body = [
        (row, col)
        for row in range(1, height)
        for col in range(1, width)
        if (row, col) not in occupied
    ]
    rng.shuffle(body)
    distractor_count = max(12, int((height - 1) * (width - 1) * density))
    for row, col in body[:distractor_count]:
        grid[row][col] = _different_color(rng, {background, 5})
    return grid


def _background(grid: list[list[int]]) -> int:
    return Counter(value for row in grid for value in row).most_common(1)[0][0]


def _paint_with_axes(
    grid: list[list[int]],
    rows: list[int],
    cols: list[int],
    policy: str,
    *,
    preserve_occupied: bool = False,
) -> list[list[int]]:
    out = copy.deepcopy(grid)
    background = _background(grid)
    for row_rank, row in enumerate(rows):
        for col_rank, col in enumerate(cols):
            if _selected(row_rank, col_rank, policy):
                if not preserve_occupied or grid[row][col] == background:
                    out[row][col] = 5
    return out


def audit_rivals(intersection_policy: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    policy = _policy(intersection_policy)

    def absolute_coordinate_parity(grid):
        rows, cols = active_axes(grid)
        out = copy.deepcopy(grid)
        for row in rows:
            for col in cols:
                parity = (row + col) % 2
                keep = parity == 0 if policy != "opposite_parity" else parity == 1
                if policy == "all":
                    keep = parity == 0
                if keep:
                    out[row][col] = 5
        return out

    def rank_diagonal_only(grid):
        rows, cols = active_axes(grid)
        out = copy.deepcopy(grid)
        for rank in range(min(len(rows), len(cols))):
            out[rows[rank]][cols[rank]] = 5
        return out

    def single_axis_rank_parity(grid):
        rows, cols = active_axes(grid)
        out = copy.deepcopy(grid)
        wanted = 1 if policy == "opposite_parity" else 0
        for row_rank, row in enumerate(rows):
            for col in cols:
                if row_rank % 2 == wanted:
                    out[row][col] = 5
        return out

    def any_nonbackground_header(grid):
        background = _background(grid)
        rows = [row for row in range(1, len(grid)) if grid[row][0] != background]
        cols = [col for col in range(1, len(grid[0])) if grid[0][col] != background]
        return _paint_with_axes(grid, rows, cols, policy)

    def preserve_occupied_selected_cells(grid):
        rows, cols = active_axes(grid)
        return _paint_with_axes(grid, rows, cols, policy, preserve_occupied=True)

    return {
        "absolute_coordinate_parity": absolute_coordinate_parity,
        "rank_diagonal_only": rank_diagonal_only,
        "single_axis_rank_parity": single_axis_rank_parity,
        "any_nonbackground_header": any_nonbackground_header,
        "preserve_occupied_selected_cells": preserve_occupied_selected_cells,
    }


def public_projection(episode: dict) -> dict:
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_challenge_bytes(episode: dict) -> bytes:
    return json.dumps(
        public_projection(episode),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode() + b"\n"


def public_challenge_id(episode: dict) -> str:
    return hashlib.sha256(public_challenge_bytes(episode)).hexdigest()


def generate_episode(
    seed: int,
    *,
    intersection_policy: str = DEFAULT_POLICY,
    demos: int = 3,
    queries: int = 4,
) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    policy = _policy(intersection_policy)
    _integer("demos", demos, MIN_DEMOS, MAX_DEMOS)
    _integer("queries", queries, MIN_QUERIES, MAX_QUERIES)

    train_inputs = [_make_input(seed, "train", index) for index in range(demos)]
    test_inputs = [_make_input(seed, "test", index) for index in range(queries)]
    train = [
        {"input": copy.deepcopy(grid), "output": apply_policy(grid, policy)}
        for grid in train_inputs
    ]
    test = [
        {"input": copy.deepcopy(grid), "output": apply_policy(grid, policy)}
        for grid in test_inputs
    ]
    return {
        "schema": "header-intersection-policy-parametric-v1",
        "status": "proposed",
        "approved": False,
        "training_admitted": False,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"intersection_policy": policy},
        "demo_count": demos,
        "query_count": queries,
        "train": train,
        "test": test,
        "program_solution": rule_text(policy),
        "public_challenge_id": public_challenge_id({"train": train, "test": test}),
    }
