#!/usr/bin/env python3
"""Proposed occupied-vs-missing corner-basis episodes for 3ab9aab86992.

This task-local prototype never changes the selected canonical generator or its
RULE_HASH.  ``occupied`` is the byte-exact canonical program: the occupied
vertex of a tiny L chooses the matching output corner.  ``missing`` preserves
all object detection and drawing logic but uses the absent cell of the tiny
2x2 box, so it selects the diagonally opposite output corner.

The hidden setting is selected once per episode.  Inputs are generated from an
independent stream and every retained label is produced by the included Racket
runtime, not by a Python answer mirror.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


TASK_ID = "3ab9aab86992"
PROTOTYPE_VERSION = "corner-basis-prototype-1"
CORNER_BASES = ("occupied", "missing")
DEFAULT_CORNER_BASIS = "occupied"
N_TRAIN = 3
N_TEST = 1
DIFFICULTY = "medium"

_OCCUPIED_BLOCK = """(corner (cond
                                                      ((and tl tr bl) 'tl)
                                                      ((and tl tr br) 'tr)
                                                      ((and tl bl br) 'bl)
                                                      (else 'br))))"""
_MISSING_BLOCK = """(corner (cond
                                                      ((and tl tr bl) 'br)
                                                      ((and tl tr br) 'bl)
                                                      ((and tl bl br) 'tr)
                                                      (else 'tl))))"""

_PARENT_CACHE: dict[str, Any] = {}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def sha256(value: bytes | str) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _json_hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")))


def _validate_seed(seed: int) -> int:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer (not bool)")
    return seed


def validate_corner_basis(corner_basis: str) -> str:
    if type(corner_basis) is not str or corner_basis not in CORNER_BASES:
        raise ValueError("corner_basis must be exactly 'occupied' or 'missing'")
    return corner_basis


def choose_corner_basis(seed: int, corner_basis: str | None = None) -> str:
    """Select one hidden semantic setting for the whole episode."""
    _validate_seed(seed)
    if corner_basis is not None:
        return validate_corner_basis(corner_basis)
    digest = sha256(f"{TASK_ID}/{PROTOTYPE_VERSION}/{seed}/hidden-rule")
    return CORNER_BASES[int(digest, 16) % len(CORNER_BASES)]


def _canonical_record(root: Path) -> dict[str, Any]:
    path = root / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as stream:
        rows = [row for row in map(json.loads, stream) if row.get("task_id") == TASK_ID]
    if len(rows) != 1:
        raise ValueError(f"expected one canonical record for {TASK_ID}, found {len(rows)}")
    return rows[0]


def rule_program(
    corner_basis: str = DEFAULT_CORNER_BASIS,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize the exact Racket program for one proposed setting."""
    validate_corner_basis(corner_basis)
    repo = _repo_root() if root is None else Path(root)
    source = _canonical_record(repo)["program_solution"]
    if source.count(_OCCUPIED_BLOCK) != 1:
        raise ValueError("canonical source no longer has the pinned occupied-corner block")
    if corner_basis == DEFAULT_CORNER_BASIS:
        return source
    variant = source.replace(_OCCUPIED_BLOCK, _MISSING_BLOCK, 1)
    if variant == source or variant.count(_MISSING_BLOCK) != 1:
        raise ValueError("failed to materialize the missing-corner variant")
    return variant


def _load_parent(root: Path):
    key = str(root.resolve())
    if key not in _PARENT_CACHE:
        path = root / "generators" / TASK_ID / "generator.py"
        spec = importlib.util.spec_from_file_location("corner_basis_parent_generator", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load selected generator from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _PARENT_CACHE[key] = module
    return _PARENT_CACHE[key]


def sample_input(
    seed: int,
    pair_index: int,
    *,
    difficulty: str = DIFFICULTY,
    root: Path | str | None = None,
):
    """Draw one lawful, one-object input independently of the hidden setting.

    A single tiny L makes the two corner-basis settings disagree on every pair,
    preventing an episode from hiding the parameter behind color/orientation
    symmetries.  This is a bounded prototype input contract, not a production
    distribution change.
    """
    _validate_seed(seed)
    if isinstance(pair_index, bool) or not isinstance(pair_index, int) or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer (not bool)")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    repo = _repo_root() if root is None else Path(root)
    parent = _load_parent(repo)
    return parent.generate(
        seed,
        pair_index,
        difficulty=difficulty,
        n_corners=1,
    )


def validate_input(grid, *, root: Path | str | None = None) -> list[str]:
    repo = _repo_root() if root is None else Path(root)
    parent = _load_parent(repo)
    errors = list(parent.self_check(grid))
    if errors:
        return errors
    observed = parent.observe_overrides(grid)
    if observed["n_corners"] != 1:
        errors.append("prototype inputs require exactly one L component")
    return errors


def validate_rule_input(grid, *, root: Path | str | None = None) -> list[str]:
    """Validate the full canonical rule domain, without prototype sampling limits."""
    repo = _repo_root() if root is None else Path(root)
    return list(_load_parent(repo).self_check(grid))


def episode_inputs(
    seed: int,
    *,
    corner_basis: str | None = None,
    difficulty: str = DIFFICULTY,
    root: Path | str | None = None,
):
    """Return four parameter-independent inputs after validating one episode draw."""
    choose_corner_basis(seed, corner_basis)
    return [
        sample_input(seed, index, difficulty=difficulty, root=root)
        for index in range(N_TRAIN + N_TEST)
    ]


def _rule_callable(source: str) -> str:
    stripped = source.strip()
    prefix = "(rule! "
    if not stripped.startswith(prefix) or not stripped.endswith(")"):
        raise ValueError("expected exactly one (rule! <lambda>) wrapper")
    body = stripped[len(prefix):-1].strip()
    if not body.startswith("(lambda (g)"):
        raise ValueError("prototype rule must be a lambda over g")
    return body


def _grid_literal(grid) -> str:
    return "'(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in grid
    ) + ")"


def _normalize_grid(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("Racket returned an empty or malformed grid")
    width = len(grid[0])
    if any(
        not isinstance(row, list)
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("Racket returned a ragged or non-ARC grid")
    return [list(row) for row in grid]


def execute_program(program: str, inputs: list) -> dict[str, Any]:
    """Execute exact Racket source on all inputs and return a JSON-safe receipt."""
    if not isinstance(program, str) or not program.strip():
        raise ValueError("program must be a nonempty string")
    if not isinstance(inputs, list) or not inputs:
        raise ValueError("inputs must be a nonempty list")
    for index, grid in enumerate(inputs):
        errors = validate_rule_input(grid)
        if errors:
            raise ValueError(f"input {index} violates the canonical rule domain: {errors}")

    from arc_repl.racket_bridge import RacketBridge

    try:
        outputs = []
        with RacketBridge(max_calls_before_restart=64) as bridge:
            bridge.eval_text(f"(define prototype-rule {_rule_callable(program)})")
            runtime_identity = bridge.runtime_identity
            for grid in inputs:
                outputs.append(
                    _normalize_grid(
                        bridge.eval_text(f"(prototype-rule {_grid_literal(grid)})")
                    )
                )
        return {
            "status": "pass",
            "backend": "racket",
            "program_sha256": sha256(program),
            "input_count": len(inputs),
            "outputs": outputs,
            "runtime_identity": runtime_identity,
        }
    except Exception as exc:  # Retain infrastructure/runtime failures in evidence.
        return {
            "status": "fail",
            "backend": "racket",
            "program_sha256": sha256(program),
            "input_count": len(inputs),
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }


def _require_outputs(receipt: dict[str, Any]) -> list:
    if receipt.get("status") != "pass":
        raise RuntimeError(json.dumps(receipt, sort_keys=True))
    return receipt["outputs"]


def assemble_episode(
    *,
    seed: int,
    corner_basis: str,
    inputs: list,
    outputs: list,
    program: str,
) -> dict[str, Any]:
    _validate_seed(seed)
    validate_corner_basis(corner_basis)
    if len(inputs) != N_TRAIN + N_TEST or len(outputs) != len(inputs):
        raise ValueError("episode requires exactly three demonstrations and one query")
    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(output)}
        for grid, output in zip(inputs, outputs)
    ]
    return {
        "train": pairs[:N_TRAIN],
        "test": pairs[N_TRAIN:],
        "program": program,
        "meta": {
            "status": "prototype",
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "seed": seed,
            "parameters": {"corner_basis": corner_basis},
            "program_sha256": sha256(program),
            "label_backend": "racket",
            "demonstration_count": N_TRAIN,
            "query_count": N_TEST,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Whitelist projection without hidden parameters, source, or query labels."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def parameter_teachability(outputs: dict[str, list], selected: str) -> dict[str, Any]:
    """Score the complete declared two-setting rival set under all holdouts."""
    validate_corner_basis(selected)
    if set(outputs) != set(CORNER_BASES):
        raise ValueError("teachability requires outputs for both corner bases")
    if any(len(values) != N_TRAIN + N_TEST for values in outputs.values()):
        raise ValueError("each setting must contain exactly four labels")
    truth = outputs[selected]
    rivals = []
    for alternative in CORNER_BASES:
        if alternative == selected:
            continue
        refuting = [
            index
            for index, (expected, rival) in enumerate(zip(truth, outputs[alternative]))
            if expected != rival
        ]
        rivals.append(
            {"corner_basis": alternative, "refuting_pair_indices": refuting}
        )
    rotations = []
    for query_index in range(N_TRAIN + N_TEST):
        demonstrations = [
            index for index in range(N_TRAIN + N_TEST) if index != query_index
        ]
        survivors = [
            rival["corner_basis"]
            for rival in rivals
            if not set(demonstrations) & set(rival["refuting_pair_indices"])
        ]
        rotations.append(
            {
                "query_index": query_index,
                "demonstration_indices": demonstrations,
                "surviving_parameter_rivals": survivors,
                "identifiable": not survivors,
            }
        )
    return {
        "selected_corner_basis": selected,
        "rivals": rivals,
        "production": rotations[-1],
        "rotations": rotations,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_manifest(root: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            records.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path.read_bytes()),
                }
            )
    return records


def build_evidence(out: Path, *, seeds: int = 8) -> dict[str, Any]:
    """Execute both settings and retain bounded, source-bound prototype evidence."""
    if isinstance(seeds, bool) or not isinstance(seeds, int) or not 1 <= seeds <= 24:
        raise ValueError("seeds must be an integer in 1..24")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    root = _repo_root()
    canonical = _canonical_record(root)
    canonical_pairs = canonical["train"] + canonical["test"]

    programs = {basis: rule_program(basis, root=root) for basis in CORNER_BASES}
    for basis, program in programs.items():
        rule_path = out / "private/rules" / f"corner-basis-{basis}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(program + "\n", encoding="utf-8")

    identities = [
        {"origin": "canonical", "pair_index": index}
        for index in range(len(canonical_pairs))
    ]
    inputs = [deepcopy(pair["input"]) for pair in canonical_pairs]
    for seed in range(seeds):
        episode = episode_inputs(seed, root=root)
        for pair_index, grid in enumerate(episode):
            identities.append(
                {"origin": "prototype", "seed": seed, "pair_index": pair_index}
            )
            inputs.append(grid)

    receipts = {
        basis: execute_program(program, inputs)
        for basis, program in programs.items()
    }
    _write_json(
        out / "private/racket-executions.json",
        {
            "schema": "corner-basis-racket-executions-v1",
            "status": "prototype",
            "inputs": [
                {**identity, "input": grid, "input_sha256": _json_hash(grid)}
                for identity, grid in zip(identities, inputs)
            ],
            "programs": {
                basis: {
                    "parameters": {"corner_basis": basis},
                    "program": programs[basis],
                    "program_sha256": sha256(programs[basis]),
                    "execution": receipt,
                }
                for basis, receipt in receipts.items()
            },
        },
    )
    outputs = {basis: _require_outputs(receipt) for basis, receipt in receipts.items()}

    canonical_count = len(canonical_pairs)
    canonical_expected = [pair["output"] for pair in canonical_pairs]
    canonical_matches = outputs[DEFAULT_CORNER_BASIS][:canonical_count] == canonical_expected

    lessons = []
    private_episodes = []
    for seed in range(seeds):
        start = canonical_count + seed * (N_TRAIN + N_TEST)
        stop = start + N_TRAIN + N_TEST
        episode_inputs_for_seed = inputs[start:stop]
        per_setting = {basis: outputs[basis][start:stop] for basis in CORNER_BASES}
        for selected in CORNER_BASES:
            lesson = parameter_teachability(per_setting, selected)
            lessons.append({"seed": seed, **lesson})
            episode = assemble_episode(
                seed=seed,
                corner_basis=selected,
                inputs=episode_inputs_for_seed,
                outputs=per_setting[selected],
                program=programs[selected],
            )
            private_episodes.append(episode)
            if seed == 0:
                _write_json(
                    out / "public" / f"episode-{selected}.json",
                    public_challenge(episode),
                )

    _write_json(out / "private/episodes.json", private_episodes)
    first = canonical_count
    _write_json(
        out / "private/distinct-witness.json",
        {
            "seed": 0,
            "pair_index": 0,
            "input": inputs[first],
            "outputs": {basis: outputs[basis][first] for basis in CORNER_BASES},
            "outputs_differ": outputs["occupied"][first] != outputs["missing"][first],
        },
    )

    owned = [
        Path(__file__).resolve(),
        Path(__file__).with_name("README.md"),
        root / "generators" / TASK_ID / "tests/test_parametric_corner_basis.py",
        root / "generators" / TASK_ID / "generator.py",
        root / "shared/data/canonical/puzzles.jsonl",
    ]
    prototype_pair_indices = range(canonical_count, len(inputs))
    all_prototype_pairs_distinguish = all(
        outputs["occupied"][index] != outputs["missing"][index]
        for index in prototype_pair_indices
    )
    rotations = [rotation for lesson in lessons for rotation in lesson["rotations"]]
    report = {
        "schema": "corner-basis-prototype-report-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameters": {
            "corner_basis": {
                "allowed": list(CORNER_BASES),
                "default": DEFAULT_CORNER_BASIS,
                "selection": "once per deterministic episode seed",
            }
        },
        "invariant_reasoning": [
            "find each monochrome tiny 2x2 L triomino",
            "classify its orientation",
            "map that orientation to one output corner",
            "draw a same-color enlarged border L in that corner",
        ],
        "semantic_difference": {
            "occupied": "use the tiny L's occupied vertex (canonical)",
            "missing": "use the absent 2x2 cell, the diagonally opposite corner",
        },
        "input_constraints": {
            "shared_across_settings": True,
            "source": "selected generator with exact n_corners=1 override",
            "reason": "every retained pair distinguishes the two declared settings",
        },
        "source_sha256": {
            path.relative_to(root).as_posix(): sha256(path.read_bytes())
            for path in owned
        },
        "program_sha256": {
            basis: sha256(program) for basis, program in programs.items()
        },
        "canonical_reference_unchanged": True,
        "canonical_rule_hash_unchanged": True,
        "canonical_labeled_pairs": canonical_count,
        "canonical_default_matches": canonical_matches,
        "racket_execution_status": {
            basis: receipt["status"] for basis, receipt in receipts.items()
        },
        "racket_label_count": sum(len(receipt.get("outputs", [])) for receipt in receipts.values()),
        "census": {
            "seeds": list(range(seeds)),
            "settings_per_seed": len(CORNER_BASES),
            "episodes": len(lessons),
            "demonstrations_per_episode": N_TRAIN,
            "queries_per_episode": N_TEST,
            "production_identifiable": sum(
                lesson["production"]["identifiable"] for lesson in lessons
            ),
            "rotations": len(rotations),
            "rotations_identifiable": sum(rotation["identifiable"] for rotation in rotations),
            "all_prototype_pairs_distinguish": all_prototype_pairs_distinguish,
        },
        "seeded_parameter_draws": [
            {"seed": seed, "corner_basis": choose_corner_basis(seed)}
            for seed in range(seeds)
        ],
        "lessons": lessons,
        "public_files": [
            "public/episode-occupied.json",
            "public/episode-missing.json",
        ],
        "private_files": [
            "private/racket-executions.json",
            "private/episodes.json",
            "private/distinct-witness.json",
            "private/rules/corner-basis-occupied.rkt",
            "private/rules/corner-basis-missing.rkt",
        ],
        "commands": [
            "python3 review.py run python3 generators/3ab9aab86992/workspace/parametric/prototype.py --out ../checks/parametric/corner-basis-seeds-0-7 --seeds 8",
            "python3 review.py run python3 -m arcpuzzles check 3ab9aab86992 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests",
        ],
        "limitations": [
            "Proposed task-local extension; not a production parametric API or approval.",
            "Measured only the declared occupied/missing parameter rival on bounded seeds.",
            "Prototype inputs intentionally contain one L; symmetric multi-object color assignments can make the settings coincide.",
            "Finite rival checks do not establish uniqueness against arbitrary programs.",
            "The selected canonical generator and Racket authority remain unchanged apart from ordinary schedule diagnostics in generator.py.",
        ],
    }
    report["passed"] = bool(
        canonical_matches
        and all(receipt["status"] == "pass" for receipt in receipts.values())
        and sha256(programs["occupied"]) != sha256(programs["missing"])
        and all_prototype_pairs_distinguish
        and report["census"]["production_identifiable"] == len(lessons)
        and report["census"]["rotations_identifiable"] == len(rotations)
    )
    _write_json(out / "report.json", report)
    _write_json(
        out / "manifest.json",
        {
            "schema": "corner-basis-prototype-manifest-v1",
            "files": _file_manifest(out),
        },
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    parser.add_argument("--seeds", type=int, default=8, help="bounded seed count, 1..24")
    args = parser.parse_args()
    report = build_evidence(args.out, seeds=args.seeds)
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "canonical_default_matches": report["canonical_default_matches"],
                "racket_label_count": report["racket_label_count"],
                "census": report["census"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
