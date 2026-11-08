"""Native episode-level bridge-axis family for task 7515881f2786.

The canonical setting bridges consecutive cyan anchors on both axes. Nearby
settings retain the same anchor grammar and consecutive-pair semantics while
selecting only horizontal or only vertical bridge construction.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any, Sequence

from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "7515881f2786"
PROTOTYPE_VERSION = "2.0.0-native"
PARAMETER_NAME = "bridge_axes"
ALLOWED_SETTINGS = ("both", "horizontal", "vertical")
DEFAULT_SETTING = "both"
CANONICAL_RULE_HASH = "7327f2eb0272"
_UNSET = object()
_HERE = Path(__file__).resolve().parent
_PROGRAMS = {
    "both": (_HERE / "canonical.rkt").read_text(encoding="utf-8"),
    "horizontal": (_HERE / "horizontal.rkt").read_text(encoding="utf-8"),
    "vertical": (_HERE / "vertical.rkt").read_text(encoding="utf-8"),
}
_GENERATOR_PATH = _HERE.parents[1] / "generator.py"
_GENERATOR_SHA256 = hashlib.sha256(_GENERATOR_PATH.read_bytes()).hexdigest()

_DEMO_SPECS = (
    (10, 12, 0),
    (12, 15, 1),
    (14, 18, 0),
    (16, 20, 1),
    (18, 23, 0),
    (20, 24, 1),
)
_QUERY_SPECS = (
    (11, 14, 1),
    (17, 21, 0),
    (24, 27, 1),
    (30, 30, 0),
)

CANDIDATE_RULES = (
    "both",
    "horizontal",
    "vertical",
    "none",
    "exactly_two_both",
    "horizontal_exact2_vertical_all",
    "horizontal_all_vertical_exact2",
    "longest_per_axis",
    "chains_only_both",
)

Grid = list[list[int]]
Cell = tuple[int, int]


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _validate_seed(seed: Any) -> int:
    return _integer("seed", seed, 0, 2**63 - 1)


def _validate_setting(setting: Any) -> str:
    if type(setting) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {list(ALLOWED_SETTINGS)}")
    return setting


def choose_setting(seed: int) -> str:
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}|bridge-axes-v2|{seed}".encode()).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def program_for(setting: Any) -> str:
    return _PROGRAMS[_validate_setting(setting)]


def _validated_grid(grid: Sequence[Sequence[int]]) -> Grid:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty rectangular sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty sequences")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or value not in (0, 8) for row in grid for value in row):
        raise ValueError("grid must use only integer colors 0 and 8")
    return [list(row) for row in grid]


def _groups(grid: Grid) -> tuple[list[Cell], dict[int, list[int]], dict[int, list[int]]]:
    dots: list[Cell] = []
    rows: dict[int, list[int]] = defaultdict(list)
    cols: dict[int, list[int]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 8:
                dots.append((row, col))
                rows[row].append(col)
                cols[col].append(row)
    for values in rows.values():
        values.sort()
    for values in cols.values():
        values.sort()
    return dots, rows, cols


def _fill_lines(
    grid: Grid,
    *,
    horizontal: bool,
    vertical: bool,
    horizontal_pred=lambda values: len(values) >= 2,
    vertical_pred=lambda values: len(values) >= 2,
) -> Grid:
    source = _validated_grid(grid)
    output = [row[:] for row in source]
    _, rows, cols = _groups(source)
    if horizontal:
        for row, anchors in rows.items():
            if not horizontal_pred(anchors):
                continue
            for left, right in zip(anchors, anchors[1:]):
                for col in range(left + 1, right):
                    if output[row][col] == 0:
                        output[row][col] = 8
    if vertical:
        for col, anchors in cols.items():
            if not vertical_pred(anchors):
                continue
            for top, bottom in zip(anchors, anchors[1:]):
                for row in range(top + 1, bottom):
                    if output[row][col] == 0:
                        output[row][col] = 8
    return output


def solve(grid: Grid, setting: Any) -> Grid:
    selected = _validate_setting(setting)
    return _fill_lines(
        grid,
        horizontal=selected in ("both", "horizontal"),
        vertical=selected in ("both", "vertical"),
    )


def apply_python(grid: Sequence[Sequence[int]], setting: Any) -> Grid:
    return solve(_validated_grid(grid), setting)


def _longest_per_axis(grid: Grid) -> Grid:
    source = _validated_grid(grid)
    output = [row[:] for row in source]
    _, rows, cols = _groups(source)
    row_lines = [(values[-1] - values[0], row, values) for row, values in rows.items() if len(values) >= 2]
    col_lines = [(values[-1] - values[0], col, values) for col, values in cols.items() if len(values) >= 2]
    if row_lines:
        _, row, anchors = max(row_lines)
        for left, right in zip(anchors, anchors[1:]):
            for col in range(left + 1, right):
                output[row][col] = 8
    if col_lines:
        _, col, anchors = max(col_lines)
        for top, bottom in zip(anchors, anchors[1:]):
            for row in range(top + 1, bottom):
                output[row][col] = 8
    return output


def solve_candidate(grid: Grid, candidate: Any) -> Grid:
    if type(candidate) is not str or candidate not in CANDIDATE_RULES:
        raise ValueError(f"candidate must be one of {list(CANDIDATE_RULES)}")
    if candidate in ALLOWED_SETTINGS:
        return solve(grid, candidate)
    if candidate == "none":
        return _validated_grid(grid)
    if candidate == "exactly_two_both":
        return _fill_lines(grid, horizontal=True, vertical=True,
                           horizontal_pred=lambda v: len(v) == 2,
                           vertical_pred=lambda v: len(v) == 2)
    if candidate == "horizontal_exact2_vertical_all":
        return _fill_lines(grid, horizontal=True, vertical=True,
                           horizontal_pred=lambda v: len(v) == 2)
    if candidate == "horizontal_all_vertical_exact2":
        return _fill_lines(grid, horizontal=True, vertical=True,
                           vertical_pred=lambda v: len(v) == 2)
    if candidate == "longest_per_axis":
        return _longest_per_axis(grid)
    if candidate == "chains_only_both":
        return _fill_lines(grid, horizontal=True, vertical=True,
                           horizontal_pred=lambda v: len(v) >= 3,
                           vertical_pred=lambda v: len(v) >= 3)
    raise AssertionError(candidate)


def _rng(seed: int, stream: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|native-v2|{seed}|{stream}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _base_points(height: int, width: int, kind: int) -> set[Cell]:
    if kind == 0:
        chain_row = 1
        chain_col = width // 2
        middle_row = height // 2
        return {
            (chain_row, 0), (chain_row, chain_col), (chain_row, width - 1),
            (middle_row, chain_col), (height - 1, chain_col),
            (height - 2, 1), (height - 2, width - 2),
            (3, 1),
        }
    chain_col = width - 2
    chain_row = height // 2
    inner_col = width // 3
    return {
        (0, chain_col), (chain_row, chain_col), (height - 1, chain_col),
        (chain_row, 0), (chain_row, inner_col),
        (1, 1), (height - 2, 1),
        (1, width - 4),
    }


def _transform(points: set[Cell], height: int, width: int, rng: random.Random) -> set[Cell]:
    result = set(points)
    if rng.randrange(2):
        result = {(height - 1 - r, c) for r, c in result}
    if rng.randrange(2):
        result = {(r, width - 1 - c) for r, c in result}
    if height == width and rng.randrange(2):
        result = {(c, r) for r, c in result}
    return result


def _scene(seed: int, stream: str, index: int, spec: tuple[int, int, int]) -> Grid:
    height, width, kind = spec
    rng = _rng(seed, stream, index)
    points = _transform(_base_points(height, width, kind), height, width, rng)
    if not 4 <= len(points) <= 8:
        raise RuntimeError("bridge profile left the 4..8 anchor grammar")
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in points:
        grid[row][col] = 8
    analysis = analyze_input(grid)
    if not analysis["horizontal_segments"] or not analysis["vertical_segments"]:
        raise RuntimeError("profile must expose both axes")
    if len({tuple(tuple(row) for row in solve(grid, mode)) for mode in ALLOWED_SETTINGS}) != 3:
        raise RuntimeError("profile does not distinguish every axis setting")
    return grid


def analyze_input(grid: Grid) -> dict[str, Any]:
    source = _validated_grid(grid)
    dots, rows, cols = _groups(source)
    horizontal_segments = [
        (row, left, right)
        for row, anchors in rows.items()
        for left, right in zip(anchors, anchors[1:])
        if right - left >= 2
    ]
    vertical_segments = [
        (col, top, bottom)
        for col, anchors in cols.items()
        for top, bottom in zip(anchors, anchors[1:])
        if bottom - top >= 2
    ]
    return {
        "height": len(source),
        "width": len(source[0]),
        "anchors": dots,
        "horizontal_segments": horizontal_segments,
        "vertical_segments": vertical_segments,
        "horizontal_chain_lines": [row for row, values in rows.items() if len(values) >= 3],
        "vertical_chain_lines": [col for col, values in cols.items() if len(values) >= 3],
    }


def episode_inputs(seed: int, *, demos: int, queries: int) -> dict[str, list[Grid]]:
    _validate_seed(seed)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    train = [_scene(seed, "demo", i, _DEMO_SPECS[i]) for i in range(demos)]
    test = [_scene(seed, "query", i, _QUERY_SPECS[i]) for i in range(queries)]
    return {"train": train, "test": test}


def generate_episode(seed: int, setting: Any, *, demos: int, queries: int) -> dict[str, Any]:
    _validate_seed(seed)
    selected = _validate_setting(setting)
    inputs = episode_inputs(seed, demos=demos, queries=queries)

    def pairs(split: str):
        return [
            {
                "input": grid,
                "output": solve(grid, selected),
                "sampling": {"seed": seed, "stream": split, "index": index},
            }
            for index, grid in enumerate(inputs[split])
        ]

    program = program_for(selected)
    return {
        "schema": "7515881f2786-native-parametric-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {PARAMETER_NAME: selected},
        "parameter": {PARAMETER_NAME: selected},
        "program_solution": program,
        "program": program,
        "generator_source": str(_GENERATOR_PATH.relative_to(_HERE.parents[3])),
        "generator_sha256": _GENERATOR_SHA256,
        "train": pairs("train"),
        "test": pairs("test"),
    }


def build_episode(seed: int, *, setting: object = _UNSET, n_train: int = 4, n_test: int = 1) -> dict[str, Any]:
    selected = choose_setting(seed) if setting is _UNSET else _validate_setting(setting)
    return generate_episode(seed, selected, demos=n_train, queries=n_test)


def episode_errors(episode: Any) -> list[str]:
    if not isinstance(episode, dict):
        return ["episode must be a mapping"]
    parameter = episode.get("parameter")
    if not isinstance(parameter, dict) or PARAMETER_NAME not in parameter:
        return [f"episode must declare parameter {PARAMETER_NAME!r}"]
    try:
        selected = _validate_setting(parameter[PARAMETER_NAME])
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if episode.get("program") != program_for(selected):
        return ["episode program does not match its selected parameter"]
    errors: list[str] = []
    rivals = [value for value in ALLOWED_SETTINGS if value != selected]
    for split_name in ("train", "test"):
        pairs = episode.get(split_name)
        if not isinstance(pairs, list) or not pairs:
            errors.append(f"episode needs at least one {split_name} pair")
            continue
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
                errors.append(f"{split_name}[{index}] must contain input and output")
                continue
            try:
                expected = solve(pair["input"], selected)
                rival_outputs = [solve(pair["input"], rival) for rival in rivals]
            except (TypeError, ValueError) as exc:
                errors.append(f"{split_name}[{index}] invalid: {exc}")
                continue
            if pair["output"] != expected:
                errors.append(f"{split_name}[{index}] output disagrees with selected setting")
            if any(output == expected for output in rival_outputs):
                errors.append(f"{split_name}[{index}] does not distinguish every alternative setting")
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    errors = episode_errors(episode)
    if errors:
        raise ValueError("invalid episode: " + "; ".join(errors))
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_view(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index is outside this episode")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(challenge: dict[str, Any]) -> bytes:
    return public_challenge_bytes(challenge)


def public_id(challenge: dict[str, Any]) -> str:
    return public_challenge_id(challenge)


def intermediate_for(grid: Grid, setting: Any) -> dict[str, Any]:
    selected = _validate_setting(setting)
    analysis = analyze_input(grid)
    return {
        "selected_axes": [axis for axis in ("horizontal", "vertical") if selected in ("both", axis)],
        "horizontal_consecutive_pairs": [list(value) for value in analysis["horizontal_segments"]],
        "vertical_consecutive_pairs": [list(value) for value in analysis["vertical_segments"]],
    }
