#!/usr/bin/env python3
"""Source-bound endpoint-policy family for ARC task 96ebf3053dbe.

The input distribution is independent of the hidden setting.  The canonical
``opposite`` setting preserves the selected canonical Racket source byte for
byte.  The alternate ``adjacent`` setting changes only which endpoint of each
6-bar receives the moved 2/5 pair.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import random
from typing import Iterable, Sequence

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "96ebf3053dbe"
VERSION = "endpoint-policy-v1"
PARAMETER_NAME = "destination_endpoint"
ALLOWED_SETTINGS = ("opposite", "adjacent")
DEFAULT_SETTING = "opposite"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
CANONICAL_SHA256 = "839e4ae1c265d3f0e7fba6ab8a2348618baa0fc4456d5a235509329b93f3bb5e"
GENERATOR_SHA256 = "569f634b21f20e43ceea612e4456f6f9fef56c6c53ff9e89c594eac8987a9467"

_CANONICAL_CHOSEN = """(define chosen
                           (if (> bh bw)
                               (if (and (< maxr (- h 1)) (= (at g (+ maxr 1) minc) 2))
                                   (list minr minc)
                                   (if (and (> minr 0) (= (at g (- minr 1) minc) 2))
                                       (list maxr minc)
                                       (list maxr minc)))
                               (if (and (> minc 0) (= (at g minr (- minc 1)) 2))
                                   (list minr maxc)
                                   (if (and
                                         (< maxc (- w 1))
                                         (= (at g minr (+ maxc 1)) 2))
                                       (list minr minc)
                                       (list minr minc)))))"""

_ADJACENT_CHOSEN = """(define chosen
                           (if (> bh bw)
                               (if (and (< maxr (- h 1)) (= (at g (+ maxr 1) minc) 2))
                                   (list maxr minc)
                                   (if (and (> minr 0) (= (at g (- minr 1) minc) 2))
                                       (list minr minc)
                                       (list maxr minc)))
                               (if (and (> minc 0) (= (at g minr (- minc 1)) 2))
                                   (list minr minc)
                                   (if (and
                                         (< maxc (- w 1))
                                         (= (at g minr (+ maxc 1)) 2))
                                       (list minr maxc)
                                       (list minr minc)))))"""


_SKIP_ANCHOR_CHOSEN = """(define chosen (list minr minc))"""
_PAINT_SELECTED = """(set! result (set-cell result rr cc 2))
                         (when
                           (and (>= ref-r 0) (< ref-r nine-row))
                           (set! result (set-cell result ref-r cc 5)))"""
_ERASE_ONLY_PAINT = """(void)"""

_PROFILES = (
    "vertical_top",
    "vertical_bottom",
    "horizontal_left",
    "horizontal_right",
    "mixed_sparse",
    "balanced",
    "mixed_dense",
)
_GENERATOR = None


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _exact_integer(value, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(value) -> str:
    if type(value) is not str or value not in ALLOWED_SETTINGS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}")
    return value


def validate_settings(settings) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"Declare exactly {PARAMETER_NAME}=opposite|adjacent")
    return _setting(settings[PARAMETER_NAME])


def _grid(value) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid dimensions must be 1..30")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return [row[:] for row in value]


def _generator():
    global _GENERATOR
    if _GENERATOR is None:
        module, _, digest = load_selected_generator(TASK_ID, root=find_root(__file__))
        if digest != GENERATOR_SHA256:
            raise ValueError("Production generator changed; re-review the parametric family")
        _GENERATOR = module
    return _GENERATOR


def canonical_program() -> str:
    programs = set()
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row.get("program_solution"))
    if len(programs) != 1:
        raise ValueError("Expected one exact canonical program for the selected task")
    source = programs.pop()
    if (
        type(source) is not str
        or _sha256(source) != CANONICAL_SHA256
        or source.count(_CANONICAL_CHOSEN) != 1
    ):
        raise ValueError("Canonical authority changed; re-review endpoint materialization")
    return source


def program_for(destination_endpoint: str) -> str:
    setting = _setting(destination_endpoint)
    source = canonical_program()
    if setting == DEFAULT_SETTING:
        return source
    alternate = source.replace(_CANONICAL_CHOSEN, _ADJACENT_CHOSEN, 1)
    if alternate == source or alternate.count(_ADJACENT_CHOSEN) != 1:
        raise ValueError("Could not materialize the adjacent-endpoint program")
    return alternate


def skip_anchor_program() -> str:
    """A finite causal rival: skip marker-side inspection and always use min/min."""
    source = canonical_program()
    result = source.replace(_CANONICAL_CHOSEN, _SKIP_ANCHOR_CHOSEN, 1)
    if result == source or result.count(_SKIP_ANCHOR_CHOSEN) != 1:
        raise ValueError("Could not materialize the skip-anchor rival")
    return result


def erase_only_program() -> str:
    """A finite shortcut rival that erases the old scene but paints no new pair."""
    source = canonical_program()
    if source.count(_PAINT_SELECTED) != 1:
        raise ValueError("Canonical paint fragment changed; re-review erase-only rival")
    result = source.replace(_PAINT_SELECTED, _ERASE_ONLY_PAINT, 1)
    if result == source:
        raise ValueError("Could not materialize the erase-only rival")
    return result


def rival_programs(destination_endpoint: str) -> dict[str, str]:
    selected = _setting(destination_endpoint)
    alternate = next(value for value in ALLOWED_SETTINGS if value != selected)
    return {
        "alternate_setting": program_for(alternate),
        "skip_anchor": skip_anchor_program(),
        "erase_only": erase_only_program(),
    }


def _adjacent_endpoint(record: dict) -> tuple[int, int]:
    cells = record["cells"]
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    minr, maxr = min(rows), max(rows)
    minc, maxc = min(cols), max(cols)
    direction = record["anchor_direction"]
    orientation = record["orientation"]
    if orientation == "vertical":
        return (minr, minc) if direction == "top" else (maxr, minc)
    if orientation == "horizontal":
        return (minr, minc) if direction == "left" else (minr, maxc)
    return minr, minc


def apply_python(grid, destination_endpoint: str) -> list[list[int]]:
    """Independent Python statement of the two endpoint policies."""
    setting = _setting(destination_endpoint)
    source = _grid(grid)
    analysis = _generator()._analysis(source)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    if setting == "opposite":
        return [row[:] for row in analysis["output"]]

    divider = analysis["divider"]
    result = [row[:] for row in source]
    for row in range(divider):
        for col, value in enumerate(source[row]):
            if value == 5:
                result[row][col] = 7
    for row in range(divider + 1, len(source)):
        for col, value in enumerate(source[row]):
            if value in (2, 6):
                result[row][col] = 7
    for record in analysis["records"]:
        row, col = _adjacent_endpoint(record)
        reflected = 2 * divider - row
        if not 0 <= reflected < divider:
            raise ValueError("Selected endpoint reflection must lie above the divider")
        result[row][col] = 2
        result[reflected][col] = 5
    return result


def _stress_grid(seed: int) -> list[list[int]]:
    """A lawful 29x30 balanced scene with long bars and boundary contact."""
    height, width, divider = 29, 30, 14
    grid = [[7] * width for _ in range(height)]
    grid[divider] = [9] * width

    # Horizontal jitter retains the proof obligations while making seeds useful.
    jitter = random.Random(int(_sha256(f"{VERSION}:stress:{seed}"), 16)).randint(0, 1)
    components = [
        ({(row, 2 + jitter) for row in range(16, 22)}, (15, 2 + jitter)),       # top
        ({(row, 14 + jitter) for row in range(21, 27)}, (27, 14 + jitter)),     # bottom
        ({(18, col) for col in range(6 + jitter, 14 + jitter)}, (18, 5 + jitter)),
        ({(27, col) for col in range(21, 29)}, (27, 29)),                       # right boundary
    ]
    for cells, anchor in components:
        for row, col in cells:
            grid[row][col] = 6
        row, col = anchor
        grid[row][col] = 2
        grid[2 * divider - row][col] = 5
    errors = _generator().self_check(grid)
    if errors:
        raise ValueError(f"Internal stress scene is invalid: {errors}")
    return grid


def _sample_inputs(seed: int, count: int) -> tuple[list[list[list[int]]], list[str]]:
    generator = _generator()
    seen: set[str] = set()
    grids: list[list[list[int]]] = []
    profiles: list[str] = []

    for slot in range(count - 1):
        profile = _PROFILES[slot % len(_PROFILES)]
        for attempt in range(128):
            sample_index = 10_000 * slot + attempt
            try:
                grid = generator.generate(
                    seed,
                    sample_index,
                    difficulty="hard",
                    scene_profile=profile,
                )
            except RuntimeError:
                continue
            grid = _grid(grid)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen or generator.self_check(grid):
                continue
            if apply_python(grid, "opposite") == apply_python(grid, "adjacent"):
                continue
            seen.add(key)
            grids.append(grid)
            profiles.append(profile)
            break
        else:
            raise ValueError(f"Could not draw distinct teaching scene for {profile}")

    stress = _stress_grid(seed)
    key = json.dumps(stress, separators=(",", ":"))
    if key in seen:
        raise ValueError("Stress query unexpectedly duplicates another input")
    grids.append(stress)
    profiles.append("balanced_max_29x30")
    return grids, profiles


def _intermediate_records(grid, destination_endpoint: str) -> list[dict]:
    setting = _setting(destination_endpoint)
    analysis = _generator()._analysis(_grid(grid))
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    records = []
    for record in analysis["records"]:
        selected = record["chosen"] if setting == "opposite" else _adjacent_endpoint(record)
        records.append(
            {
                "orientation": record["orientation"],
                "anchor": list(record["anchor"]),
                "anchor_direction": record["anchor_direction"],
                "selected_endpoint": list(selected),
                "reflected_endpoint": [2 * analysis["divider"] - selected[0], selected[1]],
            }
        )
    return records


def build_claimed_episode(
    seed: int,
    destination_endpoint: str,
    demos: int,
    queries: int,
) -> dict:
    """Build deterministic claims; native qualification independently replays Racket."""
    seed = _exact_integer(seed, "seed", 0, MAX_SEED)
    setting = _setting(destination_endpoint)
    demos = _exact_integer(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries = _exact_integer(queries, "queries", QUERY_COUNT, QUERY_COUNT)
    inputs, profiles = _sample_inputs(seed, demos + queries)
    outputs = [apply_python(grid, setting) for grid in inputs]
    pairs = [
        {"input": [row[:] for row in grid], "output": [row[:] for row in output]}
        for grid, output in zip(inputs, outputs)
    ]
    intermediates = [
        _intermediate_records(grid, setting)
        for grid in inputs
    ]
    program = program_for(setting)
    return {
        "schema": "96ebf3053dbe-endpoint-policy-episode-v1",
        "status": "proposed_unapproved",
        "training_admitted": False,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {PARAMETER_NAME: setting},
        "program": program,
        "program_solution": program,
        "program_sha256": _sha256(program),
        "train": pairs[:demos],
        "test": pairs[demos:],
        "input_profiles": {"train": profiles[:demos], "test": profiles[demos:]},
        "intermediates": {"train": intermediates[:demos], "test": intermediates[demos:]},
    }


def public_challenge(episode: dict, query_indices: Sequence[int] | None = None) -> dict:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode needs train/test lists")
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


def sequential_turn(episode: dict, query_index: int) -> dict:
    test = episode.get("test") if type(episode) is dict else None
    if type(test) is not list or not test:
        raise ValueError("episode needs nonempty test pairs")
    index = _exact_integer(query_index, "query_index", 0, len(test) - 1)
    if index == 0:
        return public_challenge(episode, query_indices=[0])
    return {"test": [{"input": deepcopy(test[index]["input"])}]}


def public_id(episode: dict, query_indices: Sequence[int] | None = None) -> str:
    return public_challenge_id(public_challenge(episode, query_indices=query_indices))


__all__ = [
    "ALLOWED_SETTINGS",
    "DEFAULT_SETTING",
    "PARAMETER_NAME",
    "QUERY_COUNT",
    "apply_python",
    "build_claimed_episode",
    "canonical_program",
    "program_for",
    "skip_anchor_program",
    "erase_only_program",
    "rival_programs",
    "public_challenge",
    "public_id",
    "sequential_turn",
    "validate_settings",
]
