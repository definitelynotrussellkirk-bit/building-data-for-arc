"""Source/mirror matching with an input-dependent match-count pointer variant.

The canonical setting reports every candidate that equals the color-2 key or
its horizontal mirror.  The alternate setting performs that same comparison as
step A, counts the resulting matches, then uses the count as a one-based pointer
into the reading-order candidates for step B.  Thus the marked position need
not itself be a match, and an off-by-one or nonmatch-count intermediate changes
the final answer.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable

TASK_ID = "26f02d922ca0"
MODES = ("all_matches", "match_count_pointer")
HERE = Path(__file__).resolve().parent
PROGRAM_PATHS = {
    "all_matches": HERE / "canonical.rkt",
    "match_count_pointer": HERE / "match-count-pointer.rkt",
}

_BASE_SOURCE = HERE.parents[1] / "generator.py"
_BASE_BODY = _BASE_SOURCE.read_bytes()
_BASE_NAME = "_26f02d922ca0_base_" + hashlib.sha256(_BASE_BODY).hexdigest()
_BASE_SPEC = importlib.util.spec_from_file_location(_BASE_NAME, _BASE_SOURCE)
if _BASE_SPEC is None or _BASE_SPEC.loader is None:
    raise ImportError("cannot load adjacent reviewed base generator")
BASE = importlib.util.module_from_spec(_BASE_SPEC)
sys.modules[_BASE_NAME] = BASE
exec(compile(_BASE_BODY, str(_BASE_SOURCE), "exec"), BASE.__dict__)

Grid = list[list[int]]
Shape = tuple[tuple[int, int], ...]


def _exact_int(value: Any, name: str, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise TypeError(f"{name} must be an exact integer in {lo}..{hi}; bool is forbidden")
    return value


def validate_mode(value: Any) -> str:
    if type(value) is not str or value not in MODES:
        raise ValueError(f"report_mode must be one of {MODES}")
    return value


def validate_request(seed: Any, demos: Any, queries: Any) -> None:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 4, 6)
    _exact_int(queries, "queries", 1, 4)


def program_for(mode: str) -> str:
    return PROGRAM_PATHS[validate_mode(mode)].read_text(encoding="utf-8")


def match_flags(grid: Grid) -> list[int]:
    errors = BASE.self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return BASE.rule_mirror(grid)[0]


def pointer_from_flags(flags: list[int]) -> Grid:
    if type(flags) is not list or not 2 <= len(flags) <= 4 or any(v not in {0, 8} for v in flags):
        raise ValueError("flags must be a 2..4 element list over {0,8}")
    matches = flags.count(8)
    if not 1 <= matches < len(flags):
        raise ValueError("pointer requires a mixed match vector")
    return [[8 if index == matches - 1 else 0 for index in range(len(flags))]]


def pointer_from_nonmatch_count(flags: list[int]) -> Grid:
    nonmatches = flags.count(0)
    return [[8 if index == nonmatches - 1 else 0 for index in range(len(flags))]]


def pointer_first_match(flags: list[int]) -> Grid:
    position = flags.index(8)
    return [[8 if index == position else 0 for index in range(len(flags))]]


def pointer_last_match(flags: list[int]) -> Grid:
    position = len(flags) - 1 - list(reversed(flags)).index(8)
    return [[8 if index == position else 0 for index in range(len(flags))]]


def mark_first_match_count(flags: list[int]) -> Grid:
    matches = flags.count(8)
    return [[8 if index < matches else 0 for index in range(len(flags))]]


def solve(grid: Grid, mode: str) -> Grid:
    mode = validate_mode(mode)
    flags = match_flags(grid)
    return [flags] if mode == "all_matches" else pointer_from_flags(flags)


def _predicate_for_profile(profile: int) -> Callable[[Grid], bool]:
    def pred(grid: Grid) -> bool:
        flags = match_flags(grid)
        if profile == 0:
            return len(flags) == 4 and flags.count(8) == 2 and flags[1] == 0
        if profile == 1:
            return len(flags) == 4 and flags.count(8) == 3 and flags[2] == 0
        if profile == 2:
            return len(flags) == 3 and flags.count(8) == 1 and flags[0] == 0
        return len(flags) == 3 and flags.count(8) == 2 and flags[1] == 0
    return pred


def _select_base_scene(seed: int, profile: int, ordinal: int) -> Grid:
    predicate = _predicate_for_profile(profile)
    # The schedule profile is sample_index mod 4.  Search only within that
    # profile, starting at a seed-specific offset, until the desired semantic
    # contrast is present.  This is constructive bounded selection, not label
    # rejection after episode assembly.
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{profile}|{ordinal}".encode()).digest()
    start = int.from_bytes(digest[:2], "big") % 64
    for attempt in range(256):
        sample_index = profile + 4 * (start + ordinal * 257 + attempt)
        grid = BASE.generate(seed, sample_index, difficulty="medium")
        if predicate(grid):
            return grid
    raise RuntimeError(f"could not construct profile {profile} contrast")


def _paint_shape(grid: Grid, top: int, left: int, shape: Shape, color: int) -> None:
    for row, col in shape:
        rr, cc = top + row, left + col
        if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])):
            raise ValueError("shape does not fit stress scene")
        if grid[rr][cc] != 0:
            raise ValueError("stress objects overlap")
        grid[rr][cc] = color


def _stress_shape(seed: int) -> Shape:
    # A connected asymmetric 7x7 hook/zigzag with enough mass to make the
    # 30x30 boundary case substantive rather than a padded tiny puzzle.
    cells = (
        {(0, c) for c in range(7)}
        | {(r, 0) for r in range(1, 7)}
        | {(6, c) for c in range(1, 4)}
        | {(r, 3) for r in range(3, 6)}
        | {(3, c) for c in range(4, 6)}
        | {(4, 5), (5, 5)}
    )
    rng = random.Random(int.from_bytes(hashlib.sha256(f"{TASK_ID}|stress|{seed}".encode()).digest()[:16], "big"))
    if rng.random() < 0.5:
        cells = {(6 - r, c) for r, c in cells}
    return BASE._normalize(cells)


def _stress_scene(seed: int) -> Grid:
    key = _stress_shape(seed)
    mirror = BASE._mirror(key)
    different = BASE._normalize((r, c) for r in range(5) for c in range(5))
    if different in {key, mirror} or not BASE._connected4(different):
        raise AssertionError("invalid stress distractor")
    grid = [[0 for _ in range(30)] for _ in range(30)]
    _paint_shape(grid, 1, 1, key, 2)
    _paint_shape(grid, 1, 11, key, 3)
    _paint_shape(grid, 1, 21, different, 4)
    _paint_shape(grid, 16, 2, mirror, 5)
    _paint_shape(grid, 16, 13, key, 6)
    errors = BASE.self_check(grid)
    if errors:
        raise AssertionError("stress scene violates base grammar: " + "; ".join(errors))
    if match_flags(grid) != [8, 0, 8, 8]:
        raise AssertionError("stress scene match pattern drifted")
    return grid


def episode_inputs(seed: int) -> dict[str, list[Grid]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    train = [
        _select_base_scene(seed, profile, ordinal)
        for ordinal, profile in enumerate((0, 1, 2, 3, 0, 1))
    ]
    test = [
        _select_base_scene(seed ^ 0x5A17, profile, ordinal + 10)
        for ordinal, profile in enumerate((0, 1, 2))
    ] + [_stress_scene(seed)]
    frozen = {json.dumps(grid, separators=(",", ":")) for grid in train + test}
    if len(frozen) != len(train) + len(test):
        raise RuntimeError("constructed duplicate inputs")
    return {"train": train, "test": test}


def generate_episode(seed: int, mode: str, demos: int = 4, queries: int = 4) -> dict[str, Any]:
    validate_request(seed, demos, queries)
    mode = validate_mode(mode)
    bank = episode_inputs(seed)
    return {
        "train": [
            {"input": grid, "output": solve(grid, mode)}
            for grid in bank["train"][:demos]
        ],
        "test": [
            {"input": grid, "output": solve(grid, mode)}
            for grid in bank["test"][:queries]
        ],
        "program_solution": program_for(mode),
    }


def teaching_survivors(train: list[dict[str, Grid]]) -> list[str]:
    return [
        mode
        for mode in MODES
        if all(solve(pair["input"], mode) == pair["output"] for pair in train)
    ]


def _rival_outputs(grid: Grid) -> dict[str, Grid]:
    flags = match_flags(grid)
    return {
        "canonical_all_matches": [flags],
        "declared_count_pointer": pointer_from_flags(flags),
        "nonmatch_count_pointer": pointer_from_nonmatch_count(flags),
        "first_match_pointer": pointer_first_match(flags),
        "last_match_pointer": pointer_last_match(flags),
        "fixed_first_pointer": [[8] + [0] * (len(flags) - 1)],
        "mark_first_match_count": mark_first_match_count(flags),
    }


def finite_rival_holes(
    train: list[dict[str, Grid]], test: list[dict[str, Grid]], selected_mode: str
) -> list[dict[str, Any]]:
    validate_mode(selected_mode)
    names = tuple(_rival_outputs(train[0]["input"]))
    holes: list[dict[str, Any]] = []
    for name in names:
        if all(_rival_outputs(pair["input"])[name] == pair["output"] for pair in train):
            disagreements = [
                index
                for index, pair in enumerate(test)
                if _rival_outputs(pair["input"])[name] != pair["output"]
            ]
            if disagreements:
                holes.append({"rival": name, "query_disagreements": disagreements})
    return holes
