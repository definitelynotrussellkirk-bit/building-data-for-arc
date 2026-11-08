"""Bounded structural, teaching, export, protected-Racket, and causal audit."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SPEC = importlib.util.spec_from_file_location(
    "_arc_61090a45e458_parametric_audit", HERE / "prototype.py"
)
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
family = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = family
SPEC.loader.exec_module(family)

SCHEMA = "arcpuzzles-61090a45e458-parametric-audit-v1"
SETTINGS = [{"recolor_policy": policy} for policy in family.RECOLOR_POLICIES]
DEMO_COUNTS = (2, 3, 4, 5, 6)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _different_cells(first: list[list[int]], second: list[list[int]]) -> int:
    if len(first) != len(second) or len(first[0]) != len(second[0]):
        raise ValueError("grid dimensions differ")
    return sum(
        a != b
        for row_a, row_b in zip(first, second)
        for a, b in zip(row_a, row_b)
    )


def structural_audit(seed_count: int) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes, public_challenge_id

    failures: list[dict[str, Any]] = []
    episodes = 0
    visible_pairs = 0
    matched_input_checks = 0
    prefix_checks = 0
    public_turn_checks = 0
    stress_checks = 0
    certificates = 0
    declared_rival_checks = 0
    cross_setting_query_disagreements = 0

    for seed in range(seed_count):
        for demos in DEMO_COUNTS:
            by_policy: dict[str, dict[str, Any]] = {}
            for settings in SETTINGS:
                policy = settings["recolor_policy"]
                context = {"seed": seed, "demos": demos, "setting": policy}
                try:
                    episode = family.generate(seed, settings, demos=demos, queries=4)
                    by_policy[policy] = episode
                    episodes += 1
                    visible_pairs += len(episode["train"]) + len(episode["test"])

                    visible = [
                        _digest(pair["input"])
                        for pair in episode["train"] + episode["test"]
                    ]
                    if len(visible) != len(set(visible)):
                        raise AssertionError("episode contains duplicate visible inputs")

                    certificate = family.teaching_certificate(
                        episode["train"], [pair["input"] for pair in episode["test"]]
                    )
                    certificates += 1
                    declared_rival_checks += len(family.HYPOTHESES) - 1
                    if certificate["survivors"] != [policy]:
                        raise AssertionError(
                            f"finite rivals survive: {certificate['survivors']}"
                        )

                    short = family.generate(seed, settings, demos=2, queries=4)
                    one = family.generate(seed, settings, demos=demos, queries=1)
                    if episode["train"][:2] != short["train"]:
                        raise AssertionError("demonstration prefix depends on count")
                    if episode["test"][0] != one["test"][0]:
                        raise AssertionError("first query depends on query count")
                    if family.public_turn(episode, 0) != family.public_turn(one, 0):
                        raise AssertionError("first public turn differs from single-query use")
                    prefix_checks += 1

                    for query_index in range(4):
                        challenge = family.public_turn(episode, query_index)
                        raw = public_challenge_bytes(challenge)
                        if hashlib.sha256(raw).hexdigest() != public_challenge_id(challenge):
                            raise AssertionError("public ID does not hash exact visible bytes")
                        decoded = json.loads(raw)
                        if set(decoded) != {"train", "test"}:
                            raise AssertionError("public challenge has private fields")
                        if len(decoded["test"]) != 1 or set(decoded["test"][0]) != {"input"}:
                            raise AssertionError("public challenge leaks answer/future query")
                        public_turn_checks += 1

                    stress = episode["test"][3]["input"]
                    if (len(stress), len(stress[0])) != (30, 30):
                        raise AssertionError("fourth query is not 30x30")
                    colored = [
                        (row, col)
                        for row, values in enumerate(stress)
                        for col, value in enumerate(values)
                        if value
                    ]
                    if len(colored) < 240:
                        raise AssertionError("30x30 stress has insufficient content")
                    if len({row for row, _ in colored}) < 24 or len({col for _, col in colored}) < 24:
                        raise AssertionError("30x30 stress has insufficient spread")
                    if not any(row in {0, 29} or col in {0, 29} for row, col in colored):
                        raise AssertionError("30x30 stress has no boundary contact")
                    stress_checks += 1
                except Exception as exc:
                    failures.append({**context, "error": f"{type(exc).__name__}: {exc}"})

            if set(by_policy) == set(family.RECOLOR_POLICIES):
                first, second = (by_policy[name] for name in family.RECOLOR_POLICIES)
                first_inputs = [pair["input"] for pair in first["train"] + first["test"]]
                second_inputs = [pair["input"] for pair in second["train"] + second["test"]]
                if first_inputs != second_inputs:
                    failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "setting": "matched_inputs",
                            "error": "settings received different visible inputs",
                        }
                    )
                else:
                    matched_input_checks += 1
                for left, right in zip(first["test"], second["test"]):
                    if left["output"] == right["output"]:
                        failures.append(
                            {
                                "seed": seed,
                                "demos": demos,
                                "setting": "query_disagreement",
                                "error": "settings agree on a held-out query",
                            }
                        )
                    else:
                        cross_setting_query_disagreements += 1

    return {
        "schema": SCHEMA,
        "task_id": family.TASK_ID,
        "scope": (
            "Bounded Python structure/count/prefix/export/stress sweep and finite "
            "declared-rival self-review; no universal uniqueness claim."
        ),
        "seed_count": seed_count,
        "seed_range": [0, seed_count - 1],
        "settings": SETTINGS,
        "demo_counts": list(DEMO_COUNTS),
        "queries": 4,
        "episodes": episodes,
        "visible_pairs": visible_pairs,
        "matched_input_checks": matched_input_checks,
        "prefix_checks": prefix_checks,
        "public_turn_checks": public_turn_checks,
        "stress_30x30_checks": stress_checks,
        "finite_rival_certificates": certificates,
        "declared_rival_checks": declared_rival_checks,
        "cross_setting_query_disagreements": cross_setting_query_disagreements,
        "hypotheses": list(family.HYPOTHESES),
        "failures": failures,
    }


def protected_audit() -> tuple[dict[str, Any], dict[str, Any]]:
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    failures: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    runtime = ROOT / "shared" / "runtime"
    requests = 0
    evaluations = 0
    cache: dict[tuple[str, str], list[list[int]]] = {}

    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            if identity.get("backend") != "racket" or identity.get("protected") is not True:
                raise RuntimeError("live protected Racket backend required")

            def execute(source: str, grid: list[list[int]]) -> list[list[int]]:
                nonlocal requests, evaluations
                requests += 1
                key = (hashlib.sha256(source.encode()).hexdigest(), _digest(grid))
                if key not in cache:
                    cache[key] = apply(source, grid)
                    evaluations += 1
                return deepcopy(cache[key])

            for seed in (0, 17):
                for demos in (2, 3, 6):
                    for settings in SETTINGS:
                        policy = settings["recolor_policy"]
                        context = {"seed": seed, "demos": demos, "setting": policy}
                        try:
                            episode = family.generate(seed, settings, demos=demos, queries=4)
                            mismatches = []
                            for index, pair in enumerate(episode["train"] + episode["test"]):
                                if execute(episode["program_solution"], pair["input"]) != pair["output"]:
                                    mismatches.append(index)
                            survivors = []
                            for candidate in SETTINGS:
                                source = family.program(candidate)
                                if all(
                                    execute(source, pair["input"]) == pair["output"]
                                    for pair in episode["train"]
                                ):
                                    survivors.append(candidate)
                            if mismatches:
                                raise AssertionError(f"Racket/Python mismatches at {mismatches}")
                            if survivors != [settings]:
                                raise AssertionError(f"native demo survivors are {survivors}")
                            jobs.append(
                                {
                                    **context,
                                    "pairs": demos + 4,
                                    "program_sha256": hashlib.sha256(
                                        episode["program_solution"].encode()
                                    ).hexdigest(),
                                    "native_survivors": survivors,
                                    "input_sha256": [
                                        _digest(pair["input"])
                                        for pair in episode["train"] + episode["test"]
                                    ],
                                }
                            )
                        except Exception as exc:
                            failures.append({**context, "error": f"{type(exc).__name__}: {exc}"})

            episode = family.generate(
                0, {"recolor_policy": "largest_target_seed"}, demos=3, queries=4
            )
            pair = episode["test"][0]
            correct_source = family.program({"recolor_policy": "largest_target_seed"})
            wrong_source = (HERE / "smallest_target_seed_counterfactual.rkt").read_text(
                encoding="utf-8"
            )
            correct = execute(correct_source, pair["input"])
            counterfactual = execute(wrong_source, pair["input"])
            expected_wrong = family.predict(pair["input"], "smallest_target_seed")
            if correct != pair["output"]:
                failures.append({"witness": "correct", "error": "correct Racket label mismatch"})
            if counterfactual != expected_wrong:
                failures.append(
                    {"witness": "counterfactual", "error": "counterfactual Racket/Python mismatch"}
                )
            if correct == counterfactual:
                failures.append({"witness": "causal", "error": "wrong intermediate unchanged"})
            witness = {
                "schema": "arcpuzzles-61090a45e458-causal-candidate-v1",
                "task_id": family.TASK_ID,
                "seed": 0,
                "settings": {"recolor_policy": "largest_target_seed"},
                "split": "test",
                "pair_index": 0,
                "step_a": (
                    "Parse the three frames, compute each enclosed target size, and select "
                    "the uniquely largest target frame."
                ),
                "intermediate": (
                    "The selected frame identity together with its target size and singleton "
                    "seed color."
                ),
                "step_b": (
                    "Use the selected seed color to recolor every frame's target while "
                    "preserving all borders and singleton seeds."
                ),
                "why_b_depends_on_a": (
                    "The global paint color is the seed inside the input-dependent largest-"
                    "target frame and cannot be chosen before that frame is selected."
                ),
                "intermediate_value": family.largest_target_intermediate(pair["input"]),
                "wrong_intermediate_value": {
                    "selector": "smallest_target_frame",
                    "seed_color": family.analyze(pair["input"])["frames"][
                        min(
                            range(3),
                            key=lambda i: family.analyze(pair["input"])["frames"][i][
                                "target_size"
                            ],
                        )
                    ]["seed_color"],
                },
                "ablation": "wrong_intermediate",
                "input": pair["input"],
                "program": correct_source,
                "program_sha256": hashlib.sha256(correct_source.encode()).hexdigest(),
                "output": correct,
                "counterfactual_program": wrong_source,
                "counterfactual_program_sha256": hashlib.sha256(
                    wrong_source.encode()
                ).hexdigest(),
                "counterfactual_output": counterfactual,
                "different_cells": _different_cells(correct, counterfactual),
            }
        finally:
            bridge.close()

    return (
        {
            "schema": SCHEMA,
            "task_id": family.TASK_ID,
            "scope": (
                "Protected-Racket parity and demonstration-only setting survival on "
                "two settings, seeds 0/17, and demo counts 2/3/6."
            ),
            "racket": identity,
            "jobs": jobs,
            "job_count": len(jobs),
            "requests": requests,
            "unique_evaluations": evaluations,
            "failures": failures,
        },
        witness,
    )


def write_examples(root: Path) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes, public_challenge_id

    if root.exists():
        shutil.rmtree(root)
    public_dir = root / "public"
    private_dir = root / "private"
    public_dir.mkdir(parents=True)
    private_dir.mkdir(parents=True)
    public_ids: list[str] = []
    private_paths: list[str] = []
    for seed in (0, 17):
        for settings in SETTINGS:
            policy = settings["recolor_policy"]
            episode = family.generate(seed, settings, demos=3, queries=4)
            private = {
                "schema": "arcpuzzles-parametric-private-example-v1",
                "task_id": family.TASK_ID,
                "seed": seed,
                "settings": settings,
                "program_solution": episode["program_solution"],
                "train": episode["train"],
                "test": episode["test"],
            }
            private_path = private_dir / f"seed-{seed}-{policy}.json"
            private_path.write_text(
                json.dumps(private, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            private_paths.append(private_path.relative_to(root).as_posix())
            for query_index in range(4):
                challenge = family.public_turn(episode, query_index)
                identifier = public_challenge_id(challenge)
                path = public_dir / f"{identifier}.json"
                raw = public_challenge_bytes(challenge)
                if path.exists() and path.read_bytes() != raw:
                    raise AssertionError("public ID collision")
                path.write_bytes(raw)
                public_ids.append(identifier)
    if len(public_ids) != len(set(public_ids)):
        raise AssertionError("duplicate public visible payloads")
    return {
        "schema": SCHEMA,
        "task_id": family.TASK_ID,
        "public_files": len(public_ids),
        "private_files": len(private_paths),
        "public_ids": sorted(public_ids),
        "private_paths": sorted(private_paths),
    }


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "evidence" / "current")
    parser.add_argument("--examples", type=Path, default=HERE / "examples" / "current")
    parser.add_argument("--seeds", type=int, default=32)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 256:
        raise SystemExit("--seeds must be in 1..256")

    structural = structural_audit(args.seeds)
    protected, witness = protected_audit()
    examples = write_examples(args.examples)
    _write(args.out / "bounded-audit.json", structural)
    _write(args.out / "protected-audit.json", protected)
    _write(args.out / "causal-candidate.json", witness)
    _write(args.out / "examples.json", examples)
    summary = {
        "schema": SCHEMA,
        "task_id": family.TASK_ID,
        "passed": not structural["failures"] and not protected["failures"],
        "episodes": structural["episodes"],
        "visible_pairs": structural["visible_pairs"],
        "declared_rival_checks": structural["declared_rival_checks"],
        "protected_jobs": protected["job_count"],
        "protected_unique_evaluations": protected["unique_evaluations"],
        "witness_different_cells": witness["different_cells"],
        "public_files": examples["public_files"],
        "failures": structural["failures"] + protected["failures"],
    }
    _write(args.out / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
