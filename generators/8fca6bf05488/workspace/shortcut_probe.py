#!/usr/bin/env python3
"""Reproducible lesson-level shortcut probe for ARC task 8fca6bf05488.

The probe intentionally imports rival declarations from the selected generator
instead of carrying a second rival-name list.  It checks two different facts:

1. every declared canonical shortcut really does fit every canonical pair; and
2. every generated four-demo lesson refutes any rival that would change its
   query answer.

Run from anywhere in the packet:
    python3 repo/generators/8fca6bf05488/workspace/shortcut_probe.py \
      --starts 16 --seeds 17 808 5150 --assert-clean \
      --out checks/shortcut-probe.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

TASK_ID = "8fca6bf05488"
HERE = Path(__file__).resolve()
TASK_DIR = HERE.parent.parent
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))


def load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"shortcut_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_canonical_pairs() -> list[dict[str, Any]]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                test = row["test"]
                return row["train"] + (test if isinstance(test, list) else [test])
    raise RuntimeError(f"canonical task {TASK_ID} not found in {path}")


def different_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [
        [row, column]
        for row, (left_row, right_row) in enumerate(zip(left, right))
        for column, (a, b) in enumerate(zip(left_row, right_row))
        if a != b
    ]


def source_sha256() -> str:
    return hashlib.sha256((TASK_DIR / "generator.py").read_bytes()).hexdigest()


def run_probe(starts: int, seeds: list[int]) -> dict[str, Any]:
    generator = load_generator()
    canonical_pairs = load_canonical_pairs()
    competitors: dict[str, Callable] = dict(generator.LESSON_COMPETITORS)
    shortcuts: dict[str, Callable] = dict(generator.CANONICAL_SHORTCUTS)

    canonical_fit: dict[str, Any] = {}
    for name, rival in shortcuts.items():
        mismatches = [
            index
            for index, pair in enumerate(canonical_pairs)
            if rival(pair["input"]) != pair["output"]
        ]
        canonical_fit[name] = {
            "pairs": len(canonical_pairs),
            "fits": len(canonical_pairs) - len(mismatches),
            "mismatch_indices": mismatches,
        }

    lessons: list[dict[str, Any]] = []
    status_counts: dict[str, Counter] = defaultdict(Counter)
    profile_counts: dict[str, Counter] = defaultdict(Counter)
    witness_by_rival: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []

    for band in ("easy", "medium", "hard"):
        for seed in seeds:
            for start in range(starts):
                demos = []
                profiles = []
                for sample_index in range(start, start + generator.EXAMPLES_NEEDED):
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    profile = generator.semantic_observables(grid)["profile"]
                    profiles.append(profile)
                    profile_counts[band][profile] += 1
                    demos.append({"input": grid, "output": generator.rule_mirror(grid)})

                query_input = generator.generate(
                    seed,
                    start + generator.EXAMPLES_NEEDED,
                    difficulty=band,
                )
                query_truth = generator.rule_mirror(query_input)
                ambiguous = []
                rival_status = {}
                for name, rival in competitors.items():
                    matching_demo_indices = [
                        index
                        for index, pair in enumerate(demos)
                        if rival(pair["input"]) == pair["output"]
                    ]
                    survives = len(matching_demo_indices) == len(demos)
                    rival_query = rival(query_input)
                    changes_query = rival_query != query_truth
                    if survives and changes_query:
                        status = "ambiguous"
                        ambiguous.append(name)
                    elif survives:
                        status = "survives_same_query"
                    else:
                        status = "refuted_by_demo"
                    status_counts[band][status] += 1
                    rival_status[name] = status

                    if name not in witness_by_rival:
                        for index, pair in enumerate(demos):
                            rival_output = rival(pair["input"])
                            diff = different_cells(rival_output, pair["output"])
                            if diff:
                                witness_by_rival[name] = {
                                    "band": band,
                                    "seed": seed,
                                    "lesson_start": start,
                                    "demo_offset": index,
                                    "sample_index": start + index,
                                    "profile": profiles[index],
                                    "different_cells": diff,
                                }
                                break

                coverage_ok = set(profiles) == set(generator.SCHEDULE_PROFILES)
                hook_reasons = generator.lesson_identifiable(demos, {"input": query_input})
                record = {
                    "band": band,
                    "seed": seed,
                    "start": start,
                    "profiles": profiles,
                    "coverage_ok": coverage_ok,
                    "ambiguous_rivals": ambiguous,
                    "hook_reasons": hook_reasons,
                    "rival_status": rival_status,
                }
                lessons.append(record)
                if not coverage_ok or ambiguous or hook_reasons:
                    failures.append(record)

    missing_witnesses = sorted(set(competitors) - set(witness_by_rival))
    shortcut_fit_failures = sorted(
        name for name, result in canonical_fit.items() if result["mismatch_indices"]
    )
    return {
        "schema": "8fca6bf05488-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha256(),
        "rule_hash": generator.RULE_HASH,
        "sampler": {
            "bands": ["easy", "medium", "hard"],
            "seeds": seeds,
            "starts_per_seed_band": starts,
            "examples_needed": generator.EXAMPLES_NEEDED,
            "lesson_policy": "four consecutive demos followed by the next sample as query",
        },
        "canonical_pairs": len(canonical_pairs),
        "canonical_shortcut_fit": canonical_fit,
        "lesson_count": len(lessons),
        "profile_counts": {band: dict(counts) for band, counts in profile_counts.items()},
        "rival_status_counts": {band: dict(counts) for band, counts in status_counts.items()},
        "witness_by_rival": witness_by_rival,
        "missing_witnesses": missing_witnesses,
        "shortcut_fit_failures": shortcut_fit_failures,
        "failure_count": len(failures),
        "failures": failures,
        "status": "pass" if not failures and not missing_witnesses and not shortcut_fit_failures else "fail",
        "limits": [
            "Finite declared-rival probe; it is not a proof of unique induction.",
            "Python rule mirror parity is separately pinned against all canonical pairs and the Racket authority gate.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=16)
    parser.add_argument("--seeds", type=int, nargs="+", default=[17, 808, 5150])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--assert-clean", action="store_true")
    args = parser.parse_args()
    if args.starts < 1:
        parser.error("--starts must be positive")

    report = run_probe(args.starts, args.seeds)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "status": report["status"],
                "lessons": report["lesson_count"],
                "failures": report["failure_count"],
                "generator_sha256": report["generator_sha256"],
                "out": str(args.out) if args.out else None,
            },
            sort_keys=True,
        )
    )
    return 1 if args.assert_clean and report["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
