"""Task-local parametric prototype for template transplantation.

The production generator and canonical authority remain unchanged.  One hidden
``stamp_transform`` is selected once for an entire episode:

* ``identity`` (canonical/default): stamp the cyan offsets unchanged.
* ``mirror_horizontal``: reflect the cyan offsets across the green anchor,
  then stamp that reflected shape at every red destination.

The legacy ``build_input``/``generate_episode`` interface retains its original
asymmetric hook/stair schedule. The native ``generate`` interface extends the
source grammar with procedural connected shapes, matched same-count teaching
interventions, separated and overlapping copies, and 8..30-cell canvas sides.
Both interfaces use the same offset transformation and preserve exact canonical
Racket bytes for identity. Native labels are claims for protected Racket replay.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
from typing import Any, Iterable

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "8de1c257a9c7"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "stamp_transform"
PARAMETER_VALUES = ("identity", "mirror_horizontal")
DEFAULT_PARAMETER = "identity"
N_TRAIN = 3
N_TEST = 1
HERE = Path(__file__).resolve().parent

_ASYMMETRIC_TEMPLATES = ("asymmetric_hook", "asymmetric_stair")
_CANVAS_SHAPES = ((17, 17), (18, 16), (16, 18), (19, 17))
_CANONICAL_OFFSET_FRAGMENT = (
    "(list (- (first p) gr) (- (second p) gc))"
)
_MIRROR_OFFSET_FRAGMENT = "(list (- (first p) gr) (- gc (second p)))"
_PARENT = None


def _load_parent():
    global _PARENT
    if _PARENT is not None:
        return _PARENT
    path = HERE.parents[1] / "generator.py"
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
        raise ValueError("seed must be nonnegative")
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


def _rng(seed: int, label: str) -> random.Random:
    payload = (
        f"{TASK_ID}|parametric|{PROTOTYPE_VERSION}|{seed}|{label}".encode()
    )
    keyed_seed = int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")
    return random.Random(keyed_seed)


def choose_parameter(seed: Any, value: Any | None = None) -> str:
    """Choose one hidden setting once per deterministic episode seed."""
    seed = _validate_seed(seed)
    if value is not None:
        return validate_parameter(value)
    return _rng(seed, "episode-parameter").choice(PARAMETER_VALUES)


def _transform_offsets(
    offsets: Iterable[tuple[int, int]], stamp_transform: str
) -> tuple[tuple[int, int], ...]:
    stamp_transform = validate_parameter(stamp_transform)
    materialized = tuple(offsets)
    if stamp_transform == "identity":
        return tuple(sorted(materialized))
    return tuple(sorted((dr, -dc) for dr, dc in materialized))


def _stamp(center: tuple[int, int], offsets: Iterable[tuple[int, int]]):
    row, col = center
    return {(row + dr, col + dc) for dr, dc in offsets}


def _valid_centers(
    height: int, width: int, offsets: Iterable[tuple[int, int]]
) -> list[tuple[int, int]]:
    offsets = tuple(offsets)
    return [
        (row, col)
        for row in range(height)
        for col in range(width)
        if all(
            0 <= row + dr < height and 0 <= col + dc < width
            for dr, dc in offsets
        )
    ]


def build_input(seed: Any, pair_index: Any) -> list[list[int]]:
    """Build one canonical-family input that is lawful for both settings."""
    seed = _validate_seed(seed)
    pair_index = _validate_pair_index(pair_index)
    parent = _load_parent()
    template_name = _ASYMMETRIC_TEMPLATES[pair_index % len(_ASYMMETRIC_TEMPLATES)]
    offsets = tuple(parent._TEMPLATES[template_name])
    mirrored = _transform_offsets(offsets, "mirror_horizontal")
    joint_offsets = tuple(sorted(set(offsets) | set(mirrored)))
    height, width = _CANVAS_SHAPES[pair_index % len(_CANVAS_SHAPES)]
    n_reds = 1 + pair_index % 4

    for attempt in range(256):
        rng = _rng(seed, f"input:{pair_index}:attempt:{attempt}")
        source_candidates = _valid_centers(height, width, offsets)
        green = rng.choice(source_candidates)
        source_cells = {green, *_stamp(green, offsets)}

        candidates = _valid_centers(height, width, joint_offsets)
        rng.shuffle(candidates)
        chosen: list[tuple[int, int]] = []
        occupied_regions: list[set[tuple[int, int]]] = []
        for center in candidates:
            region = {center, *_stamp(center, joint_offsets)}
            if region & source_cells:
                continue
            if any(region & prior for prior in occupied_regions):
                continue
            chosen.append(center)
            occupied_regions.append(region)
            if len(chosen) == n_reds:
                break
        if len(chosen) != n_reds:
            continue

        grid = [[0 for _ in range(width)] for _ in range(height)]
        gr, gc = green
        grid[gr][gc] = 3
        for dr, dc in offsets:
            grid[gr + dr][gc + dc] = 8
        for row, col in chosen:
            grid[row][col] = 2

        findings = parent.self_check(grid)
        if findings:
            continue
        if apply_rule(grid, "identity") == apply_rule(
            grid, "mirror_horizontal"
        ):
            continue
        return grid
    raise RuntimeError(
        f"could not construct pair {pair_index} for seed {seed} after 256 attempts"
    )


def apply_rule(grid: list[list[int]], stamp_transform: Any) -> list[list[int]]:
    """Compatibility spelling for the geometry-based Python reference."""
    return reference(grid, {PARAMETER_NAME: validate_parameter(stamp_transform)})


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
    stamp_transform: Any, *, root: Path | str | None = None
) -> str:
    """Materialize exact Racket source for one bounded parameter setting."""
    stamp_transform = validate_parameter(stamp_transform)
    source = _canonical_program(root)
    if stamp_transform == "identity":
        return source
    if source.count(_CANONICAL_OFFSET_FRAGMENT) != 1:
        raise ValueError("canonical horizontal-offset edit point is absent or ambiguous")
    return source.replace(_CANONICAL_OFFSET_FRAGMENT, _MIRROR_OFFSET_FRAGMENT)


def surviving_parameter_values(
    demonstrations: Iterable[dict[str, Any]],
) -> list[str]:
    materialized = list(demonstrations)
    survivors: list[str] = []
    for value in PARAMETER_VALUES:
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and apply_rule(pair["input"], value) == pair["output"]
            for pair in materialized
        ):
            survivors.append(value)
    return survivors


def generate_episode(
    seed: Any,
    *,
    stamp_transform: Any | None = None,
    n_train: Any = N_TRAIN,
    n_test: Any = N_TEST,
) -> dict[str, Any]:
    """Generate one complete private episode with one fixed hidden setting."""
    seed = _validate_seed(seed)
    selected = choose_parameter(seed, stamp_transform)
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
            "input_constraints": {
                "templates": list(_ASYMMETRIC_TEMPLATES),
                "both_settings_fit": True,
                "reason": (
                    "asymmetric templates make identity and horizontal mirror "
                    "observably different in every pair"
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

    # A lawful first input/output pair is execution plumbing, not an episode
    # demonstration. The requested labels are returned independently as tests.
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
    if lengths != {N_TRAIN + N_TEST}:
        raise ValueError("teachability requires exactly four aligned outputs")
    alternative = next(value for value in PARAMETER_VALUES if value != selected)
    refuting = [
        index
        for index, (truth, rival) in enumerate(
            zip(outputs[selected], outputs[alternative])
        )
        if truth != rival
    ]
    rotations = []
    for query_index in range(N_TRAIN + N_TEST):
        demonstrations = [
            index for index in range(N_TRAIN + N_TEST) if index != query_index
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
    """Build bounded Racket-backed evidence for both parameter settings."""
    if type(seeds) is not int or not 2 <= seeds <= 24:
        raise ValueError("seeds must be an integer in 2..24")
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
        "schema": "8de1c257a9c7-stamp-transform-racket-executions-v1",
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
    canonical_identity_matches = sum(
        observed == expected
        for observed, expected in zip(
            outputs["identity"][:canonical_count], canonical_labels
        )
    )
    canonical_mirror_coincides = sum(
        a == b
        for a, b in zip(
            outputs["identity"][:canonical_count],
            outputs["mirror_horizontal"][:canonical_count],
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
                "schema": "8de1c257a9c7-stamp-transform-private-episode-v1",
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
    identity_witness = outputs["identity"][witness_index]
    mirror_witness = outputs["mirror_horizontal"][witness_index]
    differing_cells = sum(
        a != b
        for row_a, row_b in zip(identity_witness, mirror_witness)
        for a, b in zip(row_a, row_b)
    )
    witness = {
        "task_id": TASK_ID,
        "seed": 0,
        "pair_index": 0,
        "input": inputs[witness_index],
        "identity_output": identity_witness,
        "mirror_horizontal_output": mirror_witness,
        "differing_cells": differing_cells,
        "identity_program_sha256": _program_sha256(programs["identity"]),
        "mirror_program_sha256": _program_sha256(
            programs["mirror_horizontal"]
        ),
    }
    _write_json(out / "same-input-setting-witness.json", witness)

    owned_paths = [
        HERE / "prototype.py",
        HERE / "verify.py",
        HERE / "README.md",
        HERE.parents[1]
        / "tests"
        / "test_parametric_stamp_transform_8de1c257a9c7.py",
        HERE.parents[1]
        / "tests"
        / "test_public_scalar_contract_8de1c257a9c7.py",
    ]
    identifiable_rotations = sum(
        rotation["identifiable"]
        for lesson in lessons
        for rotation in lesson["rotations"]
    )
    report = {
        "schema": "8de1c257a9c7-stamp-transform-prototype-report-v1",
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
        "canonical_default_byte_exact": programs["identity"]
        == _canonical_program(root),
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
            "canonical_identity_matches": canonical_identity_matches,
            "canonical_mirror_coincides": canonical_mirror_coincides,
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
            "outputs_differ": identity_witness != mirror_witness,
            "differing_cells": differing_cells,
        },
        "evidence": [
            "racket-executions.private.json",
            "episodes.private.json",
            "challenge-identity.public.json",
            "challenge-mirror_horizontal.public.json",
            "rules/identity.rkt",
            "rules/mirror_horizontal.rkt",
            "same-input-setting-witness.json",
        ],
        "limitations": [
            "This is a task-local proposed prototype, not production integration or approval.",
            "The bounded rule domain contains only identity and horizontal reflection.",
            "Teaching inputs deliberately use the two existing asymmetric templates; arbitrary unfiltered episodes can be ambiguous.",
            "All canonical templates are horizontally symmetric, so canonical pairs alone cannot identify the parameter.",
            "The finite seed census checks only the declared parameter rival, not every conceivable rule.",
        ],
        "lessons": lessons,
    }
    report["passed"] = bool(
        all(count == len(inputs) for count in python_matches.values())
        and canonical_identity_matches == canonical_count
        and canonical_mirror_coincides == canonical_count
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
        "schema": "8de1c257a9c7-stamp-transform-evidence-manifest-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "members": {
            path.relative_to(out).as_posix(): _file_sha256(path)
            for path in manifest_members
        },
    }
    _write_json(out / "manifest.json", manifest)
    return report


# Native admission extends the input grammar, never the meaning of the setting.
# The legacy builders above remain available with their original keyed schedule.
NATIVE_VERSION = "2.0.0"
NATIVE_ATTEMPT_LIMIT = 128
NATIVE_DEMO_LIMITS = (2, 6)
NATIVE_QUERY_LIMITS = (1, 4)
_DIRECTIONS4 = ((-1, 0), (0, -1), (0, 1), (1, 0))
_DIRECTIONS8 = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if (r, c) != (0, 0))


def normalize_settings(settings: Any = None) -> dict[str, str]:
    """Normalize only the declared setting; reject ambiguous or extra keys."""
    if settings is None:
        return {PARAMETER_NAME: DEFAULT_PARAMETER}
    if type(settings) is not dict:
        raise TypeError("settings must be a dictionary or None")
    if not settings:
        return {PARAMETER_NAME: DEFAULT_PARAMETER}
    if set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain only {PARAMETER_NAME!r}")
    return {PARAMETER_NAME: validate_parameter(settings[PARAMETER_NAME])}


def program(settings: Any = None) -> str:
    """Return canonical bytes or their single explicit horizontal-offset edit."""
    selected = normalize_settings(settings)[PARAMETER_NAME]
    source = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if selected == DEFAULT_PARAMETER:
        return source
    if source.count(_CANONICAL_OFFSET_FRAGMENT) != 1:
        raise ValueError("canonical horizontal-offset edit point is absent or ambiguous")
    return source.replace(_CANONICAL_OFFSET_FRAGMENT, _MIRROR_OFFSET_FRAGMENT)


def _connected_native(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    pending = [min(cells)]
    seen = set(pending)
    for r, c in pending:
        for dr, dc in _DIRECTIONS8:
            p = (r + dr, c + dc)
            if p in cells and p not in seen:
                seen.add(p)
                pending.append(p)
    return seen == cells


def _read_grid(grid: Any, *, native_bounds: bool) -> dict[str, Any]:
    result: dict[str, Any] = {"errors": []}
    errors = result["errors"]
    if type(grid) is not list or not grid or any(type(row) is not list for row in grid):
        errors.append("grid must be a nonempty list of row lists")
        return result
    h, w = len(grid), len(grid[0])
    if not w or any(len(row) != w for row in grid):
        errors.append("grid must be rectangular with nonempty rows")
        return result
    result.update(h=h, w=w, dimensions=[h, w])
    minimum = 8 if native_bounds else 1
    if not (minimum <= h <= 30 and minimum <= w <= 30):
        errors.append(f"both grid dimensions must be in {minimum}..30")
    if any(type(value) is not int or value not in (0, 2, 3, 8) for row in grid for value in row):
        errors.append("cells must be exact integer colors 0, 2, 3, or 8")
        return result
    positions = {color: [[r, c] for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
                 for color in (2, 3, 8)}
    reds, greens, cyans = positions[2], positions[3], positions[8]
    result.update(reds=reds, cyans=cyans, n_reds=len(reds), cyan_count=len(cyans))
    if len(greens) != 1:
        errors.append("exactly one green anchor is required")
    if not cyans:
        errors.append("at least one cyan source cell is required")
    if not reds:
        errors.append("at least one red destination is required")
    if len(greens) != 1 or not cyans:
        return result
    gr, gc = greens[0]
    offsets = [[r-gr, c-gc] for r, c in cyans]
    result.update(green=[gr, gc], shape_offsets=offsets,
                  bbox=[min(r for r, c in cyans), min(c for r, c in cyans),
                        max(r for r, c in cyans), max(c for r, c in cyans)])
    if not _connected_native({(gr, gc), *(tuple(p) for p in cyans)}):
        errors.append("green and cyan source must form one 8-connected component")
    for value in PARAMETER_VALUES:
        transformed = _transform_offsets((tuple(p) for p in offsets), value)
        if any(not (0 <= rr+dr < h and 0 <= rc+dc < w)
               for rr, rc in reds for dr, dc in transformed):
            errors.append(f"the complete {value} stamp must fit at every red destination")
    return result


def facts(grid: Any) -> dict[str, Any]:
    """JSON-safe source geometry and native grammar findings, with no labels."""
    return _read_grid(grid, native_bounds=True)


def self_check(grid: Any) -> list[str]:
    """Admit arbitrary connected source geometry on 8..30 by 8..30 canvases."""
    return list(facts(grid)["errors"])


def reference(grid: Any, settings: Any = None) -> list[list[int]]:
    """Claim labels from all observed offsets; protected Racket is authoritative.

    The rule also accepts smaller canonical/legacy scenes. The native sampler's
    dimension floor belongs to self_check, not to the transplantation operation.
    """
    selected = normalize_settings(settings)[PARAMETER_NAME]
    observed = _read_grid(grid, native_bounds=False)
    if observed["errors"]:
        raise ValueError("invalid stamp scene: " + "; ".join(observed["errors"]))
    offsets = _transform_offsets((tuple(p) for p in observed["shape_offsets"]), selected)
    output = [[0] * observed["w"] for _ in range(observed["h"])]
    for rr, rc in observed["reds"]:
        for dr, dc in offsets:
            output[rr+dr][rc+dc] = 8
    return output


def _native_rng(seed: int, label: str) -> random.Random:
    payload = f"{TASK_ID}|native|{NATIVE_VERSION}|{seed}|{label}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _grow_shape(rng: random.Random, kind: str, height: int, width: int,
                count: int, *, anchor: tuple[int, int] | None = None) -> tuple[tuple[int, int], ...]:
    """Grow source pixels from a scaffold; count does not identify the geometry."""
    if anchor is None:
        choices = [(r, c) for r in range(1, height-1) for c in range(1, width-1)
                   if (2*r, 2*c) != (height-1, width-1)
                   and (r in (1, height-2) or c in (1, width-2))]
        anchor = rng.choice(choices)
    ar, ac = anchor
    if kind == "ring":
        cells = {(r, c) for r in range(height) for c in range(width)
                 if r in (0, height-1) or c in (0, width-1)}
        interior = [(r, c) for r in range(1, height-1) for c in range(1, width-1)
                    if (r, c) != anchor]
        protected = {anchor, rng.choice(interior)}
    elif kind == "branch":
        cells = {(0, c) for c in range(width)} | {(r, width-1) for r in range(height)}
        protected = {anchor}
    else:
        cells = {(ar-1, ac)}
        protected = {anchor}
    cells -= protected
    if len(cells) > count:
        raise ValueError("source scaffold is larger than its requested cell count")
    for _ in range(count - len(cells)):
        frontier = sorted({(r+dr, c+dc) for r, c in cells for dr, dc in _DIRECTIONS4
                           if 0 <= r+dr < height and 0 <= c+dc < width}
                          - cells - protected)
        if not frontier:
            raise ValueError("source growth exhausted its bounded canvas")
        if kind == "branch":
            # Prefer one-cell-wide growth while allowing the finite request to finish.
            thin = [p for p in frontier if sum((p[0]+dr, p[1]+dc) in cells
                                              for dr, dc in _DIRECTIONS4) == 1]
            frontier = thin or frontier
        cells.add(rng.choice(frontier))
    return tuple(sorted((r-ar, c-ac) for r, c in cells))


def _render_input(height: int, width: int, green: tuple[int, int],
                  reds: list[tuple[int, int]], offsets: tuple[tuple[int, int], ...]) -> list[list[int]]:
    grid = [[0] * width for _ in range(height)]
    grid[green[0]][green[1]] = 3
    for r, c in _stamp(green, offsets):
        grid[r][c] = 8
    for r, c in reds:
        grid[r][c] = 2
    return grid


def _native_counts(grid: list[list[int]], selected: str) -> Counter:
    observed = facts(grid)
    offsets = _transform_offsets((tuple(p) for p in observed["shape_offsets"]), selected)
    return Counter((rr+dr, rc+dc) for rr, rc in observed["reds"] for dr, dc in offsets)


def _lesson_scene_ok(grid: list[list[int]], *, overlap: bool, large: bool = False) -> bool:
    observed = facts(grid)
    if observed["errors"]:
        return False
    source = {tuple(p) for p in observed["cyans"]}
    outputs = []
    for selected in PARAMETER_VALUES:
        counts = _native_counts(grid, selected)
        cells = set(counts)
        outputs.append(cells)
        if source <= cells:
            return False
        if overlap and not any(n >= 2 and n % 2 == 0 for n in counts.values()):
            return False
        if large and (len(cells) < 150 or min(r for r, c in cells) != 0
                      or max(r for r, c in cells) != 29
                      or max(c for r, c in cells) - min(c for r, c in cells) < 24):
            return False
    return outputs[0] != outputs[1]


def _place_shapes(rng: random.Random, height: int, width: int,
                  shapes: list[tuple[tuple[int, int], ...]], n_reds: int,
                  *, boundary: bool, overlap: bool, separate: bool = False) -> list[list[list[int]]] | None:
    source_offsets = tuple(sorted(set().union(*map(set, shapes))))
    joint_offsets = tuple(sorted(set(source_offsets) | {(dr, -dc) for dr, dc in source_offsets}))
    green = rng.choice(_valid_centers(height, width, source_offsets))
    source = {green, *_stamp(green, source_offsets)}
    available = [p for p in _valid_centers(height, width, joint_offsets) if p not in source]
    if len(available) < n_reds:
        return None
    rng.shuffle(available)
    valid = set(available)
    if boundary:
        all_centers = _valid_centers(height, width, joint_offsets)
        top = min(r for r, c in all_centers)
        bottom = max(r for r, c in all_centers)
        left = min(c for r, c in all_centers)
        right = max(c for r, c in all_centers)
        reds = [(top, left), (top, right), (bottom, left), (bottom, right)]
        if any(p not in valid for p in reds):
            return None
    elif overlap and n_reds >= 2:
        paired = next((p for p in available if (p[0], p[1]+1) in valid), None)
        if paired is None:
            return None
        reds = [paired, (paired[0], paired[1]+1)]
    else:
        reds = [available[0]]
    occupied_targets = set().union(*(_stamp(p, joint_offsets) | {p} for p in reds))
    for p in available:
        if len(reds) == n_reds:
            break
        if p not in reds:
            region = _stamp(p, joint_offsets) | {p}
            if separate and region & occupied_targets:
                continue
            reds.append(p)
            occupied_targets.update(region)
    if len(reds) != n_reds:
        return None
    grids = [_render_input(height, width, green, sorted(reds), offsets) for offsets in shapes]
    if not all(_lesson_scene_ok(grid, overlap=overlap, large=boundary) for grid in grids):
        return None
    if len(grids) == 2 and any(reference(grids[0], {PARAMETER_NAME:s}) == reference(grids[1], {PARAMETER_NAME:s})
                               for s in PARAMETER_VALUES):
        return None
    return grids


def _profile_metrics(grid: list[list[int]], *, split: str, slot: int, kind: str,
                     shape_attempts: int, layout_attempts: int) -> dict[str, Any]:
    observed = facts(grid)
    counts = {s:_native_counts(grid, s) for s in PARAMETER_VALUES}
    return {"split":split, "slot":slot, "kind":kind, "dimensions":observed["dimensions"],
            "shape_attempts":shape_attempts, "layout_attempts":layout_attempts,
            "cyan_count":observed["cyan_count"], "red_count":observed["n_reds"],
            "output_cells":{s:len(c) for s, c in counts.items()},
            "even_overlap_cells":{s:sum(n >= 2 and n % 2 == 0 for n in c.values()) for s, c in counts.items()}}


def _contrast_pair(seed: int) -> tuple[list[list[list[int]]], list[dict[str, Any]]]:
    config = _native_rng(seed, "contrast-profile")
    height, width = config.randint(18, 22), config.randint(20, 24)
    sh, sw = config.choice(((4, 6), (5, 5), (5, 6)))
    anchors = [(r, c) for r in range(1, sh-1) for c in range(1, sw-1)
               if (2*r, 2*c) != (sh-1, sw-1)]
    anchor = config.choice(anchors)
    count = 2*(sh+sw)-4 + config.randint(1, min(4, (sh-2)*(sw-2)-2))
    n_reds = config.randint(3, 4)
    layout_attempts = 0
    for attempt in range(NATIVE_ATTEMPT_LIMIT):
        shapes = [_grow_shape(_native_rng(seed, f"contrast:{attempt}:shape:{index}"),
                              "ring", sh, sw, count, anchor=anchor) for index in range(2)]
        if shapes[0] == shapes[1]:
            continue
        layout_attempts += 1
        grids = _place_shapes(_native_rng(seed, f"contrast:{attempt}:layout"), height, width,
                              shapes, n_reds, boundary=False, overlap=True)
        if grids is not None:
            metrics = [_profile_metrics(grid, split="train", slot=i, kind="same_count_ring_intervention",
                                         shape_attempts=attempt+1, layout_attempts=layout_attempts if i == 0 else 0)
                       for i, grid in enumerate(grids)]
            metrics[1]["layout_shared_with_train_slot"] = 0
            return grids, metrics
    raise ValueError(f"same-count teaching pair exhausted {NATIVE_ATTEMPT_LIMIT} deterministic attempts")


def _sample_profile(seed: int, split: str, slot: int, profile: tuple) -> tuple[list[list[int]], dict[str, Any]]:
    height, width, kind, sh, sw, count, n_reds, layout = profile
    boundary = layout == "boundary"
    overlap = layout in ("overlap", "boundary")
    for attempt in range(NATIVE_ATTEMPT_LIMIT):
        shape_rng = _native_rng(seed, f"{split}:{slot}:{attempt}:shape")
        anchor = (1, sw//2) if boundary else None
        offsets = _grow_shape(shape_rng, kind, sh, sw, count, anchor=anchor)
        grids = _place_shapes(_native_rng(seed, f"{split}:{slot}:{attempt}:layout"), height, width,
                              [offsets], n_reds, boundary=boundary, overlap=overlap,
                              separate=layout == "separate")
        if grids is not None:
            grid = grids[0]
            metrics = _profile_metrics(grid, split=split, slot=slot, kind=kind,
                                       shape_attempts=attempt+1, layout_attempts=attempt+1)
            metrics["layout"] = layout
            return grid, metrics
    raise ValueError(f"{split} profile {slot} exhausted {NATIVE_ATTEMPT_LIMIT} deterministic attempts")


@lru_cache(maxsize=32)
def _native_bank(seed: int) -> tuple:
    """One immutable-in-practice full bank per seed; callers receive deep copies."""
    train, metrics = _contrast_pair(seed)
    rng = _native_rng(seed, "profile-dimensions")
    demo_profiles = [
        (rng.randint(14, 17), rng.randint(17, 20), "branch", 5, 6, rng.randint(11, 15), 3, "overlap"),
        (rng.randint(12, 15), rng.randint(15, 18), "walk", 5, 5, rng.randint(9, 13), 1, "single"),
        (rng.randint(20, 23), rng.randint(17, 21), "ring", 6, 5, rng.randint(20, 23), 4, "overlap"),
        (rng.randint(23, 27), rng.randint(23, 27), "branch", 7, 7, rng.randint(15, 22), 6, "overlap"),
    ]
    query_profiles = [
        (8, 8, "branch", 3, 4, rng.randint(6, 8), 2, "overlap"),
        (rng.randint(12, 16), rng.randint(17, 21), "walk", 5, 6, rng.randint(10, 15), 1, "single"),
        (rng.randint(20, 24), rng.randint(21, 27), "ring", 5, 7, rng.randint(22, 27), 3, "separate"),
        (30, 30, "ring", 7, 9, rng.randint(40, 47), rng.randint(12, 16), "boundary"),
    ]
    for slot, profile in enumerate(demo_profiles, start=2):
        grid, row = _sample_profile(seed, "train", slot, profile)
        train.append(grid)
        metrics.append(row)
    test = []
    for slot, profile in enumerate(query_profiles):
        grid, row = _sample_profile(seed, "test", slot, profile)
        test.append(grid)
        metrics.append(row)
    if len({_grid_sha256(grid) for grid in train+test}) != 10:
        raise ValueError("fixed native bank contains duplicate inputs")
    return train, test, metrics


def generate(seed: Any, settings: Any = None, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    """Generate independent prefixes of one fixed, settings-neutral 6/4 bank."""
    seed = _validate_seed(seed)
    chosen = normalize_settings(settings)
    for name, value, bounds in (("demos", demos, NATIVE_DEMO_LIMITS), ("queries", queries, NATIVE_QUERY_LIMITS)):
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not bool, float, or string")
        if not bounds[0] <= value <= bounds[1]:
            raise ValueError(f"{name} must be in {bounds[0]}..{bounds[1]}")
    train, test, metrics = deepcopy(_native_bank(seed))
    return {
        "train":[{"input":g, "output":reference(g, chosen)} for g in train[:demos]],
        "test":[{"input":g, "output":reference(g, chosen)} for g in test[:queries]],
        "program_solution":program(chosen),
        "meta":{
            "schema":"8de1c257a9c7-native-episode-v1", "task_id":TASK_ID,
            "version":NATIVE_VERSION, "settings":chosen,
            "generation":{
                "input_seed":seed, "bank_sizes":{"demos":6, "queries":4},
                "attempt_limit_per_profile":NATIVE_ATTEMPT_LIMIT,
                "shape_rng":"SHA256 seed/profile/attempt; independent of setting and requested counts",
                "profiles":metrics,
                "total_shape_attempts":sum(m["shape_attempts"] for m in metrics),
                "total_layout_attempts":sum(m["layout_attempts"] for m in metrics),
            },
            "label_basis":"Python claims; native worker executes exact protected Racket before acceptance/export",
        },
    }
