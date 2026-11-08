#!/usr/bin/env python3
"""Proposed target-selection parameter for the D4 accent-copying family.

This task-local authoring prototype preserves the canonical production rule.
It chooses one target policy per episode and derives every label by executing
an exact, hash-pinned Racket rule with the packet's protected bridge.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "089c14df9952"
VERSION = "proposed-target-policy-v1"
ALLOWED_TARGET_POLICIES = ("all", "hinted_only")
DEFAULT_TARGET_POLICY = "all"
CANONICAL_RULE_HASH = "1fa4f01a8b99"
CANONICAL_SHA256 = "9869b96928d4c93822c555c6fafb5f67fcf12b376015a4da5d373fa43a9fbc81"

# This is the one target-selection site in the pinned canonical Racket source.
# The alternative retains the base-skipping clause and additionally skips any
# component without a red-2 orientation hint.
CANONICAL_TARGET_GUARD = """(if (> (length (deco-colors obj)) 1)
           out"""
ALTERNATIVE_TARGET_GUARD = """(if (or (> (length (deco-colors obj)) 1)
               (empty? (filter (lambda (p) (= (val p) 2))
                               (obj-cells obj))))
           out"""

FIXTURE_SPECS = (
    {
        "fixture_id": "mixed_clip_16x17",
        "seed": 4201,
        "sample_index": 2,
        "difficulty": "medium",
        "overrides": {
            "grid_h": 16,
            "grid_w": 17,
            "target_count": 3,
            "texture": "clip",
        },
    },
    {
        "fixture_id": "plain_single_16x17",
        "seed": 5101,
        "sample_index": 1,
        "difficulty": "medium",
        "overrides": {
            "grid_h": 16,
            "grid_w": 17,
            "target_count": 1,
            "texture": "plain",
        },
    },
    {
        "fixture_id": "mixed_clip_17x18",
        "seed": 5102,
        "sample_index": 2,
        "difficulty": "hard",
        "overrides": {
            "grid_h": 17,
            "grid_w": 18,
            "target_count": 3,
            "texture": "clip",
        },
    },
    {
        "fixture_id": "plain_pair_18x19",
        "seed": 5301,
        "sample_index": 1,
        "difficulty": "hard",
        "overrides": {
            "grid_h": 18,
            "grid_w": 19,
            "target_count": 2,
            "texture": "plain",
        },
    },
)


def _sha256(value: str | bytes) -> str:
    data = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(data).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid: Any) -> str:
    return _sha256(_json(normalize_grid(grid)))


def _validate_seed(seed: Any) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_TARGET_GUARD) != 1:
        raise ValueError("canonical source must contain exactly one target-selection guard")
    if ALTERNATIVE_TARGET_GUARD in source:
        raise ValueError("canonical source unexpectedly contains the alternative guard")
    return source


def canonical_source(*, root: Path | str | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if isinstance(source, str):
                    sources.add(source)
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical source for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    target_policy: str = DEFAULT_TARGET_POLICY,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    if type(target_policy) is not str or target_policy not in ALLOWED_TARGET_POLICIES:
        raise ValueError(
            "target_policy must be exactly 'all' or 'hinted_only'"
        )
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if target_policy == DEFAULT_TARGET_POLICY:
        return canonical
    alternative = canonical.replace(
        CANONICAL_TARGET_GUARD,
        ALTERNATIVE_TARGET_GUARD,
        1,
    )
    if alternative.count(ALTERNATIVE_TARGET_GUARD) != 1:
        raise AssertionError("failed to materialize the alternative target guard")
    return alternative


def _restore_canonical(source: Any) -> str:
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    canonical_count = source.count(CANONICAL_TARGET_GUARD)
    alternative_count = source.count(ALTERNATIVE_TARGET_GUARD)
    if (canonical_count, alternative_count) == (1, 0):
        restored = source
    elif (canonical_count, alternative_count) == (0, 1):
        restored = source.replace(
            ALTERNATIVE_TARGET_GUARD,
            CANONICAL_TARGET_GUARD,
            1,
        )
    else:
        raise ValueError("Racket source must contain exactly one declared target guard")
    return _check_canonical_source(restored)


def rule_callable(source: str) -> str:
    """Strip only the outer ``rule!`` wrapper from one declared rule."""
    _restore_canonical(source)
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    body = source[len("(rule!") : -1].strip()
    # Canonical programs may place line comments between ``rule!`` and the
    # lambda. Extract the unique lambda, then reproduce the executor's legacy
    # rule! convention: h/w are lexical bindings around the supplied lambda.
    marker = "(lambda (g)"
    if body.count(marker) != 1:
        raise ValueError("expected exactly one wrapped grid lambda")
    lambda_body = body[body.index(marker) :]
    return (
        "(lambda (g) "
        "(let* ((h (rows g)) (w (cols g))) "
        f"({lambda_body} g)))"
    )


def execute_rule(source: str, grid: Any, *, bridge: RacketBridge | None = None):
    normalized = normalize_grid(grid)
    if normalized is None:
        raise ValueError("grid must be a rectangular ARC integer grid")
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def fixtures(*, root: Path | str | None = None) -> list[dict[str, Any]]:
    """Return four deterministic lawful inputs independent of target policy."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID,
        root=root,
    )
    rows: list[dict[str, Any]] = []
    for spec in FIXTURE_SPECS:
        overrides = copy.deepcopy(spec["overrides"])
        grid = generator.generate(
            spec["seed"],
            spec["sample_index"],
            difficulty=spec["difficulty"],
            **overrides,
        )
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError(
                f"fixture {spec['fixture_id']} is outside the task grammar: {errors}"
            )
        observed = generator.observe_overrides(grid)
        if observed != overrides:
            raise AssertionError(
                f"fixture {spec['fixture_id']} override mismatch: "
                f"observed={observed}, expected={overrides}"
            )
        rows.append({
            "fixture_id": spec["fixture_id"],
            "generation": {
                "seed": spec["seed"],
                "sample_index": spec["sample_index"],
                "difficulty": spec["difficulty"],
                "overrides": overrides,
                "generator_path": Path(generator_path).relative_to(root).as_posix(),
                "generator_sha256": generator_sha256,
            },
            "input": normalize_grid(grid),
            "input_sha256": grid_sha256(grid),
        })
    return rows


def parameters_for_seed(seed: Any) -> dict[str, str]:
    _validate_seed(seed)
    return {
        "target_policy": random.Random(seed).choice(ALLOWED_TARGET_POLICIES)
    }


def make_episode(
    seed: int,
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    _validate_seed(seed)
    parameters = parameters_for_seed(seed)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, parameters, root=root, bridge=owned)
    return _make_episode(seed, parameters, root=root, bridge=bridge)


def _make_episode(seed, parameters, *, root, bridge):
    root = find_root(__file__) if root is None else Path(root).resolve()
    canonical = canonical_source(root=root)
    rules = {
        policy: materialize_rule(policy, source=canonical)
        for policy in ALLOWED_TARGET_POLICIES
    }
    inputs = fixtures(root=root)
    random.Random(f"{TASK_ID}:fixture-order:{VERSION}:{seed}").shuffle(inputs)
    outputs = {
        policy: [
            execute_rule(source, fixture["input"], bridge=bridge)
            for fixture in inputs
        ]
        for policy, source in rules.items()
    }
    for index, fixture in enumerate(inputs):
        if outputs["all"][index] == outputs["hinted_only"][index]:
            raise AssertionError(
                f"fixture {fixture['fixture_id']} does not distinguish target policies"
            )

    target_policy = parameters["target_policy"]
    pairs = [
        {
            **copy.deepcopy(fixture),
            "target_policy": target_policy,
            "output": output,
            "output_sha256": grid_sha256(output),
        }
        for fixture, output in zip(inputs, outputs[target_policy], strict=True)
    ]

    rival_rows = []
    ambiguities = []
    for rival_policy in ALLOWED_TARGET_POLICIES:
        demo_mismatches = [
            index
            for index in range(3)
            if outputs[rival_policy][index] != outputs[target_policy][index]
        ]
        query_mismatches = (
            [0] if outputs[rival_policy][3] != outputs[target_policy][3] else []
        )
        status = (
            "refuted_by_demonstrations"
            if demo_mismatches
            else "ambiguous_query"
            if query_mismatches
            else "matches_episode"
        )
        row = {
            "target_policy": rival_policy,
            "racket_sha256": _sha256(rules[rival_policy]),
            "status": status,
            "demonstration_mismatch_indices": demo_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": outputs[rival_policy][:3],
            "query_predictions": outputs[rival_policy][3:],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    source = rules[target_policy]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": (
            "one random.Random(seed).choice(('all', 'hinted_only')) before all pairs"
        ),
        "input_constraints_depend_on_parameter": False,
        "invariant_reasoning": [
            "identify the uniquely decorated yellow-4 base component",
            "match each eligible target skeleton under a D4 transform",
            "use a red-2 hint to resolve answer-changing symmetry",
            "stamp and boundary-clip the transformed base accents",
        ],
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "racket_source": source,
        "racket_sha256": _sha256(source),
        "racket_callable": rule_callable(source),
        "racket_callable_sha256": _sha256(rule_callable(source)),
        "racket_path": f"private/rules/target-policy-{target_policy}.rkt",
        "train": pairs[:3],
        "test": pairs[3:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": 8,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy({
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    })


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _files_manifest(out: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(
        path
        for path in out.rglob("*")
        if path.is_file() and path.name != "report.json"
    ):
        rows.append({
            "path": path.relative_to(out).as_posix(),
            "sha256": _sha256(path.read_bytes()),
            "bytes": path.stat().st_size,
        })
    return rows


def write_evidence(
    seeds,
    *,
    out: Path | str,
    root: Path | str | None = None,
) -> dict[str, Any]:
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        with RacketBridge() as bridge:
            runtime_identity = bridge.runtime_identity
            canonical = canonical_source(root=root)
            canonical_checks = []
            for row in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_rule(canonical, row["input"], bridge=bridge)
                canonical_checks.append({
                    "variant": row["variant"],
                    "split": row["split"],
                    "pair_index": row["pair_index"],
                    "matches": actual == row["output"],
                    "input_sha256": grid_sha256(row["input"]),
                    "expected_sha256": grid_sha256(row["output"]),
                    "actual_sha256": grid_sha256(actual),
                })
            if not canonical_checks or not all(
                row["matches"] for row in canonical_checks
            ):
                raise AssertionError("canonical default failed canonical pair replay")

            episodes = [
                make_episode(seed, root=root, bridge=bridge) for seed in seeds
            ]
            covered = {
                episode["parameters"]["target_policy"] for episode in episodes
            }
            if covered != set(ALLOWED_TARGET_POLICIES):
                raise ValueError(
                    "evidence seeds must cover both target_policy settings; "
                    f"covered={sorted(covered)}"
                )

            witness = fixtures(root=root)[0]["input"]
            witness_outputs = {
                policy: execute_rule(
                    materialize_rule(policy, source=canonical),
                    witness,
                    bridge=bridge,
                )
                for policy in ALLOWED_TARGET_POLICIES
            }
            if witness_outputs["all"] == witness_outputs["hinted_only"]:
                raise AssertionError("retained witness does not distinguish policies")

        source_snapshot = out / "private" / "source_snapshot"
        source_snapshot.mkdir(parents=True, exist_ok=True)
        (source_snapshot / "prototype.py").write_bytes(Path(__file__).read_bytes())
        test_source = (
            root
            / "generators"
            / TASK_ID
            / "tests"
            / "test_parametric_target_policy.py"
        )
        if test_source.is_file():
            (source_snapshot / test_source.name).write_bytes(test_source.read_bytes())

        rule_dir = out / "private" / "rules"
        rule_dir.mkdir(parents=True, exist_ok=True)
        for policy in ALLOWED_TARGET_POLICIES:
            (rule_dir / f"target-policy-{policy}.rkt").write_text(
                materialize_rule(policy, source=canonical),
                encoding="utf-8",
            )

        episode_rows = []
        for episode in episodes:
            seed = episode["seed"]
            private_path = Path("private") / f"episode-{seed:03d}.json"
            public_path = Path("public") / f"episode-{seed:03d}.json"
            _write_json(out / private_path, episode)
            _write_json(out / public_path, public_challenge(episode))
            episode_rows.append({
                "seed": seed,
                "target_policy": episode["parameters"]["target_policy"],
                "private_path": private_path.as_posix(),
                "public_path": public_path.as_posix(),
                "racket_sha256": episode["racket_sha256"],
                "ambiguities": len(episode["ambiguities"]),
            })

        _write_json(out / "private" / "canonical_replay.json", canonical_checks)
        _write_json(out / "private" / "racket_runtime_identity.json", runtime_identity)
        _write_json(out / "private" / "distinguishing_witness.json", {
            "input": witness,
            "input_sha256": grid_sha256(witness),
            "outputs_by_target_policy": witness_outputs,
            "different": (
                witness_outputs["all"] != witness_outputs["hinted_only"]
            ),
        })

        report = {
            "schema": "arcpuzzles-proposed-parametric-evidence-v1",
            "task_id": TASK_ID,
            "prototype_version": VERSION,
            "status": "proposed_unapproved",
            "approved": False,
            "parameter": {
                "name": "target_policy",
                "allowed_values": list(ALLOWED_TARGET_POLICIES),
                "original_default": DEFAULT_TARGET_POLICY,
                "selected_once_per_episode": True,
                "input_constraints_depend_on_parameter": False,
                "meaning": {
                    "all": "stamp every matching target (canonical behavior)",
                    "hinted_only": "stamp only matching targets carrying a red-2 hint",
                },
            },
            "invariant_reasoning": episodes[0]["invariant_reasoning"],
            "canonical_rule_hash": CANONICAL_RULE_HASH,
            "canonical_source_sha256": CANONICAL_SHA256,
            "prototype_sha256": _sha256(Path(__file__).read_bytes()),
            "test_source_sha256": (
                _sha256(test_source.read_bytes()) if test_source.is_file() else None
            ),
            "episodes": episode_rows,
            "counts": {
                "episodes": len(episodes),
                "demonstrations": 3 * len(episodes),
                "queries": len(episodes),
                "settings_covered": len({
                    row["target_policy"] for row in episode_rows
                }),
                "canonical_pairs_checked": len(canonical_checks),
                "ambiguous_parameter_rivals": sum(
                    row["ambiguities"] for row in episode_rows
                ),
                "racket_rule_applications": (
                    8 * len(episodes) + len(canonical_checks) + 2
                ),
            },
            "commands": {
                "evidence": (
                    "python3 review.py run python3 "
                    "generators/089c14df9952/workspace/parametric/prototype.py "
                    "--seeds 0 1 --out ../checks/parametric/target-policy"
                ),
                "focused_test": (
                    "python3 review.py run python3 -m pytest -q "
                    "generators/089c14df9952/tests/"
                    "test_parametric_target_policy.py"
                ),
            },
            "limits": [
                "finite evidence for the declared two target policies and retained seeds",
                "four deterministic generator fixtures are not a replacement production distribution",
                "declared parameter rivals do not prove universal rule identifiability",
                "prototype status does not change canonical approval or production APIs",
            ],
        }
        report["files"] = _files_manifest(out)
        _write_json(out / "report.json", report)
        return report
    except Exception as exc:
        _write_json(out / "failure.json", {
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "seeds": list(seeds),
        })
        raise


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(args.seeds, out=args.out)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
