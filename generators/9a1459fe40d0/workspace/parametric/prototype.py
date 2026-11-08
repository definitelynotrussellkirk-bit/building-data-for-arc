"""Native mark-placement family for ARC task 9a1459fe40d0.

``project_right`` is the exact canonical rule: every occupancy-XOR mirror pair
is marked at its reflected right-half coordinate. ``occupied_side`` retains the
same XOR classification but marks the coordinate that is actually occupied.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import cache
import hashlib
import random
from pathlib import Path
from typing import Any

TASK_ID = "9a1459fe40d0"
HERE = Path(__file__).resolve().parent
Grid = list[list[int]]

POLICIES = ("project_right", "occupied_side")
DEFAULT_POLICY = "project_right"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
_PAYLOAD = (1, 2, 3, 4, 5, 6, 9)

_DEMO_PROFILES = (
    {"h": 10, "w": 15, "left": 4, "right": 4, "same": 3, "different": 3},
    {"h": 12, "w": 17, "left": 5, "right": 4, "same": 3, "different": 4},
    {"h": 16, "w": 19, "left": 6, "right": 6, "same": 4, "different": 4},
    {"h": 18, "w": 21, "left": 8, "right": 7, "same": 5, "different": 5},
    {"h": 22, "w": 23, "left": 10, "right": 9, "same": 6, "different": 7},
    {"h": 26, "w": 25, "left": 12, "right": 12, "same": 8, "different": 8},
)
_QUERY_PROFILES = (
    {"h": 14, "w": 21, "left": 5, "right": 5, "same": 4, "different": 4},
    {"h": 20, "w": 25, "left": 10, "right": 10, "same": 8, "different": 8},
    {"h": 26, "w": 27, "left": 20, "right": 18, "same": 15, "different": 15},
    {"h": 30, "w": 29, "left": 35, "right": 35, "same": 30, "different": 30},
)

_OCCUPIED_SIDE_PROGRAM = """(rule! (let ((dummy 0)) (define (full-bar-col grid color) (first (filter (lambda (c) (all? (lambda (r) (= (at grid r c) color)) (range (rows grid)))) (range (cols grid))))) (let ((b (full-bar-col g 8))) (for*/fold ((out (empty-grid (rows g) (cols g) 0))) ((r (in-range (rows g))) (c (in-range b))) (let* ((mc (- (* 2 b) c)) (left (not (= (at g r c) 0))) (right (and (in-bounds? r mc (rows g) (cols g)) (not (= (at g r mc) 0))))) (if (and (in-bounds? r mc (rows g) (cols g)) (not (equal? left right))) (set-cell out r (if left c mc) 7) out))))))"""


@cache
def canonical_program() -> str:
    source = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if not source.startswith("(rule!"):
        raise ValueError("canonical.rkt does not contain a rule")
    return source


def _validate_policy(policy: Any) -> str:
    if type(policy) is not str:
        raise TypeError("mark policy must be an exact string")
    if policy not in POLICIES:
        raise ValueError(f"unknown mark policy: {policy!r}")
    return policy


def program_for(policy: str) -> str:
    policy = _validate_policy(policy)
    return canonical_program() if policy == "project_right" else _OCCUPIED_SIDE_PROGRAM


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_count(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _grid_shape(grid: Any) -> tuple[int, int]:
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
        or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)
    ):
        raise ValueError("grid must be a rectangular ARC grid")
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 7 <= width <= 30 or width % 2 == 0:
        raise ValueError("grid must have height 1..30 and odd width 7..29")
    return height, width


def pair_facts(grid: Grid) -> dict[str, Any]:
    height, width = _grid_shape(grid)
    full_bars = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if full_bars != [width // 2]:
        raise ValueError("grid needs exactly one centered full-height color-8 bar")
    bar_col = full_bars[0]
    if any(
        grid[row][col] == 8
        for row in range(height)
        for col in range(width)
        if col != bar_col
    ):
        raise ValueError("color 8 may only occur on the center bar")
    if any(value == 7 for row in grid for value in row):
        raise ValueError("color 7 is reserved for output marks")

    pairs: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for row in range(height):
        for left_col in range(bar_col):
            right_col = 2 * bar_col - left_col
            left_value = grid[row][left_col]
            right_value = grid[row][right_col]
            if left_value and right_value:
                state = "both_same" if left_value == right_value else "both_different"
                occupied_col = None
            elif left_value:
                state = "left_only"
                occupied_col = left_col
            elif right_value:
                state = "right_only"
                occupied_col = right_col
            else:
                state = "both_empty"
                occupied_col = None
            counts[state] += 1
            pairs.append({
                "row": row,
                "left_col": left_col,
                "right_col": right_col,
                "left_value": left_value,
                "right_value": right_value,
                "state": state,
                "occupied_col": occupied_col,
            })
    mismatches = [row for row in pairs if row["state"] in ("left_only", "right_only")]
    return {
        "height": height,
        "width": width,
        "bar_col": bar_col,
        "pairs": pairs,
        "mismatches": mismatches,
        "state_counts": {
            name: counts[name]
            for name in ("both_different", "both_empty", "both_same", "left_only", "right_only")
        },
        "directed_xor": [
            [row["row"], row["left_col"], row["right_col"], row["state"], row["occupied_col"]]
            for row in mismatches
        ],
    }


def apply_policy(grid: Grid, policy: str) -> Grid:
    policy = _validate_policy(policy)
    facts = pair_facts(grid)
    result = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for row in facts["mismatches"]:
        target = row["right_col"] if policy == "project_right" else row["occupied_col"]
        result[row["row"]][target] = 7
    return result


def _rng(seed: int, split: str, slot: int, purpose: str) -> random.Random:
    material = f"{TASK_ID}|mark-policy-v1|{seed}|{split}|{slot}|{purpose}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _ordered_slots(height: int, bar_col: int, rng: random.Random) -> list[tuple[int, int]]:
    boundary = [
        (0, 0),
        (height - 1, 0),
        (0, bar_col - 1),
        (height - 1, bar_col - 1),
    ]
    rest = [
        (row, col)
        for row in range(height)
        for col in range(bar_col)
        if (row, col) not in boundary
    ]
    rng.shuffle(rest)
    return boundary + rest


def _make_input(seed: int, split: str, slot: int, profile: dict[str, int]) -> Grid:
    height, width = profile["h"], profile["w"]
    bar_col = width // 2
    states = (
        ["left_only"] * profile["left"]
        + ["right_only"] * profile["right"]
        + ["both_same"] * profile["same"]
        + ["both_different"] * profile["different"]
    )
    layout_rng = _rng(seed, split, slot, "layout")
    layout_rng.shuffle(states)
    slots = _ordered_slots(height, bar_col, layout_rng)
    if len(states) > len(slots):
        raise AssertionError("profile exceeds available mirror pairs")

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        grid[row][bar_col] = 8
    color_rng = _rng(seed, split, slot, "colors")
    for index, (state, (row, left_col)) in enumerate(zip(states, slots)):
        right_col = 2 * bar_col - left_col
        first = _PAYLOAD[(color_rng.randrange(len(_PAYLOAD)) + index) % len(_PAYLOAD)]
        if state == "left_only":
            grid[row][left_col] = first
        elif state == "right_only":
            grid[row][right_col] = first
        elif state == "both_same":
            grid[row][left_col] = grid[row][right_col] = first
        else:
            choices = [value for value in _PAYLOAD if value != first]
            second = choices[color_rng.randrange(len(choices))]
            grid[row][left_col], grid[row][right_col] = first, second

    facts = pair_facts(grid)
    expected = {
        "left_only": profile["left"],
        "right_only": profile["right"],
        "both_same": profile["same"],
        "both_different": profile["different"],
    }
    for state, count in expected.items():
        if facts["state_counts"][state] != count:
            raise AssertionError(f"{state} count drifted")
    if apply_policy(grid, "project_right") == apply_policy(grid, "occupied_side"):
        raise AssertionError("profile does not distinguish policies")
    return grid


def episode_inputs(seed: int, demos: int, queries: int) -> list[Grid]:
    seed = _validate_seed(seed)
    demos = _validate_count(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries = _validate_count(queries, "queries", MIN_QUERIES, MAX_QUERIES)
    demo_inputs = [_make_input(seed, "demo", slot, _DEMO_PROFILES[slot]) for slot in range(demos)]
    query_inputs = [_make_input(seed, "query", slot, _QUERY_PROFILES[slot]) for slot in range(queries)]
    result = demo_inputs + query_inputs
    frozen = {tuple(tuple(row) for row in grid) for grid in result}
    if len(frozen) != len(result):
        raise AssertionError("episode inputs must be distinct")
    return result


def generate_episode(seed: int, mark_policy: str, demos: int, queries: int) -> dict[str, Any]:
    mark_policy = _validate_policy(mark_policy)
    inputs = episode_inputs(seed, demos, queries)
    return {
        "train": [
            {"input": grid, "output": apply_policy(grid, mark_policy)}
            for grid in inputs[:demos]
        ],
        "test": [
            {"input": grid, "output": apply_policy(grid, mark_policy)}
            for grid in inputs[demos:]
        ],
        "program_solution": program_for(mark_policy),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    if type(episode) is not dict:
        raise TypeError("episode must be a dictionary")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode needs train and test lists")
    if not 0 <= query_index < len(test):
        raise IndexError("query_index is outside the private query list")
    visible_train = []
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("every demonstration needs input and output")
        visible_train.append({"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])})
    query = test[query_index]
    if type(query) is not dict or "input" not in query:
        raise ValueError("query needs an input")
    return {"train": visible_train, "test": [{"input": deepcopy(query["input"])}]}
