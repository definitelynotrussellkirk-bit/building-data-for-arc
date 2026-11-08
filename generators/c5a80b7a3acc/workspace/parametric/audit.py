"""Reusable structural, export, protected-Racket, and causal audit for c5a80b7a3acc."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_arc_c5a80b7a3acc_parametric_audit_prototype", _PROTOTYPE_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype at {_PROTOTYPE_PATH}")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)

SCHEMA = "c5a80b7a3acc-largest-component-audit-v1"
SETTINGS = [{"result_policy": value} for value in prototype.RESULT_POLICIES]
DEMO_COUNTS = list(range(2, 7))


def _digest(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(body).hexdigest()


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _different_cells(first: list[list[int]], second: list[list[int]]) -> int:
    height = max(len(first), len(second))
    width = max(len(first[0]), len(second[0]))
    return sum(
        (first[row][col] if row < len(first) and col < len(first[0]) else None)
        != (second[row][col] if row < len(second) and col < len(second[0]) else None)
        for row in range(height)
        for col in range(width)
    )


def _public_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    from reviewer_support import public_challenge_bytes

    return public_challenge_bytes(
        {"train": episode["train"], "test": [episode["test"][query_index]]}
    )


def _rival_case(policy: str) -> dict[str, Any]:
    episode = prototype.generate(0, {"result_policy": policy}, demos=2, queries=4)
    rows = []
    for rival in prototype.HYPOTHESES:
        if rival == policy:
            continue
        failed_demos = [
            index
            for index, pair in enumerate(episode["train"])
            if prototype.predict(pair["input"], rival) != pair["output"]
        ]
        disagreeing_queries = [
            index
            for index, pair in enumerate(episode["test"])
            if prototype.predict(pair["input"], rival) != pair["output"]
        ]
        rows.append(
            {
                "rival": rival,
                "first_failed_demo": failed_demos[0] if failed_demos else None,
                "disagreeing_queries": disagreeing_queries,
            }
        )
    return {
        "setting": {"result_policy": policy},
        "seed": 0,
        "demonstrations": 2,
        "queries": 4,
        "rivals": rows,
        "surviving_wrong_rivals": [
            row["rival"] for row in rows if row["first_failed_demo"] is None
        ],
        "scope": "Finite declared shortcut bank only; not a proof of unique induction.",
    }


def structural_stress(seed_count: int = 16) -> dict[str, Any]:
    if type(seed_count) is not int or not 1 <= seed_count <= 10_000:
        raise ValueError("seed_count must be an exact integer in 1..10000")

    failures: list[dict[str, Any]] = []
    episodes = visible_pairs = matched_input_checks = 0
    prefix_checks = public_turn_checks = stress_checks = 0
    finite_rival_certificates = 0

    for seed in range(seed_count):
        for demos in DEMO_COUNTS:
            by_policy: dict[str, dict[str, Any]] = {}
            for settings in SETTINGS:
                policy = settings["result_policy"]
                context = {"seed": seed, "demos": demos, "setting": policy}
                try:
                    episode = prototype.generate(seed, settings, demos=demos, queries=4)
                    by_policy[policy] = episode
                    episodes += 1
                    pairs = episode["train"] + episode["test"]
                    visible_pairs += len(pairs)
                    if len(episode["train"]) != demos or len(episode["test"]) != 4:
                        raise AssertionError("requested counts were not exact")
                    frozen = [_freeze(pair["input"]) for pair in pairs]
                    if len(frozen) != len(set(frozen)):
                        raise AssertionError("episode contains duplicate visible inputs")

                    certificate = prototype.teaching_certificate(
                        episode["train"], [pair["input"] for pair in episode["test"]]
                    )
                    if certificate["survivors"] != [policy]:
                        raise AssertionError(
                            f"demonstrations leave survivors {certificate['survivors']}"
                        )
                    finite_rival_certificates += 1

                    short = prototype.generate(seed, settings, demos=2, queries=4)
                    one = prototype.generate(seed, settings, demos=demos, queries=1)
                    if episode["train"][:2] != short["train"]:
                        raise AssertionError("demonstration prefix depends on requested count")
                    if episode["test"][0] != one["test"][0]:
                        raise AssertionError("first query depends on requested query count")
                    if _public_bytes(episode, 0) != _public_bytes(one, 0):
                        raise AssertionError("first public turn differs from single-query use")
                    prefix_checks += 1

                    for query_index in range(4):
                        public = json.loads(_public_bytes(episode, query_index))
                        if set(public) != {"train", "test"}:
                            raise AssertionError("public challenge has unexpected top-level fields")
                        if len(public["test"]) != 1 or set(public["test"][0]) != {"input"}:
                            raise AssertionError("public challenge leaks query answers or future queries")
                        public_turn_checks += 1

                    stress = episode["test"][3]["input"]
                    if (len(stress), len(stress[0])) != (30, 30):
                        raise AssertionError("fourth query is not 30x30")
                    colored = [
                        (row, col)
                        for row, values in enumerate(stress)
                        for col, value in enumerate(values)
                        if value in {2, 3}
                    ]
                    if len(colored) < 120:
                        raise AssertionError("30x30 stress has insufficient semantic content")
                    if not any(row in {0, 29} or col in {0, 29} for row, col in colored):
                        raise AssertionError("30x30 stress does not contact a boundary")
                    stress_checks += 1
                except Exception as exc:  # evidence keeps all bounded failures
                    failures.append({**context, "error": f"{type(exc).__name__}: {exc}"})

            if set(by_policy) == set(prototype.RESULT_POLICIES):
                first = by_policy[prototype.RESULT_POLICIES[0]]
                second = by_policy[prototype.RESULT_POLICIES[1]]
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

    rival_cases = [_rival_case(policy) for policy in prototype.RESULT_POLICIES]
    for case in rival_cases:
        if case["surviving_wrong_rivals"]:
            failures.append(
                {
                    "setting": case["setting"],
                    "error": "finite rivals survive: " + ", ".join(case["surviving_wrong_rivals"]),
                }
            )

    return {
        "schema": SCHEMA,
        "task_id": prototype.TASK_ID,
        "scope": (
            "Python structural/count/prefix/export/stress sweep and finite declared-rival "
            "self-review. Protected Racket evidence is reported separately."
        ),
        "seed_count": seed_count,
        "seed_range": [0, seed_count - 1],
        "settings": SETTINGS,
        "demo_counts": DEMO_COUNTS,
        "queries": 4,
        "episodes": episodes,
        "visible_pairs": visible_pairs,
        "matched_input_checks": matched_input_checks,
        "prefix_checks": prefix_checks,
        "public_turn_checks": public_turn_checks,
        "stress_30x30_checks": stress_checks,
        "finite_rival_certificates": finite_rival_certificates,
        "rival_cases": rival_cases,
        "failures": failures,
    }


class RacketRunner:
    """One protected bridge with exact-program/input caching."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.rule_cache: dict[str, str] = {}
        self.result_cache: dict[tuple[str, str], list[list[int]]] = {}
        self.requests = 0
        self.unique_evaluations = 0
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        prototype._grid(grid)
        self.requests += 1
        key = (hashlib.sha256(source.encode()).hexdigest(), _digest(grid))
        if key in self.result_cache:
            return self.result_cache[key]
        if source not in self.rule_cache:
            self.rule_cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        result = self.bridge.eval_text(f"({self.rule_cache[source]} {literal})")
        self.result_cache[key] = result
        self.unique_evaluations += 1
        return result

    def __exit__(self, *_exc):
        self.bridge.close()


