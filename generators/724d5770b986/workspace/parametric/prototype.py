#!/usr/bin/env python3
"""Proposed, unapproved neighbourhood-radius variants for ARC 724d5770b986.

The selected production generator and canonical Racket authority remain fixed.
This task-local prototype varies only the Chebyshev neighbourhood radius: the
canonical/default radius 1 or the nearby radius 2.  One setting is chosen per
episode, all labels are executed by the exact materialized Racket rule, and
public challenges contain only visible demonstrations and query inputs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "724d5770b986"
VERSION = "proposed-neighbourhood-radius-v1"
ALLOWED_RADII = (1, 2)
DEFAULT_RADIUS = 1
MAX_TRAIN_COUNT = 4
MAX_TEST_COUNT = 8
MAX_EPISODE_INPUTS = MAX_TRAIN_COUNT + MAX_TEST_COUNT
CANONICAL_RULE_HASH = "e39c8a4e2b02"
CANONICAL_SHA256 = "31f92053867f6921de4e420f4d92859d82e5fcf319edc87a74a1c03af61d51da"
CANONICAL_RANGE_CLAUSE = "((dr (in-list ' (-1 0 1))) (dc (in-list ' (-1 0 1))))"
RADIUS_TWO_RANGE_CLAUSE = (
    "((dr (in-list ' (-2 -1 0 1 2))) (dc (in-list ' (-2 -1 0 1 2))))"
)


def _sha256(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def grid_sha256(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _validate_radius(radius: Any) -> int:
    if type(radius) is not int or radius not in ALLOWED_RADII:
        allowed = ", ".join(map(str, ALLOWED_RADII))
        raise ValueError(f"radius must be one of: {allowed}")
    return radius


def _validate_counts(train_count: Any, test_count: Any) -> tuple[int, int]:
    if type(train_count) is not int or not 1 <= train_count <= MAX_TRAIN_COUNT:
        raise ValueError(f"train_count must be a literal integer in 1..{MAX_TRAIN_COUNT}")
    if type(test_count) is not int or not 1 <= test_count <= MAX_TEST_COUNT:
        raise ValueError(f"test_count must be a literal integer in 1..{MAX_TEST_COUNT}")
    return train_count, test_count


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_RANGE_CLAUSE) != 1:
        raise ValueError("canonical source must contain exactly one radius-one range clause")
    if RADIUS_TWO_RANGE_CLAUSE in source:
        raise ValueError("canonical source unexpectedly contains the radius-two clause")
    return source


def canonical_source(*, root: str | Path | None = None) -> str:
    root_path = find_root(__file__) if root is None else Path(root)
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    radius: int = DEFAULT_RADIUS,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    setting = _validate_radius(radius)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if setting == DEFAULT_RADIUS:
        return canonical
    return canonical.replace(CANONICAL_RANGE_CLAUSE, RADIUS_TWO_RANGE_CLAUSE, 1)


def rule_setting(source: Any, *, root: str | Path | None = None) -> int:
    if not isinstance(source, str):
        raise ValueError("variant source must be Racket text")
    canonical = canonical_source(root=root)
    if source == canonical:
        return 1
    if source == canonical.replace(CANONICAL_RANGE_CLAUSE, RADIUS_TWO_RANGE_CLAUSE, 1):
        return 2
    raise ValueError("source is not the pinned canonical rule or its guarded radius-two variant")


def rule_callable(source: str, *, root: str | Path | None = None) -> str:
    """Return the exact callable inside one guarded ``(rule! ...)`` wrapper."""
    rule_setting(source, root=root)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len(prefix) : -1]
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def execute_rule_many(
    source: str,
    grids: Iterable[Any],
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    normalized_grids = [normalize_grid(grid) for grid in grids]
    if not normalized_grids:
        raise ValueError("at least one grid is required")
    grid_literals = [
        "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        for grid in normalized_grids
    ]
    expression = f"(map {rule_callable(source, root=root)} '({' '.join(grid_literals)}))"
    if bridge is None:
        with RacketBridge() as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    return [normalize_grid(grid) for grid in result]


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[int]]:
    return execute_rule_many(source, [grid], bridge=bridge, root=root)[0]


def distinguishing_input() -> list[list[int]]:
    """A lawful hand-built witness for radius 1 versus radius 2, including clipping."""
    grid = [[0] * 9 for _ in range(9)]
    grid[0][0] = 1
    grid[1][1] = 7
    grid[4][4] = 1
    grid[3][4] = 6
    grid[4][5] = 8
    return grid


def distinguishing_cells(grid: Any) -> list[list[int]]:
    """Original-black cells painted by radius 2 but not radius 1."""
    normalized = normalize_grid(grid)
    height, width = len(normalized), len(normalized[0])
    triggers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if normalized[row][col] == 1
    ]
    if not triggers:
        return []
    cells: list[list[int]] = []
    for row in range(height):
        for col in range(width):
            if normalized[row][col] != 0:
                continue
            distance = min(max(abs(row - tr), abs(col - tc)) for tr, tc in triggers)
            if distance == 2:
                cells.append([row, col])
    return cells


def parameters_for_seed(seed: Any) -> dict[str, int]:
    validated = _validate_seed(seed)
    return {"radius": random.Random(validated).choice(ALLOWED_RADII)}


def _sample_inputs(
    seed: int,
    count: int,
    *,
    root: Path,
) -> tuple[list[list[list[int]]], dict[str, Any]]:
    if type(count) is not int or not 1 <= count <= MAX_EPISODE_INPUTS:
        raise ValueError(f"count must be a literal integer in 1..{MAX_EPISODE_INPUTS}")
    generator, source_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    profiles = tuple(generator.GENERAL_PROFILES)
    difficulties = ("easy", "medium", "hard", None)
    rng = random.Random(seed ^ 0x724D5770B986)
    accepted: list[list[list[int]]] = []
    accepted_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    max_attempts = max(240, count * 60)

    for attempt in range(max_attempts):
        profile = profiles[attempt % len(profiles)]
        difficulty = difficulties[(attempt // len(profiles)) % len(difficulties)]
        source_seed = rng.randrange(2**63)
        sample_index = attempt
        try:
            grid = normalize_grid(
                generator.generate(
                    source_seed,
                    sample_index,
                    difficulty=difficulty,
                    scene_profile=profile,
                )
            )
        except (AssertionError, ValueError):
            continue
        cells = distinguishing_cells(grid)
        if not cells:
            continue
        key = _stable_json(grid)
        if key in seen:
            continue
        seen.add(key)
        accepted.append(grid)
        accepted_rows.append(
            {
                "profile": profile,
                "difficulty": difficulty,
                "source_seed": source_seed,
                "sample_index": sample_index,
                "input_sha256": grid_sha256(grid),
                "distinguishing_cell_count": len(cells),
                "distinguishing_cells": cells[:24],
            }
        )
        if len(accepted) == count:
            break

    if len(accepted) != count:
        raise RuntimeError(
            f"sampler produced {len(accepted)} of {count} distinct radius-identifying inputs "
            f"after {max_attempts} attempts"
        )
    return accepted, {
        "kind": "selected_generator_rejection_sample",
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": generator_sha256,
        "attempt_limit": max_attempts,
        "attempts_used": accepted_rows[-1]["sample_index"] + 1,
        "accepted": accepted_rows,
    }


def _make_episode_with_bridge(
    seed: int,
    train_count: int,
    test_count: int,
    root: Path,
    bridge: RacketBridge,
) -> dict[str, Any]:
    parameters = parameters_for_seed(seed)
    radius = parameters["radius"]
    inputs, input_source = _sample_inputs(seed, train_count + test_count, root=root)
    sources = {setting: materialize_rule(setting, root=root) for setting in ALLOWED_RADII}
    outputs = {
        setting: execute_rule_many(source, inputs, bridge=bridge, root=root)
        for setting, source in sources.items()
    }
    selected_outputs = outputs[radius]
    train = [
        {"input": copy.deepcopy(grid), "output": copy.deepcopy(output)}
        for grid, output in zip(inputs[:train_count], selected_outputs[:train_count])
    ]
    test = [
        {"input": copy.deepcopy(grid), "output": copy.deepcopy(output)}
        for grid, output in zip(inputs[train_count:], selected_outputs[train_count:])
    ]

    rivals: list[dict[str, Any]] = []
    ambiguities: list[int] = []
    for setting in ALLOWED_RADII:
        demo_mismatches = [
            index
            for index in range(train_count)
            if outputs[setting][index] != selected_outputs[index]
        ]
        query_mismatches = [
            index
            for index in range(test_count)
            if outputs[setting][train_count + index] != selected_outputs[train_count + index]
        ]
        if setting == radius:
            status = "matches_episode"
        elif demo_mismatches:
            status = "refuted_by_demonstrations"
        else:
            status = "survives_demonstrations"
            ambiguities.append(setting)
        rivals.append(
            {
                "radius": setting,
                "status": status,
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        )

    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "seed": seed,
        "parameters": parameters,
        "parameter_contract": {
            "name": "radius",
            "allowed_values": list(ALLOWED_RADII),
            "default": DEFAULT_RADIUS,
            "metric": "Chebyshev",
            "fixed_per_episode": True,
            "input_constraints": [
                "inputs are 8..30 by 8..30 ARC grids from the selected generator",
                "blue cells are triggers and only original-black cells may be painted",
                "every retained input has an original-black cell at minimum trigger distance two",
            ],
        },
        "rule": {
            "radius": radius,
            "racket_source": sources[radius],
            "sha256": _sha256(sources[radius]),
        },
        "input_source": input_source,
        "train": train,
        "test": test,
        "parameter_rivals": rivals,
        "ambiguities": ambiguities,
    }


def make_episode(
    seed: Any,
    *,
    train_count: Any = 2,
    test_count: Any = 4,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    validated_seed = _validate_seed(seed)
    validated_train, validated_test = _validate_counts(train_count, test_count)
    root_path = find_root(__file__) if root is None else Path(root)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode_with_bridge(
                validated_seed, validated_train, validated_test, root_path, owned
            )
    return _make_episode_with_bridge(
        validated_seed, validated_train, validated_test, root_path, bridge
    )


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Allowlist visible demonstrations and query inputs; deep-copy every grid."""
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(episode))


