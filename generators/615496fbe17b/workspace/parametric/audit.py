#!/usr/bin/env python3
"""Bounded adversarial audit for a native parametric adapter.

This task-local tool is intentionally reusable: it checks deterministic matched
inputs, prefix stability, independent count bounds, declared teaching rivals,
large-grid coverage, Python labels, and a bounded protected-Racket replay.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from reviewer_support import find_root

TASK = "615496fbe17b"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"


def load_adapter():
    path = HOME / "adapter.py"
    name = f"audit_{TASK}_{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 256:
        raise SystemExit("--seeds must be in [1, 256]")

    adapter = load_adapter()
    settings = [dict(item) for item in adapter.SETTINGS]
    failures: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    episodes = pairs = stress_30 = 0

    for seed in range(args.seeds):
        baselines = {
            key(setting): adapter.generate(seed, setting, 6, 4)
            for setting in settings
        }
        first_inputs = [
            pair["input"]
            for pair in baselines[key(settings[0])]["train"] + baselines[key(settings[0])]["test"]
        ]
        for setting in settings[1:]:
            other_inputs = [
                pair["input"]
                for pair in baselines[key(setting)]["train"] + baselines[key(setting)]["test"]
            ]
            if other_inputs != first_inputs:
                failures.append({"seed": seed, "kind": "settings_changed_inputs", "settings": setting})
        for setting in settings:
            baseline = baselines[key(setting)]
            if baseline != adapter.generate(seed, setting, 6, 4):
                failures.append({"seed": seed, "kind": "nondeterministic", "settings": setting})
            for demos in (2, 3, 6):
                for queries in (1, 4):
                    episode = adapter.generate(seed, setting, demos, queries)
                    episodes += 1
                    pairs += demos + queries
                    if episode["train"] != baseline["train"][:demos] or episode["test"] != baseline["test"][:queries]:
                        failures.append({
                            "seed": seed,
                            "kind": "prefix_instability",
                            "settings": setting,
                            "demos": demos,
                            "queries": queries,
                        })
                    holes = adapter.audit_episode(episode, setting["hole_behavior"])
                    if holes:
                        failures.append({
                            "seed": seed,
                            "kind": "teaching_rival_survived",
                            "settings": setting,
                            "demos": demos,
                            "details": holes,
                        })
                    for pair in episode["train"] + episode["test"]:
                        unique_inputs.add(key(pair["input"]))
                        if adapter.solve(pair["input"], setting) != pair["output"]:
                            failures.append({"seed": seed, "kind": "python_label_mismatch", "settings": setting})
                        if len(pair["input"]) == 30 and len(pair["input"][0]) == 30:
                            stress_30 += 1
            left = baselines[key(settings[0])]
            right = baselines[key(settings[1])]
            if not any(a["output"] != b["output"] for a, b in zip(left["train"], right["train"])):
                failures.append({"seed": seed, "kind": "settings_not_taught"})

    protected_evaluations = 0
    protected_identity = None
    from arcpuzzles.parametric_worker import _real_evaluator

    evaluate, protected_identity, bridge = _real_evaluator(ROOT / "shared" / "runtime")
    try:
        replay_seeds = sorted({0, min(17, args.seeds - 1)})
        for seed in replay_seeds:
            inputs = adapter.generate(seed, settings[0], 2, 4)
            grids = [pair["input"] for pair in inputs["train"] + inputs["test"]]
            for setting in settings:
                text = adapter.program(setting)
                for grid in grids:
                    protected_evaluations += 1
                    actual = evaluate(text, grid)
                    expected = adapter.solve(grid, setting)
                    if actual != expected:
                        failures.append({
                            "seed": seed,
                            "kind": "protected_racket_mismatch",
                            "settings": setting,
                            "input_sha256": hashlib.sha256(key(grid).encode()).hexdigest(),
                        })
    finally:
        bridge.close()

    report = {
        "schema": "arcpuzzles-parametric-bounded-audit-v1",
        "task_id": TASK,
        "seed_count": args.seeds,
        "settings": settings,
        "demo_counts": [2, 3, 6],
        "query_counts": [1, 4],
        "episodes": episodes,
        "pairs_checked": pairs,
        "unique_input_count": len(unique_inputs),
        "stress_30_pair_occurrences": stress_30,
        "protected_racket_evaluations": protected_evaluations,
        "racket": protected_identity,
        "failure_count": len(failures),
        "failures": failures,
        "status": "passed" if not failures else "failed",
        "finite_scope_note": "No finding in this bounded rival set is not a proof of universal rule uniqueness.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "task_id", "status", "episodes", "pairs_checked", "unique_input_count",
        "stress_30_pair_occurrences", "protected_racket_evaluations", "failure_count"
    )}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
