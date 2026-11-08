#!/usr/bin/env python3
"""Build compact bounded teaching and protected-Racket evidence for this family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ADAPTER_PATH = HERE / "adapter.py"


def _adapter():
    spec = importlib.util.spec_from_file_location("_audit_1cbcf1ed9a32_adapter", ADAPTER_PATH)
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load task-local adapter")
    spec.loader.exec_module(module)
    return module


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def build_report():
    adapter = _adapter()
    failures = []
    teaching_jobs = 0
    generated_pairs = 0
    large_cases = 0
    minimum_survivors = {}
    for seed in range(32):
        for setting in adapter.OUTPUT_MODES:
            for demos in range(2, 7):
                episode = adapter.generate(seed, {"output_mode": setting}, demos, 4)
                certificate = adapter.certificate(
                    episode["train"], [pair["input"] for pair in episode["test"]]
                )
                teaching_jobs += 1
                generated_pairs += demos + 4
                large_cases += sum(
                    len(pair["input"]) == len(pair["input"][0]) == 30
                    for pair in episode["test"]
                )
                if certificate["survivors"] != [setting]:
                    failures.append(
                        {
                            "seed": seed,
                            "setting": setting,
                            "demos": demos,
                            "survivors": certificate["survivors"],
                        }
                    )
                if demos == 2 and seed in (0, 17):
                    minimum_survivors[f"{setting}:seed={seed}"] = certificate["survivors"]

    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    wrapped = {}
    racket_evaluations = 0
    with RacketBridge() as bridge:
        identity = dict(bridge.runtime_identity)

        def execute(program, grid):
            nonlocal racket_evaluations
            if program not in wrapped:
                wrapped[program] = wrap_rule(program)
            racket_evaluations += 1
            return bridge.eval_text(f"({wrapped[program]} {_literal(grid)})")

        replay_jobs = []
        for seed in (0, 17):
            for setting in adapter.OUTPUT_MODES:
                episode = adapter.generate(seed, {"output_mode": setting}, 3, 4)
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = execute(episode["program_solution"], pair["input"])
                        if actual != pair["output"]:
                            failures.append(
                                {
                                    "kind": "racket_label_mismatch",
                                    "seed": seed,
                                    "setting": setting,
                                    "split": split,
                                    "index": index,
                                }
                            )
                replay_jobs.append(
                    {
                        "seed": seed,
                        "setting": setting,
                        "demos": 3,
                        "queries": 4,
                        "program_sha256": hashlib.sha256(
                            episode["program_solution"].encode("utf-8")
                        ).hexdigest(),
                    }
                )

        causal = adapter.causal_case()
        actual = execute(causal["program"], causal["input"])
        counterfactual = execute(causal["counterfactual_program"], causal["input"])
        if actual != causal["output"] or counterfactual != causal["counterfactual_output"]:
            failures.append({"kind": "causal_replay_mismatch"})
        if actual == counterfactual:
            failures.append({"kind": "causal_counterfactual_unchanged"})

    report = {
        "schema": "arcpuzzles-1cbcf1ed9a32-parametric-audit-v1",
        "task_id": adapter.prototype.TASK_ID,
        "status": "passed" if not failures else "failed",
        "settings": list(adapter.OUTPUT_MODES),
        "demo_counts": [2, 3, 4, 5, 6],
        "queries": 4,
        "seed_range": [0, 31],
        "teaching_jobs": teaching_jobs,
        "generated_pairs": generated_pairs,
        "exact_30x30_query_cases": large_cases,
        "finite_hypotheses": list(adapter.HYPOTHESES),
        "minimum_lesson_survivors": minimum_survivors,
        "protected_racket": {
            "backend": identity.get("backend"),
            "protected": identity.get("protected"),
            "binary_sha256": identity.get("binary_sha256"),
            "prelude_sha256": identity.get("prelude_sha256"),
            "bridge_sha256": identity.get("bridge_sha256"),
            "evaluations": racket_evaluations,
            "jobs": replay_jobs,
        },
        "causal_probe": {
            "ablation": causal["ablation"],
            "selector": causal["selector"],
            "intermediate": causal["intermediate"],
            "wrong_intermediate": causal["wrong_intermediate"],
            "input_sha256": hashlib.sha256(
                json.dumps(causal["input"], separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
            "output": causal["output"],
            "counterfactual_output": causal["counterfactual_output"],
        },
        "failures": failures,
        "limits": (
            "Finite audit of two declared programs and eight named Python rivals over "
            "32 seeds and demo counts 2..6; it is not a universal uniqueness or learning claim."
        ),
    }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    report = build_report()
    raw = json.dumps(report, sort_keys=True, indent=2) + "\n"
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(raw, encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "teaching_jobs": report["teaching_jobs"],
        "racket_evaluations": report["protected_racket"]["evaluations"],
        "output": str(destination),
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
