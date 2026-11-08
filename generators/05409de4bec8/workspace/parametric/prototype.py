"""Proposed episode-level rectangle-policy variant for ``05409de4bec8``.

This module is deliberately separate from the selected production generator.
The hidden parameter is chosen once per episode.  ``longer`` is the exact
canonical rule; ``both`` draws every exact-pair row and column for rectangles.
All target selection, distractor erasure, and non-rectangle behavior are shared.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_ID = "05409de4bec8"
PARAMETER_NAME = "rectangle_policy"
ALLOWED_SETTINGS = ("longer", "both")
DEFAULT_SETTING = "longer"
PROTOTYPE_VERSION = "1.0.0"
_UNSET = object()

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
GENERATOR_PATH = HERE.parents[1] / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _load_production_generator():
    name = "generator_05409de4bec8_parametric_source"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load production generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PRODUCTION = _load_production_generator()


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a plain integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")


def _validate_setting(setting: str) -> None:
    if type(setting) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a literal string")
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {setting!r}"
        )


def _validate_count(name: str, value: int) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be a plain integer (not bool)")
    if not 1 <= value <= 32:
        raise ValueError(f"{name} must lie in 1..32")


def choose_setting(seed: int) -> str:
    """Choose one hidden setting deterministically for the complete episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}:rectangle-policy:{seed}".encode()).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def canonical_program() -> str:
    programs = {
        record["program_solution"]
        for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines()
        if (record := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise RuntimeError(f"expected one canonical program, found {len(programs)}")
    return next(iter(programs))


_BOTH_AXES_PROGRAM = """(rule!
  (let* ((target-color
          (find-first
           (lambda (color)
             (let* ((cells (find-color g color))
                    (row-count (length (remove-duplicates (map first cells))))
                    (col-count (length (remove-duplicates (map second cells)))))
               (and (= (length cells) 4)
                    (<= row-count 3)
                    (<= col-count 3))))
           (filter (lambda (color) (!= color 0)) (grid-colors g))))
         (target-cells (find-color g target-color))
         (target-rows (remove-duplicates (map first target-cells)))
         (target-cols (remove-duplicates (map second target-cells)))
         (row-pairs
          (filter
           (lambda (row)
             (= (count-where (lambda (cell) (= (first cell) row)) target-cells) 2))
           target-rows))
         (col-pairs
          (filter
           (lambda (col)
             (= (count-where (lambda (cell) (= (second cell) col)) target-cells) 2))
           target-cols)))
    (cellmap
     g (r c v)
     (if (or (find (lambda (row) (= row r)) row-pairs)
             (find (lambda (col) (= col c)) col-pairs))
         target-color
         0))))"""


def program_for(setting: str) -> str:
    _validate_setting(setting)
    return canonical_program() if setting == DEFAULT_SETTING else _BOTH_AXES_PROGRAM


def is_rectangle(grid: list[list[int]]) -> bool:
    analysis = _PRODUCTION._analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return bool(analysis["facts"]["rectangle"])


def apply_python(grid: list[list[int]], setting: str) -> list[list[int]]:
    """Independent authoring mirror; retained labels are executed in Racket."""
    _validate_setting(setting)
    if setting == "longer":
        return _PRODUCTION.rule_mirror(grid)
    return _PRODUCTION._all_pair_lines(grid)


def _input_for(seed: int, sample_index: int) -> list[list[int]]:
    difficulties = ("easy", "medium", "hard", None)
    return _PRODUCTION.generate(
        seed,
        sample_index,
        difficulty=difficulties[sample_index % len(difficulties)],
    )


def _query_indices(seed: int, start: int, count: int, used: set[str]) -> list[int]:
    indices: list[int] = []
    cursor = start
    while len(indices) < count and cursor < start + 1000:
        if _PRODUCTION.schedule_profile(seed, cursor) in ("rectangle_a", "rectangle_b"):
            grid = _input_for(seed, cursor)
            key = json.dumps(grid, separators=(",", ":"))
            if key not in used:
                used.add(key)
                indices.append(cursor)
        cursor += 1
    if len(indices) != count:
        raise RuntimeError("could not materialize enough distinct rectangle queries")
    return indices


def build_episode(
    seed: int,
    *,
    setting: object = _UNSET,
    demo_count: int = 5,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one fixed-rule episode with separate demo and query counts."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    selected = choose_setting(seed) if setting is _UNSET else setting
    _validate_setting(selected)

    demo_indices = list(range(demo_count))
    demo_inputs = [_input_for(seed, index) for index in demo_indices]
    used = {json.dumps(grid, separators=(",", ":")) for grid in demo_inputs}
    if len(used) != len(demo_inputs):
        raise RuntimeError("demonstrations must be distinct")
    if not any(is_rectangle(grid) for grid in demo_inputs):
        raise RuntimeError("demonstrations do not identify rectangle_policy")

    query_indices = _query_indices(seed, demo_count, query_count, used)
    inputs = demo_inputs + [_input_for(seed, index) for index in query_indices]
    pairs = [
        {"input": grid, "output": apply_python(grid, selected)}
        for grid in inputs
    ]
    other = next(value for value in ALLOWED_SETTINGS if value != selected)
    if not any(
        apply_python(pair["input"], other) != pair["output"]
        for pair in pairs[:demo_count]
    ):
        raise RuntimeError("demonstrations do not refute the alternative setting")
    if not all(
        is_rectangle(pair["input"])
        and apply_python(pair["input"], other) != pair["output"]
        for pair in pairs[demo_count:]
    ):
        raise RuntimeError("every retained query must distinguish the settings")

    program = program_for(selected)
    return {
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
        "program": program,
        "meta": {
            "seed": seed,
            PARAMETER_NAME: selected,
            "demo_count": demo_count,
            "query_count": query_count,
            "demo_indices": demo_indices,
            "query_indices": query_indices,
            "prototype_version": PROTOTYPE_VERSION,
            "production_generator_version": _PRODUCTION.VERSION,
            "production_generator_sha256": hashlib.sha256(
                GENERATOR_PATH.read_bytes()
            ).hexdigest(),
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project an episode to visible content only."""
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }
