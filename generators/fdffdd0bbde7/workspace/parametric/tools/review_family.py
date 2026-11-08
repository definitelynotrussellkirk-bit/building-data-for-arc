#!/usr/bin/env python3
"""Bounded census and protected-Racket review for the promoted family.

This is intentionally task-local: future reviewers can rerun one command after
changing the adapter or generator and retain a compact, machine-readable audit.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root


TASK_ID = "fdffdd0bbde7"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / f"generators/{TASK_ID}/workspace/parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
DEFAULT_OUT = PARAMETRIC / "evidence/current/self-review.json"
MODES = ("single_stage", "border_routed_cascade")


def _load_prototype():
    name = "parametric_fdffdd0bbde7_review_source"
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prototype from {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _racket_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(f"({wrap_rule(program)} {_racket_literal(grid)})")


def collect_seed_report(
    prototype: Any,
    *,
    seed: int,
    demo_counts: Iterable[int] = (2, 3, 6),
    query_counts: Iterable[int] = (1, 4),
) -> dict[str, Any]:
    """Audit deterministic generation, teaching, branches, and stress coverage."""
    demo_counts = tuple(demo_counts)
    query_counts = tuple(query_counts)
    report: dict[str, Any] = {
        "seed": seed,
        "combinations": 0,
        "episodes": 0,
        "labeled_pairs_checked": 0,
        "matched_input_instances": 0,
        "distinct_inputs": 0,
        "setting_disagreements": 0,
        "stress_30x30": 0,
        "teaching_failures": [],
        "determinism_failures": [],
        "branch_failures": [],
    }
    all_inputs: set[str] = set()
    for demos in demo_counts:
        for queries in query_counts:
            report["combinations"] += 1
            episodes = {
                mode: prototype.generate_episode(
                    seed, composition=mode, demos=demos, queries=queries
                )
                for mode in MODES
            }
            report["episodes"] += len(episodes)
            for mode, episode in episodes.items():
                rerun = prototype.generate_episode(
                    seed, composition=mode, demos=demos, queries=queries
                )
                if episode != rerun:
                    report["determinism_failures"].append(
                        {"mode": mode, "demos": demos, "queries": queries}
                    )
                report["labeled_pairs_checked"] += len(episode["train"]) + len(episode["test"])

            left = episodes[MODES[0]]
            right = episodes[MODES[1]]
            for split in ("train", "test"):
                left_inputs = [pair["input"] for pair in left[split]]
                right_inputs = [pair["input"] for pair in right[split]]
                if left_inputs != right_inputs:
                    report["determinism_failures"].append(
                        {
                            "kind": "settings_not_input_matched",
                            "split": split,
                            "demos": demos,
                            "queries": queries,
                        }
                    )
                for left_pair, right_pair in zip(left[split], right[split]):
                    report["matched_input_instances"] += 1
                    all_inputs.add(_compact(left_pair["input"]))
                    if left_pair["output"] != right_pair["output"]:
                        report["setting_disagreements"] += 1
                    else:
                        report["teaching_failures"].append(
                            {
                                "kind": "settings_agree",
                                "split": split,
                                "demos": demos,
                                "queries": queries,
                            }
                        )

            for mode in MODES:
                teaching = prototype.assess_demos(left["train"], mode)
                if teaching["declared_setting_survivors"] != [mode] or teaching["shortcut_survivors"]:
                    report["teaching_failures"].append(
                        {
                            "mode": mode,
                            "demos": demos,
                            "queries": queries,
                            "assessment": teaching,
                        }
                    )

            for split in ("train", "test"):
                for index, pair in enumerate(left[split]):
                    counts = prototype.branch_counts(pair["input"])
                    if counts["border"] < 1 or counts["interior"] < 1:
                        report["branch_failures"].append(
                            {
                                "split": split,
                                "index": index,
                                "demos": demos,
                                "queries": queries,
                                "counts": counts,
                            }
                        )
            if queries == 4:
                stress = [
                    pair["input"]
                    for pair in left["test"]
                    if len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                ]
                if len(stress) != 1:
                    report["teaching_failures"].append(
                        {
                            "kind": "missing_unique_30x30_stress",
                            "demos": demos,
                            "queries": queries,
                            "found": len(stress),
                        }
                    )
                else:
                    report["stress_30x30"] += 1
    report["distinct_inputs"] = len(all_inputs)
    return report


def run_racket_review(prototype: Any, seeds: Iterable[int]) -> dict[str, Any]:
    seeds = tuple(seeds)
    calls = 0
    labels = 0
    counterfactuals = 0
    records: list[dict[str, Any]] = []
    if not seeds:
        return {
            "backend": "protected-racket",
            "seeds": [],
            "calls": 0,
            "labels_verified": 0,
            "counterfactual_cases": 0,
            "records": [],
        }
    programs = {mode: prototype.rule_text(mode) for mode in MODES}
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        for seed in seeds:
            for mode in MODES:
                episode = prototype.generate_episode(
                    seed, composition=mode, demos=2, queries=4
                )
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        observed = _execute(bridge, programs[mode], pair["input"])
                        calls += 1
                        labels += 1
                        if observed != pair["output"]:
                            raise AssertionError(
                                f"Racket label mismatch seed={seed} mode={mode} {split}[{index}]"
                            )
                records.append(
                    {
                        "seed": seed,
                        "mode": mode,
                        "program_sha256": _sha256_text(programs[mode]),
                        "labels": 6,
                    }
                )

            grid = prototype.select_inputs(seed, demos=2, queries=4)["train"][0]["input"]
            for case in prototype.causal_cases(grid):
                actual = _execute(bridge, case["program"], grid)
                counterfactual = _execute(bridge, case["counterfactual_program"], grid)
                calls += 2
                counterfactuals += 1
                if actual != case["output"] or counterfactual != case["counterfactual_output"]:
                    raise AssertionError(
                        f"Racket causal replay mismatch seed={seed} ablation={case['ablation']}"
                    )
                if actual == counterfactual:
                    raise AssertionError(
                        f"ineffective causal ablation seed={seed} ablation={case['ablation']}"
                    )
    return {
        "backend": "protected-racket",
        "seeds": list(seeds),
        "calls": calls,
        "labels_verified": labels,
        "counterfactual_cases": counterfactuals,
        "records": records,
    }


def build_review(
    *, seed_start: int = 0, seed_count: int, racket_seeds: Iterable[int]
) -> dict[str, Any]:
    if seed_start < 0:
        raise ValueError("seed_start must be nonnegative")
    if seed_count < 0:
        raise ValueError("seed_count must be nonnegative")
    prototype = _load_prototype()
    seed_reports = [
        collect_seed_report(prototype, seed=seed)
        for seed in range(seed_start, seed_start + seed_count)
    ]
    failures = {
        key: sum(len(report[key]) for report in seed_reports)
        for key in ("teaching_failures", "determinism_failures", "branch_failures")
    }
    if any(failures.values()):
        raise AssertionError(f"bounded family review found failures: {failures}")
    return {
        "schema": "arcpuzzles-task-local-parametric-review-v1",
        "task_id": TASK_ID,
        "prototype_sha256": hashlib.sha256(PROTOTYPE_PATH.read_bytes()).hexdigest(),
        "seed_start": seed_start,
        "seed_count": seed_count,
        "demo_counts": [2, 3, 6],
        "query_counts": [1, 4],
        "totals": {
            "combinations": sum(row["combinations"] for row in seed_reports),
            "episodes": sum(row["episodes"] for row in seed_reports),
            "labeled_pairs_checked": sum(row["labeled_pairs_checked"] for row in seed_reports),
            "matched_input_instances": sum(row["matched_input_instances"] for row in seed_reports),
            "setting_disagreements": sum(row["setting_disagreements"] for row in seed_reports),
            "stress_30x30": sum(row["stress_30x30"] for row in seed_reports),
            "failure_counts": failures,
        },
        "seed_reports": seed_reports,
        "racket": run_racket_review(prototype, tuple(racket_seeds)),
    }


def display_path(path: Path) -> str:
    """Return a stable repo-relative display path when possible."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_log(path: Path, review: dict[str, Any]) -> None:
    totals = review["totals"]
    racket = review["racket"]
    lines = [
        f"task={review['task_id']}",
        f"prototype_sha256={review['prototype_sha256']}",
        f"seed_start={review['seed_start']}",
        f"seed_count={review['seed_count']}",
        f"combinations={totals['combinations']}",
        f"episodes={totals['episodes']}",
        f"labeled_pairs_checked={totals['labeled_pairs_checked']}",
        f"matched_input_instances={totals['matched_input_instances']}",
        f"setting_disagreements={totals['setting_disagreements']}",
        f"stress_30x30={totals['stress_30x30']}",
        f"failure_counts={_compact(totals['failure_counts'])}",
        f"racket_calls={racket['calls']}",
        f"racket_labels_verified={racket['labels_verified']}",
        f"racket_counterfactual_cases={racket['counterfactual_cases']}",
        "status=pass",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=20)
    parser.add_argument("--racket-seeds", default="0,17")
    args = parser.parse_args(argv)
    racket_seeds = tuple(int(value) for value in args.racket_seeds.split(",") if value)
    review = build_review(
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        racket_seeds=racket_seeds,
    )
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_log(out.with_suffix(".log"), review)
    print(
        json.dumps(
            {
                "status": "pass",
                "out": display_path(out),
                "totals": review["totals"],
                "racket": {
                    key: review["racket"][key]
                    for key in ("calls", "labels_verified", "counterfactual_cases")
                },
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
