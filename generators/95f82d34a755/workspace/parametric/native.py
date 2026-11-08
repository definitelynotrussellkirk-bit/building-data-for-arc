"""Native parametric family for header-equality field construction.

The canonical setting preserves the selected Racket source byte-for-byte.  The
alternative first constructs that complete equality field, derives its first
nonzero coordinate in row-major order, and cyclically aligns that coordinate to
output (0, 0).
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "95f82d34a755"
PARAMETER = "match_alignment"
CANONICAL = "in_place"
ALTERNATIVE = "first_match_to_origin"
SETTINGS = (CANONICAL, ALTERNATIVE)
HOME = Path(__file__).resolve().parent

# output height, output width, requested first-match row, requested first-match col
DEMO_SPECS = (
    (4, 5, 1, 2),
    (6, 7, 2, 1),
    (8, 9, 3, 4),
    (10, 12, 0, 3),
    (14, 16, 4, 0),
    (18, 20, 5, 6),
)
QUERY_SPECS = (
    (9, 11, 2, 3),
    (15, 19, 4, 2),
    (23, 26, 6, 7),
    (29, 29, 8, 9),
)


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS}")
    return value


def program(settings: dict[str, Any]) -> str:
    alignment = _setting(settings)
    filename = "canonical.rkt" if alignment == CANONICAL else "first_match_to_origin.rkt"
    return (HOME / filename).read_text(encoding="utf-8")


def counterfactual_program(anchor: tuple[int, int] | list[int] = (0, 0)) -> str:
    """Materialize the alternative with Step A replaced by a forced anchor."""
    if (
        type(anchor) not in (tuple, list)
        or len(anchor) != 2
        or any(type(value) is not int or value < 0 for value in anchor)
    ):
        raise ValueError("anchor must contain two nonnegative exact integers")
    source = (HOME / "first_match_to_origin.rkt").read_text(encoding="utf-8")
    row_old = "(ar (first anchor))"
    col_old = "(ac (second anchor))"
    if source.count(row_old) != 1 or source.count(col_old) != 1:
        raise ValueError("alternative rule changed; review counterfactual materialization")
    return source.replace(row_old, f"(ar {anchor[0]})").replace(col_old, f"(ac {anchor[1]})")


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    height, width = len(grid), len(grid[0])
    if not 2 <= height <= 30 or not 2 <= width <= 30:
        raise ValueError("header grid dimensions must be 2..30")
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be exact integer ARC colors")
    return height, width


def match_field(grid: list[list[int]]) -> list[list[int]]:
    height, width = _validate_grid(grid)
    return [
        [grid[r + 1][0] if grid[r + 1][0] == grid[0][c + 1] else 0 for c in range(width - 1)]
        for r in range(height - 1)
    ]


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    field = match_field(grid)
    matches = [(r, c) for r, row in enumerate(field) for c, value in enumerate(row) if value]
    if not matches:
        raise ValueError("header equality field must contain a nonzero match")
    colors = sorted({value for row in field for value in row if value})
    return {
        "field": field,
        "first_match": list(matches[0]),
        "match_count": len(matches),
        "match_colors": colors,
        "row_labels": [row[0] for row in grid[1:]],
        "column_labels": list(grid[0][1:]),
    }


def shift_field(field: list[list[int]], row_shift: int, col_shift: int) -> list[list[int]]:
    height, width = len(field), len(field[0])
    return [
        [field[(r + row_shift) % height][(c + col_shift) % width] for c in range(width)]
        for r in range(height)
    ]


def transform(grid: list[list[int]], alignment: str) -> list[list[int]]:
    if alignment not in SETTINGS:
        raise ValueError(f"unknown alignment: {alignment!r}")
    analysis = analyze(grid)
    if alignment == CANONICAL:
        return copy.deepcopy(analysis["field"])
    row, col = analysis["first_match"]
    return shift_field(analysis["field"], row, col)


def _rng(seed: int, *parts: Any) -> random.Random:
    payload = json.dumps([TASK_ID, "native-equality-v1", seed, *parts], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _palette(seed: int) -> tuple[int, int, int, int, int]:
    colors = list(range(1, 10))
    _rng(seed, "palette").shuffle(colors)
    return colors[0], colors[1], colors[2], colors[3], colors[4]


def _shared_sequence(
    length: int, values: tuple[int, int, int], rng: random.Random, *, first: int
) -> list[int]:
    if length <= 0:
        return []
    rest = [values[(index + rng.randrange(3)) % 3] for index in range(max(0, length - 1))]
    sequence = [first, *rest]
    if length >= 3:
        for index, value in enumerate(values):
            sequence[index] = value
        sequence[0] = first
        # Reinsert any shared color displaced by the forced first value.
        missing = [value for value in values if value not in sequence]
        for offset, value in enumerate(missing, start=1):
            sequence[-offset] = value
    return sequence


def sample_input(
    seed: int, index: int, spec: tuple[int, int, int, int]
) -> tuple[list[list[int]], dict[str, Any]]:
    out_h, out_w, anchor_r, anchor_c = spec
    if not (0 <= anchor_r < out_h and 0 <= anchor_c < out_w):
        raise ValueError("requested first match is outside the output field")
    row_only, col_only, pivot, shared_a, shared_b = _palette(seed)
    shared = (pivot, shared_a, shared_b)
    rng = _rng(seed, index, "headers", spec)
    row_tail = _shared_sequence(out_h - anchor_r, shared, rng, first=pivot)
    col_tail = _shared_sequence(out_w - anchor_c, shared, _rng(seed, index, "columns", spec), first=pivot)
    row_labels = [row_only] * anchor_r + row_tail
    col_labels = [col_only] * anchor_c + col_tail
    grid = [[0 for _ in range(out_w + 1)] for _ in range(out_h + 1)]
    grid[0][1:] = col_labels
    for r, value in enumerate(row_labels, start=1):
        grid[r][0] = value
    noise_rng = _rng(seed, index, "body", spec)
    for r in range(1, out_h + 1):
        for c in range(1, out_w + 1):
            # The body is deliberately irrelevant but nontrivial; the two headers
            # alone determine the exact output.
            grid[r][c] = 0 if noise_rng.random() < 0.58 else noise_rng.randrange(1, 10)
    analysis = analyze(grid)
    if analysis["first_match"] != [anchor_r, anchor_c]:
        raise AssertionError("sampler failed to preserve requested first match")
    if len(set(analysis["match_colors"])) < 3:
        raise AssertionError("sampler failed to exercise all shared match colors")
    return grid, {
        "input_shape": [out_h + 1, out_w + 1],
        "output_shape": [out_h, out_w],
        "first_match": [anchor_r, anchor_c],
        "match_count": analysis["match_count"],
        "match_colors": analysis["match_colors"],
        "palette": [row_only, col_only, pivot, shared_a, shared_b],
    }


def _first_anchor(grid: list[list[int]]) -> tuple[int, int]:
    row, col = analyze(grid)["first_match"]
    return row, col


def _row_only_shift(grid: list[list[int]]) -> list[list[int]]:
    analysis = analyze(grid)
    return shift_field(analysis["field"], analysis["first_match"][0], 0)


def _column_only_shift(grid: list[list[int]]) -> list[list[int]]:
    analysis = analyze(grid)
    return shift_field(analysis["field"], 0, analysis["first_match"][1])


def _fixed_shift(grid: list[list[int]], row: int, col: int) -> list[list[int]]:
    return shift_field(analyze(grid)["field"], row, col)


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "first_match_row_only": _row_only_shift,
    "first_match_column_only": _column_only_shift,
    "fixed_shift_0_1": lambda grid: _fixed_shift(grid, 0, 1),
    "fixed_shift_1_0": lambda grid: _fixed_shift(grid, 1, 0),
    "fixed_shift_1_1": lambda grid: _fixed_shift(grid, 1, 1),
}


def lesson_certificate(
    demos: list[dict[str, Any]], query_inputs: list[list[list[int]]]
) -> dict[str, Any]:
    if type(demos) is not list or not demos or type(query_inputs) is not list or not query_inputs:
        raise ValueError("nonempty demonstrations and query inputs are required")
    for pair in demos:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("each demonstration needs input and output")
        analyze(pair["input"])
        _validate_grid(pair["output"])
    for grid in query_inputs:
        analyze(grid)
    surviving_values = [
        value
        for value in SETTINGS
        if all(transform(pair["input"], value) == pair["output"] for pair in demos)
    ]
    surviving_settings = [{PARAMETER: value} for value in surviving_values]
    intended_queries = (
        [transform(grid, surviving_values[0]) for grid in query_inputs]
        if len(surviving_values) == 1
        else []
    )
    surviving_rivals: list[str] = []
    ambiguous_rivals: list[dict[str, Any]] = []
    for name, rival in RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            surviving_rivals.append(name)
            disagreements = [
                index
                for index, (grid, intended) in enumerate(zip(query_inputs, intended_queries))
                if rival(grid) != intended
            ]
            if disagreements:
                ambiguous_rivals.append({"name": name, "query_indices": disagreements})
    return {
        "surviving_settings": surviving_settings,
        "surviving_rivals": surviving_rivals,
        "ambiguous_rivals": ambiguous_rivals,
        "query_count": len(query_inputs),
        "scope": "two declared settings and five finite one-axis/fixed-shift shortcuts; demonstrations fitted before query disagreement checks",
    }


def generate(
    seed: int, settings: dict[str, Any], demos: int, queries: int
) -> dict[str, Any]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    alignment = _setting(settings)
    demos = _exact_int(demos, 3, 6, "demos")
    queries = _exact_int(queries, 1, 4, "queries")
    pairs: dict[str, list[dict[str, Any]]] = {"train": [], "test": []}
    sampling: dict[str, list[dict[str, Any]]] = {"train": [], "test": []}
    for split, count, specs, offset in (
        ("train", demos, DEMO_SPECS, 0),
        ("test", queries, QUERY_SPECS, 1000),
    ):
        for index in range(count):
            grid, receipt = sample_input(seed, offset + index, specs[index])
            pairs[split].append({"input": grid, "output": transform(grid, alignment)})
            sampling[split].append(receipt)
    encoded = [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in pairs.values()
        for pair in split
    ]
    if len(encoded) != len(set(encoded)):
        raise ValueError("episode contains duplicate inputs")
    certificate = lesson_certificate(
        pairs["train"], [pair["input"] for pair in pairs["test"]]
    )
    if certificate["surviving_settings"] != [copy.deepcopy(settings)]:
        raise ValueError("visible demonstrations do not uniquely teach the declared setting")
    if certificate["ambiguous_rivals"]:
        raise ValueError(f"finite shortcut ambiguity: {certificate['ambiguous_rivals']}")
    return {
        **pairs,
        "program_solution": program(settings),
        "settings": copy.deepcopy(settings),
        "seed": seed,
        "certificate": certificate,
        "sampling": sampling,
        "status": "proposed",
        "training_admitted": False,
    }


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes

    index = _exact_int(index, 0, len(episode["test"]) - 1, "query index")
    return json.loads(
        public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]})
    )
