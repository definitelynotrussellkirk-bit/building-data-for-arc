"""Task-local selector-role prototype for ``a9f315ca9cc7``.

The production generator and canonical Racket authority stay fixed.  This
proposed extension chooses once per episode whether copies of the complete 3x3
input are placed at foreground mask cells (the canonical rule) or at background
mask cells (the nearby role-inversion variant).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "a9f315ca9cc7"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "selector_role"
ALLOWED_SETTINGS = ("foreground", "background")
DEFAULT_SETTING = "foreground"
_UNSET = object()

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
_PRODUCTION, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)
CANONICAL_PATH = canonical_path(ROOT)

PARAMETER_SPEC = {
    "name": PARAMETER_NAME,
    "allowed_values": list(ALLOWED_SETTINGS),
    "original_default": DEFAULT_SETTING,
    "selection_scope": "one deterministic value per complete episode",
    "meaning": {
        "foreground": "copy the full input into blocks selected by nonzero cells",
        "background": "copy the full input into blocks selected by zero cells",
    },
    "invariant_reasoning": [
        "read the complete 3x3 input as both block mask and copied template",
        "evaluate the selected role independently at each mask cell",
        "copy the exact input into selected 3x3 blocks and leave other blocks zero",
    ],
    "dependent_input_constraints": [
        "input remains exactly 3x3 with background 0 and one nonzero color",
        "both zero and nonzero cells must occur so both selector roles are observable",
    ],
}


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, string, or None)")


def _validate_setting(setting: str) -> None:
    if type(setting) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {setting!r}"
        )


def choose_setting(seed: int) -> str:
    """Choose one hidden rule value deterministically for the whole episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}:selector-role:{PROTOTYPE_VERSION}:{seed}".encode()
    ).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def _canonical_program() -> str:
    found: list[str] = []
    for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK_ID:
            found.append(record["program_solution"])
    if len(found) != 1:
        raise RuntimeError(f"expected one canonical program for {TASK_ID}, found {len(found)}")
    return found[0]


def program_for(setting: str) -> str:
    """Materialize a complete exact Racket rule for one selector role."""
    _validate_setting(setting)
    if setting == DEFAULT_SETTING:
        return _canonical_program()
    return "(rule! (lambda (g) (self-tile g (lambda (v) (= v 0)))))"


def apply_python(grid: list[list[int]], setting: str) -> list[list[int]]:
    """Authoring mirror; retained labels are independently executed in Racket."""
    _validate_setting(setting)
    errors = _PRODUCTION.self_check(grid)
    if errors:
        raise ValueError("input is outside the production grammar: " + "; ".join(errors))

    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width * width)] for _ in range(height * height)]
    for block_row in range(height):
        for block_col in range(width):
            value = grid[block_row][block_col]
            selected = value != 0 if setting == "foreground" else value == 0
            if not selected:
                continue
            for row in range(height):
                for col in range(width):
                    output[block_row * height + row][block_col * width + col] = grid[row][col]
    return output


def _input_for(seed: int, sample_index: int) -> list[list[int]]:
    difficulties = ("easy", "medium", "hard", None)
    return _PRODUCTION.generate(
        seed,
        sample_index,
        difficulty=difficulties[sample_index % len(difficulties)],
    )


def build_episode(seed: int, *, setting: object = _UNSET) -> dict[str, Any]:
    """Build three demonstrations and one query under one fixed hidden rule."""
    _validate_seed(seed)
    selected = choose_setting(seed) if setting is _UNSET else setting
    _validate_setting(selected)

    demo_indices = [0, 1, 2]
    query_indices = [3]
    inputs = [_input_for(seed, index) for index in demo_indices + query_indices]
    pairs = [
        {"input": grid, "output": apply_python(grid, selected)}
        for grid in inputs
    ]
    program = program_for(selected)
    return {
        "train": pairs[: len(demo_indices)],
        "test": pairs[len(demo_indices) :],
        "program": program,
        "meta": {
            "seed": seed,
            PARAMETER_NAME: selected,
            "demo_indices": demo_indices,
            "query_indices": query_indices,
            "prototype_version": PROTOTYPE_VERSION,
            "production_generator_version": _PRODUCTION.VERSION,
            "production_generator_sha256": GENERATOR_SHA256,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return the visible task without hidden settings, Racket, or query labels."""
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }
