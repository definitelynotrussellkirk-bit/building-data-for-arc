"""Deterministic native prototype for one-pass and two-pass diagonal completion."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

TASK_ID = "b4d9320e0d9d"
HOME = Path(__file__).resolve().parent
COMPLETION_ROUNDS = ("one_pass", "two_pass")
_PROGRAMS = {
    "one_pass": (HOME / "rules" / "canonical.rkt").read_text(),
    "two_pass": (HOME / "rules" / "two_pass.rkt").read_text(),
}

DEMO_PROFILES = ((9, 9), (11, 12), (14, 15), (17, 18), (20, 22), (24, 25))
QUERY_PROFILES = ((13, 16), (19, 21), (25, 27), (30, 30))
_MOTIF_CYCLE = (
    "cascade",
    "occupied_corner",
    "cascade",
    "mixed_diagonal",
    "cascade",
    "orthogonal_pair",
    "cascade",
    "legal_pair",
)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(value: Any) -> str:
    if type(value) is not str or value not in COMPLETION_ROUNDS:
        raise ValueError(f"completion_rounds must be one of {COMPLETION_ROUNDS}")
    return value


def program_for(completion_rounds: str) -> str:
    return _PROGRAMS[_mode(completion_rounds)]


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty row lists")
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must each be in 1..30")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact ARC colors 0..9")
    return len(grid), width


def apply_pass(grid: list[list[int]]) -> list[list[int]]:
    """Mirror one canonical pass: tests read the original, writes accumulate in a copy."""
    height, width = _validate_grid(grid)
    out = copy.deepcopy(grid)
    for row in range(height - 1):
        for col in range(width - 1):
            a = grid[row][col]
            b = grid[row][col + 1]
            d = grid[row + 1][col]
            e = grid[row + 1][col + 1]
            if a != 0 and a == e and b == 0 and d == 0:
                out[row][col + 1] = a
                out[row + 1][col] = a
            elif b != 0 and b == d and a == 0 and e == 0:
                out[row][col] = b
                out[row + 1][col + 1] = b
    return out


def apply_rounds(grid: list[list[int]], completion_rounds: str) -> list[list[int]]:
    mode = _mode(completion_rounds)
    first = apply_pass(grid)
    return first if mode == "one_pass" else apply_pass(first)


def _digest(seed: int, split: str, index: int, slot: int, salt: str) -> int:
    raw = f"{TASK_ID}|cascade-v1|{seed}|{split}|{index}|{slot}|{salt}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _anchors(side: int) -> list[int]:
    values = list(range(0, side - 2, 5))
    last = side - 3
    if not values:
        return [last]
    if last - values[-1] < 4:
        values[-1] = last
    elif values[-1] != last:
        values.append(last)
    return sorted(set(values))


def _rotate(cell: tuple[int, int], turns: int, reflect: bool) -> tuple[int, int]:
    row, col = cell
    for _ in range(turns % 4):
        row, col = col, 2 - row
    if reflect:
        col = 2 - col
    return row, col


def _motif_cells(kind: str, color: int, other: int) -> list[tuple[int, int, int]]:
    if kind == "cascade":
        return [(1, 0, color), (2, 1, color), (0, 2, color)]
    if kind == "occupied_corner":
        return [(0, 0, color), (1, 1, color), (0, 1, color)]
    if kind == "mixed_diagonal":
        return [(0, 0, color), (1, 1, other)]
    if kind == "orthogonal_pair":
        return [(0, 0, color), (0, 1, color)]
    if kind == "legal_pair":
        return [(0, 0, color), (1, 1, color)]
    raise ValueError(kind)


def make_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    _integer(index, "index", 0, len(profiles) - 1)
    height, width = profiles[index]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    row_anchors = _anchors(height)
    col_anchors = _anchors(width)
    positions = [(row, col) for row in row_anchors for col in col_anchors]
    cascade_number = 0
    corners = {
        (row_anchors[0], col_anchors[0]),
        (row_anchors[0], col_anchors[-1]),
        (row_anchors[-1], col_anchors[0]),
        (row_anchors[-1], col_anchors[-1]),
    }
    for slot, (row0, col0) in enumerate(positions):
        kind = _MOTIF_CYCLE[slot % len(_MOTIF_CYCLE)]
        if split == "query" and index == 3 and (row0, col0) in corners:
            kind = "cascade"
        color = 1 + _digest(seed, split, index, slot, "color") % 9
        other = 1 + _digest(seed, split, index, slot, "other") % 9
        if other == color:
            other = color % 9 + 1
        if kind == "cascade":
            turns = cascade_number % 4
            cascade_number += 1
            reflect = False
        else:
            turns = _digest(seed, split, index, slot, "turn") % 4
            reflect = bool(_digest(seed, split, index, slot, "reflect") % 2)
        for local_row, local_col, value in _motif_cells(kind, color, other):
            local_row, local_col = _rotate((local_row, local_col), turns, reflect)
            target = (row0 + local_row, col0 + local_col)
            if grid[target[0]][target[1]] != 0:
                raise AssertionError("motif overlap")
            grid[target[0]][target[1]] = value
    return grid


def episode_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    _integer(seed, "seed", 0, 2**63 - 1)
    return {
        "train": [make_input(seed, "demo", index) for index in range(len(DEMO_PROFILES))],
        "test": [make_input(seed, "query", index) for index in range(len(QUERY_PROFILES))],
    }


def generate_episode(seed: int, completion_rounds: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    mode = _mode(completion_rounds)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    inputs = episode_inputs(seed)
    train = [
        {"input": copy.deepcopy(grid), "output": apply_rounds(grid, mode)}
        for grid in inputs["train"][:demos]
    ]
    test = [
        {"input": copy.deepcopy(grid), "output": apply_rounds(grid, mode)}
        for grid in inputs["test"][:queries]
    ]
    return {"train": train, "test": test, "program_solution": program_for(mode)}


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or isinstance(query_index, bool):
        raise ValueError("query_index must be an exact integer")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("episode/query_index is invalid")
    return {
        "train": copy.deepcopy(train),
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }


def _modified_pass(grid: list[list[int]], policy: str) -> list[list[int]]:
    height, width = _validate_grid(grid)
    out = apply_pass(grid) if policy == "orthogonal_too" else copy.deepcopy(grid)
    for row in range(height - 1):
        for col in range(width - 1):
            a, b = grid[row][col], grid[row][col + 1]
            d, e = grid[row + 1][col], grid[row + 1][col + 1]
            main_equal = a != 0 and a == e
            anti_equal = b != 0 and b == d
            if policy == "one_empty_corner":
                if main_equal and (b == 0 or d == 0):
                    if b == 0: out[row][col + 1] = a
                    if d == 0: out[row + 1][col] = a
                elif anti_equal and (a == 0 or e == 0):
                    if a == 0: out[row][col] = b
                    if e == 0: out[row + 1][col + 1] = b
            elif policy == "ignore_color_equality":
                if a != 0 and e != 0 and b == 0 and d == 0:
                    out[row][col + 1] = a; out[row + 1][col] = a
                elif b != 0 and d != 0 and a == 0 and e == 0:
                    out[row][col] = b; out[row + 1][col + 1] = b
            elif policy == "orthogonal_too":
                if a != 0 and a == b and d == 0 and e == 0:
                    out[row + 1][col] = a; out[row + 1][col + 1] = a
                elif d != 0 and d == e and a == 0 and b == 0:
                    out[row][col] = d; out[row][col + 1] = d
                elif a != 0 and a == d and b == 0 and e == 0:
                    out[row][col + 1] = a; out[row + 1][col + 1] = a
                elif b != 0 and b == e and a == 0 and d == 0:
                    out[row][col] = b; out[row + 1][col] = b
            elif policy == "main_only":
                if main_equal and b == 0 and d == 0:
                    out[row][col + 1] = a; out[row + 1][col] = a
            elif policy == "anti_only":
                if anti_equal and a == 0 and e == 0:
                    out[row][col] = b; out[row + 1][col + 1] = b
            else:
                raise ValueError(policy)
    return out


def _apply_policy_rounds(grid: list[list[int]], mode: str, policy: str) -> list[list[int]]:
    first = _modified_pass(grid, policy)
    return first if mode == "one_pass" else _modified_pass(first, policy)


def audit_rivals(completion_rounds: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    mode = _mode(completion_rounds)
    other = "two_pass" if mode == "one_pass" else "one_pass"
    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
        f"declared_setting:{other}": lambda grid, other=other: apply_rounds(grid, other),
        "identity": lambda grid: copy.deepcopy(grid),
    }
    for policy in ("one_empty_corner", "ignore_color_equality", "orthogonal_too", "main_only", "anti_only"):
        rivals[policy] = lambda grid, policy=policy: _apply_policy_rounds(grid, mode, policy)
    return rivals


def teaching_certificate(episode: dict[str, Any], completion_rounds: str) -> dict[str, Any]:
    mode = _mode(completion_rounds)
    demos = episode.get("train")
    queries = episode.get("test")
    if type(demos) is not list or type(queries) is not list or not demos or not queries:
        raise ValueError("episode must contain nonempty train/test lists")
    declared = [
        candidate
        for candidate in COMPLETION_ROUNDS
        if all(apply_rounds(pair["input"], candidate) == pair["output"] for pair in demos)
    ]
    surviving: list[str] = []
    query_changing: list[str] = []
    refutations: dict[str, list[int]] = {}
    for name, rival in audit_rivals(mode).items():
        mismatches = [index for index, pair in enumerate(demos) if rival(pair["input"]) != pair["output"]]
        refutations[name] = mismatches
        if not mismatches:
            surviving.append(name)
            if any(rival(pair["input"]) != pair["output"] for pair in queries):
                query_changing.append(name)
    return {
        "declared_setting_survivors": declared,
        "surviving_named_rivals": surviving,
        "query_changing_named_survivors": query_changing,
        "demo_refutation_indices": refutations,
        "scope": "Finite declared settings and named deterministic rivals only.",
    }


def dependency_trace(grid: list[list[int]]) -> dict[str, Any]:
    first = apply_pass(grid)
    second = apply_pass(first)
    changed = sum(a != b for row_a, row_b in zip(first, second) for a, b in zip(row_a, row_b))
    return {
        "step_a": "complete every eligible original 2x2 window once",
        "intermediate": first,
        "step_b": "recompute eligibility from the first-pass grid and complete once more",
        "step_b_output": second,
        "skip_step_b_output": first,
        "changed_cells_in_step_b": changed,
    }


def analyse_grid(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    first = apply_pass(grid)
    second = apply_pass(first)
    changed_second = sum(a != b for row_a, row_b in zip(first, second) for a, b in zip(row_a, row_b))
    nonzero = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    boundaries = 0
    if any(value != 0 for value in grid[0]): boundaries += 1
    if any(value != 0 for value in grid[-1]): boundaries += 1
    if any(row[0] != 0 for row in grid): boundaries += 1
    if any(row[-1] != 0 for row in grid): boundaries += 1
    return {
        "shape": [height, width],
        "nonzero_cells": len(nonzero),
        "colors": sorted({value for _, _, value in nonzero}),
        "cascade_witnesses": changed_second // 2,
        "occupied_boundaries": boundaries,
    }
