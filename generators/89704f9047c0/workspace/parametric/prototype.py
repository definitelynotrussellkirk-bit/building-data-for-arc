#!/usr/bin/env python3
"""Episode-fixed tie-preference variants for nearest-corner filling.

The input grammar is unchanged: four distinct nonzero corner markers on a black
rectangle.  The parameters only decide which side wins exact Manhattan-distance
ties.  Inputs are sampled without consulting the settings so all four variants
receive matched demonstrations and queries.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import canonical_path, find_root, public_challenge_id


TASK_ID = "89704f9047c0"
PROTOTYPE_VERSION = "1.0.0"
ROW_TIES = ("top", "bottom")
COLUMN_TIES = ("left", "right")
DEFAULT_SETTINGS = {"row_tie": "top", "column_tie": "left"}
SETTINGS = tuple(
    {"row_tie": row_tie, "column_tie": column_tie}
    for row_tie in ROW_TIES
    for column_tie in COLUMN_TIES
)
DEMO_DIMS = ((5, 6), (6, 7), (5, 7), (6, 6), (7, 8), (8, 9))
QUERY_DIMS = (
    (29, 30),
    (30, 29),
    (29, 29),
    (30, 30),
    (27, 30),
    (30, 27),
    (27, 29),
    (29, 27),
)

_CORNER_FACTS = (
    "(list 0 0 (at g 0 0) 0)",
    "(list 0 (- (cols g) 1) (at g 0 (- (cols g) 1)) 1)",
    "(list (- (rows g) 1) 0 (at g (- (rows g) 1) 0) 2)",
    "(list (- (rows g) 1) (- (cols g) 1) (at g (- (rows g) 1) (- (cols g) 1)) 3)",
)
_CORNER_FACT_TEMPLATES = (
    "(list 0 0 (at g 0 0) {rank})",
    "(list 0 (- (cols g) 1) (at g 0 (- (cols g) 1)) {rank})",
    "(list (- (rows g) 1) 0 (at g (- (rows g) 1) 0) {rank})",
    "(list (- (rows g) 1) (- (cols g) 1) (at g (- (rows g) 1) (- (cols g) 1)) {rank})",
)


def _root(root: Path | str | None = None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


def _canonical_program(*, root: Path | str | None = None) -> str:
    matches: list[str] = []
    with canonical_path(_root(root)).open(encoding="utf-8") as stream:
        for raw in stream:
            if not raw.strip():
                continue
            row = json.loads(raw)
            if row.get("task_id") == TASK_ID:
                value = row.get("program_solution")
                if type(value) is str and value.strip():
                    matches.append(value)
    if len(matches) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}, found {len(matches)}")
    return matches[0]


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"row_tie", "column_tie"}:
        raise ValueError("settings must contain exactly row_tie and column_tie")
    row_tie = value["row_tie"]
    column_tie = value["column_tie"]
    if type(row_tie) is not str or row_tie not in ROW_TIES:
        raise ValueError(f"row_tie must be one of {ROW_TIES}, got {row_tie!r}")
    if type(column_tie) is not str or column_tie not in COLUMN_TIES:
        raise ValueError(f"column_tie must be one of {COLUMN_TIES}, got {column_tie!r}")
    return {"row_tie": row_tie, "column_tie": column_tie}


def _preference_order(settings: dict[str, str]) -> tuple[int, int, int, int]:
    chosen = _settings(settings)
    top = (0, 1) if chosen["column_tie"] == "left" else (1, 0)
    bottom = (2, 3) if chosen["column_tie"] == "left" else (3, 2)
    return (*top, *bottom) if chosen["row_tie"] == "top" else (*bottom, *top)


def _priority_ranks(settings: dict[str, str]) -> tuple[int, int, int, int]:
    ranks = [0, 0, 0, 0]
    for rank, corner_index in enumerate(_preference_order(settings)):
        ranks[corner_index] = rank
    return tuple(ranks)


def program(settings: Any, *, root: Path | str | None = None) -> str:
    """Return exact canonical Racket or a priority-only bounded variant."""
    chosen = _settings(settings)
    canonical = _canonical_program(root=root)
    if chosen == DEFAULT_SETTINGS:
        return canonical
    result = canonical
    for corner_index, (old, template) in enumerate(zip(_CORNER_FACTS, _CORNER_FACT_TEMPLATES)):
        if result.count(old) != 1:
            raise ValueError(f"canonical rule changed at corner priority site {corner_index}")
        result = result.replace(old, template.format(rank=_priority_ranks(chosen)[corner_index]))
    return result


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 2 <= len(value) <= 30
        or type(value[0]) is not list
        or not 2 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a rectangular 2..30 ARC grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    corners = (value[0][0], value[0][-1], value[-1][0], value[-1][-1])
    if any(color == 0 for color in corners) or len(set(corners)) != 4:
        raise ValueError("the four corners must be distinct nonzero colors")
    corner_cells = {(0, 0), (0, width - 1), (len(value) - 1, 0), (len(value) - 1, width - 1)}
    if any(
        value[row][column] != 0
        for row in range(len(value))
        for column in range(width)
        if (row, column) not in corner_cells
    ):
        raise ValueError("only the four corners may be nonzero")
    return deepcopy(value)


def apply_python(grid: Any, settings: Any) -> list[list[int]]:
    """Independent mirror used for authoring; protected Racket verifies labels."""
    source = _grid(grid)
    chosen = _settings(settings)
    height, width = len(source), len(source[0])
    colors = (source[0][0], source[0][-1], source[-1][0], source[-1][-1])
    positions = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    ranks = _priority_ranks(chosen)
    return [
        [
            colors[
                min(
                    range(4),
                    key=lambda index: (
                        abs(row - positions[index][0]) + abs(column - positions[index][1]),
                        ranks[index],
                    ),
                )
            ]
            for column in range(width)
        ]
        for row in range(height)
    ]


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"{TASK_ID}|{PROTOTYPE_VERSION}|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _input(seed: int, split: str, index: int, dims: tuple[int, int]) -> list[list[int]]:
    height, width = dims
    rng = _rng(seed, split, index)
    palette = rng.sample(range(1, 10), 4)
    # A second independent shuffle prevents sorted-palette roles from becoming
    # coupled to the deterministic dimension schedule.
    rng.shuffle(palette)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1] = palette
    return grid


def generate_episode(seed: Any, settings: Any, *, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    """Build a deterministic fixed-setting episode with independent counts."""
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, len(DEMO_DIMS), "demos")
    queries = _integer(queries, 1, len(QUERY_DIMS), "queries")
    chosen = _settings(settings)

    train = []
    for index, dims in enumerate(DEMO_DIMS[:demos]):
        grid = _input(seed, "demo", index, dims)
        train.append({"input": grid, "output": apply_python(grid, chosen)})
    test = []
    for index, dims in enumerate(QUERY_DIMS[:queries]):
        grid = _input(seed, "query", index, dims)
        test.append({"input": grid, "output": apply_python(grid, chosen)})

    episode = {
        "schema": "89704f9047c0-tie-preference-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "settings": deepcopy(chosen),
        "program": program(chosen),
        "train": train,
        "test": test,
    }
    errors = episode_errors(episode)
    if errors:
        raise AssertionError("constructed invalid episode: " + "; ".join(errors))
    return episode


def teaching_survivors(episode: Any) -> list[dict[str, str]]:
    """Return finite settings whose Python outputs fit all demonstrations."""
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a train list")
    survivors = []
    for settings in SETTINGS:
        if all(
            type(pair) is dict
            and "input" in pair
            and "output" in pair
            and apply_python(pair["input"], settings) == pair["output"]
            for pair in episode["train"]
        ):
            survivors.append(deepcopy(settings))
    return survivors


def episode_errors(episode: Any) -> list[str]:
    if type(episode) is not dict:
        return ["episode must be a dictionary"]
    errors: list[str] = []
    try:
        chosen = _settings(episode.get("settings"))
    except ValueError as error:
        return [str(error)]
    if episode.get("program") != program(chosen):
        errors.append("episode program does not match settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        errors.append("episode needs 2..6 demonstrations")
        train = []
    if type(test) is not list or not 1 <= len(test) <= 8:
        errors.append("episode needs 1..8 queries")
        test = []
    seen: set[str] = set()
    teaching_inputs_valid = bool(train)
    for split, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            label = f"{split}[{index}]"
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                errors.append(f"{label} must contain input and output")
                if split == "train":
                    teaching_inputs_valid = False
                continue
            try:
                source = _grid(pair["input"])
                expected = apply_python(source, chosen)
            except ValueError as error:
                errors.append(f"{label} invalid input: {error}")
                if split == "train":
                    teaching_inputs_valid = False
                continue
            key = json.dumps(source, separators=(",", ":"))
            if key in seen:
                errors.append(f"{label} duplicates an earlier input")
            seen.add(key)
            if pair["output"] != expected:
                errors.append(f"{label} output does not match settings")
    if teaching_inputs_valid and teaching_survivors({"train": train}) != [chosen]:
        errors.append("demonstrations do not identify the selected setting uniquely")
    return errors


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    """Expose demos plus exactly one unlabeled query, with no count/future hints."""
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if type(query_index) is not int or isinstance(query_index, bool):
        raise TypeError("query_index must be an exact integer")
    if not 0 <= query_index < len(episode["test"]):
        raise IndexError("query_index is outside the private episode")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_turn_id(episode: Any, query_index: Any = 0) -> str:
    return public_challenge_id(public_turn(episode, query_index))
