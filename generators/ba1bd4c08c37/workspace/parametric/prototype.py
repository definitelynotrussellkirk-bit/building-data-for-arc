"""Isolated parametric-rule prototype for ARC task ba1bd4c08c37.

The selected production generator and canonical authority remain separate.  One
hidden ``output_corner`` is chosen once for a complete six-pair episode:

* ``top_left`` (canonical/default),
* ``top_right``,
* ``bottom_left``, or
* ``bottom_right``.

Every input keeps the production generator's doubly symmetric foreground box.
The prototype filters generated inputs so the four *raw* corner crops are all
different; this makes every demonstration informative about the episode-level
setting.  Retained evidence is labelled by executing materialized Racket.  The
Python reference below is only a test/debug mirror.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from puzzle_generators.base import stable_rng
from reviewer_support import canonical_path, find_root

TASK_ID = "ba1bd4c08c37"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "output_corner"
PARAMETER_VALUES = (
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
)
DEFAULT_PARAMETER = "top_left"
N_TRAIN = 5
N_TEST = 1
PAIR_COUNT = N_TRAIN + N_TEST
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "enum",
        "allowed": list(PARAMETER_VALUES),
        "default": DEFAULT_PARAMETER,
        "chosen": "once per episode from the deterministic episode seed",
        "input_constraints": (
            "production-valid symmetric foreground boxes whose four raw "
            "half-height by half-width corner crops are pairwise distinct"
        ),
    }
}

_PARENT = None
_FINAL_CROP = (
    "(build-grid half-h half-w (i j) "
    "(at g (+ r1 i) (+ c1 j)))"
)
_CORNER_CROPS = {
    "top_left": _FINAL_CROP,
    "top_right": (
        "(build-grid half-h half-w (i j) "
        "(at g (+ r1 i) (+ c1 half-w j)))"
    ),
    "bottom_left": (
        "(build-grid half-h half-w (i j) "
        "(at g (+ r1 half-h i) (+ c1 j)))"
    ),
    "bottom_right": (
        "(build-grid half-h half-w (i j) "
        "(at g (+ r1 half-h i) (+ c1 half-w j)))"
    ),
}


def _load_parent():
    global _PARENT
    if _PARENT is not None:
        return _PARENT
    root = find_root(__file__)
    candidates = (
        root / f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py",
        root / f"generators/{TASK_ID}/generator.py",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise ImportError(f"cannot locate selected generator for {TASK_ID}")
    spec = importlib.util.spec_from_file_location(f"_parametric_parent_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load selected generator at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _PARENT = module
    return module


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("episode seed must be an integer (not bool, float, or string)")
    if seed < 0:
        raise ValueError("episode seed must be nonnegative")
    return seed


def _validate_pair_index(pair_index: Any) -> int:
    if type(pair_index) is not int:
        raise TypeError("pair_index must be an integer")
    if pair_index < 0:
        raise ValueError("pair_index must be nonnegative")
    return pair_index


def validate_parameter(value: Any) -> str:
    if type(value) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if value not in PARAMETER_VALUES:
        raise ValueError(
            f"unknown {PARAMETER_NAME}={value!r}; expected one of {PARAMETER_VALUES}"
        )
    return value


def choose_parameters(seed: Any, output_corner: Any | None = None) -> dict[str, str]:
    """Choose exactly one hidden setting for the whole deterministic episode."""
    seed = _validate_seed(seed)
    if output_corner is not None:
        return {PARAMETER_NAME: validate_parameter(output_corner)}
    rng = stable_rng(seed, f"{TASK_ID}|parametric-rule", PROTOTYPE_VERSION)
    return {PARAMETER_NAME: PARAMETER_VALUES[rng.randrange(len(PARAMETER_VALUES))]}


def _canonical_program(root: Path | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root).resolve()
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(root).open(encoding="utf-8"))
        if row.get("task_id") == TASK_ID and row.get("program_solution")
    }
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}; found {len(programs)}")
    return programs.pop()


def racket_program(parameters: dict[str, Any], *, root: Path | None = None) -> str:
    """Materialize exact Racket source for one corner setting.

    The default path returns the canonical source byte-for-byte.  Alternatives
    change only the final crop offsets in that same source.
    """
    if type(parameters) is not dict:
        raise TypeError("parameters must be a dictionary")
    if set(parameters) != {PARAMETER_NAME}:
        raise ValueError(f"parameters must contain exactly {PARAMETER_NAME!r}")
    corner = validate_parameter(parameters[PARAMETER_NAME])
    source = _canonical_program(root)
    if corner == DEFAULT_PARAMETER:
        return source
    if source.count(_FINAL_CROP) != 1:
        raise ValueError("canonical source no longer has the expected unique crop fragment")
    return source.replace(_FINAL_CROP, _CORNER_CROPS[corner], 1)


def racket_callable(source: str) -> str:
    """Return the plain callable body for this prototype's exact rule sources.

    The repository-layout ``wrap_rule`` helper currently has a lazy dependency
    on a staged ``scripts.comment_solutions`` namespace.  These programs are
    already plain ``(rule! <lambda>)`` forms and need no shorthand or dictionary
    rewriting, so peeling only that wrapper is both narrower and portable.
    """
    if type(source) is not str:
        raise TypeError("Racket source must be a string")
    from puzzle_generators.rule_wrap import strip_rule_wrapper

    body = strip_rule_wrapper(source)
    if not body.lstrip().startswith(("(lambda ", "(λ ")):
        raise ValueError("prototype source must wrap a lambda callable")
    return body


def python_reference(
    grid: list[list[int]], *, output_corner: str = DEFAULT_PARAMETER
) -> list[list[int]]:
    """Debug mirror of the materialized corner crop; evidence uses Racket."""
    corner = validate_parameter(output_corner)
    parent = _load_parent()
    errors = parent.self_check(grid)
    if errors:
        raise ValueError("input is outside the production manifold: " + "; ".join(errors))
    top, left, bottom, right = parent._bbox(grid)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    row_start = top if corner.startswith("top_") else top + half_h
    col_start = left if corner.endswith("_left") else left + half_w
    return [
        list(row[col_start : col_start + half_w])
        for row in grid[row_start : row_start + half_h]
    ]


def _all_corner_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {
        corner: python_reference(grid, output_corner=corner)
        for corner in PARAMETER_VALUES
    }


def _pairwise_distinct(outputs: dict[str, list[list[int]]]) -> bool:
    fingerprints = {
        json.dumps(value, separators=(",", ":")) for value in outputs.values()
    }
    return len(fingerprints) == len(PARAMETER_VALUES)


def _build_input_with_metadata(seed: Any, pair_index: Any) -> tuple[list[list[int]], dict[str, Any]]:
    seed = _validate_seed(seed)
    pair_index = _validate_pair_index(pair_index)
    parent = _load_parent()
    input_seed = seed * 1_000_003 + 97
    difficulties = ("easy", "medium", "hard")
    difficulty = difficulties[(seed + pair_index) % len(difficulties)]
    # Keep the production six-slot semantic schedule.  Vary only the generator
    # seed while searching away the rare rotationally symmetric seed quadrant.
    for attempt in range(128):
        candidate_seed = input_seed + attempt * 7_919 + pair_index * 101
        grid = parent.generate(candidate_seed, pair_index, difficulty=difficulty)
        outputs = _all_corner_outputs(grid)
        if _pairwise_distinct(outputs):
            return grid, {
                "candidate_seed": candidate_seed,
                "sample_index": pair_index,
                "difficulty": difficulty,
                "search_attempt": attempt,
            }
    raise RuntimeError(
        f"could not find a four-corner-distinguishing input for seed={seed}, "
        f"pair_index={pair_index}"
    )


def build_input(seed: Any, pair_index: Any) -> list[list[int]]:
    """Return one production-valid input that distinguishes all four settings."""
    grid, _ = _build_input_with_metadata(seed, pair_index)
    return grid


def generate_episode(
    seed: Any,
    *,
    output_corner: Any | None = None,
    n_train: int = N_TRAIN,
    n_test: int = N_TEST,
) -> dict[str, Any]:
    """Build a deterministic private episode using one fixed corner setting."""
    seed = _validate_seed(seed)
    if type(n_train) is not int or type(n_test) is not int:
        raise TypeError("n_train and n_test must be integers")
    if n_train < 1 or n_test < 1:
        raise ValueError("n_train and n_test must be positive")
    parameters = choose_parameters(seed, output_corner)
    corner = parameters[PARAMETER_NAME]
    pairs = []
    pair_metadata = []
    for pair_index in range(n_train + n_test):
        grid, metadata = _build_input_with_metadata(seed, pair_index)
        outputs = _all_corner_outputs(grid)
        if not _pairwise_distinct(outputs):
            raise AssertionError("accepted prototype input does not separate all settings")
        pairs.append({"input": grid, "output": outputs[corner]})
        pair_metadata.append(metadata)
    return {
        "schema": "arc-parametric-private-episode-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": parameters,
        "parameter_spec": deepcopy(PARAMETER_SPEC),
        "program": racket_program(parameters),
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "meta": {
            "pair_generation": pair_metadata,
            "labels": "Python debug mirror; retained builder evidence re-executes Racket",
            "all_pairs_distinguish_all_settings": True,
        },
    }


def grid_literal(grid: list[list[int]]) -> str:
    parent = _load_parent()
    errors = parent.self_check(grid)
    if errors:
        raise ValueError("cannot encode invalid prototype input: " + "; ".join(errors))
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"'({rows})"


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden setting, source, seed, and every test answer."""
    return {
        "schema": "arc-parametric-public-challenge-v1",
        "task_id": TASK_ID,
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }
