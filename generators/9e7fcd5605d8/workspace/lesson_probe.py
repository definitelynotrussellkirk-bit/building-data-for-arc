#!/usr/bin/env python3
"""Deterministic cyclic-query curriculum probe for task 9e7fcd5605d8.

The shared census checks one production query position.  This task-local probe
holds out every member of each five-pair window in turn, so a scheduled lesson
cannot pass only because the distinguishing example happened to be the query.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HOME = Path(__file__).resolve().parents[1]
TASK_ID = HOME.name


def load_generator() -> Any:
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stable_seed(band: str, lesson_index: int) -> int:
    raw = f"cyclic-lesson-probe:v1:{TASK_ID}:{band}:{lesson_index}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:8], 16)


def grid_hash(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def run(per_band: int) -> dict[str, Any]:
    gen = load_generator()
    report: dict[str, Any] = {
        "schema": "arcpuzzles-task-cyclic-lesson-probe-v1",
        "task_id": TASK_ID,
        "per_band": per_band,
        "n_demos": gen.EXAMPLES_NEEDED,
        "n_queries_per_window": gen.EXAMPLES_NEEDED + 1,
        "bands": {},
        "errors": [],
        "limits": [
            "Finite deterministic sampling, not proof of universal induction.",
            "Outputs use the Python rule mirror; the shared source-bound census separately checks the selected Racket authority.",
            "Only declared canonical-fitting rivals are scored.",
        ],
    }

    canonical_shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    rivals = {**canonical_shortcuts, **competitors}
    if not rivals:
        report["errors"].append("no declared rivals")

    all_hashes: set[str] = set()
    for band in ("easy", "medium", "hard"):
        band_errors: list[dict[str, Any]] = []
        rival_refutations = {name: 0 for name in rivals}
        rotation_checks = 0
        for lesson_index in range(per_band):
            seed = stable_seed(band, lesson_index)
            start = lesson_index
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                findings = gen.self_check(grid, difficulty=band)
                if findings:
                    band_errors.append(
                        {
                            "lesson": lesson_index,
                            "sample_index": sample_index,
                            "kind": "self_check",
                            "findings": findings,
                        }
                    )
                all_hashes.add(grid_hash(grid))
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})

            for query_index in range(len(pairs)):
                demos = pairs[:query_index] + pairs[query_index + 1 :]
                query = pairs[query_index]["input"]
                findings = gen.lesson_identifiable(demos, query)
                rotation_checks += 1
                if findings:
                    band_errors.append(
                        {
                            "lesson": lesson_index,
                            "query_index": query_index,
                            "kind": "lesson_identifiable",
                            "findings": findings,
                        }
                    )
                for name, rival in rivals.items():
                    if any(rival(pair["input"]) != pair["output"] for pair in demos):
                        rival_refutations[name] += 1
                    else:
                        band_errors.append(
                            {
                                "lesson": lesson_index,
                                "query_index": query_index,
                                "kind": "rival_survived",
                                "rival": name,
                            }
                        )

        report["bands"][band] = {
            "lessons": per_band,
            "rotation_checks": rotation_checks,
            "rival_refutations": rival_refutations,
            "errors": band_errors,
        }
        report["errors"].extend(
            {"band": band, **error} for error in band_errors
        )

    report["unique_inputs"] = len(all_hashes)
    report["status"] = "pass" if not report["errors"] else "fail"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.per_band <= 0:
        parser.error("--per-band must be positive")
    report = run(args.per_band)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
