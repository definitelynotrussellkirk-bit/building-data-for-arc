#!/usr/bin/env python3
"""Bounded protected-Racket teaching audit for assignment_basis episodes."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "9b6d928388be"
HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"assignment_basis": "holes"},
    {"assignment_basis": "area_rank"},
)
SEEDS = (0, 17, 29)
DEMO_COUNTS = (2, 6)


def _load(name: str, filename: str):
    path = HERE / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _grid(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _diff(left: list[list[int]], right: list[list[int]]) -> int:
    return sum(
        a != b
        for row_a, row_b in zip(left, right, strict=True)
        for a, b in zip(row_a, row_b, strict=True)
    )


def _raw(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    args.out.mkdir(parents=True)

    adapter = _load("_audit_9b_adapter", "adapter.py")
    prototype = _load("_audit_9b_prototype", "prototype.py")
    named = adapter.rival_programs()
    jobs: list[dict[str, Any]] = []
    evaluations = 0
    harmful: list[dict[str, Any]] = []

    with RacketBridge() as bridge:
        identity = dict(bridge.runtime_identity)
        if identity.get("protected") is not True:
            raise RuntimeError(f"protected Racket required, got {identity}")

        def apply(source: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            evaluations += 1
            return bridge.eval_text(f"({wrap_rule(source)} {_grid(grid)})")

        for settings in SETTINGS:
            basis = settings["assignment_basis"]
            alternate = SETTINGS[1] if basis == "holes" else SETTINGS[0]
            candidates = {
                "alternate_setting": adapter.program(alternate),
                **named,
            }
            for seed in SEEDS:
                for demos in DEMO_COUNTS:
                    episode = adapter.generate(seed, settings, demos=demos, queries=4)
                    chosen = adapter.program(settings)
                    for split in ("train", "test"):
                        for pair in episode[split]:
                            if apply(chosen, pair["input"]) != pair["output"]:
                                raise AssertionError(
                                    f"chosen label mismatch: {settings=} {seed=} {demos=} {split=}"
                                )
                    rival_rows = []
                    for name, source in candidates.items():
                        demo_outputs = [apply(source, p["input"]) for p in episode["train"]]
                        survives = all(
                            got == pair["output"]
                            for got, pair in zip(demo_outputs, episode["train"], strict=True)
                        )
                        disagreements = []
                        if survives:
                            query_outputs = [apply(source, p["input"]) for p in episode["test"]]
                            disagreements = [
                                index for index, (got, pair) in enumerate(
                                    zip(query_outputs, episode["test"], strict=True)
                                ) if got != pair["output"]
                            ]
                        row = {
                            "name": name,
                            "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
                            "survives_demos": survives,
                            "query_disagreements": disagreements,
                        }
                        rival_rows.append(row)
                        if survives and disagreements:
                            harmful.append({
                                "settings": settings,
                                "seed": seed,
                                "demos": demos,
                                **row,
                            })
                    jobs.append({
                        "settings": settings,
                        "seed": seed,
                        "demos": demos,
                        "queries": 4,
                        "pairs": demos + 4,
                        "chosen_sha256": hashlib.sha256(chosen.encode()).hexdigest(),
                        "rivals": rival_rows,
                    })

        if harmful:
            raise AssertionError(f"query-only survivors remain: {harmful}")

        matched = []
        prefix = []
        for seed in SEEDS:
            episodes = [adapter.generate(seed, s, 2, 4) for s in SETTINGS]
            left = [p["input"] for p in episodes[0]["train"] + episodes[0]["test"]]
            right = [p["input"] for p in episodes[1]["train"] + episodes[1]["test"]]
            if left != right:
                raise AssertionError(f"settings are not input matched for seed {seed}")
            matched.append({"seed": seed, "pairs": len(left)})
            for settings in SETTINGS:
                short = adapter.generate(seed, settings, 2, 1)
                long = adapter.generate(seed, settings, 6, 4)
                same_queries = adapter.generate(seed, settings, 2, 4)
                if short["train"] != long["train"][:2]:
                    raise AssertionError("demo stream is not prefix stable")
                if short["test"] != long["test"][:1] or same_queries["test"] != long["test"]:
                    raise AssertionError("query stream depends on requested demo count")
                prefix.append({"settings": settings, "seed": seed, "status": "pass"})

        witness_episode = adapter.generate(17, SETTINGS[1], 2, 4)
        witness_pair = witness_episode["test"][0]
        correct_source = adapter.program(SETTINGS[1])
        wrong_source = adapter.counterfactual_program(SETTINGS[1], "wrong_intermediate")
        correct = apply(correct_source, witness_pair["input"])
        wrong = apply(wrong_source, witness_pair["input"])
        changed = _diff(correct, wrong)
        if correct != witness_pair["output"] or changed == 0:
            raise AssertionError("wrong-intermediate witness is not causal")
        witness = {
            "schema": "arcpuzzles-9b6d928388be-audited-case-v1",
            "task_id": TASK_ID,
            "settings": SETTINGS[1],
            "input": witness_pair["input"],
            "program": correct_source,
            "output": correct,
            "counterfactual_program": wrong_source,
            "counterfactual_output": wrong,
            "intermediate_value": prototype.assignment_intermediate(
                witness_pair["input"], "area_rank"
            ),
            "ablation": "wrong_intermediate",
            "changed_final_cells": changed,
        }

    stress = adapter.generate(0, SETTINGS[1], 2, 4)["test"][0]
    stress_input = stress["input"]
    stress_report = {
        "shape": [len(stress_input), len(stress_input[0])],
        "nonzero_input_cells": sum(v != 0 for row in stress_input for v in row),
        "changed_cells": _diff(stress_input, stress["output"]),
    }
    if stress_report["shape"] != [30, 30] or stress_report["nonzero_input_cells"] < 100:
        raise AssertionError(f"insubstantial stress case: {stress_report}")

    report = {
        "schema": "arcpuzzles-9b6d928388be-bounded-self-audit-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "backend": identity,
        "jobs": len(jobs),
        "job_details": jobs,
        "racket_evaluations": evaluations,
        "harmful_demo_survivors": harmful,
        "matched_input_checks": matched,
        "prefix_checks": prefix,
        "named_rivals": sorted(named),
        "claim_scope": "Only the finite executable rivals listed in this report.",
        "stress": stress_report,
        "audited_case": "audited-case.json",
    }
    (args.out / "self-audit-report.json").write_text(_raw(report), encoding="utf-8")
    (args.out / "audited-case.json").write_text(_raw(witness), encoding="utf-8")
    print(json.dumps({
        "status": "passed",
        "jobs": len(jobs),
        "racket_evaluations": evaluations,
        "harmful_demo_survivors": 0,
        "changed_final_cells": witness["changed_final_cells"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
