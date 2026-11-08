"""Protected-Racket audit for the native frame-selection metric family."""
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
TASK_ID = "75be7448827f"


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_audit_75be7448827f_prototype"
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
    settings = [{"selection_metric": metric} for metric in P.METRICS]
    programs = {metric: P.program({"selection_metric": metric}) for metric in P.METRICS}
    wrapped = {metric: wrap_rule(source) for metric, source in programs.items()}
    findings: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    labels = rival_checks = parity_checks = query_separations = prefix_checks = 0
    witness_case = None

    with RacketBridge(max_calls_before_restart=512) as bridge:
        runtime_identity = bridge.runtime_identity
        evaluations = 0

        def execute(metric: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal evaluations
            evaluations += 1
            return bridge.eval_text(f"({wrapped[metric]} {_grid_literal(grid)})")

        for seed in seeds:
            for demos in demo_counts:
                long_by_metric = {
                    metric: P.generate(seed, {"selection_metric": metric}, demos, queries)
                    for metric in P.METRICS
                }
                baseline_inputs = [
                    pair["input"]
                    for pair in long_by_metric[P.METRICS[0]]["train"]
                    + long_by_metric[P.METRICS[0]]["test"]
                ]
                for metric in P.METRICS[1:]:
                    if baseline_inputs != [
                        pair["input"]
                        for pair in long_by_metric[metric]["train"]
                        + long_by_metric[metric]["test"]
                    ]:
                        findings.append({"kind": "setting_dependent_inputs", "seed": seed, "demos": demos})
                short = P.generate(seed, {"selection_metric": "raw_count"}, demos, 1)
                prefix_checks += 1
                if short["test"][0]["input"] != long_by_metric["raw_count"]["test"][0]["input"]:
                    findings.append({"kind": "query_prefix_drift", "seed": seed, "demos": demos})

                for metric, episode in long_by_metric.items():
                    survivors = P.setting_survivors(episode["train"])
                    rivals = P.rival_survivors(episode["train"], selected_metric=metric)
                    rival_checks += len(P.RIVALS)
                    if survivors != [metric]:
                        findings.append({
                            "kind": "setting_survivor", "seed": seed, "demos": demos,
                            "metric": metric, "survivors": survivors,
                        })
                    if rivals:
                        findings.append({
                            "kind": "rival_survivor", "seed": seed, "demos": demos,
                            "metric": metric, "survivors": rivals,
                        })
                    pairs = episode["train"] + episode["test"]
                    for pair_index, pair in enumerate(pairs):
                        labels += 1
                        for candidate in P.METRICS:
                            racket_output = execute(candidate, pair["input"])
                            python_output = P.transform(pair["input"], candidate)
                            parity_checks += 1
                            if racket_output != python_output:
                                findings.append({
                                    "kind": "racket_python_mismatch", "seed": seed,
                                    "demos": demos, "metric": candidate,
                                    "selected_metric": metric, "pair_index": pair_index,
                                })
                        selected = execute(metric, pair["input"])
                        if selected != pair["output"]:
                            findings.append({
                                "kind": "selected_label_mismatch", "seed": seed,
                                "demos": demos, "metric": metric, "pair_index": pair_index,
                            })
                    for query_index, pair in enumerate(episode["test"]):
                        query_separations += 1
                        outputs = [P.transform(pair["input"], candidate) for candidate in P.METRICS]
                        if outputs[0] == outputs[1]:
                            findings.append({
                                "kind": "query_not_separating", "seed": seed,
                                "demos": demos, "metric": metric,
                                "query_index": query_index,
                            })
                    if witness_case is None and seed == seeds[-1] and demos == 3 and metric == "raw_count":
                        pair = episode["test"][-1]
                        witness_case = {
                            "settings": {"selection_metric": metric},
                            "input": pair["input"],
                            "output": pair["output"],
                            "counterfactual_program": programs["occupied_density"],
                            "counterfactual_output": P.transform(pair["input"], "occupied_density"),
                            "dependency": P.dependency(pair["input"], metric),
                        }
                    records.append({
                        "seed": seed,
                        "demos": demos,
                        "queries": queries,
                        "metric": metric,
                        "program_sha256": _sha(programs[metric]),
                        "input_sha256": [
                            _sha(_frozen(pair["input"]))
                            for pair in episode["train"] + episode["test"]
                        ],
                        "rival_survivors": rivals,
                    })

    if witness_case is None:
        raise ValueError("audit did not select its retained witness case")
    if witness_case["output"] == witness_case["counterfactual_output"]:
        findings.append({"kind": "counterfactual_unchanged"})
    largest = witness_case["input"]
    frames = P.parse_frames(largest)
    summary = {
        "schema": "arcpuzzles-parametric-selection-metric-audit-v1",
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
        "largest_query_nonzero_cells": sum(cell != 0 for row in largest for cell in row),
        "largest_query_frame_metrics": [
            {"bbox": frame["bbox"], "count": frame["count"], "area": frame["area"]}
            for frame in frames
        ],
        "runtime_identity": runtime_identity,
        "program_sha256": {metric: _sha(source) for metric, source in programs.items()},
        "records": records,
        "witness_case": witness_case,
        "findings": findings,
        "status": "passed" if not findings else "findings",
        "limits": (
            "Finite declared-rival and seed/count audit only; it does not prove universal "
            "identifiability, generalization, owner acceptance, or training admission."
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
