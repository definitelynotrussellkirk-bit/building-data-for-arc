#!/usr/bin/env python3
"""Exhaust cyclic lesson starts and query positions for d4171e13daca.

This task-local authoring probe uses the generator's own rule mirror and
``lesson_identifiable`` contract. The source-bound Racket lesson census remains
the label-authority check; this script cheaply covers more schedule starts and
seed cycles than the shared census currently enumerates.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_ROOT / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "d4171e13daca_rotation_probe_generator", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _profile_key(observed: dict[str, Any]) -> str:
    return "/".join(
        str(observed[name])
        for name in ("frame_count", "layout_style", "outer_margin")
    )


def run(seed_count: int, start_count: int, bands: tuple[str, ...]) -> dict[str, Any]:
    g = _load_generator()
    n_train = int(g.EXAMPLES_NEEDED)
    labeled_pairs = n_train + 1
    production_failures: list[dict[str, Any]] = []
    rotation_failures: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    profile_counts: Counter[str] = Counter()

    for band in bands:
        for seed in range(seed_count):
            last_index = start_count - 1 + labeled_pairs
            cache: dict[int, dict[str, Any]] = {}
            for sample_index in range(last_index):
                grid = g.generate(seed, sample_index, difficulty=band)
                pair = {"input": grid, "output": g.rule_mirror(grid)}
                cache[sample_index] = pair
                unique_inputs.add(_grid_hash(grid))
                profile_counts[_profile_key(g.observe_overrides(grid))] += 1

            for start in range(start_count):
                pairs = [cache[index] for index in range(start, start + labeled_pairs)]
                production_reasons = g.lesson_identifiable(
                    pairs[:n_train], {"input": pairs[-1]["input"]}
                )
                if production_reasons:
                    production_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "query_index": n_train,
                            "reasons": production_reasons,
                        }
                    )

                for query_index, query in enumerate(pairs):
                    demos = [
                        pair
                        for index, pair in enumerate(pairs)
                        if index != query_index
                    ]
                    reasons = g.lesson_identifiable(
                        demos, {"input": query["input"]}
                    )
                    if reasons:
                        rotation_failures.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "accepted_indices": list(
                                    range(start, start + labeled_pairs)
                                ),
                                "profiles": [
                                    g.observe_overrides(pair["input"])
                                    for pair in pairs
                                ],
                                "query_input_sha256": _grid_hash(query["input"]),
                                "reasons": reasons,
                            }
                        )

    production_total = len(bands) * seed_count * start_count
    rotation_total = production_total * labeled_pairs
    source_hash = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    return {
        "schema": "d4171e13daca-query-rotation-probe-v1",
        "task_id": g.TASK_ID,
        "generator_version": g.VERSION,
        "generator_sha256": source_hash,
        "rule_hash": g.RULE_HASH,
        "label_basis": (
            "generator.rule_mirror; selected Racket parity is checked separately "
            "by the battery and source-bound lesson census"
        ),
        "schedule": {
            "n_train": n_train,
            "labeled_pairs_per_window": labeled_pairs,
            "query_policy": "every labeled pair held out once",
            "bands": list(bands),
            "seed_range": [0, seed_count - 1],
            "start_range": [0, start_count - 1],
            "declared_competitors": sorted(g.LESSON_COMPETITORS),
        },
        "counts": {
            "production_windows": production_total,
            "production_failures": len(production_failures),
            "query_rotations": rotation_total,
            "rotation_failures": len(rotation_failures),
            "unique_generated_inputs": len(unique_inputs),
            "profile_counts": dict(sorted(profile_counts.items())),
        },
        "production_failures": production_failures,
        "rotation_failures": rotation_failures,
        "status": (
            "pass"
            if not production_failures and not rotation_failures
            else "fail"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=50)
    parser.add_argument("--starts", type=int, default=10)
    parser.add_argument(
        "--bands", nargs="+", default=["easy", "medium", "hard"]
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seeds < 1 or args.starts < 1:
        parser.error("--seeds and --starts must be positive")

    result = run(args.seeds, args.starts, tuple(args.bands))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["counts"], sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
