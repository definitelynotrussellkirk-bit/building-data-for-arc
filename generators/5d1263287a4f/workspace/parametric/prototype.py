"""Proposed episode-fixed output transform for ARC task ``5d1263287a4f``.

This is intentionally separate from the approved production generator.  The
input rule remains "split into thirds and read the left source panel".  One
hidden ``output_transform`` is selected for an entire episode and demonstrated
consistently: preserve the source, mirror it horizontally, or flip it vertically.
The ``identity`` setting materializes the exact canonical Racket authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_id,
)

TASK_ID = "5d1263287a4f"
PARAMETER_NAME = "output_transform"
ALLOWED_SETTINGS = (
    "identity",
    "horizontal_mirror",
    "vertical_flip",
)
DEFAULT_SETTING = "identity"
PROTOTYPE_VERSION = "1.0.0"
CANONICAL_PROGRAM_SHA256 = (
    "8e689dae100ddceb2122503b4aa592a6e906335cb8d1a9b16f14f8f95ea8a1ee"
)
INPUT_CONSTRAINTS = (
    "production-lawful three-panel input",
    "left source panel is asymmetric under horizontal mirror and vertical flip",
    "the three setting outputs are pairwise distinct",
)
_UNSET = object()

ROOT = find_root(__file__)
_PRODUCTION, GENERATOR_PATH, PRODUCTION_GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


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
    """Choose one deterministic hidden setting for the complete episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}:{PARAMETER_NAME}:{PROTOTYPE_VERSION}:{seed}".encode("utf-8")
    ).digest()
    return ALLOWED_SETTINGS[digest[0] % len(ALLOWED_SETTINGS)]


def canonical_program(*, root: str | Path | None = None) -> str:
    """Return the one exact canonical Racket source, with a source-bound pin."""
    selected_root = ROOT if root is None else Path(root).resolve()
    programs = {
        row["program_solution"]
        for line in canonical_path(selected_root).read_text(encoding="utf-8").splitlines()
        if line.strip()
        and (row := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise RuntimeError(f"expected one canonical program, found {len(programs)}")
    source = next(iter(programs))
    actual = _sha256_text(source)
    if actual != CANONICAL_PROGRAM_SHA256:
        raise RuntimeError(
            "canonical program source changed: "
            f"expected {CANONICAL_PROGRAM_SHA256}, got {actual}"
        )
    return source


def program_for(setting: str) -> str:
    """Materialize the exact Racket program for one bounded setting."""
    _validate_setting(setting)
    source = canonical_program()
    if setting == DEFAULT_SETTING:
        return source
    anchor = "(at g r c)"
    if source.count(anchor) != 1:
        raise RuntimeError("canonical crop expression is no longer uniquely replaceable")
    expression = {
        "horizontal_mirror": "(at g r (- pw 1 c))",
        "vertical_flip": "(at g (- h 1 r) c)",
    }[setting]
    return source.replace(anchor, expression)


def rule_callable(program: str) -> str:
    """Wrap exact ``rule!`` source as a Racket callable over one grid."""
    if type(program) is not str or not program.strip():
        raise TypeError("program must be nonempty Racket source text")
    return wrap_rule(program)


def apply_python(grid: list[list[int]], setting: str) -> list[list[int]]:
    """Independent authoring mirror; retained labels are re-executed in Racket."""
    _validate_setting(setting)
    source = _PRODUCTION.rule_mirror(grid)
    if setting == "identity":
        return [row[:] for row in source]
    if setting == "horizontal_mirror":
        return [list(reversed(row)) for row in source]
    return [row[:] for row in reversed(source)]


def _input_for(seed: int, sample_index: int) -> list[list[int]]:
    difficulties = ("easy", "medium", "hard", None)
    return _PRODUCTION.generate(
        seed,
        sample_index,
        difficulty=difficulties[sample_index % len(difficulties)],
    )


def _setting_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {
        setting: apply_python(grid, setting)
        for setting in ALLOWED_SETTINGS
    }


def _is_identifying_input(grid: list[list[int]]) -> bool:
    outputs = _setting_outputs(grid)
    return len({_grid_key(output) for output in outputs.values()}) == len(outputs)


def _collect_inputs(seed: int, count: int) -> tuple[list[list[list[int]]], list[int]]:
    inputs: list[list[list[int]]] = []
    indices: list[int] = []
    seen: set[str] = set()
    cursor = 0
    # Production draws are small and diverse; this bound is deliberately finite
    # so unsupported requests fail rather than clone or silently shrink pairs.
    while len(inputs) < count and cursor < 4096:
        grid = _input_for(seed, cursor)
        key = _grid_key(grid)
        if key not in seen and _is_identifying_input(grid):
            seen.add(key)
            inputs.append(grid)
            indices.append(cursor)
        cursor += 1
    if len(inputs) != count:
        raise RuntimeError(
            f"could not collect {count} distinct identifying inputs in 4096 draws"
        )
    return inputs, indices


def build_episode(
    seed: int,
    *,
    setting: object = _UNSET,
    demo_count: int = 4,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one fixed-setting episode with independent demo/query counts."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    selected = choose_setting(seed) if setting is _UNSET else setting
    _validate_setting(selected)

    inputs, sample_indices = _collect_inputs(seed, demo_count + query_count)
    pairs = [
        {"input": copy.deepcopy(grid), "output": apply_python(grid, selected)}
        for grid in inputs
    ]
    demos = pairs[:demo_count]
    queries = pairs[demo_count:]

    rival_refutations = {
        rival: sum(
            apply_python(pair["input"], rival) != pair["output"]
            for pair in demos
        )
        for rival in ALLOWED_SETTINGS
        if rival != selected
    }
    if any(count == 0 for count in rival_refutations.values()):
        raise RuntimeError("demonstrations do not identify the selected setting")
    if not all(_is_identifying_input(pair["input"]) for pair in queries):
        raise RuntimeError("every query must distinguish all parameter settings")

    program = program_for(selected)
    canonical = canonical_program()
    return {
        "train": demos,
        "test": queries,
        "program": program,
        "meta": {
            "seed": seed,
            PARAMETER_NAME: selected,
            "allowed_settings": list(ALLOWED_SETTINGS),
            "default_setting": DEFAULT_SETTING,
            "demo_count": demo_count,
            "query_count": query_count,
            "demo_indices": sample_indices[:demo_count],
            "query_indices": sample_indices[demo_count:],
            "rival_demo_refutations": rival_refutations,
            "input_constraints": list(INPUT_CONSTRAINTS),
            "prototype_version": PROTOTYPE_VERSION,
            "production_generator_version": _PRODUCTION.VERSION,
            "production_generator_sha256": PRODUCTION_GENERATOR_SHA256,
            "canonical_program_sha256": _sha256_text(canonical),
            "program_sha256": _sha256_text(program),
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy only visible demonstrations and unlabeled query inputs."""
    if not isinstance(episode, dict):
        raise TypeError("episode must be a mapping")
    try:
        train = episode["train"]
        test = episode["test"]
        return {
            "train": [
                {
                    "input": copy.deepcopy(pair["input"]),
                    "output": copy.deepcopy(pair["output"]),
                }
                for pair in train
            ],
            "test": [
                {"input": copy.deepcopy(pair["input"])}
                for pair in test
            ],
        }
    except (KeyError, TypeError) as exc:
        raise ValueError("episode must contain train/test pairs") from exc


def public_filename(episode: dict[str, Any]) -> str:
    """Opaque public name derived only from exact visible challenge bytes."""
    return f"challenge-{public_challenge_id(public_challenge(episode))}.json"
