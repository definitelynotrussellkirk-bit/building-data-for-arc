"""Bounded adversarial and protected-Racket audit for the copy-policy family."""
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

HERE = Path(__file__).resolve().parent
TASK_ID = "70a3d3e2c975"


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_audit_70a3d3e2c975_prototype"
    cached = sys.modules.get(name)
    if cached is not None and Path(cached.__file__).resolve() == path:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


P = _load_prototype()


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _frozen(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def run_audit(
    *,
    seeds: tuple[int, ...] = (0, 17),
    demo_counts: tuple[int, ...] = (2, 3, 6),
    queries: int = 4,
) -> dict[str, Any]:
    settings = [{"copy_policy": policy} for policy in P.POLICIES]
    programs = {setting["copy_policy"]: P.program(setting) for setting in settings}
    wrapped = {policy: wrap_rule(source) for policy, source in programs.items()}
    findings: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    labels = rival_checks = parity_checks = query_separations = prefix_checks = 0
    witness_case = None

    with RacketBridge(max_calls_before_restart=512) as bridge:
        runtime_identity = bridge.runtime_identity
        evaluations = 0

        def execute(policy: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            evaluations += 1
            return bridge.eval_text(f"({wrapped[policy]} {_grid_literal(grid)})")

        for seed in seeds:
            for demos in demo_counts:
                long_by_policy = {
                    policy: P.generate(seed, {"copy_policy": policy}, demos, queries)
                    for policy in P.POLICIES
                }
                baseline_inputs = [
                    pair["input"]
                    for pair in long_by_policy[P.POLICIES[0]]["train"]
                    + long_by_policy[P.POLICIES[0]]["test"]
                ]
                for policy in P.POLICIES[1:]:
                    if baseline_inputs != [
                        pair["input"]
                        for pair in long_by_policy[policy]["train"]
                        + long_by_policy[policy]["test"]
                    ]:
                        findings.append({"kind": "setting_dependent_inputs", "seed": seed, "demos": demos})
                short = P.generate(seed, {"copy_policy": "all_colors"}, demos, 1)
                prefix_checks += 1
                if short["test"][0]["input"] != long_by_policy["all_colors"]["test"][0]["input"]:
                    findings.append({"kind": "query_prefix_drift", "seed": seed, "demos": demos})

                for policy, episode in long_by_policy.items():
                    survivors = P.setting_survivors(episode["train"])
                    rivals = P.rival_survivors(episode["train"], selected_policy=policy)
                    rival_checks += len(P.RIVALS)
                    if survivors != [policy]:
                        findings.append({"kind": "setting_survivor", "seed": seed, "demos": demos,
                                         "policy": policy, "survivors": survivors})
                    if rivals:
                        findings.append({"kind": "rival_survivor", "seed": seed, "demos": demos,
                                         "policy": policy, "survivors": rivals})
                    pairs = episode["train"] + episode["test"]
                    for pair_index, pair in enumerate(pairs):
                        labels += 1
                        for candidate in P.POLICIES:
                            racket_output = execute(candidate, pair["input"])
                            python_output = P.transform(pair["input"], candidate)
                            parity_checks += 1
                            if racket_output != python_output:
                                findings.append({"kind": "racket_python_mismatch", "seed": seed,
                                                 "demos": demos, "policy": candidate,
                                                 "selected_policy": policy, "pair_index": pair_index})
                        selected = execute(policy, pair["input"])
                        if selected != pair["output"]:
                            findings.append({"kind": "selected_label_mismatch", "seed": seed,
                                             "demos": demos, "policy": policy,
                                             "pair_index": pair_index})
                    for query_index, pair in enumerate(episode["test"]):
                        query_separations += 1
                        outputs = [P.transform(pair["input"], candidate) for candidate in P.POLICIES]
                        if outputs[0] == outputs[1]:
                            findings.append({"kind": "query_not_separating", "seed": seed,
                                             "demos": demos, "policy": policy,
                                             "query_index": query_index})
                    if witness_case is None and seed == seeds[-1] and demos == 3 and policy == "all_colors":
                        pair = episode["test"][-1]
                        witness_case = {
                            "settings": {"copy_policy": policy},
                            "input": pair["input"],
                            "output": pair["output"],
                            "counterfactual_program": programs["rarest_color"],
                            "counterfactual_output": P.transform(pair["input"], "rarest_color"),
                            "dependency": P.dependency(pair["input"], policy),
                        }
                    records.append({
                        "seed": seed,
                        "demos": demos,
                        "queries": queries,
                        "policy": policy,
                        "program_sha256": _sha(programs[policy]),
                        "input_sha256": [_sha(_frozen(pair["input"])) for pair in episode["train"] + episode["test"]],
                        "rival_survivors": rivals,
                    })

    if witness_case is None:
        raise ValueError("audit did not select its retained witness case")
    if witness_case["output"] == witness_case["counterfactual_output"]:
        findings.append({"kind": "counterfactual_unchanged"})
    largest = witness_case["input"]
    summary = {
        "schema": "arcpuzzles-parametric-copy-policy-audit-v1",
        "task_id": TASK_ID,
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries": queries,
        "settings": settings,
        "episodes": len(records),
        "selected_labels": labels,
        "racket_evaluations": evaluations,
        "racket_python_parity_checks": parity_checks,
        "named_rival_checks": rival_checks,
        "query_separation_checks": query_separations,
        "prefix_checks": prefix_checks,
        "largest_query_shape": [len(largest), len(largest[0])],
        "largest_query_source_cells": sum(
            cell not in (0, 9)
            for row in largest
            for cell in row[: len(largest[0]) // 2]
        ),
        "runtime_identity": runtime_identity,
        "program_sha256": {policy: _sha(source) for policy, source in programs.items()},
        "records": records,
        "witness_case": witness_case,
        "findings": findings,
        "status": "passed" if not findings else "findings",
        "limits": (
            "Finite declared-rival and seed/count audit only; it does not prove universal "
            "identifiability or owner acceptance. Width 30 is outside the odd-width axis grammar."
        ),
    }
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError(f"refusing existing output: {args.out}")
    args.out.mkdir(parents=True)
    summary = run_audit()
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (args.out / "witness-case.json").write_text(
        json.dumps(summary["witness_case"], indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({key: summary[key] for key in (
        "status", "episodes", "selected_labels", "racket_evaluations",
        "named_rival_checks", "query_separation_checks", "largest_query_shape", "findings"
    )}, indent=2, sort_keys=True))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
