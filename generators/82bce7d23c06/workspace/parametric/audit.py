#!/usr/bin/env python3
"""Bounded protected-Racket self-audit for 82bce7d23c06."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def _load_family():
    path = Path(__file__).resolve().with_name("prototype.py")
    name = "_audit_82b_" + hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load adjacent prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def build_report(*, seeds=(0, 17, 97), demos=(2, 3, 6), include_racket=True):
    family = _load_family()
    settings = [dict(row) for row in family.SETTINGS]
    failures = []
    jobs = []
    racket_evaluations = 0
    causal_case = None
    bridge = None
    wrap_rule = None
    if include_racket:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule as wrapper

        bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
        wrap_rule = wrapper
    try:
        for seed in seeds:
            for demo_count in demos:
                baseline_inputs = None
                for setting in settings:
                    episode = family.generate(seed, setting, demo_count, 4)
                    inputs = [
                        pair["input"]
                        for split in ("train", "test")
                        for pair in episode[split]
                    ]
                    if baseline_inputs is None:
                        baseline_inputs = inputs
                    elif inputs != baseline_inputs:
                        failures.append({
                            "seed": seed,
                            "demos": demo_count,
                            "settings": setting,
                            "finding": "inputs differ across settings",
                        })
                    certificate = family.lesson_certificate(episode["train"], setting)
                    if certificate["surviving_settings"] != [setting]:
                        failures.append({
                            "seed": seed,
                            "demos": demo_count,
                            "settings": setting,
                            "finding": "selected setting is not uniquely identified",
                            "certificate": certificate,
                        })
                    if certificate["surviving_shortcuts"]:
                        failures.append({
                            "seed": seed,
                            "demos": demo_count,
                            "settings": setting,
                            "finding": "declared shortcut survives visible demonstrations",
                            "certificate": certificate,
                        })
                    if (len(episode["train"]), len(episode["test"])) != (demo_count, 4):
                        failures.append({
                            "seed": seed,
                            "demos": demo_count,
                            "settings": setting,
                            "finding": "episode count mismatch",
                        })
                    stress = family.analyze(episode["test"][-1]["input"])
                    if (
                        stress["input_shape"] != [1, 6]
                        or stress["output_shape"] != [30, 30]
                        or stress["nonzero_count"] != 5
                        or stress["projected_component_count"] != 3
                        or stress["source_color_run_count"] != 4
                        or stress["projected_nonzero_count"] <= 100
                        or stress["boundary_sides"] != ["bottom", "left", "right", "top"]
                    ):
                        failures.append({
                            "seed": seed,
                            "demos": demo_count,
                            "settings": setting,
                            "finding": "30x30 stress is not substantive/boundary-spanning",
                            "analysis": stress,
                        })
                    if bridge is not None and wrap_rule is not None:
                        wrapped = wrap_rule(episode["program_solution"])
                        for split in ("train", "test"):
                            for pair_index, pair in enumerate(episode[split]):
                                actual = bridge.eval_text(
                                    f"({wrapped} {_literal(pair['input'])})"
                                )
                                racket_evaluations += 1
                                if actual != pair["output"]:
                                    failures.append({
                                        "seed": seed,
                                        "demos": demo_count,
                                        "settings": setting,
                                        "split": split,
                                        "pair_index": pair_index,
                                        "finding": "protected Racket label mismatch",
                                    })
                        if setting["finish"] == "component_count_relay":
                            pair = episode["train"][0]
                            wrong = bridge.eval_text(
                                f"({wrap_rule(family.counterfactual_program())} "
                                f"{_literal(pair['input'])})"
                            )
                            racket_evaluations += 1
                            expected_wrong = family.counterfactual_transform(pair["input"])
                            if wrong != expected_wrong or wrong == pair["output"]:
                                failures.append({
                                    "seed": seed,
                                    "demos": demo_count,
                                    "settings": setting,
                                    "finding": "counterfactual failed to match/change output",
                                })
                            if causal_case is None:
                                causal_case = {
                                    "settings": setting,
                                    "program": episode["program_solution"],
                                    "input": pair["input"],
                                    "output": pair["output"],
                                    "counterfactual_program": family.counterfactual_program(),
                                    "counterfactual_output": wrong,
                                    "intermediate_value": family.intermediate(pair["input"]),
                                    "ablation": "wrong_intermediate",
                                }
                    jobs.append({
                        "seed": seed,
                        "demos": demo_count,
                        "queries": 4,
                        "settings": setting,
                        "certificate": certificate,
                        "stress": stress,
                    })
    finally:
        if bridge is not None:
            bridge.close()
    return {
        "schema": "arcpuzzles-parametric-bounded-self-audit-v1",
        "task_id": family.TASK_ID,
        "status": "passed" if not failures else "failed",
        "jobs": jobs,
        "failures": failures,
        "causal_case": causal_case,
        "summary": {
            "jobs": len(jobs),
            "seeds": list(seeds),
            "demo_counts": list(demos),
            "settings": settings,
            "declared_shortcuts": list(family.SHORTCUTS),
            "racket_evaluations": racket_evaluations,
            "query_outputs_used_for_teaching_check": False,
            "all_inputs_setting_neutral": not any(
                row.get("finding") == "inputs differ across settings" for row in failures
            ),
            "all_declared_shortcuts_rejected": not any(
                row.get("finding") == "declared shortcut survives visible demonstrations"
                for row in failures
            ),
        },
        "racket": (
            {"backend": "racket", "protected": True}
            if include_racket
            else {"backend": "not_run", "protected": False}
        ),
        "limits": (
            "Finite seeds, demo counts, settings and named shortcuts only; this does not "
            "prove universal identifiability, owner acceptance or training admission."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(f"choose a new output path: {args.out}")
    report = build_report(include_racket=not args.no_racket)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["summary"]}, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
