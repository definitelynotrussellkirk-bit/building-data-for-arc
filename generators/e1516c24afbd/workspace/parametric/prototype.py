"""Task-local episode-level parameter prototype for ARC task e1516c24afbd.

This is proposed evidence only.  It does not alter the selected production
rule or generator.  Two small parameters are chosen once per episode:

* ``target_state``: mark aligned ``00`` cells (canonical) or aligned ``11``
  cells (a nearby occupancy-rule variant).
* ``output_color``: use color 2 (canonical) or color 3.

All retained inputs contain every occupancy state, and input foreground colors
are fixed to 1 and 9, so every demonstration distinguishes all four settings.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator

_SELECTED_ROOT = find_root(__file__)
selected_generator, SELECTED_GENERATOR_PATH, SELECTED_GENERATOR_SHA256 = (
    load_selected_generator("e1516c24afbd", root=_SELECTED_ROOT)
)

TASK_ID = "e1516c24afbd"
PROTOTYPE_VERSION = "1.0.0"
STATUS = "proposed_unapproved"

DEFAULT_TARGET_STATE = "00"
DEFAULT_OUTPUT_COLOR = 2
ALLOWED_TARGET_STATES = ("00", "11")
ALLOWED_OUTPUT_COLORS = (2, 3)
SETTINGS = tuple(
    (state, color)
    for state in ALLOWED_TARGET_STATES
    for color in ALLOWED_OUTPUT_COLORS
)
CANONICAL_SHA256 = "1436e19f4a5b3ccac2c6e482304504a691ea0c0d2a78027ae6b610e2e7fa7289"

_CANONICAL_IF = (
    "(if (and (zero? (at g r c)) (zero? (at g (+ r h) c))) 2 0)"
)
_CONDITIONS = {
    "00": "(and (zero? (at g r c)) (zero? (at g (+ r h) c)))",
    "11": (
        "(and (not (zero? (at g r c))) "
        "(not (zero? (at g (+ r h) c))))"
    ),
}


def _sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")


def _validate_setting(target_state: Any, output_color: Any) -> tuple[str, int]:
    if not isinstance(target_state, str):
        raise TypeError("target_state must be a string")
    if target_state not in ALLOWED_TARGET_STATES:
        raise ValueError(
            f"target_state must be one of {ALLOWED_TARGET_STATES}, got {target_state!r}"
        )
    if type(output_color) is not int:
        raise TypeError("output_color must be a literal Python integer")
    if output_color not in ALLOWED_OUTPUT_COLORS:
        raise ValueError(
            f"output_color must be one of {ALLOWED_OUTPUT_COLORS}, got {output_color!r}"
        )
    return target_state, output_color


def canonical_source(*, root: str | Path | None = None) -> str:
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    for line in canonical_path(root_path).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            source = row["program_solution"]
            if _sha256(source) != CANONICAL_SHA256:
                raise RuntimeError("canonical source hash changed")
            return source
    raise RuntimeError(f"canonical source missing for {TASK_ID}")


def materialize_rule(
    target_state: Any = DEFAULT_TARGET_STATE,
    output_color: Any = DEFAULT_OUTPUT_COLOR,
    *,
    source: str | None = None,
) -> str:
    """Materialize one bounded Racket variant; default bytes stay canonical."""
    target_state, output_color = _validate_setting(target_state, output_color)
    source = canonical_source() if source is None else source
    if source.count(_CANONICAL_IF) != 1:
        raise ValueError("expected exactly one canonical occupancy/output expression")
    if target_state == DEFAULT_TARGET_STATE and output_color == DEFAULT_OUTPUT_COLOR:
        return source
    replacement = f"(if {_CONDITIONS[target_state]} {output_color} 0)"
    return source.replace(_CANONICAL_IF, replacement, 1)


def parameters_for_seed(seed: Any) -> dict[str, str | int]:
    """Choose exactly one setting before constructing any episode pair."""
    _validate_seed(seed)
    target_state, output_color = SETTINGS[seed % len(SETTINGS)]
    return {"target_state": target_state, "output_color": output_color}


def _shape(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if any(not isinstance(row, list) or not row for row in grid):
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if len(grid) % 2:
        raise ValueError("grid height must be even")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be literal integer colors 0..9")
    return len(grid), width


def apply_python(
    grid: list[list[int]],
    target_state: Any = DEFAULT_TARGET_STATE,
    output_color: Any = DEFAULT_OUTPUT_COLOR,
) -> list[list[int]]:
    target_state, output_color = _validate_setting(target_state, output_color)
    height, width = _shape(grid)
    half_h = height // 2
    output: list[list[int]] = []
    for row in range(half_h):
        out_row: list[int] = []
        for col in range(width):
            state = ("1" if grid[row][col] != 0 else "0") + (
                "1" if grid[half_h + row][col] != 0 else "0"
            )
            out_row.append(output_color if state == target_state else 0)
        output.append(out_row)
    return output


def _episode_inputs(seed: int) -> list[dict[str, Any]]:
    """Create four lawful, setting-independent fixtures with all four states."""
    specifications = (
        (3, 3, 1, "random"),
        (4, 5, 2, "cluster"),
        (5, 4, 3, "diagonal"),
        (6, 6, 4, "checker"),
    )
    rows: list[dict[str, Any]] = []
    for pair_index, (half_h, grid_w, zero_count, layout) in enumerate(specifications):
        generator_seed = seed * 101 + pair_index + 17
        grid = selected_generator.generate(
            generator_seed,
            pair_index,
            half_h=half_h,
            grid_w=grid_w,
            top_color=1,
            bot_color=9,
            both_zero_count=zero_count,
            layout=layout,
        )
        facts = selected_generator.semantic_observables(grid)
        if selected_generator.self_check(grid):
            raise AssertionError("prototype fixture left the selected teaching grammar")
        if any(facts["state_counts"][state] < 1 for state in ("00", "10", "01", "11")):
            raise AssertionError("prototype fixture does not contain all four states")
        rows.append(
            {
                "input": grid,
                "sampling": {
                    "generator_seed": generator_seed,
                    "sample_index": pair_index,
                    "half_h": half_h,
                    "grid_w": grid_w,
                    "top_color": 1,
                    "bot_color": 9,
                    "both_zero_count": zero_count,
                    "layout": layout,
                    "state_counts": facts["state_counts"],
                },
            }
        )
    return rows


def build_episode(seed: Any) -> dict[str, Any]:
    _validate_seed(seed)
    parameter = parameters_for_seed(seed)
    setting = (parameter["target_state"], parameter["output_color"])
    source = materialize_rule(*setting)
    inputs = _episode_inputs(seed)
    pairs = [
        {
            **row,
            "output": apply_python(row["input"], *setting),
            "input_sha256": _sha256(json.dumps(row["input"], separators=(",", ":"))),
        }
        for row in inputs
    ]
    alternatives = [candidate for candidate in SETTINGS if candidate != setting]
    rival_rows = []
    for alternative in alternatives:
        mismatch_indices = [
            index
            for index, pair in enumerate(pairs)
            if apply_python(pair["input"], *alternative) != pair["output"]
        ]
        rival_rows.append(
            {
                "target_state": alternative[0],
                "output_color": alternative[1],
                "demonstration_mismatch_indices": [
                    index for index in mismatch_indices if index < 3
                ],
                "query_mismatch_indices": [
                    index - 3 for index in mismatch_indices if index >= 3
                ],
            }
        )
    return {
        "schema": "e1516c24afbd-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": STATUS,
        "approved": False,
        "seed": seed,
        "parameter": parameter,
        "parameter_selection": "SETTINGS[seed % 4], once before all pairs",
        "input_constraints_depend_on_parameter": False,
        "program": source,
        "program_sha256": _sha256(source),
        "generator_version": selected_generator.VERSION,
        "generator_source_sha256": SELECTED_GENERATOR_SHA256,
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_rivals": rival_rows,
    }


def episode_errors(episode: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(episode, dict):
        return ["episode must be a dictionary"]
    try:
        parameter = episode["parameter"]
        setting = _validate_setting(
            parameter["target_state"], parameter["output_color"]
        )
    except (KeyError, TypeError, ValueError) as exc:
        return [f"invalid episode parameter: {exc}"]
    if episode.get("parameter") != parameters_for_seed(episode.get("seed")):
        errors.append("parameter is not the deterministic once-per-episode selection")
    try:
        expected_program = materialize_rule(*setting)
    except (TypeError, ValueError, RuntimeError) as exc:
        errors.append(f"could not materialize selected program: {exc}")
        expected_program = None
    if episode.get("program") != expected_program:
        errors.append("episode program does not match selected parameter")

    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or len(train) != 3:
        errors.append("episode must contain exactly three training pairs")
        train = []
    if not isinstance(test, list) or len(test) != 1:
        errors.append("episode must contain exactly one test pair")
        test = []

    alternatives = [candidate for candidate in SETTINGS if candidate != setting]
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                errors.append(f"{split_name}[{index}] must contain input and output")
                continue
            try:
                expected = apply_python(pair["input"], *setting)
            except (TypeError, ValueError) as exc:
                errors.append(f"{split_name}[{index}] invalid input: {exc}")
                continue
            if pair["output"] != expected:
                errors.append(f"{split_name}[{index}] output does not match selected setting")
            if split_name == "train":
                for alternative in alternatives:
                    if apply_python(pair["input"], *alternative) == pair["output"]:
                        errors.append(
                            f"train[{index}] does not refute alternative {alternative}"
                        )
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Strip private parameter/program data and query labels."""
    return copy.deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [{"input": pair["input"]} for pair in episode["test"]],
        }
    )
