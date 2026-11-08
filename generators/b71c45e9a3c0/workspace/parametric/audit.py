#!/usr/bin/env python3
"""Bounded authoring audit for the b71c45e9a3c0 largest-key size relay family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def _load_family():
    path = Path(__file__).resolve().with_name("prototype.py")
    name = "_audit_b71c45e9a3c0_" + hashlib.sha256(path.read_bytes()).hexdigest()
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
    settings = [{"scope": value} for value in family.SCOPES]
    jobs = []
    failures = []
    racket_evaluations = 0
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
                            "setting": setting,
                            "finding": "inputs differ across settings",
                        })
                    certificate = family.lesson_certificate(episode["train"], setting)
                    analyses = [family.analyze(grid) for grid in inputs]
                    if any(row["errors"] for row in analyses):
                        failures.append({
                            "seed": seed,
                            "demos": demo_count,
                            "setting": setting,
                            "finding": "invalid generated input",
                            "errors": [row["errors"] for row in analyses],
                        })
                    if certificate["surviving_settings"] != [setting]:
                        failures.append({
                            "seed": seed,
                            "demos": demo_count,
                            "setting": setting,
                            "finding": "selected setting not uniquely identified",
                            "certificate": certificate,
                        })
                    if certificate["surviving_shortcuts"]:
                        failures.append({
                            "seed": seed,
                            "demos": demo_count,
                            "setting": setting,
                            "finding": "declared shortcut survives demos",
                            "certificate": certificate,
                        })
                    if (len(episode["train"]), len(episode["test"])) != (demo_count, 4):
                        failures.append({
                            "seed": seed,
                            "demos": demo_count,
                            "setting": setting,
                            "finding": "count mismatch",
                        })
                    stress = analyses[-1]
                    if (
                        stress["nonzero_count"] < 45
                        or stress["boundary_sides"] != ["bottom", "left", "right", "top"]
                        or len(stress["component_sizes"]) != 6
                    ):
                        failures.append({
                            "seed": seed,
                            "demos": demo_count,
                            "setting": setting,
                            "finding": "30x30 stress is not substantive/boundary-spanning",
                            "analysis": stress,
                        })
                    if bridge is not None and wrap_rule is not None:
                        wrapped = wrap_rule(episode["program_solution"])
                        for split in ("train", "test"):
                            for pair in episode[split]:
                                actual = bridge.eval_text(
                                    f"({wrapped} {_literal(pair['input'])})"
                                )
                                racket_evaluations += 1
                                if actual != pair["output"]:
                                    failures.append({
                                        "seed": seed,
                                        "demos": demo_count,
                                        "setting": setting,
                                        "finding": "Racket label mismatch",
                                    })
                        if setting["scope"] == "largest_key_size":
                            pair = episode["train"][0]
                            wrong = bridge.eval_text(
                                f"({wrap_rule(family.counterfactual_program())} "
                                f"{_literal(pair['input'])})"
                            )
                            racket_evaluations += 1
                            if (
                                wrong == pair["output"]
                                or wrong != family.counterfactual_transform(pair["input"])
                            ):
                                failures.append({
                                    "seed": seed,
                                    "demos": demo_count,
                                    "setting": setting,
                                    "finding": "counterfactual did not change/match",
                                })
                    jobs.append({
                        "seed": seed,
                        "demos": demo_count,
                        "queries": 4,
                        "settings": setting,
                        "surviving_settings": certificate["surviving_settings"],
                        "surviving_shortcuts": certificate["surviving_shortcuts"],
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
        "summary": {
            "jobs": len(jobs),
            "seeds": list(seeds),
            "demo_counts": list(demos),
            "settings": settings,
            "declared_shortcuts": sorted(family.SHORTCUTS),
            "racket_evaluations": racket_evaluations,
            "query_outputs_used_for_teaching_check": False,
            "all_inputs_setting_neutral": not any(
                row.get("finding") == "inputs differ across settings" for row in failures
            ),
            "all_declared_shortcuts_rejected": not any(
                row.get("finding") == "declared shortcut survives demos" for row in failures
            ),
        },
        "racket": (
            {"backend": "racket", "protected": True}
            if include_racket
            else {"backend": "not_run", "protected": False}
        ),
        "limits": (
            "Finite seeds/demo counts and named rivals only; this does not prove universal "
            "identifiability, owner acceptance, or training admission."
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
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": report["status"], **report["summary"]}, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