def _canonical_check(root: Path, bridge: RacketBridge) -> dict[str, Any]:
    source = materialize_rule(DEFAULT_RADIUS, root=root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    actual = execute_rule_many(source, [pair["input"] for pair in pairs], bridge=bridge, root=root)
    rows = []
    for pair, output in zip(pairs, actual):
        expected = pair["output"]
        rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": grid_sha256(pair["input"]),
                "expected_sha256": grid_sha256(expected),
                "actual_sha256": grid_sha256(output),
                "passed": output == expected,
            }
        )
    if not rows or not all(row["passed"] for row in rows):
        raise AssertionError("canonical radius-one replay failed")
    return {
        "task_id": TASK_ID,
        "rule_hash": CANONICAL_RULE_HASH,
        "source_sha256": _sha256(source),
        "pairs": rows,
        "passed": True,
    }


def _distinguishing_witness(root: Path, bridge: RacketBridge) -> dict[str, Any]:
    grid = distinguishing_input()
    outputs = {
        str(radius): execute_rule(
            materialize_rule(radius, root=root), grid, bridge=bridge, root=root
        )
        for radius in ALLOWED_RADII
    }
    if _stable_json(outputs["1"]) == _stable_json(outputs["2"]):
        raise AssertionError("declared radii are not distinct on the retained witness")
    return {
        "input": grid,
        "input_sha256": grid_sha256(grid),
        "distinguishing_cells": distinguishing_cells(grid),
        "outputs": outputs,
        "output_sha256": {key: grid_sha256(value) for key, value in outputs.items()},
    }


