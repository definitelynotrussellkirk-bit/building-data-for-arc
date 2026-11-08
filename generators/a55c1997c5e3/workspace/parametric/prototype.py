"""Task-local parametric prototype for a55c1997c5e3.

The input grammar and longest-path reasoning stay fixed.  The episode parameter
changes only the total direction order used *after* the input-dependent set of
maximum-node paths has been enumerated.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys
from typing import Any, Iterable

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "a55c1997c5e3"
ALLOWED_TIE_ORDERS = (
    "right_down_left_up",
    "up_left_down_right",
)
DEFAULT_SETTINGS = {"tie_order": "right_down_left_up"}
ORDER_DIRECTIONS = {
    "right_down_left_up": (0, 1, 2, 3),
    "up_left_down_right": (3, 2, 1, 0),
}
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4

_CANONICAL_DIRECTION_BLOCK = (
    "(define (dir-priority a b)  ;; right 0, down 1, left 2, up 3\n"
    "       (cond ((= (first a) (first b))\n"
    "              (if (< (second a) (second b)) 0 2))\n"
    "             ((< (first a) (first b)) 1)\n"
    "             (else 3)))\n"
)
_ALTERNATE_DIRECTION_BLOCK = (
    "(define (dir-priority a b)  ;; up 0, left 1, down 2, right 3\n"
    "       (cond ((= (first a) (first b))\n"
    "              (if (< (second a) (second b)) 3 1))\n"
    "             ((< (first a) (first b)) 2)\n"
    "             (else 0)))\n"
)

# The first two demonstrations are deliberately sufficient at the minimum
# request.  Additional demonstrations broaden topology rather than padding the
# same witness.  Dimensions are all distinct, making accidental duplicate
# visible inputs fail loudly.
_DEMO_SPECS = (
    ("complete_direction_order", 22, 23),
    ("deep_lexicographic_tie", 20, 24),
    ("tie_down_over_left", 24, 27),
    ("longest_over_priority", 18, 22),
    ("branchy_unique_longest", 28, 30),
    ("tie_right_over_down", 21, 26),
)
_QUERY_SPECS = (
    ("tie_right_over_down", 19, 25),
    ("tie_down_over_left", 26, 28),
    ("deep_lexicographic_tie", 23, 29),
    ("complete_direction_order", 30, 30),
)

_TASK_MODULE = None
_CANONICAL_SOURCE = None


def _exact_int(value: Any, *, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _validate_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"tie_order"}:
        raise ValueError("settings must name exactly tie_order")
    value = settings["tie_order"]
    if type(value) is not str or value not in ALLOWED_TIE_ORDERS:
        raise ValueError("tie_order must be one of " + ", ".join(ALLOWED_TIE_ORDERS))
    return {"tie_order": value}


def task_generator():
    """Load only this task's adjacent generator source, never a cached peer."""
    global _TASK_MODULE
    if _TASK_MODULE is not None:
        return _TASK_MODULE
    path = Path(__file__).resolve().parents[2] / "generator.py"
    name = "_a55c1997c5e3_generator_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load task generator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if getattr(module, "TASK_ID", None) != TASK_ID:
        raise ValueError("adjacent task generator identity differs")
    _TASK_MODULE = module
    return module


def _canonical_program() -> str:
    global _CANONICAL_SOURCE
    if _CANONICAL_SOURCE is not None:
        return _CANONICAL_SOURCE
    ledger = canonical_path(find_root(__file__))
    matches: list[str] = []
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if type(program) is str and program:
                    matches.append(program)
    if len(matches) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}, found {len(matches)}")
    if matches[0].count(_CANONICAL_DIRECTION_BLOCK) != 1:
        raise ValueError("canonical direction block is missing or non-unique")
    _CANONICAL_SOURCE = matches[0]
    return matches[0]


def rule_source(settings: Any) -> str:
    chosen = _validate_settings(settings)["tie_order"]
    canonical = _canonical_program()
    if chosen == DEFAULT_SETTINGS["tie_order"]:
        return canonical
    return canonical.replace(_CANONICAL_DIRECTION_BLOCK, _ALTERNATE_DIRECTION_BLOCK, 1)


def restore_canonical_direction_block(program: str) -> str:
    """Restore the one allowed variant block; useful for exact-source review."""
    if type(program) is not str or program.count(_ALTERNATE_DIRECTION_BLOCK) != 1:
        raise ValueError("program does not contain the unique alternate direction block")
    return program.replace(_ALTERNATE_DIRECTION_BLOCK, _CANONICAL_DIRECTION_BLOCK, 1)


def _mixed_seed(seed: int, slot: int, profile: str, height: int, width: int) -> int:
    payload = json.dumps(
        [TASK_ID, seed, slot, profile, height, width],
        separators=(",", ":"),
    ).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")


def _large_levels(rng: random.Random) -> tuple[list[int], list[int]]:
    """Use every border of a 30x30 canvas while retaining blank corridors."""
    rows = [0, rng.randint(4, 6), rng.randint(11, 14), rng.randint(19, 22), 28]
    cols = [0, rng.randint(5, 7), rng.randint(13, 15), rng.randint(20, 22), 28]
    if any(b - a < 3 for a, b in zip(rows, rows[1:])):
        raise AssertionError("large row levels lost a blank corridor")
    if any(b - a < 3 for a, b in zip(cols, cols[1:])):
        raise AssertionError("large column levels lost a blank corridor")
    return rows, cols


