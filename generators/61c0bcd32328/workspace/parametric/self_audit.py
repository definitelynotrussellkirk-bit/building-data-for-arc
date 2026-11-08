#!/usr/bin/env python3
"""Reusable bounded audit for the native corner-direction family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "61c0bcd32328"

for candidate in (ROOT / "shared" / "runtime", ROOT / "src"):
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def _load_native():
    path = HERE / "native.py"
    name = "_audit_native_61c0bcd32328_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load native implementation at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _changed(pair: dict[str, Any]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(pair["input"])
        for col, value in enumerate(values)
        if pair["output"][row][col] != value
    ]


def python_audit(stress_seeds: int = 64) -> dict[str, Any]:
    if type(stress_seeds) is not int or stress_seeds <= 0:
        raise ValueError("stress_seeds must be an exact positive integer")
    native = _load_native()
    episodes = 0
    matched_input_checks = 0
    prefix_checks = 0
    finite_rival_fits = 0
    thirty_by_thirty_pairs = 0
    public_projection_checks = 0
    max_foreground = 0
    min_changed_30 = None

    for seed in range(stress_seeds):
        for demos in (2, 6):
            by_query: dict[int, dict[str, dict[str, Any]]] = {}
            for queries in (1, 4):
                by_query[queries] = {}
                for direction in native.DIRECTIONS:
                    setting = {"direction": direction}
                    episode = native.generate(seed, setting, demos, queries)
                    by_query[queries][direction] = episode
                    episodes += 1
                    certificate = native.teaching_certificate(episode)
                    assert certificate["setting_survivors"] == [direction]
                    finite_rival_fits += len(certificate["plausible_rival_survivors"])
                    visible = native.public_turn(episode, 0)
                    assert set(visible) == {"train", "test"}
                    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
                    public_projection_checks += 1

                assert _inputs(by_query[queries]["clockwise"]) == _inputs(
                    by_query[queries]["counterclockwise"]
                )
                matched_input_checks += 1

            for direction in native.DIRECTIONS:
                one = by_query[1][direction]
                full = by_query[4][direction]
                assert one["train"] == full["train"]
                assert one["test"] == full["test"][:1]
                prefix_checks += 1

                two_demos = native.generate(seed, {"direction": direction}, 2, 4)
                assert two_demos["train"] == full["train"][:2]
                assert two_demos["test"] == full["test"]
                prefix_checks += 1

                stress = full["test"][3]
                assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
                info = native.analyze(stress["input"])
                changed = _changed(stress)
                assert info["foreground_count"] >= 80
                assert len(changed) >= 12
                assert max(row for row, _ in changed) - min(row for row, _ in changed) >= 24
                assert max(col for _, col in changed) - min(col for _, col in changed) >= 24
                max_foreground = max(max_foreground, info["foreground_count"])
                min_changed_30 = len(changed) if min_changed_30 is None else min(min_changed_30, len(changed))
                thirty_by_thirty_pairs += 1

    if finite_rival_fits:
        raise AssertionError(f"finite rivals survived {finite_rival_fits} episode certificates")
    return {
        "status": "passed",
        "stress_seeds": stress_seeds,
        "episodes": episodes,
        "matched_input_checks": matched_input_checks,
        "prefix_checks": prefix_checks,
        "finite_rival_fits": finite_rival_fits,
        "public_projection_checks": public_projection_checks,
        "thirty_by_thirty_pairs": thirty_by_thirty_pairs,
        "max_foreground_30": max_foreground,
        "min_changed_cells_30": min_changed_30,
    }


def _execute_racket(bridge, wrap_rule, program: str, grid: list[list[int]]) -> list[list[int]]:
    callable_rule = wrap_rule(program)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    value = bridge.eval_text(f"({callable_rule} {literal})")
    if type(value) is not list or not value or any(type(row) is not list for row in value):
        raise ValueError("Racket result is not a grid")
    return [[int(cell) for cell in row] for row in value]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def full_audit(out: Path, *, stress_seeds: int = 64) -> dict[str, Any]:
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    started = time.monotonic()
    native = _load_native()
    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))

    from arcpuzzles.parametric_worker import evaluate_contract
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    from reviewer_support import public_challenge_bytes, public_challenge_id

    jobs = [
        {"seed": seed, "settings": {"direction": direction}, "demos": demos, "queries": 4}
        for seed in (0, 17)
        for demos in (2, 3, 6)
        for direction in native.DIRECTIONS
    ]
    evaluated = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    if evaluated.get("racket", {}).get("backend") != "racket" or evaluated["racket"].get("protected") is not True:
        raise AssertionError("protected Racket evaluation is required")

    python_report = python_audit(stress_seeds)
    witness = native.dependency_witness()
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        correct = _execute_racket(bridge, wrap_rule, witness["program"], witness["input"])
        counterfactual = _execute_racket(
            bridge, wrap_rule, witness["counterfactual_program"], witness["input"]
        )
    if correct != witness["correct_output"]:
        raise AssertionError("protected canonical output differs from Python claim")
    if counterfactual != witness["counterfactual_output"]:
        raise AssertionError("protected counterfactual output differs from Python claim")
    if correct == counterfactual:
        raise AssertionError("wrong intermediate did not change final output")

    out.mkdir(parents=True)
    public_dir = out / "public"
    public_dir.mkdir()
    public_rows = []
    for direction in native.DIRECTIONS:
        episode = native.generate(17, {"direction": direction}, 3, 4)
        visible = native.public_turn(episode, 0)
        identifier = public_challenge_id(visible)
        path = public_dir / f"challenge-{identifier}.json"
        path.write_bytes(public_challenge_bytes(visible))
        public_rows.append({"direction": direction, "public_id": identifier, "path": path.name})

    audited_case = {
        "settings": witness["settings"],
        "program": witness["program"],
        "input": witness["input"],
        "output": correct,
        "counterfactual_program": witness["counterfactual_program"],
        "counterfactual_output": counterfactual,
        "intermediate_value": witness["intermediate_value"],
        "wrong_intermediate_value": witness["wrong_intermediate_value"],
        "ablation": witness["ablation"],
    }
    (out / "audited-case.json").write_text(
        json.dumps(audited_case, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    dependency = {
        "status": "passed",
        "step_a": witness["step_a"],
        "intermediate": witness["intermediate"],
        "step_b": witness["step_b"],
        "why_b_depends_on_a": witness["why_b_depends_on_a"],
        "ablation": witness["ablation"],
        "changed_cells": len(_changed({"input": correct, "output": counterfactual})),
        "racket": {
            key: identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        },
        "program_sha256": hashlib.sha256(witness["program"].encode()).hexdigest(),
        "counterfactual_program_sha256": hashlib.sha256(
            witness["counterfactual_program"].encode()
        ).hexdigest(),
    }
    (out / "dependency-replay.json").write_text(
        json.dumps(dependency, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    sources = [
        HERE / "adapter.py",
        HERE / "native.py",
        HERE / "canonical.rkt",
        HERE / "counterclockwise.rkt",
        HERE / "promotion.json",
        HERE / "self_audit.py",
        HERE.parents[1] / "generator.py",
        HERE.parents[1] / "tests" / "test_parametric_native.py",
    ]
    report = {
        "schema": "61c0bcd32328-native-self-audit-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "training_admitted": False,
        "qualification_or_acceptance_performed": False,
        "jobs": jobs,
        "native_checks": evaluated["checks"],
        "protected_racket": evaluated["racket"],
        "racket_evaluations": evaluated["racket_evaluations"] + 2,
        "verified_pair_labels": sum(job["demos"] + job["queries"] for job in jobs),
        "python_stress": python_report,
        "finite_rivals": list(native.PLAUSIBLE_RIVALS),
        "dependency": dependency,
        "public_exports": public_rows,
        "source_sha256": {path.relative_to(ROOT).as_posix(): _sha(path) for path in sources},
        "limits": [
            "Protected Racket scope is the declared 12 jobs over seeds 0/17 and demo counts 2/3/6, not a universal seed proof.",
            "Learnability covers the two declared settings and eight executable plausible rivals only.",
            "Reviewer qualification evidence is not owner acceptance or training admission.",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    (out / "self-audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "jobs": len(jobs),
                "racket_evaluations": report["racket_evaluations"],
                "stress_episodes": python_report["episodes"],
                "elapsed_seconds": report["elapsed_seconds"],
            },
            sort_keys=True,
        )
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--stress-seeds", type=int, default=64)
    args = parser.parse_args()
    full_audit(args.out, stress_seeds=args.stress_seeds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
