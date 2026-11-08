#!/usr/bin/env python3
"""Deterministic overlap-policy family for ARC task ``b7e4aaffabac``.

Both settings use exactly the canonical two-rectangle input grammar.  The
canonical ``trimmed`` policy paints the gap only on the one-cell-inset interior
of the shared facing span.  The ``full`` policy performs the same object and
gap analysis, then paints the entire raw shared span.  Inputs are independent
of the selected setting, demonstrations are prefix-stable, and the four query
profiles are fixed independently of the demonstration count.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Sequence

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "b7e4aaffabac"
PARAMETER_NAME = "overlap_policy"
ALLOWED_SETTINGS = ("trimmed", "full")
DEFAULT_SETTING = "trimmed"
ALTERNATE_SETTING = "full"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
PROTOTYPE_VERSION = "1.0.0"

# (height, width, orientation, raw overlap, gap, perpendicular offset,
#  separation-axis edge policy).  The first two demonstrations deliberately
# oppose orientation and include both offset and boundary contact.  Query
# profiles are separate from demonstration profiles so changing demo count
# cannot silently change the query set.
_DEMO_PROFILES = (
    (12, 17, "horizontal", 5, 2, 1, "none"),
    (13, 18, "vertical", 6, 3, -1, "start"),
    (16, 21, "horizontal", 3, 1, 0, "end"),
    (18, 22, "vertical", 7, 4, 2, "none"),
    (20, 25, "horizontal", 8, 5, -2, "start"),
    (22, 27, "vertical", 4, 2, 0, "end"),
)
_QUERY_PROFILES = (
    (14, 19, "horizontal", 6, 3, 2, "none"),
    (19, 23, "vertical", 5, 1, -2, "start"),
    (24, 28, "horizontal", 7, 4, -1, "end"),
    (30, 30, "vertical", 9, 6, 1, "none"),
)

_FULL_REPLACEMENTS = (
    ("(lo (+ (max lr1 rr1) 1))", "(lo (max lr1 rr1))"),
    ("(hi (- (min lr2 rr2) 1))", "(hi (min lr2 rr2))"),
    ("(lo (+ (max tc1 bc1) 1))", "(lo (max tc1 bc1))"),
    ("(hi (- (min tc2 bc2) 1))", "(hi (min tc2 bc2))"),
)


def _exact_integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(
            f"{name} must be an exact integer in {low}..{high}; bool is forbidden"
        )
    return value


def _setting(value: Any) -> str:
    if type(value) is not str or value not in ALLOWED_SETTINGS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {value!r}")
    return value


def validate_settings(settings: dict[str, Any] | None) -> str:
    """Validate the native settings object and return its scalar policy."""
    if settings is None:
        return DEFAULT_SETTING
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain exactly {{{PARAMETER_NAME!r}}}")
    return _setting(settings[PARAMETER_NAME])


def _validate_counts(demos: Any, queries: Any) -> tuple[int, int]:
    return (
        _exact_integer(demos, "demos", MIN_DEMOS, MAX_DEMOS),
        _exact_integer(queries, "queries", QUERY_COUNT, QUERY_COUNT),
    )


@lru_cache(maxsize=1)
def canonical_program() -> str:
    """Load the unique canonical Racket program from this exact source tree."""
    root = find_root(__file__)
    programs = set()
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and type(row.get("program_solution")) is str:
            programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}, found {len(programs)}")
    program = next(iter(programs))
    if not program.strip():
        raise ValueError("canonical program is empty")
    return program


@lru_cache(maxsize=1)
def full_program() -> str:
    """Materialize the alternate program with four source-guarded edits."""
    source = canonical_program()
    result = source
    for old, new in _FULL_REPLACEMENTS:
        if result.count(old) != 1:
            raise ValueError(f"canonical overlap fragment changed; re-review required: {old}")
        result = result.replace(old, new, 1)
    if result == source:
        raise ValueError("full-span program did not differ from canonical source")
    return result


def program_for(overlap_policy: str = DEFAULT_SETTING) -> str:
    setting = _setting(overlap_policy)
    return canonical_program() if setting == DEFAULT_SETTING else full_program()


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        raise ValueError("grid dimensions must be at most 30x30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors 0..9")
    return height, width


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = _validate_grid(grid)
    unseen = {(row, col) for row in range(height) for col in range(width) if grid[row][col] != 0}
    components: list[dict[str, Any]] = []
    while unseen:
        seed = min(unseen)
        color = grid[seed[0]][seed[1]]
        stack = [seed]
        cells: set[tuple[int, int]] = set()
        while stack:
            row, col = stack.pop()
            if (row, col) not in unseen or grid[row][col] != color:
                continue
            unseen.remove((row, col))
            cells.add((row, col))
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    stack.append(neighbor)
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        r1, c1, r2, c2 = min(rows), min(cols), max(rows), max(cols)
        rectangle = {
            (row, col)
            for row in range(r1, r2 + 1)
            for col in range(c1, c2 + 1)
        }
        if cells != rectangle:
            raise ValueError("every nonzero component must be a solid rectangle")
        components.append(
            {
                "color": color,
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
                "cells": cells,
            }
        )
    if len(components) != 2:
        raise ValueError(f"expected exactly two nonzero rectangles, found {len(components)}")
    if len({row["color"] for row in components}) != 2 or any(
        row["color"] in (0, 8) for row in components
    ):
        raise ValueError("rectangle colors must be distinct and exclude 0 and 8")
    return components


def analyze_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    """Return the step-A geometry used by either overlap policy."""
    height, width = _validate_grid(grid)
    first, second = _components(grid)
    columns_disjoint = first["c2"] < second["c1"] or second["c2"] < first["c1"]
    rows_disjoint = first["r2"] < second["r1"] or second["r2"] < first["r1"]
    if columns_disjoint == rows_disjoint:
        raise ValueError("rectangles must be separated on exactly one axis")

    if columns_disjoint:
        left, right = sorted((first, second), key=lambda item: item["c1"])
        raw_lo = max(left["r1"], right["r1"])
        raw_hi = min(left["r2"], right["r2"])
        gap_lo, gap_hi = left["c2"] + 1, right["c1"] - 1
        orientation = "horizontal"
        full_cells = {
            (row, col)
            for row in range(raw_lo, raw_hi + 1)
            for col in range(gap_lo, gap_hi + 1)
        }
        trimmed_cells = {
            (row, col)
            for row in range(raw_lo + 1, raw_hi)
            for col in range(gap_lo, gap_hi + 1)
        }
        offset = right["r1"] - left["r1"]
    else:
        top, bottom = sorted((first, second), key=lambda item: item["r1"])
        raw_lo = max(top["c1"], bottom["c1"])
        raw_hi = min(top["c2"], bottom["c2"])
        gap_lo, gap_hi = top["r2"] + 1, bottom["r1"] - 1
        orientation = "vertical"
        full_cells = {
            (row, col)
            for row in range(gap_lo, gap_hi + 1)
            for col in range(raw_lo, raw_hi + 1)
        }
        trimmed_cells = {
            (row, col)
            for row in range(gap_lo, gap_hi + 1)
            for col in range(raw_lo + 1, raw_hi)
        }
        offset = bottom["c1"] - top["c1"]

    raw_overlap = raw_hi - raw_lo + 1
    gap = gap_hi - gap_lo + 1
    if raw_overlap < 3 or gap < 1 or not trimmed_cells:
        raise ValueError("lawful scenes require raw overlap >= 3 and a nonempty gap")
    edge_touch = any(
        item["r1"] == 0
        or item["c1"] == 0
        or item["r2"] == height - 1
        or item["c2"] == width - 1
        for item in (first, second)
    )
    boxes = [
        {
            "color": item["color"],
            "r1": item["r1"],
            "c1": item["c1"],
            "r2": item["r2"],
            "c2": item["c2"],
        }
        for item in sorted((first, second), key=lambda item: (item["r1"], item["c1"]))
    ]
    return {
        "orientation": orientation,
        "boxes": boxes,
        "gap": gap,
        "gap_bounds": [gap_lo, gap_hi],
        "raw_overlap": raw_overlap,
        "raw_span": [raw_lo, raw_hi],
        "trimmed_span": [raw_lo + 1, raw_hi - 1],
        "offset": offset,
        "edge_touch": edge_touch,
        "full_cells": [list(cell) for cell in sorted(full_cells)],
        "trimmed_cells": [list(cell) for cell in sorted(trimmed_cells)],
    }


def apply_from_intermediate(
    grid: list[list[int]],
    intermediate: dict[str, Any],
    overlap_policy: str,
) -> list[list[int]]:
    """Apply step B using an explicit step-A record (used by causal evidence)."""
    _validate_grid(grid)
    setting = _setting(overlap_policy)
    if type(intermediate) is not dict:
        raise ValueError("intermediate must be an object")
    key = "trimmed_cells" if setting == "trimmed" else "full_cells"
    cells = intermediate.get(key)
    if type(cells) is not list:
        raise ValueError(f"intermediate must contain {key}")
    result = deepcopy(grid)
    height, width = len(result), len(result[0])
    for cell in cells:
        if (
            type(cell) is not list
            or len(cell) != 2
            or any(type(value) is not int for value in cell)
        ):
            raise ValueError("intermediate cells must be [row, col] exact integers")
        row, col = cell
        if not 0 <= row < height or not 0 <= col < width:
            raise ValueError("intermediate cell lies outside the grid")
        if result[row][col] != 0:
            raise ValueError("intermediate bridge cell must lie on the zero background")
        result[row][col] = 8
    return result


def apply_python(grid: list[list[int]], overlap_policy: str) -> list[list[int]]:
    """Independent Python claim; qualification replays exact Racket programs."""
    setting = _setting(overlap_policy)
    source = deepcopy(grid)
    intermediate = analyze_intermediate(source)
    return apply_from_intermediate(source, intermediate, setting)


def _seeded_rng(seed: int, stream: str, index: int) -> random.Random:
    payload = f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:{stream}:{index}".encode()
    digest = hashlib.sha256(payload).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _horizontal_scene(
    seed: int,
    stream: str,
    index: int,
    height: int,
    width: int,
    overlap: int,
    gap: int,
    offset: int,
    edge: str,
) -> list[list[int]]:
    if edge not in {"none", "start", "end"}:
        raise ValueError(f"unknown edge policy {edge!r}")
    rng = _seeded_rng(seed, stream, index)
    colors = rng.sample((1, 2, 3, 4, 5, 6, 7, 9), 2)
    left_width = 2 + rng.randrange(3)
    right_width = 2 + rng.randrange(3)
    total_width = left_width + gap + right_width
    if total_width > width:
        raise AssertionError("profile does not fit the separation axis")
    remaining_cols = width - total_width
    if edge == "start":
        start_col = 0
    elif edge == "end":
        start_col = remaining_cols
    else:
        if remaining_cols < 2:
            raise AssertionError("non-edge profile needs margins on both sides")
        start_col = 1 + rng.randrange(remaining_cols - 1)

    extra = abs(offset)
    union_height = overlap + extra
    remaining_rows = height - union_height
    if remaining_rows < 2:
        raise AssertionError("profile does not fit with perpendicular margins")
    start_row = 1 + rng.randrange(remaining_rows - 1)
    if offset >= 0:
        left_rows = (start_row, start_row + overlap + extra - 1)
        right_rows = (start_row + extra, start_row + extra + overlap - 1)
    else:
        left_rows = (start_row + extra, start_row + extra + overlap - 1)
        right_rows = (start_row, start_row + overlap + extra - 1)
    left_cols = (start_col, start_col + left_width - 1)
    right_cols = (left_cols[1] + gap + 1, left_cols[1] + gap + right_width)

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for color, rows, cols in (
        (colors[0], left_rows, left_cols),
        (colors[1], right_rows, right_cols),
    ):
        for row in range(rows[0], rows[1] + 1):
            for col in range(cols[0], cols[1] + 1):
                if grid[row][col] != 0:
                    raise AssertionError("profile rectangles collided")
                grid[row][col] = color
    return grid


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _build_scene(
    seed: int,
    stream: str,
    index: int,
    profile: tuple[int, int, str, int, int, int, str],
) -> list[list[int]]:
    height, width, orientation, overlap, gap, offset, edge = profile
    if orientation == "horizontal":
        grid = _horizontal_scene(
            seed, stream, index, height, width, overlap, gap, offset, edge
        )
    elif orientation == "vertical":
        grid = _transpose(
            _horizontal_scene(
                seed, stream, index, width, height, overlap, gap, offset, edge
            )
        )
    else:
        raise AssertionError(f"unknown orientation {orientation!r}")
    info = analyze_intermediate(grid)
    if (
        info["orientation"] != orientation
        or info["raw_overlap"] != overlap
        or info["gap"] != gap
        or bool(info["offset"]) != bool(offset)
        or info["edge_touch"] != (edge != "none")
    ):
        raise AssertionError(f"constructed profile drifted: {profile!r} -> {info!r}")
    return grid


def _sample_inputs(seed: int, demos: int, queries: int) -> tuple[list[list[list[int]]], list[str]]:
    seed = _exact_integer(seed, "seed", 0, MAX_SEED)
    demos, queries = _validate_counts(demos, queries)
    grids = [
        _build_scene(seed, "demo", index, _DEMO_PROFILES[index])
        for index in range(demos)
    ]
    profiles = [f"demo_{index + 1}" for index in range(demos)]
    grids.extend(
        _build_scene(seed, "query", index, _QUERY_PROFILES[index])
        for index in range(queries)
    )
    profiles.extend(f"query_{index + 1}" for index in range(queries))
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in grids]
    if len(serialized) != len(set(serialized)):
        raise AssertionError("parametric sampler emitted duplicate inputs")
    return grids, profiles


def build_claimed_episode(
    seed: int,
    overlap_policy: str,
    demos: int,
    queries: int,
) -> dict[str, Any]:
    """Build deterministic labels; native qualification independently replays Racket."""
    seed = _exact_integer(seed, "seed", 0, MAX_SEED)
    setting = _setting(overlap_policy)
    demos, queries = _validate_counts(demos, queries)
    inputs, profiles = _sample_inputs(seed, demos, queries)
    outputs = [apply_python(grid, setting) for grid in inputs]
    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(output)}
        for grid, output in zip(inputs, outputs)
    ]
    intermediates = [analyze_intermediate(grid) for grid in inputs]
    program = program_for(setting)
    return {
        "schema": "b7e4aaffabac-overlap-policy-episode-v1",
        "status": "proposed_unapproved",
        "training_admitted": False,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {PARAMETER_NAME: setting},
        "program": program,
        "program_solution": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "train": pairs[:demos],
        "test": pairs[demos:],
        "input_profiles": {"train": profiles[:demos], "test": profiles[demos:]},
        "intermediates": {
            "train": intermediates[:demos],
            "test": intermediates[demos:],
        },
    }


def surviving_settings(pairs: list[dict[str, Any]]) -> list[str]:
    if type(pairs) is not list or not pairs:
        raise ValueError("pairs must be a nonempty list")
    survivors: list[str] = []
    for setting in ALLOWED_SETTINGS:
        fits = True
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("each pair must contain input and output")
            if apply_python(pair["input"], setting) != pair["output"]:
                fits = False
                break
        if fits:
            survivors.append(setting)
    return survivors


_ORIENTATION_MARKER = "(define horizontal (or (< c2a c1b) (< c2b c1a)))"


def orientation_shortcut_program(overlap_policy: str, orientation: str) -> str:
    """Finite shortcut rival that hard-codes one separation orientation."""
    selected = _setting(overlap_policy)
    if orientation not in {"horizontal", "vertical"}:
        raise ValueError("orientation must be 'horizontal' or 'vertical'")
    source = program_for(selected)
    if source.count(_ORIENTATION_MARKER) != 1:
        raise ValueError("canonical orientation fragment changed; re-review required")
    replacement = "(define horizontal #t)" if orientation == "horizontal" else "(define horizontal #f)"
    result = source.replace(_ORIENTATION_MARKER, replacement, 1)
    if result == source:
        raise ValueError("orientation shortcut did not differ from selected program")
    return result


def rival_programs(overlap_policy: str) -> dict[str, str]:
    selected = _setting(overlap_policy)
    alternate = next(value for value in ALLOWED_SETTINGS if value != selected)
    return {
        "alternate_setting": program_for(alternate),
        "horizontal_only": orientation_shortcut_program(selected, "horizontal"),
        "vertical_only": orientation_shortcut_program(selected, "vertical"),
    }


def public_challenge(
    episode: dict[str, Any],
    query_indices: Sequence[int] | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode needs nonempty train/test lists")
    if query_indices is None:
        indices = list(range(len(test)))
    else:
        if not isinstance(query_indices, (list, tuple)):
            raise ValueError("query_indices must be a list or tuple")
        indices = []
        for value in query_indices:
            index = _exact_integer(value, "query index", 0, len(test) - 1)
            if index in indices:
                raise ValueError("query indices must be distinct")
            indices.append(index)
    candidate = {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": deepcopy(test[index]["input"])} for index in indices],
    }
    return json.loads(public_challenge_bytes(candidate))


def public_id(episode: dict[str, Any], query_indices: Sequence[int] | None = None) -> str:
    return public_challenge_id(public_challenge(episode, query_indices=query_indices))


def sequential_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    test = episode.get("test") if type(episode) is dict else None
    if type(test) is not list or not test:
        raise ValueError("episode needs nonempty test pairs")
    index = _exact_integer(query_index, "query_index", 0, len(test) - 1)
    if index == 0:
        return public_challenge(episode, query_indices=[0])
    return {"test": [{"input": deepcopy(test[index]["input"])}]}


__all__ = [
    "ALLOWED_SETTINGS",
    "DEFAULT_SETTING",
    "MAX_SEED",
    "PARAMETER_NAME",
    "QUERY_COUNT",
    "analyze_intermediate",
    "apply_from_intermediate",
    "apply_python",
    "build_claimed_episode",
    "canonical_program",
    "full_program",
    "orientation_shortcut_program",
    "program_for",
    "public_challenge",
    "public_id",
    "rival_programs",
    "sequential_turn",
    "surviving_settings",
    "validate_settings",
]
