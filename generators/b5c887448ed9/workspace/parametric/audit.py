#!/usr/bin/env python3
"""Bounded protected-Racket self-review for the b5c887448ed9 family."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
HOME = ROOT / "generators/b5c887448ed9/workspace/parametric"
SETTINGS = (
    {"overwrite_policy": "reading_order"},
    {"overwrite_policy": "longest_path_last"},
)


def load_adapter():
    path = HOME / "adapter.py"
    spec = importlib.util.spec_from_file_location("audit_b5c887448ed9_adapter", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    public_dir = args.out / "public"
    public_dir.mkdir(exist_ok=True)
    adapter = load_adapter()
    programs = {row["overwrite_policy"]: adapter.program(row) for row in SETTINGS}
    bridge = RacketBridge(max_calls_before_restart=96)
    cache = {}
    jobs = []
    failures = []
    public_rows = []
    causal = None

    def execute(policy, grid, program=None):
        text = program if program is not None else programs[policy]
        key = (hashlib.sha256(text.encode()).hexdigest(), json.dumps(grid, separators=(",", ":")))
        if key not in cache:
            cache[key] = bridge.eval_text(f"({wrap_rule(text)} {literal(grid)})")
        return cache[key]

    try:
        for seed in (0, 17):
            for demos in (2, 3, 6):
                sequences = []
                for setting in SETTINGS:
                    policy = setting["overwrite_policy"]
                    episode = adapter.generate(seed, setting, demos, 4)
                    pairs = episode["train"] + episode["test"]
                    sequences.append([pair["input"] for pair in pairs])
                    for pair_index, pair in enumerate(pairs):
                        actual = execute(policy, pair["input"])
                        if actual != pair["output"]:
                            failures.append({
                                "failure": "Racket/Python mismatch",
                                "seed": seed,
                                "demos": demos,
                                "policy": policy,
                                "pair_index": pair_index,
                            })
                    certificate = adapter.teaching_check(episode)
                    if (certificate["declared_survivors"] != [setting]
                            or certificate["harmful_survivors"]
                            or not all(certificate["query_identifiable"])):
                        failures.append({
                            "failure": "teaching ambiguity",
                            "seed": seed,
                            "demos": demos,
                            "policy": policy,
                            "certificate": certificate,
                        })
                    jobs.append({
                        "seed": seed,
                        "demos": demos,
                        "settings": setting,
                        "labels_checked": len(pairs),
                        "certificate": certificate,
                        "query_facts": [adapter.analyze(pair["input"]) for pair in episode["test"]],
                    })

                    if demos == 3:
                        one = adapter.generate(seed, setting, 3, 1)
                        first = public_challenge_bytes(adapter.model_view(one, 0))
                        for query_index in range(4):
                            view = adapter.model_view(episode, query_index)
                            body = public_challenge_bytes(view)
                            if query_index == 0 and body != first:
                                failures.append({
                                    "failure": "first turn depends on total query count",
                                    "seed": seed,
                                    "policy": policy,
                                })
                            hidden = deepcopy(episode)
                            hidden.update(seed=-1, settings={"private": True}, program_solution="private")
                            for pair in hidden["test"]:
                                pair["output"] = [[9]]
                            if adapter.model_view(hidden, query_index) != view:
                                failures.append({
                                    "failure": "private leakage",
                                    "seed": seed,
                                    "policy": policy,
                                    "query_index": query_index,
                                })
                            pid = public_challenge_id(view)
                            path = public_dir / f"challenge-{pid}.json"
                            if path.exists():
                                failures.append({"failure": "duplicate public payload", "public_id": pid})
                            else:
                                path.write_bytes(body)
                            public_rows.append({
                                "seed": seed,
                                "settings": setting,
                                "query_index": query_index,
                                "public_id": pid,
                                "sha256": hashlib.sha256(body).hexdigest(),
                                "path": path.relative_to(args.out).as_posix(),
                            })

                    if causal is None and seed == 17 and demos == 2 and policy == "longest_path_last":
                        pair = episode["test"][-1]
                        facts = adapter.analyze(pair["input"])
                        counter = adapter.counterfactual_program(setting)
                        counter_out = execute(policy, pair["input"], counter)
                        if counter_out == pair["output"]:
                            failures.append({"failure": "causal ablation unchanged"})
                        causal = {
                            "settings": setting,
                            "program": programs[policy],
                            "input": pair["input"],
                            "output": pair["output"],
                            "intermediate_value": {
                                "path_lengths": facts["path_lengths"],
                                "reading_order": facts["reading_order"],
                                "longest_path_order": facts["longest_path_order"],
                            },
                            "counterfactual_program": counter,
                            "counterfactual_output": counter_out,
                            "ablation": "wrong_intermediate",
                        }
                if sequences[0] != sequences[1]:
                    failures.append({"failure": "setting changed inputs", "seed": seed, "demos": demos})
    finally:
        bridge.shutdown()

    if causal is not None:
        (args.out / "causal-case.json").write_text(json.dumps(causal, indent=2, sort_keys=True) + "\n")
    report = {
        "schema": "b5c887448ed9-native-self-review-v1",
        "task_id": "b5c887448ed9",
        "status": "passed" if not failures else "failed",
        "source_binding": {
            "generator_sha256": sha(ROOT / "generators/b5c887448ed9/generator.py"),
            "adapter_sha256": sha(HOME / "adapter.py"),
            "prototype_sha256": sha(HOME / "prototype.py"),
            "canonical_sha256": sha(HOME / "canonical.rkt"),
        },
        "episodes_checked": len(jobs),
        "label_claims_checked": sum(row["labels_checked"] for row in jobs),
        "distinct_protected_racket_evaluations": len(cache),
        "public_turns_written": len(public_rows),
        "jobs": jobs,
        "public_turns": public_rows,
        "causal_case_path": "causal-case.json" if causal else None,
        "failures": failures,
        "limits": "Finite two-seed, 2/3/6-demo audit against nine executable shortcuts; not a universal uniqueness proof.",
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        key: report[key]
        for key in (
            "status",
            "episodes_checked",
            "label_claims_checked",
            "distinct_protected_racket_evaluations",
            "public_turns_written",
            "failures",
        )
    }, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