def _file_rows(root: Path, paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(paths):
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": _sha256(path.read_bytes()),
                "bytes": path.stat().st_size,
            }
        )
    return rows


def write_evidence(
    seeds: Iterable[Any],
    *,
    train_count: Any = 2,
    test_count: Any = 4,
    out: str | Path,
    root: str | Path | None = None,
) -> dict[str, Any]:
    validated_train, validated_test = _validate_counts(train_count, test_count)
    validated_seeds = tuple(_validate_seed(seed) for seed in seeds)
    if not validated_seeds:
        raise ValueError("at least one seed is required")
    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(out_path)
    root_path = find_root(__file__) if root is None else Path(root)

    with RacketBridge() as bridge:
        canonical_check = _canonical_check(root_path, bridge)
        witness = _distinguishing_witness(root_path, bridge)
        episodes = [
            make_episode(
                seed,
                train_count=validated_train,
                test_count=validated_test,
                root=root_path,
                bridge=bridge,
            )
            for seed in validated_seeds
        ]

    challenge_ids = [public_id(episode) for episode in episodes]
    if len(set(challenge_ids)) != len(challenge_ids):
        raise ValueError("duplicate visible challenge generated for supplied seeds")
    ordered = sorted(zip(challenge_ids, episodes), key=lambda item: item[0])
    challenge_ids = [challenge_id for challenge_id, _episode in ordered]
    episodes = [episode for _challenge_id, episode in ordered]

    out_path.mkdir(parents=True)
    evidence_paths: list[Path] = []

    canonical_path_out = out_path / "private/canonical-radius-one-replay.json"
    _write_json(canonical_path_out, canonical_check)
    evidence_paths.append(canonical_path_out)

    witness_path = out_path / "private/distinguishing-witness.json"
    _write_json(witness_path, witness)
    evidence_paths.append(witness_path)

    for radius in ALLOWED_RADII:
        rule_path = out_path / f"private/rules/radius-{radius}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(materialize_rule(radius, root=root_path), encoding="utf-8")
        evidence_paths.append(rule_path)

    episode_rows = []
    for index, (episode, challenge_id) in enumerate(zip(episodes, challenge_ids)):
        private_path = out_path / f"private/episode-{index:03d}.json"
        public_path = out_path / f"public/challenge-{challenge_id}.json"
        _write_json(private_path, episode)
        public_path.parent.mkdir(parents=True, exist_ok=True)
        public_path.write_bytes(public_bytes(episode))
        evidence_paths.extend((private_path, public_path))
        episode_rows.append(
            {
                "index": index,
                "parameters": copy.deepcopy(episode["parameters"]),
                "rule_sha256": episode["rule"]["sha256"],
                "public_id": challenge_id,
                "public_path": str(public_path.relative_to(out_path)),
                "private_path": str(private_path.relative_to(out_path)),
                "input_sha256": [
                    grid_sha256(pair["input"])
                    for pair in episode["train"] + episode["test"]
                ],
                "ambiguities": copy.deepcopy(episode["ambiguities"]),
            }
        )

    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": "proposed_unapproved",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "canonical_rule": {
            "radius": DEFAULT_RADIUS,
            "rule_hash": CANONICAL_RULE_HASH,
            "source_sha256": CANONICAL_SHA256,
            "replay_path": str(canonical_path_out.relative_to(out_path)),
        },
        "parameter": {
            "name": "radius",
            "allowed_values": list(ALLOWED_RADII),
            "default": DEFAULT_RADIUS,
            "metric": "Chebyshev",
        },
        "counts": {
            "episodes": len(episodes),
            "settings_exercised": len({episode["parameters"]["radius"] for episode in episodes}),
            "demonstrations_per_episode": validated_train,
            "queries_per_episode": validated_test,
            "ambiguous_parameter_rivals": sum(len(episode["ambiguities"]) for episode in episodes),
            "canonical_pairs_checked": len(canonical_check["pairs"]),
        },
        "episodes": episode_rows,
        "witness_path": str(witness_path.relative_to(out_path)),
        "runtime": racket_runtime_status(),
        "limitations": [
            "finite rival check covers only the declared radii 1 and 2",
            "retained episodes cover only the supplied seeds and selected-generator sampler",
            "prototype status does not approve variants or admit examples to training",
        ],
        "files": _file_rows(out_path, evidence_paths),
    }
    report_path = out_path / "report.json"
    _write_json(report_path, report)

    manifest = {
        "schema": "arcpuzzles-evidence-manifest-v1",
        "report": {
            "path": "report.json",
            "sha256": _sha256(report_path.read_bytes()),
            "bytes": report_path.stat().st_size,
        },
        "files": report["files"],
    }
    _write_json(out_path / "manifest.json", manifest)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 0])
    parser.add_argument("--train", type=int, default=2, dest="train_count")
    parser.add_argument("--test", type=int, default=4, dest="test_count")
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = write_evidence(
        args.seeds,
        train_count=args.train_count,
        test_count=args.test_count,
        out=args.out,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": report["task_id"],
                "prototype_version": report["prototype_version"],
                "counts": report["counts"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