def _render_profile(seed: int, slot: int, profile: str, height: int, width: int) -> list[list[int]]:
    task = task_generator()
    template = task._TEMPLATES[profile]
    abstract_nodes = tuple(template["nodes"])
    abstract_rows = sorted({row for row, _ in abstract_nodes})
    abstract_cols = sorted({col for _, col in abstract_nodes})
    rng = random.Random(_mixed_seed(seed, slot, profile, height, width))

    if (height, width, profile) == (30, 30, "complete_direction_order"):
        row_levels, col_levels = _large_levels(rng)
    elif profile == "complete_direction_order":
        row_levels, col_levels = task._sample_direction_layout(height, width, rng)
    else:
        row_levels = task._sample_levels(len(abstract_rows), height - 2, rng)
        if profile == "tie_down_over_left":
            col_levels = task._sample_endpoint_columns(width, rng)
        else:
            col_levels = task._sample_levels(len(abstract_cols), width - 2, rng)

    if len(row_levels) != len(abstract_rows) or len(col_levels) != len(abstract_cols):
        raise AssertionError("profile level count mismatch")
    row_map = dict(zip(abstract_rows, row_levels))
    col_map = dict(zip(abstract_cols, col_levels))
    grid = task.full_grid(height, width, 0)
    for node in abstract_nodes:
        color = 2 if node == template["start"] else 8
        task.draw_rect(grid, row_map[node[0]], col_map[node[1]], 2, 2, color)
    errors = task.strict_canonical_like(grid)
    if errors:
        raise ValueError(f"prototype rendered an unlawful {profile} input: {errors[0]}")
    return grid


def sample_inputs(seed: Any, demos: Any, queries: Any) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    seed = _exact_int(seed, name="seed", low=0, high=2**63 - 1)
    demos = _exact_int(demos, name="demos", low=MIN_DEMOS, high=MAX_DEMOS)
    queries = _exact_int(queries, name="queries", low=QUERY_COUNT, high=QUERY_COUNT)
    train = [
        _render_profile(seed, index, profile, height, width)
        for index, (profile, height, width) in enumerate(_DEMO_SPECS[:demos])
    ]
    test = [
        _render_profile(seed, 100 + index, profile, height, width)
        for index, (profile, height, width) in enumerate(_QUERY_SPECS[:queries])
    ]
    encoded = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(encoded) != len(set(encoded)):
        raise ValueError("prototype sampled duplicate visible inputs")
    return train, test


def _validate_order(order: Iterable[int]) -> tuple[int, int, int, int]:
    value = tuple(order)
    if len(value) != 4 or set(value) != {0, 1, 2, 3} or any(type(v) is not int for v in value):
        raise ValueError("direction order must be a permutation of 0,1,2,3")
    return value


def python_mirror_for_order(grid: Any, order: Iterable[int]) -> list[list[int]]:
    task = task_generator()
    direction_order = _validate_order(order)
    analysis = task._analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    ranks = {direction: rank for rank, direction in enumerate(direction_order)}
    best = min(
        analysis["max_paths"],
        key=lambda path: tuple(ranks[direction] for direction in task._path_directions(path)),
    )
    return task._paint_edges(grid, zip(best, best[1:]))


def python_mirror(grid: Any, settings: Any) -> list[list[int]]:
    chosen = _validate_settings(settings)["tie_order"]
    return python_mirror_for_order(grid, ORDER_DIRECTIONS[chosen])


def generate_episode(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    selected = _validate_settings(settings)
    train_inputs, test_inputs = sample_inputs(seed, demos, queries)
    program = rule_source(selected)
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": [
            {"input": grid, "output": python_mirror(grid, selected)}
            for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": python_mirror(grid, selected)}
            for grid in test_inputs
        ],
        "program_solution": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
    }


def setting_survivors(episode: Any) -> list[dict[str, str]]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a train list")
    survivors: list[dict[str, str]] = []
    for tie_order in ALLOWED_TIE_ORDERS:
        setting = {"tie_order": tie_order}
        if all(
            type(pair) is dict
            and python_mirror(pair.get("input"), setting) == pair.get("output")
            for pair in episode["train"]
        ):
            survivors.append(setting)
    return survivors


def total_order_audit(episode: Any) -> dict[str, Any]:
    """Finite adversarial audit over all 24 constant direction orders."""
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    survivors: list[dict[str, Any]] = []
    for order in itertools.permutations((0, 1, 2, 3)):
        if all(
            python_mirror_for_order(pair["input"], order) == pair["output"]
            for pair in episode["train"]
        ):
            disagreements = [
                index
                for index, pair in enumerate(episode["test"])
                if python_mirror_for_order(pair["input"], order) != pair["output"]
            ]
            survivors.append({"order": list(order), "query_disagreements": disagreements})
    return {"tested_orders": 24, "survivors": survivors}


def public_challenge(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    try:
        return {
            "train": [
                {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                for pair in episode["train"]
            ],
            "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
        }
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs need input/output grids") from error


def public_bytes(episode: Any) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: Any) -> str:
    return public_challenge_id(public_challenge(episode))
