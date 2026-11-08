"""Task-local parametric prototype for ring-partner direction.

The selected production generator and canonical authority remain separate and
unchanged.  One hidden ``ring_partner_axis`` is selected once for an episode:

* ``row`` (canonical/default): each dot's 3x3 ring copies its same-row partner.
* ``column``: each ring instead copies its same-column partner.

The input family is unchanged: every lawful rectangle corner has exactly one
partner on each axis.  Diagonal-colour rectangles make the settings coincide,
while the existing same-row-colour rectangles distinguish them.  The six-pair
period-three schedule contains four distinguishing pairs, so any five-pair
single-query holdout still identifies the selected setting.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "0832c700ffb9"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "ring_partner_axis"
PARAMETER_VALUES = ("row", "column")
DEFAULT_PARAMETER = "row"
N_TRAIN = 5
N_TEST = 1
HERE = Path(__file__).resolve().parent

_ROW_PARTNER_FRAGMENT = """(and
                                                  (= (first d) dr)
                                                  (!= (second d) dc))"""
_COLUMN_PARTNER_FRAGMENT = """(and
                                                  (= (second d) dc)
                                                  (!= (first d) dr))"""
_PARENT = None


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
    spec = importlib.util.spec_from_file_location(
        f"_parametric_parent_{TASK_ID}", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load selected generator at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _PARENT = module
    return module


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if seed < 0:
        raise ValueError("prototype seed must be nonnegative")
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


def choose_parameter(seed: Any, value: Any | None = None) -> str:
    """Choose one hidden setting once for the complete deterministic episode."""
    seed = _validate_seed(seed)
    if value is not None:
        return validate_parameter(value)
    return PARAMETER_VALUES[seed % len(PARAMETER_VALUES)]


def episode_difficulty(seed: Any) -> str:
    seed = _validate_seed(seed)
    return ("easy", "medium", "hard")[seed % 3]


def build_input(seed: Any, pair_index: Any) -> list[list[int]]:
    """Build one selected-family input lawful under both parameter settings."""
    seed = _validate_seed(seed)
    pair_index = _validate_pair_index(pair_index)
    parent = _load_parent()
    grid = parent.generate(
        seed,
        pair_index,
        difficulty=episode_difficulty(seed),
    )
    findings = parent.self_check(grid)
    if findings:
        raise RuntimeError("selected generator returned an unlawful input: " + findings[0])
    return grid


def _ring_color(axis: str):
    axis = validate_parameter(axis)

    def ring(dot, dots) -> int:
        row, col, _ = dot
        if axis == "row":
            partner = next(
                (
                    other[2]
                    for other in dots
                    if other[0] == row and other[1] != col
                ),
                None,
            )
        else:
            partner = next(
                (
                    other[2]
                    for other in dots
                    if other[1] == col and other[0] != row
                ),
                None,
            )
        return 0 if partner is None else partner

    return ring


def apply_rule(grid: list[list[int]], ring_partner_axis: Any) -> list[list[int]]:
    """Python assertion mirror; retained labels are checked with Racket."""
    axis = validate_parameter(ring_partner_axis)
    parent = _load_parent()
    findings = parent.self_check(grid)
    if findings:
        raise ValueError("invalid selected-family input: " + "; ".join(findings))
    return parent._render(grid, ring_color=_ring_color(axis))


def _canonical_program(root: Path | str | None = None) -> str:
    root_path = find_root(__file__) if root is None else Path(root)
    with canonical_path(root_path).open(encoding="utf-8") as stream:
        programs = {
            row["program_solution"]
            for row in map(json.loads, stream)
            if row.get("task_id") == TASK_ID
        }
    if len(programs) != 1:
        raise ValueError(
            f"expected one canonical program for {TASK_ID}, found {len(programs)}"
        )
    return programs.pop()


def racket_program(
    ring_partner_axis: Any, *, root: Path | str | None = None
) -> str:
    """Materialize exact Racket source for one bounded parameter setting."""
    axis = validate_parameter(ring_partner_axis)
    source = _canonical_program(root)
    if axis == "row":
        return source
    if source.count(_ROW_PARTNER_FRAGMENT) != 1:
        raise ValueError("canonical row-partner edit point is absent or ambiguous")
    return source.replace(_ROW_PARTNER_FRAGMENT, _COLUMN_PARTNER_FRAGMENT)


def surviving_parameter_values(
    demonstrations: Iterable[dict[str, Any]],
) -> list[str]:
    materialized = list(demonstrations)
    survivors: list[str] = []
    for axis in PARAMETER_VALUES:
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and apply_rule(pair["input"], axis) == pair["output"]
            for pair in materialized
        ):
            survivors.append(axis)
    return survivors


def generate_episode(
    seed: Any,
    *,
    ring_partner_axis: Any | None = None,
    n_train: Any = N_TRAIN,
    n_test: Any = N_TEST,
) -> dict[str, Any]:
    """Generate one complete private episode with one fixed hidden setting."""
    seed = _validate_seed(seed)
    selected = choose_parameter(seed, ring_partner_axis)
    if type(n_train) is not int or type(n_test) is not int:
        raise TypeError("n_train and n_test must be integers")
    if n_train < 1 or n_test < 1:
        raise ValueError("episodes require at least one train and one test pair")

    pairs = []
    for pair_index in range(n_train + n_test):
        grid = build_input(seed, pair_index)
        pairs.append({"input": grid, "output": apply_rule(grid, selected)})
    return {
        "schema": "arcpuzzles-task-parametric-prototype-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "version": PROTOTYPE_VERSION,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": racket_program(selected),
        "meta": {
            "seed": seed,
            PARAMETER_NAME: selected,
            "parameter_values": list(PARAMETER_VALUES),
            "canonical_default": selected == DEFAULT_PARAMETER,
            "selection": "once per deterministic episode seed",
            "difficulty": episode_difficulty(seed),
            "input_constraints": {
                "selected_family_self_check": True,
                "row_and_column_partner_unique": True,
                "schedule_profiles": [
                    _load_parent().schedule_profile(seed, index, episode_difficulty(seed))
                    for index in range(n_train + n_test)
                ],
                "reason": (
                    "diagonal rectangles preserve the shared behavior while "
                    "same-row-colour rectangles distinguish row from column"
                ),
            },
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Whitelist projection with no hidden setting, program, seed, or query labels."""
    return {
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _program_sha256(program: str) -> str:
    return hashlib.sha256(program.encode()).hexdigest()


def _grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def execute_program(
    program: str,
    inputs: list[list[list[int]]],
    *,
    expected_setting: str,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Run one exact program in the included isolated Racket verifier."""
    from arc_repl.isolated_verifier import Limits, verify_candidate

    expected_setting = validate_parameter(expected_setting)
    allowed = {
        value: racket_program(value, root=root) for value in PARAMETER_VALUES
    }
    if program != allowed[expected_setting]:
        raise ValueError("program does not match the declared parameter setting")
    if not isinstance(inputs, list) or not 1 <= len(inputs) <= 120:
        raise ValueError("execution batch must contain 1..120 inputs")

    canary = {
        "input": deepcopy(inputs[0]),
        "output": apply_rule(inputs[0], expected_setting),
    }
    task = {
        "train": [canary],
        "test": [{"input": deepcopy(grid)} for grid in inputs],
    }
    return verify_candidate(
        task,
        program,
        racket_path=os.environ.get("RACKET_PATH", ""),
        limits=Limits(max_pairs=128),
    )


def _require_outputs(receipt: dict[str, Any]) -> list[list[list[int]]]:
    if receipt.get("status") != "pass":
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    outputs = receipt.get("test_outputs")
    if not isinstance(outputs, list):
        raise RuntimeError("Racket receipt omitted test_outputs")
    return outputs


def _teachability(
    outputs: dict[str, list[list[list[int]]]], selected: str
) -> dict[str, Any]:
    selected = validate_parameter(selected)
    if set(outputs) != set(PARAMETER_VALUES):
        raise ValueError("teachability requires outputs for every parameter setting")
    lengths = {len(value) for value in outputs.values()}
    expected_pairs = N_TRAIN + N_TEST
    if lengths != {expected_pairs}:
        raise ValueError(f"teachability requires exactly {expected_pairs} aligned outputs")
    alternative = next(value for value in PARAMETER_VALUES if value != selected)
    refuting = [
        index
        for index, (truth, rival) in enumerate(
            zip(outputs[selected], outputs[alternative])
        )
        if truth != rival
    ]
    rotations = []
    for query_index in range(expected_pairs):
        demonstrations = [
            index for index in range(expected_pairs) if index != query_index
        ]
        survives = not bool(set(demonstrations) & set(refuting))
        rotations.append(
            {
                "query_index": query_index,
                "demonstration_indices": demonstrations,
                "surviving_parameter_rivals": [alternative] if survives else [],
                "identifiable": not survives,
            }
        )
    return {
        "selected": selected,
        "alternative": alternative,
        "refuting_pair_indices": refuting,
        "production": rotations[-1],
        "rotations": rotations,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_evidence(out: Path, *, seeds: int = 8) -> dict[str, Any]:
    """Build bounded Racket-backed evidence for both partner-axis settings."""
    if type(seeds) is not int or not 2 <= seeds <= 16:
        raise ValueError("seeds must be an integer in 2..16")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)

    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    identities: list[dict[str, Any]] = []
    inputs: list[list[list[int]]] = []
    for pair in canonical:
        inputs.append(deepcopy(pair["input"]))
        identities.append(
            {
                "origin": "canonical",
                "variant": pair.get("variant"),
                "split": pair.get("split"),
                "pair_index": pair.get("pair_index"),
            }
        )
    generated_start = len(inputs)
    for seed in range(seeds):
        for pair_index in range(N_TRAIN + N_TEST):
            grid = build_input(seed, pair_index)
            inputs.append(grid)
            identities.append(
                {"origin": "prototype", "seed": seed, "pair_index": pair_index}
            )

    programs = {
        value: racket_program(value, root=root) for value in PARAMETER_VALUES
    }
    executions: dict[str, Any] = {
        "schema": "0832c700ffb9-ring-partner-axis-racket-executions-v1",
        "status": "proposed_prototype",
        "inputs": [
            {**identity, "input": grid, "input_sha256": _grid_sha256(grid)}
            for identity, grid in zip(identities, inputs)
        ],
        "programs": {},
    }
    outputs: dict[str, list[list[list[int]]]] = {}
    for value, program in programs.items():
        receipt = execute_program(
            program, inputs, expected_setting=value, root=root
        )
        executions["programs"][value] = {
            "program_sha256": _program_sha256(program),
            "receipt": receipt,
        }
        _write_json(out / "racket-executions.private.json", executions)
        outputs[value] = _require_outputs(receipt)

    python_matches = {
        value: sum(
            observed == apply_rule(grid, value)
            for grid, observed in zip(inputs, outputs[value])
        )
        for value in PARAMETER_VALUES
    }
    canonical_labels = [pair["output"] for pair in canonical]
    canonical_count = len(canonical)
    canonical_row_matches = sum(
        observed == expected
        for observed, expected in zip(
            outputs["row"][:canonical_count], canonical_labels
        )
    )
    canonical_axis_coincides = sum(
        row_output == column_output
        for row_output, column_output in zip(
            outputs["row"][:canonical_count],
            outputs["column"][:canonical_count],
        )
    )

    lessons = []
    private_episodes = []
    covering: dict[str, int] = {}
    for seed in range(seeds):
        start = generated_start + seed * (N_TRAIN + N_TEST)
        per_setting = {
            value: outputs[value][start : start + N_TRAIN + N_TEST]
            for value in PARAMETER_VALUES
        }
        selected = choose_parameter(seed)
        covering.setdefault(selected, seed)
        teaching = _teachability(per_setting, selected)
        lessons.append({"seed": seed, **teaching})

        pairs = [
            {
                "input": deepcopy(inputs[start + pair_index]),
                "output": deepcopy(per_setting[selected][pair_index]),
            }
            for pair_index in range(N_TRAIN + N_TEST)
        ]
        private_episodes.append(
            {
                "schema": "0832c700ffb9-ring-partner-axis-private-episode-v1",
                "status": "proposed_prototype",
                "task_id": TASK_ID,
                "seed": seed,
                "parameters": {PARAMETER_NAME: selected},
                "program": programs[selected],
                "program_sha256": _program_sha256(programs[selected]),
                "label_backend": "racket",
                "train": pairs[:N_TRAIN],
                "test": pairs[N_TRAIN:],
                "teachability": teaching,
            }
        )

    if set(covering) != set(PARAMETER_VALUES):
        raise RuntimeError(
            f"bounded seed census did not cover both settings: {covering}"
        )

    retained_episodes = [
        next(
            episode
            for episode in private_episodes
            if episode["seed"] == covering[value]
        )
        for value in PARAMETER_VALUES
    ]
    _write_json(out / "episodes.private.json", retained_episodes)
    for value, episode in zip(PARAMETER_VALUES, retained_episodes):
        _write_json(
            out / f"challenge-{value}.public.json", public_challenge(episode)
        )

    rules_dir = out / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    for value, program in programs.items():
        (rules_dir / f"{value}.rkt").write_text(program + "\n", encoding="utf-8")

    witness_index = generated_start
    row_witness = outputs["row"][witness_index]
    column_witness = outputs["column"][witness_index]
    differing_cells = sum(
        left != right
        for row_left, row_right in zip(row_witness, column_witness)
        for left, right in zip(row_left, row_right)
    )
    witness = {
        "task_id": TASK_ID,
        "seed": 0,
        "pair_index": 0,
        "profile": _load_parent().schedule_profile(0, 0, episode_difficulty(0)),
        "input": inputs[witness_index],
        "row_output": row_witness,
        "column_output": column_witness,
        "differing_cells": differing_cells,
        "row_program_sha256": _program_sha256(programs["row"]),
        "column_program_sha256": _program_sha256(programs["column"]),
    }
    _write_json(out / "same-input-setting-witness.json", witness)

    owned_paths = [
        HERE / "prototype.py",
        HERE / "verify.py",
        HERE / "README.md",
        HERE.parents[1] / "tests" / "test_parametric_ring_partner_axis.py",
    ]
    identifiable_rotations = sum(
        rotation["identifiable"]
        for lesson in lessons
        for rotation in lesson["rotations"]
    )
    report = {
        "schema": "0832c700ffb9-ring-partner-axis-prototype-report-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameters": {
            PARAMETER_NAME: {
                "allowed": list(PARAMETER_VALUES),
                "default": DEFAULT_PARAMETER,
                "selection": "once per deterministic episode seed",
            }
        },
        "canonical_rule_unchanged": True,
        "canonical_default_byte_exact": programs["row"] == _canonical_program(root),
        "program_sha256": {
            value: _program_sha256(program)
            for value, program in programs.items()
        },
        "source_sha256": {
            path.relative_to(root).as_posix(): _file_sha256(path)
            for path in owned_paths
        },
        "racket_execution": {
            "inputs": len(inputs),
            "labels": sum(len(value) for value in outputs.values()),
            "python_matches": python_matches,
            "canonical_pairs": canonical_count,
            "canonical_row_matches": canonical_row_matches,
            "canonical_axis_coincides": canonical_axis_coincides,
        },
        "census": {
            "seeds": list(range(seeds)),
            "episodes": len(lessons),
            "demonstrations_per_episode": N_TRAIN,
            "queries_per_episode": N_TEST,
            "rotations": len(lessons) * (N_TRAIN + N_TEST),
            "identifiable_rotations": identifiable_rotations,
            "selected_parameter_by_seed": [
                {"seed": seed, PARAMETER_NAME: choose_parameter(seed)}
                for seed in range(seeds)
            ],
            "covering_seeds": covering,
        },
        "same_input_witness": {
            "path": "same-input-setting-witness.json",
            "outputs_differ": row_witness != column_witness,
            "differing_cells": differing_cells,
        },
        "evidence": [
            "racket-executions.private.json",
            "episodes.private.json",
            "challenge-row.public.json",
            "challenge-column.public.json",
            "rules/row.rkt",
            "rules/column.rkt",
            "same-input-setting-witness.json",
        ],
        "limitations": [
            "This is a task-local proposed prototype, not production integration or approval.",
            "The bounded rule domain contains only row and column partner selection.",
            "Canonical diagonal-colour examples do not identify the axis because both partners have the same colour.",
            "Teaching relies on the selected generator's same-row-colour rectangles and period-three schedule.",
            "The finite seed census checks only the declared parameter rival, not every conceivable rule.",
        ],
        "lessons": lessons,
    }
    report["passed"] = bool(
        all(count == len(inputs) for count in python_matches.values())
        and canonical_row_matches == canonical_count
        and report["canonical_default_byte_exact"]
        and report["same_input_witness"]["outputs_differ"]
        and identifiable_rotations == report["census"]["rotations"]
        and set(covering) == set(PARAMETER_VALUES)
    )
    _write_json(out / "report.json", report)

    manifest_members = sorted(
        path
        for path in out.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    manifest = {
        "schema": "0832c700ffb9-ring-partner-axis-evidence-manifest-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "members": {
            path.relative_to(out).as_posix(): _file_sha256(path)
            for path in manifest_members
        },
    }
    _write_json(out / "manifest.json", manifest)
    return report
