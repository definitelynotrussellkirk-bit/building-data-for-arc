#!/usr/bin/env python3
"""Cheap source-bound support census; does not generate reference labels.

Run through review.py run. Canonical authoring data is read for profile counts;
do not run during a visible-only solve. The shared lesson-census remains the
authority-backed check of complete lessons and query rotations.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "17f92e205b34"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--per-band", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band <= 0 or args.out.exists():
        parser.error("per-band must be positive and output must be new")
    root = find_root(__file__)
    paths = [root / "generators" / TASK_ID / "generator.py",
             root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"]
    source = next(path for path in paths if path.is_file())
    spec = importlib.util.spec_from_file_location("reflection_distribution_probe", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    profiles = {(len(pair["input"]), len(pair["input"][0]),
                 len({v for row in pair["input"] for v in row}))
                for pair in canonical_pairs(TASK_ID, root=root)}
    report = {"schema": "reflection-support-census-v1", "task_id": TASK_ID,
              "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "rule_hash": generator.RULE_HASH, "seed": args.seed,
              "sample_indices": [0, args.per_band - 1], "per_band": {},
              "scope": "Input support only; no reference execution or lesson correctness claim.",
              "failures": []}
    for band in ("easy", "medium", "hard"):
        histograms = {name: Counter() for name in generator.AXES}
        directions, witnesses = Counter(), Counter()
        unique = set()
        exact = 0
        for index in range(args.per_band):
            grid = generator.generate(args.seed, index, difficulty=band)
            errors = generator.self_check(grid)
            if errors:
                report["failures"].append({"difficulty": band, "sample_index": index,
                                           "input": grid, "errors": errors})
            for key, value in generator.observe_overrides(grid).items():
                histograms[key][value] += 1
            upper = any(v and r < c for r, row in enumerate(grid) for c, v in enumerate(row))
            lower = any(v and r > c for r, row in enumerate(grid) for c, v in enumerate(row))
            directions["mixed" if upper and lower else "upper_only" if upper else "lower_only"] += 1
            for name, predicate in generator.SEMANTIC_WITNESSES.items():
                witnesses[name] += bool(predicate(grid))
            unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            exact += (len(grid), len(grid[0]), len({v for row in grid for v in row})) in profiles
        report["per_band"][band] = {"draws": args.per_band, "unique_inputs": len(unique),
                                     "canonical_profile_hits": exact,
                                     "directions": dict(directions), "witnesses": dict(witnesses),
                                     "axis_histograms": {k: dict(sorted(v.items())) for k, v in histograms.items()}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"generator_sha256": report["generator_sha256"],
                      "draws": args.per_band * 3, "failures": len(report["failures"]),
                      "out": str(args.out)}))
    return bool(report["failures"])


if __name__ == "__main__":
    raise SystemExit(main())