def protected_audit() -> tuple[dict[str, Any], dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    seeds = (0, 17)
    demo_counts = (2, 3, 6)

    with RacketRunner() as execute:
        for seed in seeds:
            for demos in demo_counts:
                for settings in SETTINGS:
                    policy = settings["result_policy"]
                    context = {"seed": seed, "demos": demos, "setting": policy}
                    try:
                        episode = prototype.generate(seed, settings, demos=demos, queries=4)
                        mismatches = []
                        for index, pair in enumerate(episode["train"] + episode["test"]):
                            if execute(episode["program_solution"], pair["input"]) != pair["output"]:
                                mismatches.append(index)
                        native_survivors = []
                        for candidate in SETTINGS:
                            source = prototype.program(candidate)
                            if all(
                                execute(source, pair["input"]) == pair["output"]
                                for pair in episode["train"]
                            ):
                                native_survivors.append(candidate)
                        if mismatches:
                            raise AssertionError(f"Racket/Python label mismatches at {mismatches}")
                        if native_survivors != [settings]:
                            raise AssertionError(f"native demo survivors are {native_survivors}")
                        jobs.append(
                            {
                                **context,
                                "pairs": demos + 4,
                                "program_sha256": hashlib.sha256(
                                    episode["program_solution"].encode()
                                ).hexdigest(),
                                "native_survivors": native_survivors,
                                "input_sha256": [
                                    _digest(pair["input"])
                                    for pair in episode["train"] + episode["test"]
                                ],
                            }
                        )
                    except Exception as exc:
                        failures.append({**context, "error": f"{type(exc).__name__}: {exc}"})

        episode = prototype.generate(
            0, {"result_policy": "largest_component"}, demos=3, queries=4
        )
        pair = episode["test"][0]
        correct_source = prototype.program({"result_policy": "largest_component"})
        wrong_source = (HERE / "union_largest_counterfactual.rkt").read_text(encoding="utf-8")
        correct_intermediate = prototype.predict(pair["input"], "direct")
        wrong_intermediate = prototype._crop(prototype._stage_a(pair["input"], "union"))
        correct = execute(correct_source, pair["input"])
        wrong = execute(wrong_source, pair["input"])
        if correct != pair["output"]:
            failures.append({"witness": "correct", "error": "correct Racket output mismatches claim"})
        if wrong != prototype.predict(pair["input"], "union_largest"):
            failures.append({"witness": "wrong", "error": "counterfactual Racket output mismatches Python"})
        if correct == wrong:
            failures.append({"witness": "causal", "error": "wrong intermediate did not change output"})

        witness = {
            "schema": "c5a80b7a3acc-largest-component-causal-witness-v1",
            "task_id": prototype.TASK_ID,
            "setting": {"result_policy": "largest_component"},
            "seed": 0,
            "split": "query",
            "query_index": 0,
            "step_a": (
                "normalize the color-2 and color-3 source objects, then use marker 7 to "
                "choose intersection or marker absence to choose symmetric difference"
            ),
            "input_dependent_intermediate": {
                "name": "cropped Stage-A set-result grid",
                "correct": correct_intermediate,
                "wrong_union": wrong_intermediate,
                "correct_component_sizes": prototype.observe(pair["input"])[
                    "result_component_sizes"
                ],
            },
            "step_b": (
                "find four-connected components in the Stage-A result, select the unique "
                "largest (row-major top-left tie break), and crop/repaint it color 8"
            ),
            "why_b_depends_on_a": (
                "the candidate components and their sizes do not exist until Stage A creates "
                "the intermediate; replacing only Stage A by union changes Stage B's selected "
                "component and final output"
            ),
            "input": pair["input"],
            "correct_program": correct_source,
            "correct_program_sha256": hashlib.sha256(correct_source.encode()).hexdigest(),
            "wrong_intermediate_program": wrong_source,
            "wrong_intermediate_program_sha256": hashlib.sha256(wrong_source.encode()).hexdigest(),
            "correct_output": correct,
            "wrong_intermediate_output": wrong,
            "different_cells_with_shape_padding": _different_cells(correct, wrong),
            "input_sha256": _digest(pair["input"]),
            "correct_output_sha256": _digest(correct),
            "wrong_output_sha256": _digest(wrong),
            "protected_racket": True,
            "runtime_identity": execute.identity,
        }
        execution = {
            "schema": "c5a80b7a3acc-protected-racket-audit-v1",
            "task_id": prototype.TASK_ID,
            "seeds": list(seeds),
            "demo_counts": list(demo_counts),
            "queries": 4,
            "jobs": jobs,
            "job_count": len(jobs),
            "requests": execute.requests,
            "unique_evaluations": execute.unique_evaluations,
            "programs_compiled": len(execute.rule_cache),
            "runtime_identity": execute.identity,
            "failures": failures,
        }
    return execution, witness


def write_examples(root: Path) -> dict[str, Any]:
    from reviewer_support import public_challenge_id

    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    public_dir = root / "public"
    private_dir = root / "private"
    public_dir.mkdir(parents=True)
    private_dir.mkdir(parents=True)
    public_ids: list[str] = []
    private_files: list[str] = []

    for settings in SETTINGS:
        policy = settings["result_policy"]
        episode = prototype.generate(17, settings, demos=3, queries=4)
        certificate = prototype.teaching_certificate(
            episode["train"], [pair["input"] for pair in episode["test"]]
        )
        private = {
            "task_id": prototype.TASK_ID,
            "seed": 17,
            "settings": settings,
            "episode": episode,
            "teaching_certificate": certificate,
            "public_query_ids": [],
        }
        for query_index in range(4):
            visible = {"train": episode["train"], "test": [episode["test"][query_index]]}
            public_id = public_challenge_id(visible)
            (public_dir / f"{public_id}.json").write_bytes(_public_bytes(episode, query_index))
            public_ids.append(public_id)
            private["public_query_ids"].append(public_id)
        private_path = private_dir / f"{policy}.json"
        private_path.write_text(json.dumps(private, sort_keys=True, indent=2) + "\n")
        private_files.append(str(private_path))

    return {
        "schema": "c5a80b7a3acc-example-export-v1",
        "settings": SETTINGS,
        "demos": 3,
        "queries_per_setting": 4,
        "public_files": len(public_ids),
        "public_ids": sorted(public_ids),
        "private_files": private_files,
        "root": str(root),
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--witness-out", type=Path, required=True)
    parser.add_argument("--examples-out", type=Path, required=True)
    args = parser.parse_args()

    structural = structural_stress(args.seeds)
    protected, witness = protected_audit()
    examples = write_examples(args.examples_out)
    report = {
        "schema": SCHEMA,
        "task_id": prototype.TASK_ID,
        "structural": structural,
        "protected_racket": protected,
        "examples": examples,
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(HERE.glob("*"))
            if path.is_file() and path.suffix in {".py", ".rkt", ".json"}
        },
    }
    _write_json(args.out, report)
    _write_json(args.witness_out, witness)
    failures = len(structural["failures"]) + len(protected["failures"])
    print(
        json.dumps(
            {
                "status": "pass" if failures == 0 else "fail",
                "episodes": structural["episodes"],
                "visible_pairs": structural["visible_pairs"],
                "finite_rival_certificates": structural["finite_rival_certificates"],
                "protected_jobs": protected["job_count"],
                "racket_unique_evaluations": protected["unique_evaluations"],
                "witness_different_cells": witness["different_cells_with_shape_padding"],
                "public_files": examples["public_files"],
                "failures": failures,
                "out": str(args.out),
                "witness_out": str(args.witness_out),
                "examples_out": str(args.examples_out),
            },
            sort_keys=True,
        )
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
