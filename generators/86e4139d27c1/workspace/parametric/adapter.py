"""Native authoring adapter for canonical plus and causal survivor-route lessons."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import canonical_path, find_root


TASK_ID = "86e4139d27c1"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
CONTINUATIONS = ("plus_only", "survivor_route")
HYPOTHESES = CONTINUATIONS + (
    "original_first",
    "original_second",
    "original_third",
    "last_survivor",
    "horizontal_first",
    "paint_first_step",
    "paint_target",
)
_CARDINAL_PLUS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))


def _continuation(value: object) -> str:
    if type(value) is not str or value not in CONTINUATIONS:
        raise ValueError("continuation must be plus_only or survivor_route")
    return value


def grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 3 <= len(value) <= 30
        or type(value[0]) is not list
        or not 3 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 3..30 with exact integer colors 0..9")
    return value


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line))["task_id"] == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("require one exact canonical program")
    return programs.pop()


def program(settings: dict[str, object]) -> str:
    if type(settings) is not dict or set(settings) != {"continuation"}:
        raise ValueError("only the continuation setting is declared")
    continuation = _continuation(settings["continuation"])
    if continuation == "plus_only":
        return canonical_program()
    return (HERE / "survivor_route.rkt").read_text(encoding="utf-8")


def _blue_cells(value: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(value)
        for col, cell in enumerate(values)
        if cell == 1
    ]


def _stage_plus(value: list[list[int]]) -> tuple[list[list[int]], tuple[int, int], tuple[tuple[int, int], ...]]:
    blues = _blue_cells(value)
    if len(blues) != 3:
        raise ValueError("parametric scenes require exactly three blue markers")
    if any(cell in (3, 8) for row in value for cell in row):
        raise ValueError("green and azure are reserved for rule output")
    (row_a, col_a), (row_b, col_b) = blues[:2]
    midpoint = ((row_a + row_b) // 2, (col_a + col_b) // 2)
    footprint = tuple((midpoint[0] + dr, midpoint[1] + dc) for dr, dc in _CARDINAL_PLUS)
    output = [row[:] for row in value]
    for row, col in footprint:
        if 0 <= row < len(output) and 0 <= col < len(output[0]):
            output[row][col] = 3
    return output, midpoint, footprint


def _route_cells(midpoint: tuple[int, int], target: tuple[int, int]) -> list[tuple[int, int]]:
    row, col = midpoint
    route: list[tuple[int, int]] = []
    while (row, col) != target:
        if row < target[0]:
            row += 1
        elif row > target[0]:
            row -= 1
        elif col < target[1]:
            col += 1
        else:
            col -= 1
        route.append((row, col))
    return route[1:-1]


def _paint_route(stage: list[list[int]], midpoint: tuple[int, int], target: tuple[int, int]) -> list[list[int]]:
    output = [row[:] for row in stage]
    for row, col in _route_cells(midpoint, target):
        output[row][col] = 8
    return output


def observe(value: list[list[int]]) -> dict[str, object]:
    grid(value)
    blues = _blue_cells(value)
    stage, midpoint, footprint = _stage_plus(value)
    survivors = _blue_cells(stage)
    if not survivors:
        raise ValueError("stage A must leave at least one blue survivor")
    target = survivors[0]
    selected_overlap = sum(point not in survivors for point in blues[:2])
    return {
        "original_blues": tuple(blues),
        "midpoint": midpoint,
        "footprint": footprint,
        "stage_a": stage,
        "survivors": tuple(survivors),
        "survivor_target": target,
        "selected_overlap_count": selected_overlap,
        "route_cells": tuple(_route_cells(midpoint, target)),
    }


def transform(value: list[list[int]], continuation: str) -> list[list[int]]:
    continuation = _continuation(continuation)
    observed = observe(value)
    stage = observed["stage_a"]
    assert isinstance(stage, list)
    if continuation == "plus_only":
        return [row[:] for row in stage]
    return _paint_route(stage, observed["midpoint"], observed["survivor_target"])


def predict(value: list[list[int]], hypothesis: str) -> list[list[int]]:
    if hypothesis in CONTINUATIONS:
        return transform(value, hypothesis)
    observed = observe(value)
    original = observed["original_blues"]
    survivors = observed["survivors"]
    if hypothesis == "original_first":
        target = original[0]
    elif hypothesis == "original_second":
        target = original[1]
    elif hypothesis == "original_third":
        target = original[2]
    elif hypothesis == "last_survivor":
        target = survivors[-1]
    elif hypothesis == "horizontal_first":
        return _paint_route_variant(
            observed["stage_a"], observed["midpoint"], observed["survivor_target"], horizontal_first=True
        )
    elif hypothesis == "paint_first_step":
        return _paint_route_variant(
            observed["stage_a"], observed["midpoint"], observed["survivor_target"], skip_first=False
        )
    elif hypothesis == "paint_target":
        return _paint_route_variant(
            observed["stage_a"], observed["midpoint"], observed["survivor_target"], keep_target=False
        )
    else:
        raise ValueError("unknown declared hypothesis")
    return _paint_route(observed["stage_a"], observed["midpoint"], target)


_DEMO_SCENES = (
    ("overlap_both", 11, 13),
    ("overlap_none", 12, 14),
    ("overlap_one", 13, 15),
    ("diagonal", 14, 16),
    ("clipped", 15, 17),
    ("decorated", 16, 18),
)
_QUERY_SCENES = (
    ("overlap_one", 18, 20),
    ("clipped", 20, 22),
    ("decorated", 24, 26),
    ("stress30", 30, 30),
)
_DECOR_COLORS = (2, 4, 5, 6, 7, 9)


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"continuation"}:
        raise ValueError("only the continuation setting is declared")
    return _continuation(settings["continuation"])


def _full_route(
    midpoint: tuple[int, int],
    target: tuple[int, int],
    *,
    horizontal_first: bool = False,
) -> list[tuple[int, int]]:
    row, col = midpoint
    route: list[tuple[int, int]] = []
    while (row, col) != target:
        if horizontal_first and col != target[1]:
            col += 1 if col < target[1] else -1
        elif not horizontal_first and row != target[0]:
            row += 1 if row < target[0] else -1
        elif col != target[1]:
            col += 1 if col < target[1] else -1
        else:
            row += 1 if row < target[0] else -1
        route.append((row, col))
    return route


def _paint_route_variant(
    stage: list[list[int]],
    midpoint: tuple[int, int],
    target: tuple[int, int],
    *,
    horizontal_first: bool = False,
    skip_first: bool = True,
    keep_target: bool = True,
) -> list[list[int]]:
    route = _full_route(midpoint, target, horizontal_first=horizontal_first)
    start = 1 if skip_first else 0
    stop = -1 if keep_target else None
    cells = route[start:stop]
    output = [row[:] for row in stage]
    for row, col in cells:
        output[row][col] = 8
    return output


def _profile_points(profile: str, height: int, width: int, rng: random.Random) -> tuple[tuple[int, int], ...]:
    if profile == "overlap_both":
        row = 3 + rng.randrange(max(1, min(3, height - 7)))
        col = 4 + rng.randrange(max(1, min(3, width - 8)))
        points = ((row, col - 1), (row, col + 1), (height - 2, width - 2))
    elif profile == "overlap_none":
        row = 2 + rng.randrange(max(1, min(3, height - 6)))
        left = 1 + rng.randrange(2)
        right = width - 3 - rng.randrange(2)
        points = ((row, left), (row, right), (height - 2, width - 2))
    elif profile == "overlap_one":
        row = 2 + rng.randrange(max(1, min(3, height - 7)))
        col = 2 + rng.randrange(max(1, min(3, width - 8)))
        points = ((row, col), (row + 1, col + 3), (height - 2, width - 2))
    elif profile == "diagonal":
        row = 1 + rng.randrange(2)
        col = 1 + rng.randrange(2)
        points = ((row, col), (height // 2, width // 2 + 1), (height - 2, width - 2))
    elif profile == "clipped":
        left = 2 + rng.randrange(2)
        right = width - 3 - rng.randrange(2)
        points = ((0, left), (0, right), (height - 2, width - 2))
    elif profile == "decorated":
        row = 2 + rng.randrange(3)
        points = ((row, 2), (row, width - 4), (height - 2, width - 2))
    elif profile == "stress30":
        points = ((2, 3), (20, 23), (28, 28))
    else:
        raise ValueError(f"unknown scene profile: {profile}")
    if tuple(sorted(points)) != points or len(set(points)) != 3:
        raise AssertionError("scene markers must be distinct and row-major")
    return points


def _scene(profile: str, height: int, width: int, rng: random.Random) -> list[list[int]]:
    value = [[0] * width for _ in range(height)]
    points = _profile_points(profile, height, width, rng)
    for row, col in points:
        value[row][col] = 1
    observed = observe(value)
    if not observed["route_cells"]:
        raise AssertionError("scene must expose a substantive survivor route")
    route = set(_full_route(observed["midpoint"], observed["survivor_target"]))
    if route & (set(points) - {observed["survivor_target"]}):
        raise AssertionError("survivor route may not cross another blue marker")
    forbidden = set(points) | set(observed["footprint"]) | route
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in forbidden
    ]
    rng.shuffle(candidates)
    if profile == "stress30":
        count = 80
    elif profile == "decorated":
        count = min(40, max(20, height * width // 12))
    else:
        count = 2 + rng.randrange(4)
    for row, col in candidates[:count]:
        value[row][col] = rng.choice(_DECOR_COLORS)
    checked = observe(value)
    if checked["survivor_target"] != observed["survivor_target"] or checked["route_cells"] != observed["route_cells"]:
        raise AssertionError("decor changed the causal scene")
    return value


def generate(seed: int, settings: dict[str, object], demos: int, queries: int) -> dict[str, object]:
    _integer(seed, "seed", 0, 2**63 - 1)
    continuation = _settings(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 4, 4)
    rng = random.Random(hashlib.sha256(f"86e4139d27c1-survivor-input-v1:{seed}".encode()).digest())
    train = []
    test = []
    for profile, height, width in _DEMO_SCENES[:demos]:
        value = _scene(profile, height, width, rng)
        train.append({"input": value, "output": transform(value, continuation)})
    for profile, height, width in _QUERY_SCENES:
        value = _scene(profile, height, width, rng)
        test.append({"input": value, "output": transform(value, continuation)})
    inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(inputs) != len(set(inputs)):
        raise ValueError("distinct scene budget exhausted; no partial episode")
    return {"train": train, "test": test, "program_solution": program(settings)}


def _hash_grid(value: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def certificate(train: list[dict[str, object]], query_inputs: list[list[list[int]]]) -> dict[str, object]:
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("two through six teaching demonstrations are required")
    if type(query_inputs) is not list or len(query_inputs) != 4:
        raise ValueError("exactly four query inputs are required")
    for pair in train:
        if type(pair) is not dict or set(pair) < {"input", "output"}:
            raise ValueError("each demonstration needs input and output")
        grid(pair["input"])
        grid(pair["output"])
    for value in query_inputs:
        grid(value)
        observe(value)
    survivors = [
        hypothesis
        for hypothesis in HYPOTHESES
        if all(predict(pair["input"], hypothesis) == pair["output"] for pair in train)
    ]
    if len(survivors) != 1 or survivors[0] not in CONTINUATIONS:
        raise ValueError("demonstrations do not identify one continuation against declared rivals")
    witness_input = next(
        pair["input"] for pair in train if observe(pair["input"])["selected_overlap_count"] == 2
    )
    correct = predict(witness_input, "survivor_route")
    wrong = predict(witness_input, "original_first")
    predictions = [predict(value, survivors[0]) for value in query_inputs]
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demos": len(train),
        "queries": len(query_inputs),
        "predicted_query_sha256": [_hash_grid(value) for value in predictions],
        "causal_witness": {
            "selected_overlap_count": 2,
            "stage_a_survivor": list(observe(witness_input)["survivor_target"]),
            "wrong_pre_stage_target": list(observe(witness_input)["original_blues"][0]),
            "correct_output_sha256": _hash_grid(correct),
            "wrong_intermediate_output_sha256": _hash_grid(wrong),
        },
        "scope": "Finite declared rivals only; query answers were not provided to the certificate.",
    }
