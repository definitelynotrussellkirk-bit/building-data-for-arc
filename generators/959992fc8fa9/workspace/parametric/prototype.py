"""Native finite parametric family for ARC generator 959992fc8fa9.

The default ``intersection_policy=different_red`` is the exact canonical rule:
each sparse source paints its complete row and column; one reaching color stays
that color and two or more distinct reaching colors become red (2).

The nearby ``repeated_color_priority`` setting keeps the same source geometry
but adds a real input-dependent composition. Step A counts source colors and
identifies the unique color occurring twice. Step B resolves mixed-color
intersections: the repeated color wins only when it is one of the reaching
colors; other mixed intersections remain red.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any


TASK_ID = "959992fc8fa9"
PARAMETER_NAME = "intersection_policy"
POLICIES = ("different_red", "repeated_color_priority")
DEFAULT_SETTINGS = {PARAMETER_NAME: "different_red"}

_HOME = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
REPEATED_COLOR_PRIORITY_PROGRAM = (
    _HOME / "repeated-color-priority.rkt"
).read_text(encoding="utf-8")

DEMO_PROFILES = (
    (13, 13, 4, (1,), (11,)),
    (14, 14, 4, (0,), (0,)),
    (15, 15, 5, (14,), (14,)),
    (16, 16, 5, (0, 15), (0, 15)),
    (12, 18, 4, (0, 11), (0, 17)),
    (18, 12, 5, (0, 17), (0, 11)),
)
QUERY_PROFILES = (
    (13, 17, 4, (0,), (16,)),
    (17, 14, 5, (16,), (0,)),
    (22, 24, 5, (0, 21), (0, 23)),
    (30, 30, 5, (0, 29), (0, 29)),
)

_COLOR_TEMPLATES = {
    4: (
        (1, 4, 4, 8),
        (3, 6, 6, 9),
        (1, 5, 5, 7),
        (3, 7, 7, 9),
        (1, 6, 6, 9),
        (3, 5, 5, 8),
    ),
    5: (
        (1, 4, 4, 7, 9),
        (3, 6, 6, 8, 9),
        (1, 5, 5, 7, 8),
        (3, 7, 7, 8, 9),
        (1, 6, 6, 7, 9),
        (3, 5, 5, 8, 9),
    ),
}

SHORTCUTS = (
    "minimum_color_priority",
    "maximum_color_priority",
    "first_source_priority",
    "last_source_priority",
    "all_source_crossings_red",
    "global_repeated_at_every_crossing",
)

_PRIORITY_EXPRESSION = """(let find-priority
                     ((rest pixels))
                     (if (null? rest)
                         -1
                         (let* ((p (car rest))
                                (candidate (third p))
                                (count (for/sum ((q pixels))
                                         (if (= (third q) candidate) 1 0))))
                           (if (> count 1)
                               candidate
                               (find-priority (cdr rest))))))"""


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain only {PARAMETER_NAME}")
    policy = settings[PARAMETER_NAME]
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError(f"{PARAMETER_NAME} must be one of {POLICIES}")
    return policy


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> list[list[int]]:
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
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings: Any) -> str:
    """Return exact Racket source for one declared setting."""
    policy = _validate_settings(settings)
    return (
        CANONICAL_PROGRAM
        if policy == "different_red"
        else REPEATED_COLOR_PRIORITY_PROGRAM
    )


def counterfactual_program(kind: str = "first_source") -> str:
    """Return a bounded wrong-intermediate Racket program for witness replay."""
    if kind != "first_source":
        raise ValueError("only first_source is a retained counterfactual")
    old = f"(priority {_PRIORITY_EXPRESSION})"
    new = "(priority (third (first pixels)))"
    if REPEATED_COLOR_PRIORITY_PROGRAM.count(old) != 1:
        raise ValueError("priority-expression source guard failed")
    return REPEATED_COLOR_PRIORITY_PROGRAM.replace(old, new, 1)


def source_pixels(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    """Return non-background source pixels in row-major order."""
    _validate_grid(grid)
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def repeated_color_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    """Step A: identify the unique source color occurring exactly twice."""
    pixels = source_pixels(grid)
    if not 4 <= len(pixels) <= 5:
        raise ValueError("family inputs require four or five source pixels")
    if any(value == 2 for _, _, value in pixels):
        raise ValueError("family inputs reserve red 2 for output collisions")
    rows = [row for row, _, _ in pixels]
    cols = [col for _, col, _ in pixels]
    if len(rows) != len(set(rows)) or len(cols) != len(set(cols)):
        raise ValueError("source pixels must occupy distinct rows and columns")
    counts = Counter(value for _, _, value in pixels)
    repeated = [color for color, count in counts.items() if count == 2]
    if len(repeated) != 1 or any(count not in (1, 2) for count in counts.values()):
        raise ValueError("family inputs need exactly one repeated pair")
    return {
        "priority_color": repeated[0],
        "counts": dict(sorted(counts.items())),
        "source_count": len(pixels),
    }


def _resolve_with_priority(
    grid: list[list[int]], priority_color: int | None
) -> list[list[int]]:
    pixels = source_pixels(grid)
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            colors = {
                value
                for source_row, source_col, value in pixels
                if row == source_row or col == source_col
            }
            if not colors:
                value = 0
            elif len(colors) == 1:
                value = next(iter(colors))
            elif priority_color is not None and priority_color in colors:
                value = priority_color
            else:
                value = 2
            output[row][col] = value
    return output


def transform(grid: list[list[int]], settings: Any) -> list[list[int]]:
    """Independent Python label claim for a declared setting."""
    policy = _validate_settings(settings)
    intermediate = repeated_color_intermediate(grid)
    priority = (
        None
        if policy == "different_red"
        else int(intermediate["priority_color"])
    )
    return _resolve_with_priority(grid, priority)


def _source_count_crossings_red(grid: list[list[int]]) -> list[list[int]]:
    pixels = source_pixels(grid)
    output = [[0 for _ in row] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            reaching = [
                value
                for source_row, source_col, value in pixels
                if row == source_row or col == source_col
            ]
            if len(reaching) == 1:
                output[row][col] = reaching[0]
            elif len(reaching) > 1:
                output[row][col] = 2
    return output


def _global_repeated_at_every_crossing(grid: list[list[int]]) -> list[list[int]]:
    pixels = source_pixels(grid)
    priority = int(repeated_color_intermediate(grid)["priority_color"])
    output = [[0 for _ in row] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            reaching = [
                value
                for source_row, source_col, value in pixels
                if row == source_row or col == source_col
            ]
            if len(reaching) == 1:
                output[row][col] = reaching[0]
            elif len(reaching) > 1:
                output[row][col] = priority
    return output


def shortcut_output(grid: list[list[int]], shortcut: str) -> list[list[int]]:
    """Execute one named plausible but intentionally wrong rule."""
    pixels = source_pixels(grid)
    colors = [value for _, _, value in pixels]
    if shortcut == "minimum_color_priority":
        return _resolve_with_priority(grid, min(colors))
    if shortcut == "maximum_color_priority":
        return _resolve_with_priority(grid, max(colors))
    if shortcut == "first_source_priority":
        return _resolve_with_priority(grid, colors[0])
    if shortcut == "last_source_priority":
        return _resolve_with_priority(grid, colors[-1])
    if shortcut == "all_source_crossings_red":
        return _source_count_crossings_red(grid)
    if shortcut == "global_repeated_at_every_crossing":
        return _global_repeated_at_every_crossing(grid)
    raise ValueError(f"unknown shortcut: {shortcut}")


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _axis_values(
    size: int, count: int, forced: tuple[int, ...], rng: random.Random
) -> list[int]:
    selected: list[int] = []
    for value in forced:
        if value not in selected:
            selected.append(value)
    pool = [value for value in range(size) if value not in selected]
    rng.shuffle(pool)
    selected.extend(pool[: count - len(selected)])
    if len(selected) != count:
        raise RuntimeError("profile cannot supply enough distinct axis values")
    return selected


def _sample_grid(
    seed: int,
    split: str,
    index: int,
    profile: tuple[int, int, int, tuple[int, ...], tuple[int, ...]],
) -> list[list[int]]:
    height, width, count, forced_rows, forced_cols = profile
    rng = _rng(seed, split, index)
    rows = sorted(_axis_values(height, count, forced_rows, rng))
    cols = _axis_values(width, count, forced_cols, rng)
    rng.shuffle(cols)
    template_options = _COLOR_TEMPLATES[count]
    colors = template_options[(seed + index + (0 if split == "train" else 3)) % len(template_options)]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for (row, col), color in zip(zip(rows, cols), colors):
        grid[row][col] = color
    repeated_color_intermediate(grid)
    return grid


def sample_inputs(seed: int) -> dict[str, list[list[list[int]]]]:
    """Sample all six demonstrations and four stable queries, setting-neutrally."""
    _exact_int(seed, "seed", 0, 2**63 - 1)
    return {
        "train": [
            _sample_grid(seed, "train", index, profile)
            for index, profile in enumerate(DEMO_PROFILES)
        ],
        "test": [
            _sample_grid(seed, "test", index, profile)
            for index, profile in enumerate(QUERY_PROFILES)
        ],
    }


def generate(seed: int, settings: Any, demos: int, queries: int) -> dict[str, Any]:
    """Generate one deterministic private episode with stable count prefixes."""
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)
    _validate_settings(settings)
    sampled = sample_inputs(seed)
    train_inputs = sampled["train"][:demos]
    test_inputs = sampled["test"][:queries]
    return {
        "train": [
            {"input": copy.deepcopy(grid), "output": transform(grid, settings)}
            for grid in train_inputs
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": transform(grid, settings)}
            for grid in test_inputs
        ],
        "program_solution": program(settings),
    }


def lesson_certificate(
    train: list[dict[str, Any]], query_inputs: list[list[list[int]]]
) -> dict[str, Any]:
    """Fit finite declared settings and named shortcuts to demonstrations only."""
    if type(train) is not list or not train:
        raise ValueError("train must contain demonstrations")
    if type(query_inputs) is not list or not query_inputs:
        raise ValueError("query_inputs must contain at least one grid")

    settings_space = [
        {PARAMETER_NAME: "different_red"},
        {PARAMETER_NAME: "repeated_color_priority"},
    ]
    setting_rows: dict[str, dict[str, Any]] = {}
    survivors: list[dict[str, str]] = []
    for candidate in settings_space:
        predictions = [transform(pair["input"], candidate) for pair in train]
        fits = all(
            prediction == pair["output"]
            for prediction, pair in zip(predictions, train)
        )
        key = candidate[PARAMETER_NAME]
        setting_rows[key] = {
            "fits_all_demos": fits,
            "first_eliminating_demo": next(
                (
                    index
                    for index, (prediction, pair) in enumerate(zip(predictions, train))
                    if prediction != pair["output"]
                ),
                None,
            ),
        }
        if fits:
            survivors.append(copy.deepcopy(candidate))

    intended = survivors[0] if len(survivors) == 1 else None
    shortcut_rows: dict[str, dict[str, Any]] = {}
    surviving_shortcuts: list[str] = []
    for shortcut in SHORTCUTS:
        predictions = [shortcut_output(pair["input"], shortcut) for pair in train]
        fits = all(
            prediction == pair["output"]
            for prediction, pair in zip(predictions, train)
        )
        if fits:
            surviving_shortcuts.append(shortcut)
        query_disagreements = None
        if intended is not None:
            query_disagreements = sum(
                shortcut_output(grid, shortcut) != transform(grid, intended)
                for grid in query_inputs
            )
        shortcut_rows[shortcut] = {
            "fits_all_demos": fits,
            "first_eliminating_demo": next(
                (
                    index
                    for index, (prediction, pair) in enumerate(zip(predictions, train))
                    if prediction != pair["output"]
                ),
                None,
            ),
            "query_disagreements": query_disagreements,
        }

    return {
        "surviving_settings": survivors,
        "declared_settings": setting_rows,
        "surviving_shortcuts": surviving_shortcuts,
        "shortcuts": shortcut_rows,
        "query_outputs_consulted": False,
        "scope": "finite two-setting family plus six named shortcuts; not universal uniqueness",
    }


def public_projection(episode: dict[str, Any]) -> dict[str, Any]:
    """Return model-visible demos and query inputs only."""
    return {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            public_projection(episode),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def public_id(episode: dict[str, Any]) -> str:
    return hashlib.sha256(public_bytes(episode)).hexdigest()


def visible_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _exact_int(query_index, "query_index", 0, len(episode["test"]) - 1)
    return public_projection(
        {"train": episode["train"], "test": [episode["test"][query_index]]}
    )


def visible_turn_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    return (
        json.dumps(
            visible_turn(episode, query_index),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")
